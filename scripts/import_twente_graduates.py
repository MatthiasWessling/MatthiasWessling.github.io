#!/usr/bin/env python3
"""
Import Twente PhD graduates from a local thesis PDF folder into graduates.csv.

For each PDF:
  1) Extract title/author/date/ISBN from the title pages (PyMuPDF)
  2) Resolve a University of Twente Pure record via ISBN→DOI, Crossref title
     search, or optional seed URL
  3) Extract Pure metadata (DOI, PDF link, abstract) when available
  4) Append a Twente row to graduates.csv and write data/twente_match_report.json

Excludes:
  - 1993_Wessling.pdf (own thesis)
  - *_compress.pdf duplicates

Usage:
  python scripts/import_twente_graduates.py
  python scripts/import_twente_graduates.py --write-csv
  python scripts/import_twente_graduates.py --write-csv --import-md --overwrite
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import fitz  # PyMuPDF

sys.path.insert(0, str(Path(__file__).resolve().parent))
from extract_rwth_record import short_webpage_summary  # noqa: E402
from extract_ut_record import extract_ut_metadata, fetch_html  # noqa: E402
from import_graduates_from_csv import import_rows, slugify  # noqa: E402


DEFAULT_PDF_DIR = (
    "/Users/matthiaswessling/Library/Mobile Documents/"
    "com~apple~CloudDocs/iCloud Downloads/PhD/Twente Thesis Supervised"
)
DEFAULT_CSV = "data/graduates.csv"
DEFAULT_REPORT = "data/twente_match_report.json"
DEFAULT_CACHE = "data/ut_cache"
DEFAULT_MD_DIR = "data/ut_markdown"
MAILTO = "pub.nachweis@ub.rwth-aachen.de"
USER_AGENT = f"twente-graduates/1.0 (mailto:{MAILTO})"

CSV_FIELDS = [
    "name",
    "graduate_date",
    "thesis_title",
    "topics",
    "institution",
    "record_url",
    "doi",
    "thesis_pdf",
    "linkedin",
    "orcid",
    "image",
    "summary",
]

SKIP_BASENAMES = {
    "1993_Wessling.pdf",
    "2009_Papenburg_compress.pdf",
}

MONTHS = {
    "january": 1,
    "januari": 1,
    "february": 2,
    "februari": 2,
    "march": 3,
    "maart": 3,
    "april": 4,
    "may": 5,
    "mei": 5,
    "june": 6,
    "juni": 6,
    "july": 7,
    "juli": 7,
    "august": 8,
    "augustus": 8,
    "september": 9,
    "october": 10,
    "oktober": 10,
    "november": 11,
    "december": 12,
}

SEED_URLS: Dict[str, str] = {
    "2001_Krause": "https://research.utwente.nl/en/publications/polymer-nanofoams/",
    "2006_Visser": (
        "https://research.utwente.nl/en/publications/"
        "mixed-gas-plasticization-phenomena-in-asymmetric-membranes-2/"
    ),
    "2009_Papenburg": (
        "https://research.utwente.nl/en/publications/"
        "design-strategies-for-tissue-engineering-scaffolds/"
    ),
    "2016 A IJzer": (
        "https://research.utwente.nl/en/publications/"
        "adsorption-materials-for-the-recovery-and-separation-of-biobased-/"
    ),
}

# Scanned/OCR-broken PDFs where front-matter title extraction fails.
TITLE_OVERRIDES: Dict[str, str] = {
    "1996_Wijers": (
        "Supported liquid membranes for removal of heavy metals: "
        "permeability, selectivity and stability"
    ),
    "1998_Vegt van der": (
        "Molecular dynamics simulations of sorption and diffusion "
        "in rubbery and glassy polymers"
    ),
}

NAME_OVERRIDES: Dict[str, str] = {
    "1996_Bos": "Aaltje Bos",
    "1996_Wijers": "Marie Christiana Wijers",
    "1997_Krol": "J.J. Krol",
    "1998_Vegt van der": "Nico F.A. van der Vegt",
    "2000_Nauta": "Warner Jan Nauta",
    "2002_Geeter de": "L. de Geeter",
    "2003_Nijmeijer": "Kitty Nijmeijer",
}


def http_get_json(url: str, timeout: int = 30) -> Dict[str, Any]:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.load(resp)


def resolve_doi_to_url(doi: str) -> str:
    doi = (doi or "").strip()
    if not doi:
        return ""
    target = doi if doi.startswith("http") else f"https://doi.org/{doi}"
    req = urllib.request.Request(
        target,
        headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
            "Accept": "text/html",
        },
    )
    with urllib.request.urlopen(req, timeout=40) as resp:
        return resp.geturl()


def parse_filename(path: Path) -> Dict[str, str]:
    stem = path.stem
    year = ""
    m = re.match(r"^(\d{4})[_\s]+(.+)$", stem)
    if m:
        year = m.group(1)
    return {"stem": stem, "year": year, "filename": path.name}


def inventory_pdfs(pdf_dir: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for path in sorted(pdf_dir.glob("*.pdf")):
        if path.name in SKIP_BASENAMES or path.name.lower().endswith("_compress.pdf"):
            continue
        meta = parse_filename(path)
        meta["pdf_path"] = str(path)
        rows.append(meta)
    return rows


def normalize_spaces(text: str) -> str:
    text = text.replace("\u00a0", " ")
    return re.sub(r"[ \t]+", " ", text)


def extract_pdf_front_matter(pdf_path: Path, max_pages: int = 6) -> Dict[str, Any]:
    doc = fitz.open(pdf_path)
    pages: List[str] = []
    for i in range(min(max_pages, doc.page_count)):
        pages.append(normalize_spaces(doc.load_page(i).get_text("text")))
    doc.close()
    text = "\n".join(pages)
    compact = re.sub(r"\n{2,}", "\n", text)

    title = ""
    # English dissertation marker
    m = re.search(
        r"^(?P<title>.+?)\n+\s*(?:DISSERTATION|PROEFSCHRIFT)\b",
        compact,
        flags=re.I | re.S | re.M,
    )
    if m:
        title = re.sub(r"\s+", " ", m.group("title")).strip(" \n\t-–")
    if not title:
        # First substantial block before "ter verkrijging" / "to obtain"
        m = re.search(
            r"^(?P<title>.+?)\n+\s*(?:ter verkrijging|to obtain)\b",
            compact,
            flags=re.I | re.S | re.M,
        )
        if m:
            title = re.sub(r"\s+", " ", m.group("title")).strip()
    # Drop committee junk if accidentally captured
    title = re.split(r"\bGraduation committee\b", title, maxsplit=1, flags=re.I)[0]
    title = re.sub(r"\s+", " ", title).strip(" \n\t-–:")
    if len(title) > 220:
        title = title[:220].rsplit(" ", 1)[0]

    author = ""
    m = re.search(
        r"(?:door|by)\s*\n+\s*([A-ZÀ-Ü][^\n]{2,80})",
        compact,
        flags=re.I,
    )
    if m:
        author = re.sub(r"\s+", " ", m.group(1)).strip()
        author = re.split(r"\b(?:geboren|born)\b", author, maxsplit=1, flags=re.I)[0].strip()
    if not author:
        m = re.search(
            r"\n([A-Z][A-Za-zÀ-ü'’\-]+(?:\s+[A-Z][A-Za-zÀ-ü'’\-]+){0,4})\s*\n+\s*(?:born|geboren)\b",
            compact,
            flags=re.I,
        )
        if m:
            author = re.sub(r"\s+", " ", m.group(1)).strip()

    graduate_date = ""
    # Dutch: op vrijdag 13 december 1996
    m = re.search(
        r"\bop\s+(?:maandag|dinsdag|woensdag|donderdag|vrijdag|zaterdag|zondag)?\s*"
        r"(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})",
        compact,
        flags=re.I,
    )
    if not m:
        # English: on Wednesday 18th of November 2009 / on Friday 13 December 1996
        m = re.search(
            r"\bon\s+(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)?\s*"
            r"(\d{1,2})(?:st|nd|rd|th)?\s+(?:of\s+)?([A-Za-z]+)\s+(\d{4})",
            compact,
            flags=re.I,
        )
    if m:
        day = int(m.group(1))
        month = MONTHS.get(m.group(2).lower(), 0)
        year = int(m.group(3))
        if month:
            graduate_date = f"{year:04d}-{month:02d}-{day:02d}"

    isbn = ""
    m = re.search(r"ISBN[:\s]*([0-9][0-9\- ]{8,})", compact, flags=re.I)
    if m:
        isbn = re.sub(r"[^0-9Xx]", "", m.group(1))

    mentions_wessling = bool(re.search(r"\bWessling\b", compact, flags=re.I))

    doi_guess = ""
    if isbn:
        digits = re.sub(r"[^0-9Xx]", "", isbn)
        if digits.startswith("978") and len(digits) >= 13:
            doi_guess = f"10.3990/1.{digits[:13]}"
        elif digits.startswith("90") and len(digits) >= 10:
            # Convert ISBN-10 style Dutch numbers to ISBN-13 used in UT DOIs.
            doi_guess = f"10.3990/1.978{digits[:10]}"
        elif len(digits) >= 10:
            doi_guess = f"10.3990/1.{digits}"

    return {
        "title": title,
        "author": author,
        "graduate_date": graduate_date,
        "isbn": isbn,
        "doi_guess": doi_guess,
        "mentions_wessling": mentions_wessling,
        "text_sample": compact[:1200],
    }


def surname_from_stem(stem: str) -> str:
    rest = re.sub(r"^\d{4}[_\s]+", "", stem)
    rest = re.sub(r"(?i)\bthesis\b", "", rest).strip(" _-")
    # Prefer last significant token ("Vegt van der" -> Vegt)
    parts = [p for p in re.split(r"[\s_]+", rest) if p]
    particles = {"van", "der", "de", "den", "a", "h", "s", "m"}
    significant = [p for p in parts if p.lower() not in particles]
    return significant[-1] if significant else (parts[-1] if parts else rest)


def clean_thesis_title(title: str, author: str = "") -> str:
    """Remove cover blurbs / duplicated OCR titles from PDF front matter."""
    t = re.sub(r"\s+", " ", (title or "")).strip(" -–:")
    if not t:
        return ""
    # Cut marketing/cover text.
    t = re.split(
        r"\b(?:Cover|The research|This work|Contents|Graduation committee|©|Copyright)\b",
        t,
        maxsplit=1,
        flags=re.I,
    )[0].strip(" -–:")
    # Remove trailing author name if present.
    if author:
        author_l = author.strip()
        if author_l and author_l.lower() in t.lower():
            idx = t.lower().find(author_l.lower())
            if idx > 12:
                t = t[:idx].strip(" -–:")
    # Detect duplicated half: "FOO BAR FOO BAR"
    words = t.split()
    if len(words) >= 8 and len(words) % 2 == 0:
        mid = len(words) // 2
        if [w.lower() for w in words[:mid]] == [w.lower() for w in words[mid:]]:
            t = " ".join(words[:mid])
    # Heuristic: if title continues into subtitle-ish lowercase author residue
    t = re.split(r"\bMembrane Technology Group\b", t, maxsplit=1, flags=re.I)[0].strip()
    t = re.split(r"\bMembrane Development and\b", t, maxsplit=1, flags=re.I)[0].strip()
    # Title-case all-caps short titles
    if t.isupper() and len(t) > 8:
        t = t.title()
        for acr in ("CO2", "CH4", "N2", "O2", "RED", "NMR", "DSC", "MD"):
            t = re.sub(rf"\b{acr.title()}\b", acr, t)
            t = re.sub(rf"\b{acr.lower()}\b", acr, t, flags=re.I)
    # Prefer nicer casing for known phrase starts
    if t and t[0].islower():
        t = t[0].upper() + t[1:]
    return t.strip(" -–:")


def crossref_by_title(
    title: str,
    *,
    surname: str,
    pause: float,
) -> Optional[Dict[str, Any]]:
    title = clean_thesis_title(title)
    if not title or len(title) < 12:
        return None
    params = {
        "query.bibliographic": title,
        "rows": "8",
        "mailto": MAILTO,
    }
    if surname:
        params["query.author"] = surname
    url = "https://api.crossref.org/works?" + urllib.parse.urlencode(params)
    try:
        data = http_get_json(url)
    except urllib.error.HTTPError as exc:
        if exc.code == 429:
            time.sleep(max(pause * 4, 8))
            data = http_get_json(url)
        else:
            raise
    time.sleep(pause)
    title_l = re.sub(r"[^a-z0-9]+", " ", title.lower())
    title_tokens = {t for t in title_l.split() if len(t) > 2}
    surname_l = (surname or "").lower()
    best: Optional[Tuple[int, Dict[str, Any]]] = None
    for it in data.get("message", {}).get("items", []):
        cand = " ".join(it.get("title") or [])
        cand_l = re.sub(r"[^a-z0-9]+", " ", cand.lower())
        cand_tokens = {t for t in cand_l.split() if len(t) > 2}
        if not cand_tokens or not title_tokens:
            continue
        overlap = len(title_tokens & cand_tokens) / max(len(title_tokens), 1)
        authors = " ".join(
            f"{a.get('given', '')} {a.get('family', '')}".lower()
            for a in (it.get("author") or [])
        )
        doi = (it.get("DOI") or "").lower()
        work_type = (it.get("type") or "").lower()
        score = int(overlap * 10)
        if work_type == "dissertation":
            score += 5
        elif "10.3990/" not in doi:
            # Avoid linking journal papers as the thesis record.
            score -= 8
        if "10.3990/" in doi:
            score += 5
        if surname_l and surname_l in authors:
            score += 5
        elif surname_l:
            score -= 6
        if overlap < 0.55 and "10.3990/" not in doi:
            continue
        if overlap < 0.4:
            continue
        if best is None or score > best[0]:
            best = (score, it)
    if not best or best[0] < 10:
        return None
    it = best[1]
    doi = it.get("DOI") or ""
    if "10.3990/" not in doi.lower() and (it.get("type") or "") != "dissertation":
        return None
    return {
        "title": " ".join(it.get("title") or []),
        "doi": doi,
        "score": best[0],
        "type": it.get("type") or "",
    }


def topics_from_title(title: str) -> str:
    if not title:
        return ""
    candidates = [
        ("gas diffusion", "gas diffusion electrodes"),
        ("co2", "CO2 reduction"),
        ("membrane", "membranes"),
        ("electrochem", "electrochemistry"),
        ("hydrogen", "hydrogen"),
        ("fuel cell", "fuel cells"),
        ("porous", "porous media"),
        ("tissue", "tissue engineering"),
        ("scaffold", "tissue engineering"),
        ("electrodialysis", "ion-exchange membranes"),
        ("ion exchange", "ion-exchange membranes"),
        ("ion-exchange", "ion-exchange membranes"),
        ("nanofiltration", "filtration"),
        ("ultrafiltration", "filtration"),
        ("filtration", "filtration"),
        ("gas separation", "gas separation"),
        ("plasticiz", "gas separation"),
        ("hollow fiber", "hollow fiber membranes"),
        ("polymer", "polymers"),
        ("adsorption", "membranes"),
        ("chromatography", "membranes"),
        ("microfluidic", "microfluidics"),
        ("fouling", "fouling"),
        ("facilitated transport", "membranes"),
        ("pervaporation", "membranes"),
    ]
    lower = title.lower()
    found: List[str] = []
    for needle, label in candidates:
        if needle in lower and label not in found:
            found.append(label)
        if len(found) >= 4:
            break
    return "; ".join(found)


def load_csv(path: Path) -> Tuple[List[str], List[Dict[str, str]]]:
    with path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        fields = list(reader.fieldnames or [])
        rows = [dict(r) for r in reader]
    for f in CSV_FIELDS:
        if f not in fields:
            fields.append(f)
    for r in rows:
        for f in CSV_FIELDS:
            r.setdefault(f, "")
        if not (r.get("institution") or "").strip():
            r["institution"] = "RWTH"
        if not (r.get("record_url") or "").strip() and (r.get("rwth_url") or "").strip():
            r["record_url"] = r["rwth_url"]
    return fields, rows


def write_csv(path: Path, rows: List[Dict[str, str]]) -> None:
    rows_sorted = sorted(
        rows,
        key=lambda r: (r.get("graduate_date") or "", r.get("name") or ""),
        reverse=True,
    )
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows_sorted)


def cache_abstract_markdown(md_dir: Path, record_url: str, meta: Dict[str, Any]) -> None:
    md_dir.mkdir(parents=True, exist_ok=True)
    slug = slugify(
        Path(urllib.parse.urlparse(record_url).path).name or meta.get("author") or "thesis"
    )
    path = md_dir / f"{slug}.md"
    body = [
        f"# {meta.get('title') or ''}",
        "",
        f"Author: {meta.get('author') or ''}",
        f"Record: {record_url}",
        f"DOI: {meta.get('doi') or ''}",
        "",
        "## Abstract",
        "",
        meta.get("abstract") or "_No abstract._",
        "",
    ]
    path.write_text("\n".join(body), encoding="utf-8")


def try_pure_from_doi(doi: str, *, pause: float) -> str:
    if not doi:
        return ""
    try:
        resolved = resolve_doi_to_url(doi)
        time.sleep(pause)
    except Exception:
        return ""
    if "research.utwente.nl/en/publications/" in resolved:
        return resolved.rstrip("/") + "/"
    return ""


def resolve_candidate(
    item: Dict[str, Any],
    *,
    pause: float,
    cache_dir: Path,
) -> Dict[str, Any]:
    stem = item["stem"]
    report: Dict[str, Any] = {
        "stem": stem,
        "filename": item["filename"],
        "year": item["year"],
        "status": "needs_manual",
        "record_url": "",
        "doi": "",
        "notes": [],
    }

    pdf_meta = extract_pdf_front_matter(Path(item["pdf_path"]))
    if stem in TITLE_OVERRIDES:
        pdf_meta["title"] = TITLE_OVERRIDES[stem]
        report["notes"].append("title_override")
    if stem in NAME_OVERRIDES:
        # Prefer canonical display names for OCR-broken / legal-name variants.
        pdf_meta["author"] = NAME_OVERRIDES[stem]
        report["notes"].append("name_override")

    report["pdf"] = {
        "title": pdf_meta.get("title"),
        "author": pdf_meta.get("author"),
        "graduate_date": pdf_meta.get("graduate_date"),
        "isbn": pdf_meta.get("isbn"),
        "doi_guess": pdf_meta.get("doi_guess"),
        "mentions_wessling": pdf_meta.get("mentions_wessling"),
    }

    surname = surname_from_stem(stem)
    pure_url = SEED_URLS.get(stem, "")
    if pure_url:
        report["notes"].append("seed_url")

    doi = ""
    if not pure_url and pdf_meta.get("doi_guess"):
        doi = pdf_meta["doi_guess"]
        pure_url = try_pure_from_doi(doi, pause=pause)
        if pure_url:
            report["notes"].append("isbn_doi_resolved")
        else:
            report["notes"].append("isbn_doi_miss")

    if not pure_url and pdf_meta.get("title"):
        try:
            xref = crossref_by_title(
                pdf_meta["title"], surname=surname, pause=pause
            )
        except Exception as exc:  # noqa: BLE001
            xref = None
            report["notes"].append(f"crossref_error:{exc}")
        if xref and xref.get("doi"):
            report["notes"].append(f"crossref_score:{xref.get('score')}")
            doi = xref["doi"]
            pure_url = try_pure_from_doi(doi, pause=pause)
            if pure_url:
                report["notes"].append("crossref_doi_resolved")

    meta: Dict[str, Any] = {}
    if pure_url:
        if "/publications/" in pure_url and not pure_url.endswith("/"):
            pure_url += "/"
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_key = slugify(Path(urllib.parse.urlparse(pure_url).path).name) or "page"
        cache_file = cache_dir / f"{cache_key}.html"
        try:
            if cache_file.is_file() and cache_file.stat().st_size > 1000:
                html_body = cache_file.read_text(encoding="utf-8", errors="replace")
            else:
                html_body = fetch_html(pure_url)
                cache_file.write_text(html_body, encoding="utf-8")
                time.sleep(pause)
            meta = extract_ut_metadata(pure_url, html_body=html_body)
            # Reject Pure hits whose author clearly does not match filename surname.
            pure_author = (meta.get("author") or "").lower()
            if surname and surname.lower() not in pure_author.replace("ł", "l").replace("ø", "o"):
                # Allow diacritic-insensitive contains for Dlugolecki etc.
                norm_author = (
                    pure_author.encode("ascii", "ignore").decode("ascii").lower()
                )
                norm_surname = (
                    surname.encode("ascii", "ignore").decode("ascii").lower()
                )
                if norm_surname not in norm_author:
                    report["notes"].append(
                        f"author_mismatch:{meta.get('author')}!={surname}"
                    )
                    pure_url = ""
                    meta = {}
                    report["record_url"] = ""
                    report["status"] = "needs_manual"
            if meta:
                report["record_url"] = pure_url
                doi = meta.get("doi") or doi
                report["doi"] = doi
                if meta.get("mentions_wessling") or pdf_meta.get("mentions_wessling"):
                    report["status"] = "matched"
                else:
                    report["status"] = "matched_unverified_supervisor"
                    report["notes"].append("no_wessling_mention")
                report["extracted"] = {
                    "title": meta.get("title"),
                    "author": meta.get("author"),
                    "graduate_date": meta.get("graduate_date"),
                    "thesis_pdf": meta.get("thesis_pdf"),
                    "has_abstract": bool(meta.get("abstract")),
                }
        except Exception as exc:  # noqa: BLE001
            report["notes"].append(f"extract_error:{exc}")
            report["status"] = "needs_manual"
            meta = {}

    # Prefer Pure author/title; fall back to PDF front matter.
    name = (meta.get("author") or pdf_meta.get("author") or stem).strip()
    if stem in NAME_OVERRIDES:
        name = NAME_OVERRIDES[stem]
    title = clean_thesis_title(
        meta.get("title") or pdf_meta.get("title") or "",
        author=name,
    )
    graduate_date = (
        meta.get("graduate_date")
        or pdf_meta.get("graduate_date")
        or (f"{item['year']}-01-01" if item.get("year") else "")
    ).strip()
    thesis_pdf = (meta.get("thesis_pdf") or "").strip()
    doi = (meta.get("doi") or doi or "").strip()
    # Drop non-UT DOIs when we have no Pure record (e.g. accidental journal hit).
    if not report.get("record_url") and doi and "10.3990/" not in doi:
        doi = ""
    summary = short_webpage_summary(meta.get("abstract") or "")
    topics = topics_from_title(title)

    if report["status"] == "needs_manual" and title and name:
        # Still import as a local-PDF-backed entry without repository link.
        report["status"] = "imported_from_pdf_only"
        report["notes"].append("no_pure_record")

    csv_row = {
        "name": name,
        "graduate_date": graduate_date,
        "thesis_title": title,
        "topics": topics,
        "institution": "Twente",
        "record_url": report.get("record_url") or "",
        "doi": doi if report.get("record_url") or doi.startswith("10.3990/") else doi,
        "thesis_pdf": thesis_pdf,
        "linkedin": "",
        "orcid": "",
        "image": "",
        "summary": summary,
    }
    # Only keep DOI if it looks real / resolved; drop failed isbn guesses without Pure.
    if not report.get("record_url") and doi and not thesis_pdf:
        # Keep ISBN-based DOI anyway — doi.org may still resolve later.
        pass

    report["csv_row"] = csv_row
    if meta:
        report["abstract"] = meta.get("abstract") or ""
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Import Twente PhD graduates into graduates.csv from local PDFs."
    )
    parser.add_argument("--pdf-dir", default=DEFAULT_PDF_DIR)
    parser.add_argument("--csv", default=DEFAULT_CSV)
    parser.add_argument("--report", default=DEFAULT_REPORT)
    parser.add_argument("--cache-dir", default=DEFAULT_CACHE)
    parser.add_argument("--markdown-dir", default=DEFAULT_MD_DIR)
    parser.add_argument("--pause", type=float, default=0.6)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--write-csv", action="store_true")
    parser.add_argument("--import-md", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repo = Path(__file__).resolve().parents[1]
    pdf_dir = Path(args.pdf_dir)
    csv_path = Path(args.csv)
    report_path = Path(args.report)
    cache_dir = Path(args.cache_dir)
    md_dir = Path(args.markdown_dir)
    if not csv_path.is_absolute():
        csv_path = repo / csv_path
    if not report_path.is_absolute():
        report_path = repo / report_path
    if not cache_dir.is_absolute():
        cache_dir = repo / cache_dir
    if not md_dir.is_absolute():
        md_dir = repo / md_dir

    if not pdf_dir.is_dir():
        raise SystemExit(f"PDF directory not found: {pdf_dir}")

    items = inventory_pdfs(pdf_dir)
    if args.limit:
        items = items[: args.limit]
    print(f"Inventory: {len(items)} Twente theses (after exclusions)")

    reports: List[Dict[str, Any]] = []
    for i, item in enumerate(items, start=1):
        print(f"[{i}/{len(items)}] {item['filename']}")
        report = resolve_candidate(item, pause=args.pause, cache_dir=cache_dir)
        title = (report.get("extracted") or {}).get("title") or report["csv_row"].get(
            "thesis_title"
        )
        print(
            f"  -> {report['status']}: {report.get('record_url') or '(no url)'} | {title}"
        )
        if report.get("abstract") and report.get("record_url"):
            cache_abstract_markdown(
                md_dir,
                report["record_url"],
                {
                    "title": report["csv_row"]["thesis_title"],
                    "author": report["csv_row"]["name"],
                    "doi": report["csv_row"]["doi"],
                    "abstract": report["abstract"],
                },
            )
        reports.append(report)

    matched = sum(1 for r in reports if str(r["status"]).startswith("matched"))
    pdf_only = sum(1 for r in reports if r["status"] == "imported_from_pdf_only")
    manual = sum(1 for r in reports if r["status"] == "needs_manual")
    summary = {
        "total": len(reports),
        "matched": matched,
        "imported_from_pdf_only": pdf_only,
        "needs_manual": manual,
        "with_pdf_link": sum(1 for r in reports if r["csv_row"].get("thesis_pdf")),
        "with_doi": sum(1 for r in reports if r["csv_row"].get("doi")),
        "items": [],
    }
    slim_items = []
    for r in reports:
        slim = dict(r)
        if "abstract" in slim:
            slim["abstract_chars"] = len(slim.pop("abstract") or "")
        slim_items.append(slim)
    summary["items"] = slim_items
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(
        f"Report: {report_path} matched={matched} pdf_only={pdf_only} "
        f"needs_manual={manual} pdf_links={summary['with_pdf_link']}"
    )

    if not args.write_csv:
        print("Pass --write-csv to append into graduates.csv")
        return

    _fields, existing = load_csv(csv_path)
    kept = [r for r in existing if (r.get("institution") or "").strip() != "Twente"]
    twente_rows = [r["csv_row"] for r in reports]
    existing_slugs = {slugify(r.get("name") or "") for r in kept}
    for row in twente_rows:
        slug = slugify(row["name"])
        if slug in existing_slugs:
            row["name"] = f"{row['name']} (Twente)"
        existing_slugs.add(slugify(row["name"]))

    merged = kept + twente_rows
    if args.dry_run:
        print(f"Dry-run: would write {len(merged)} CSV rows ({len(twente_rows)} Twente)")
        return

    write_csv(csv_path, merged)
    print(f"Wrote {csv_path} ({len(kept)} RWTH + {len(twente_rows)} Twente)")

    if args.import_md:
        out_dir = repo / "content" / "graduates"
        import_rows(
            csv_path,
            out_dir,
            overwrite=args.overwrite,
            dry_run=False,
        )


if __name__ == "__main__":
    main()
