#!/usr/bin/env python3
"""
Scrape RWTH Publications PhD theses linked to Wessling and build graduates.csv.

Uses the public search:
  https://publications.rwth-aachen.de/search?ln=de&cc=PhDThesis&sc=1&p=Wessling+Dissertation

Only imports theses where Wessling is the *first* Thesis advisor
(excludes second-examiner / co-advisor-only cases).

Usage:
  python scripts/scrape_rwth_wessling_graduates.py
  python scripts/scrape_rwth_wessling_graduates.py --dry-run
  python scripts/scrape_rwth_wessling_graduates.py --skip-enrich
  python scripts/scrape_rwth_wessling_graduates.py --import-md --overwrite
"""

from __future__ import annotations

import argparse
import csv
import html as htmlmod
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Allow importing sibling modules when run as a script.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from extract_rwth_record import extract_rwth_metadata  # noqa: E402
from import_graduates_from_csv import import_rows, slugify  # noqa: E402


SEARCH_URL = (
    "https://publications.rwth-aachen.de/search"
    "?ln=de&cc=PhDThesis&sc=1&p=Wessling+Dissertation&rg=100"
)
DEFAULT_CSV = "data/graduates.csv"
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
)
CSV_FIELDS = [
    "name",
    "graduate_date",
    "thesis_title",
    "topics",
    "rwth_url",
    "doi",
    "thesis_pdf",
    "linkedin",
    "image",
    "summary",
]


def fetch_html(url: str, timeout: int = 60) -> str:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Cookie": "APP_INIT=1",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        encoding = resp.headers.get_content_charset() or "utf-8"
        return resp.read().decode(encoding, errors="replace")


def clean_title(raw: str) -> str:
    title = htmlmod.unescape(re.sub(r"<[^>]+>", "", raw))
    title = re.sub(r"\s+", " ", title).strip()
    # Drop German parallel title after " = "
    if " = " in title:
        title = title.split(" = ", 1)[0].strip()
    return title


def normalize_person_name(author: str) -> str:
    """Convert 'Lastname, Firstname' / 'Last, F.' to 'Firstname Lastname'."""
    cleaned = re.sub(r"\s+", " ", author).strip()
    if "," not in cleaned:
        return cleaned
    last, first = [part.strip() for part in cleaned.split(",", 1)]
    if not first:
        return cleaned
    return f"{first} {last}".strip()


def is_wessling_name(name: str) -> bool:
    return "wessling" in name.lower()


def parse_search_page(page_html: str) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for m in re.finditer(
        r'<a[^>]+href="[^"]*?/record/(\d+)"[^>]*>\s*<b>(.*?)</b>\s*</a>(.*?)</td>',
        page_html,
        re.S | re.I,
    ):
        record_id, title_html, rest = m.group(1), m.group(2), m.group(3)
        people: List[Tuple[str, str]] = []
        for am in re.finditer(
            r'itemprop="name">(.*?)</span>(.{0,120})', rest, re.S
        ):
            name = htmlmod.unescape(am.group(1)).strip()
            tail = am.group(2)
            role_m = re.search(r"roleDsp[^>]*>\s*\(([^)]+)\)", tail)
            role = role_m.group(1).strip() if role_m else ""
            people.append((name, role))

        author = people[0][0] if people else ""
        advisors = [n for n, role in people if "advisor" in role.lower()]
        doi_m = re.search(r"(10\.18154/[A-Za-z0-9.\-_/]+)", rest) or re.search(
            r"(10\.\d{4,9}/[A-Za-z0-9.\-_/]+)", rest
        )
        year_m = re.search(
            r"Dissertation[^<]{0,120}?((?:20\d{2})(?:\s*&\s*20\d{2})?)", rest
        )
        year = ""
        if year_m:
            years = re.findall(r"20\d{2}", year_m.group(1))
            year = years[-1] if years else ""

        rows.append(
            {
                "record_id": record_id,
                "thesis_title": clean_title(title_html),
                "author_raw": author,
                "advisors": advisors,
                "doi": doi_m.group(1) if doi_m else "",
                "year": year,
                "rwth_url": f"https://publications.rwth-aachen.de/record/{record_id}",
            }
        )
    return rows


def scrape_search_results() -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Return (included_first_advisor, excluded_second_examiner)."""
    all_rows: List[Dict[str, Any]] = []
    seen: set[str] = set()
    jrec = 1
    while True:
        url = f"{SEARCH_URL}&jrec={jrec}"
        page_html = fetch_html(url)
        page_rows = parse_search_page(page_html)
        if not page_rows:
            break
        new_count = 0
        for row in page_rows:
            rid = row["record_id"]
            if rid in seen:
                continue
            seen.add(rid)
            all_rows.append(row)
            new_count += 1
        if new_count == 0:
            break
        if len(page_rows) < 100:
            break
        jrec += 100
        time.sleep(0.35)

    included: List[Dict[str, Any]] = []
    excluded: List[Dict[str, Any]] = []
    for row in all_rows:
        advisors = row.get("advisors") or []
        if advisors and is_wessling_name(advisors[0]):
            included.append(row)
        else:
            excluded.append(row)
    return included, excluded


def topics_from_title(title: str) -> str:
    """Light keyword hints from the thesis title (semicolon-separated)."""
    if not title:
        return ""
    candidates = [
        ("gas diffusion", "gas diffusion electrodes"),
        ("co2", "CO2 reduction"),
        ("co₂", "CO2 reduction"),
        ("membrane", "membranes"),
        ("electrochem", "electrochemistry"),
        ("hydrogen", "hydrogen"),
        ("fuel cell", "fuel cells"),
        ("porous", "porous media"),
        ("wetting", "wettability"),
        ("wettability", "wettability"),
        ("bipolar", "bipolar membranes"),
        ("hollow fiber", "hollow fiber membranes"),
        ("nanofiber", "nanofibers"),
        ("battery", "batteries"),
        ("desalination", "desalination"),
        ("filtration", "filtration"),
        ("polymer", "polymers"),
        ("catalys", "catalysis"),
        ("simulation", "simulation"),
        ("modeling", "modeling"),
        ("modelling", "modeling"),
    ]
    lower = title.lower()
    found: List[str] = []
    for needle, label in candidates:
        if needle in lower and label not in found:
            found.append(label)
        if len(found) >= 4:
            break
    return "; ".join(found)


def enrich_record(row: Dict[str, Any]) -> Dict[str, Any]:
    """Fetch record page for full name, date, PDF when available."""
    enriched = dict(row)
    try:
        meta = extract_rwth_metadata(row["rwth_url"])
    except (urllib.error.URLError, TimeoutError, ValueError) as exc:
        enriched["enrich_error"] = str(exc)
        return enriched

    author = meta.get("author") or row.get("author_raw") or ""
    enriched["name"] = normalize_person_name(author) if author else ""
    enriched["thesis_title"] = meta.get("thesis_title") or row.get("thesis_title") or ""
    if " = " in enriched["thesis_title"]:
        enriched["thesis_title"] = enriched["thesis_title"].split(" = ", 1)[0].strip()
    enriched["doi"] = meta.get("doi") or row.get("doi") or ""
    enriched["thesis_pdf"] = meta.get("pdf_url") or ""
    graduate_date = meta.get("graduate_date") or ""
    if not graduate_date and (meta.get("year") or row.get("year")):
        year = str(meta.get("year") or row.get("year"))
        graduate_date = f"{year}-01-01"
    enriched["graduate_date"] = graduate_date
    enriched["topics"] = topics_from_title(enriched["thesis_title"])
    return enriched


def load_existing_csv(path: Path) -> Dict[str, Dict[str, str]]:
    """Index existing CSV rows by slug for preserving image/linkedin/etc."""
    if not path.is_file():
        return {}
    by_slug: Dict[str, Dict[str, str]] = {}
    with path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            name = (row.get("name") or "").strip()
            if not name:
                continue
            by_slug[slugify(name)] = row
    return by_slug


def merge_preserve(
    scraped: Dict[str, str], existing: Optional[Dict[str, str]]
) -> Dict[str, str]:
    out = dict(scraped)
    if not existing:
        return out
    for key in ("linkedin", "image", "summary", "topics"):
        old = (existing.get(key) or "").strip()
        new = (out.get(key) or "").strip()
        if old and (not new or key in {"linkedin", "image", "summary"}):
            # Prefer curated local fields; keep scraped topics if empty locally
            if key == "topics" and new:
                continue
            out[key] = old
    return out


def to_csv_row(row: Dict[str, Any]) -> Dict[str, str]:
    name = (row.get("name") or normalize_person_name(row.get("author_raw") or "")).strip()
    graduate_date = (row.get("graduate_date") or "").strip()
    if not graduate_date and row.get("year"):
        graduate_date = f"{row['year']}-01-01"
    thesis_title = (row.get("thesis_title") or "").strip()
    return {
        "name": name,
        "graduate_date": graduate_date,
        "thesis_title": thesis_title,
        "topics": (row.get("topics") or topics_from_title(thesis_title)).strip(),
        "rwth_url": (row.get("rwth_url") or "").strip(),
        "doi": (row.get("doi") or "").strip(),
        "thesis_pdf": (row.get("thesis_pdf") or "").strip(),
        "linkedin": (row.get("linkedin") or "").strip(),
        "image": (row.get("image") or "").strip(),
        "summary": (row.get("summary") or "").strip(),
    }


def write_csv(path: Path, rows: List[Dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    # Newest first
    rows_sorted = sorted(
        rows,
        key=lambda r: (r.get("graduate_date") or "", r.get("name") or ""),
        reverse=True,
    )
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rows_sorted)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Scrape RWTH Wessling PhD theses; keep only first-advisor cases."
        )
    )
    parser.add_argument(
        "--csv",
        default=DEFAULT_CSV,
        help=f"Output CSV path (default: {DEFAULT_CSV})",
    )
    parser.add_argument(
        "--skip-enrich",
        action="store_true",
        help="Do not fetch individual record pages (faster, leaner fields)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print summary only; do not write CSV",
    )
    parser.add_argument(
        "--import-md",
        action="store_true",
        help="Also run import_graduates_from_csv after writing CSV",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="With --import-md, overwrite existing graduate markdown files",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Optional limit on included records (for testing)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repo_root = Path(__file__).resolve().parents[1]
    csv_path = Path(args.csv)
    if not csv_path.is_absolute():
        csv_path = repo_root / csv_path

    print("Fetching RWTH search results…")
    included, excluded = scrape_search_results()
    print(f"Search hits: {len(included) + len(excluded)}")
    print(f"  First advisor Wessling (include): {len(included)}")
    print(f"  Second examiner / other (exclude): {len(excluded)}")

    excluded_path = csv_path.with_name("graduates_excluded_second_examiner.csv")
    if not args.dry_run:
        excl_rows = [
            {
                "name": normalize_person_name(r.get("author_raw") or ""),
                "thesis_title": r.get("thesis_title") or "",
                "first_advisor": (r.get("advisors") or [""])[0],
                "advisors": "; ".join(r.get("advisors") or []),
                "rwth_url": r.get("rwth_url") or "",
                "doi": r.get("doi") or "",
                "year": r.get("year") or "",
            }
            for r in excluded
        ]
        excluded_path.parent.mkdir(parents=True, exist_ok=True)
        with excluded_path.open("w", newline="", encoding="utf-8") as fh:
            fields = [
                "name",
                "thesis_title",
                "first_advisor",
                "advisors",
                "rwth_url",
                "doi",
                "year",
            ]
            writer = csv.DictWriter(fh, fieldnames=fields)
            writer.writeheader()
            writer.writerows(excl_rows)
        print(f"Wrote excluded list: {excluded_path}")

    if args.limit and args.limit > 0:
        included = included[: args.limit]
        print(f"Limited to first {len(included)} included records")

    existing = load_existing_csv(csv_path)
    csv_rows: List[Dict[str, str]] = []

    for i, row in enumerate(included, start=1):
        if args.skip_enrich:
            row["name"] = normalize_person_name(row.get("author_raw") or "")
            row["topics"] = topics_from_title(row.get("thesis_title") or "")
            if row.get("year") and not row.get("graduate_date"):
                row["graduate_date"] = f"{row['year']}-01-01"
        else:
            print(f"[{i}/{len(included)}] Enrich {row['rwth_url']}")
            row = enrich_record(row)
            time.sleep(0.6)

        csv_row = to_csv_row(row)
        if not csv_row["name"]:
            print(f"  skip (no name): {row.get('rwth_url')}")
            continue
        slug = slugify(csv_row["name"])
        # Also try matching abbreviated existing names by record URL
        matched = existing.get(slug)
        if not matched:
            for ex in existing.values():
                if (ex.get("rwth_url") or "").rstrip("/") == csv_row["rwth_url"].rstrip("/"):
                    matched = ex
                    break
        csv_row = merge_preserve(csv_row, matched)
        csv_rows.append(csv_row)

    print(f"CSV rows ready: {len(csv_rows)}")
    if args.dry_run:
        for row in csv_rows[:10]:
            print(
                f"  - {row['name']} | {row['graduate_date']} | {row['thesis_title'][:60]}"
            )
        if len(csv_rows) > 10:
            print(f"  … and {len(csv_rows) - 10} more")
        print("Dry-run: CSV not written")
        return

    write_csv(csv_path, csv_rows)
    print(f"Wrote {csv_path}")

    if args.import_md:
        out_dir = repo_root / "content" / "graduates"
        import_rows(
            csv_path,
            out_dir,
            overwrite=args.overwrite,
            dry_run=False,
        )


if __name__ == "__main__":
    main()
