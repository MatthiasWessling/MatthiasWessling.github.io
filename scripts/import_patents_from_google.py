#!/usr/bin/env python3
"""
Import Patents entries from Google Patents XHR JSON into content/patents-products/.

Pipeline:
  1. Merge inventor search JSON dumps under data/google_patents_xhr/
  2. Deduplicate patent families (priority date + title similarity)
  3. Download drawing figures to themes/custom/static/images/patents/<slug>/
  4. Write Hugo markdown with summary, topics, organization, and meta fields

Usage:
  python scripts/import_patents_from_google.py
  python scripts/import_patents_from_google.py --dry-run
  python scripts/import_patents_from_google.py --overwrite
  python scripts/import_patents_from_google.py --skip-images
  python scripts/import_patents_from_google.py --limit 5
"""

from __future__ import annotations

import argparse
import html
import json
import re
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_XHR_DIR = ROOT / "data" / "google_patents_xhr"
DEFAULT_OUT_DIR = ROOT / "content" / "patents-products"
DEFAULT_IMAGE_ROOT = ROOT / "themes" / "custom" / "static" / "images" / "patents"
IMAGE_CDN = "https://patentimages.storage.googleapis.com"

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)

# Curated pages that should not be overwritten by the importer.
PRESERVE_SLUGS = {
    "method-producing-pvdf-membrane-reactor",
}

# Publication numbers already covered by curated pages (skip generating a sibling).
PRESERVE_FAMILY_PUBS = {
    "WO2024023237A1",
    "EP4561744A1",
    "DE102022118981A1",
}

ORG_RULES: Sequence[Tuple[str, str]] = (
    (r"rwth|rheinisch[- ]westf", "RWTH"),
    (r"dwi|leibniz.*interaktiv|wollforschung", "DWI"),
    (r"twente|universiteit twente|universit[aä]t twente|univ twente", "Twente"),
    (r"gambro", "Gambro"),
    (r"sartorius", "Sartorius"),
    (r"magneto", "Magneto"),
    (r"akzo", "Akzo Nobel"),
    (r"membrane technology and research|\bmtr\b", "MTR"),
    (r"norit", "Norit"),
    (r"nx filtration", "NX Filtration"),
    (r"fumatech|fuma[- ]tech", "FUMATECH"),
    (r"evonik", "Evonik"),
    (r"wetsus", "Wetsus"),
    (r"mosaic", "Mosaic"),
    (r"aquamarijn", "Aquamarijn"),
    (r"neokidney", "Neokidney"),
    (r"\btno\b|toegepast[- ].*onderzoek", "TNO"),
    (r"xolo", "XOLO"),
    (r"stichting voor de technische wetenschappen", "STW"),
)

TOPIC_RULES: Sequence[Tuple[str, str]] = (
    (r"hollow[- ]?fib|microtube|hollow fibre", "hollow fiber membranes"),
    (r"hydrogel|flow lithograph", "hydrogels"),
    (r"polyelectrolyte|pec membrane", "polyelectrolyte membranes"),
    (r"desalin|capacitive deionization|flow[- ]electrode|fcdi", "desalination"),
    (r"gas separation|gas[- ]permeab|vapor recovery", "gas separation"),
    (r"fuel cell|redox flow|electro[- ]?catalyst|hydrogen compressor|electrode arrangement", "electrochemistry"),
    (r"pedot|conductive polymer", "conductive polymers"),
    (r"hemodial|anticoagulant|blood|extracorporeal", "medical membranes"),
    (r"ultrafilt|microfilt|nanofilt|filter device|fouling", "filtration"),
    (r"additive manufacture|laser sinter|3d print", "additive manufacturing"),
    (r"membrane reactor|polyvinylidene|pvdf", "membrane reactors"),
    (r"ion[- ]permeab|ion exchange", "ion-exchange membranes"),
    (r"spinneret|membrane system", "membrane fabrication"),
    (r"stirring|gas[- ]introduction|gassing", "gas-liquid reactors"),
    (r"membrane", "membranes"),
    (r"polymer", "polymers"),
)


@dataclass
class PatentRecord:
    publication_number: str
    title: str
    inventor: str
    assignee: str
    priority_date: str
    filing_date: str
    publication_date: str
    grant_date: str
    language: str
    snippet: str
    google_patents_url: str
    family_country_status: str
    thumbnail_path: str = ""
    pdf_path: str = ""
    figures: List[Dict[str, str]] = field(default_factory=list)
    siblings: List[str] = field(default_factory=list)

    @property
    def sort_date(self) -> str:
        return self.priority_date or self.publication_date or self.filing_date or "0000-00-00"


def clean_text(value: Optional[str]) -> str:
    if not value:
        return ""
    text = html.unescape(value)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text.replace("\u2026", "...")


def slugify(value: str) -> str:
    value = value.lower().strip()
    replacements = {
        "ä": "ae",
        "ö": "oe",
        "ü": "ue",
        "ß": "ss",
    }
    for src, dst in replacements.items():
        value = value.replace(src, dst)
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-{2,}", "-", value).strip("-")
    return value[:72] or "patent"


def toml_string(value: str) -> str:
    escaped = (
        (value or "")
        .replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", " ")
        .replace("\r", " ")
        .replace("\t", " ")
        .strip()
    )
    return f'"{escaped}"'


def title_case_safe(title: str) -> str:
    title = clean_text(title)
    if not title:
        return "Untitled patent"
    # Keep all-caps short acronyms; otherwise sentence-case-ish.
    if title.isupper() and len(title) > 12:
        title = title.capitalize()
        # Capitalize words after colons / separators lightly
        title = re.sub(r"([:]\s*)([a-z])", lambda m: m.group(1) + m.group(2).upper(), title)
    if title and title[0].islower():
        title = title[0].upper() + title[1:]
    return title


def pub_preference(pub: str) -> Tuple[int, str]:
    p = (pub or "").upper()
    if p.startswith("WO"):
        score = 0
    elif p.startswith("EP") and p.endswith(("B1", "B2")):
        score = 1
    elif p.startswith("US") and re.search(r"B\d$", p):
        score = 2
    elif p.startswith("EP") and p.endswith("C0"):
        score = 5
    elif p.startswith("EP"):
        score = 3
    elif p.startswith("US"):
        score = 4
    elif p.startswith("DE") and not re.search(r"D\d$", p):
        score = 6
    elif p.startswith("NL"):
        score = 7
    else:
        score = 9
    # Prefer granted / substantive over pure translation kinds.
    if re.search(r"^(ATE|CY\d|ES\d)", p) or re.search(r"(D\d|T\d)$", p):
        score += 20
    return score, p


def stem_token(tok: str) -> str:
    if tok.endswith("ies") and len(tok) > 4:
        return tok[:-3] + "y"
    if tok.endswith("sses"):
        return tok[:-2]
    if tok.endswith("s") and not tok.endswith("ss") and len(tok) > 3:
        return tok[:-1]
    return tok


def title_tokens(title: str) -> Set[str]:
    stop = {
        "method",
        "process",
        "for",
        "the",
        "a",
        "an",
        "of",
        "and",
        "to",
        "in",
        "with",
        "by",
        "its",
        "thereof",
        "their",
        "use",
        "using",
        "having",
        "comprising",
        "production",
        "producing",
        "preparation",
        "preparing",
        "manufacture",
        "manufacturing",
        "device",
        "apparatus",
        "system",
        "fibre",
        "fiber",
    }
    tokens = set()
    for tok in re.findall(r"[a-z0-9]+", (title or "").lower()):
        if tok in {"fibre", "fiber"}:
            tokens.add("fiber")
            continue
        if tok in stop or len(tok) <= 2:
            continue
        tokens.add(stem_token(tok))
    return tokens


def similar_titles(a: str, b: str, *, threshold: float = 0.42) -> bool:
    ta, tb = title_tokens(a), title_tokens(b)
    if not ta or not tb:
        return False
    return (len(ta & tb) / len(ta | tb)) >= threshold


def family_status(patent: Dict[str, Any]) -> str:
    family = (
        patent.get("family_metadata", {})
        .get("aggregated", {})
        .get("country_status", [])
    )
    parts = []
    for entry in family:
        code = entry.get("country_code") or ""
        state = (entry.get("best_patent_stage") or {}).get("state") or ""
        if code:
            parts.append(f"{code}={state}" if state else code)
    return ";".join(parts)


def load_xhr_records(xhr_dir: Path) -> Dict[str, PatentRecord]:
    records: Dict[str, PatentRecord] = {}
    files = sorted(xhr_dir.glob("*.json"))
    if not files:
        raise FileNotFoundError(f"No Google Patents JSON dumps in {xhr_dir}")

    for path in files:
        data = json.loads(path.read_text(encoding="utf-8"))
        clusters = (data.get("results") or {}).get("cluster") or []
        for cluster in clusters:
            for item in cluster.get("result") or []:
                patent = item.get("patent") or {}
                pub = patent.get("publication_number") or ""
                if not pub:
                    continue
                patent_id = item.get("id") or ""
                url = (
                    f"https://patents.google.com/{patent_id}"
                    if patent_id
                    else f"https://patents.google.com/patent/{pub}"
                )
                rec = PatentRecord(
                    publication_number=pub,
                    title=clean_text(patent.get("title")),
                    inventor=clean_text(patent.get("inventor")),
                    assignee=clean_text(patent.get("assignee")),
                    priority_date=patent.get("priority_date") or "",
                    filing_date=patent.get("filing_date") or "",
                    publication_date=patent.get("publication_date") or "",
                    grant_date=patent.get("grant_date") or "",
                    language=patent.get("language") or "",
                    snippet=clean_text(patent.get("snippet")),
                    google_patents_url=url,
                    family_country_status=family_status(patent),
                    thumbnail_path=patent.get("thumbnail") or "",
                    pdf_path=patent.get("pdf") or "",
                    figures=list(patent.get("figures") or []),
                )
                # Prefer the copy that has figures / PDF / richer metadata.
                prev = records.get(pub)
                if prev is None:
                    records[pub] = rec
                else:
                    score = (len(rec.figures), 1 if rec.pdf_path else 0, len(rec.snippet))
                    prev_score = (len(prev.figures), 1 if prev.pdf_path else 0, len(prev.snippet))
                    if score > prev_score:
                        records[pub] = rec
    return records


def choose_representatives(records: Iterable[PatentRecord]) -> List[PatentRecord]:
    items = sorted(
        records,
        key=lambda r: (r.priority_date or "0000", pub_preference(r.publication_number), r.publication_number),
    )
    groups: List[List[PatentRecord]] = []
    for rec in items:
        placed = False
        for group in groups:
            head = group[0]
            if rec.priority_date and rec.priority_date == head.priority_date and similar_titles(
                rec.title, head.title
            ):
                group.append(rec)
                placed = True
                break
        if not placed:
            groups.append([rec])

    reps: List[PatentRecord] = []
    for group in groups:
        group_sorted = sorted(group, key=lambda r: pub_preference(r.publication_number))
        rep = group_sorted[0]
        rep.siblings = [g.publication_number for g in group_sorted[1:]]
        # Prefer figure-rich / PDF-rich sibling metadata on the representative.
        best_figs = rep
        for cand in group_sorted:
            cand_valid = sum(
                1
                for fig in cand.figures
                if is_cdn_rel_path((fig or {}).get("full") or (fig or {}).get("thumbnail") or "")
            )
            best_valid = sum(
                1
                for fig in best_figs.figures
                if is_cdn_rel_path((fig or {}).get("full") or (fig or {}).get("thumbnail") or "")
            )
            if cand_valid > best_valid or (
                cand_valid == best_valid and cand.pdf_path and not best_figs.pdf_path
            ):
                best_figs = cand
            if len(cand.snippet) > len(rep.snippet):
                rep.snippet = cand.snippet
            if len(cand.inventor) > len(rep.inventor):
                rep.inventor = cand.inventor
            if len(cand.assignee) > len(rep.assignee):
                rep.assignee = cand.assignee
        rep.figures = best_figs.figures
        rep.thumbnail_path = best_figs.thumbnail_path or rep.thumbnail_path
        rep.pdf_path = best_figs.pdf_path or rep.pdf_path
        reps.append(rep)

    reps.sort(key=lambda r: r.sort_date, reverse=True)
    return reps


def normalize_organization(assignee: str) -> str:
    text = (assignee or "").lower()
    for pattern, label in ORG_RULES:
        if re.search(pattern, text, flags=re.I):
            return label
    if not assignee:
        return "Other"
    # Truncate messy long assignee strings into a short label.
    short = re.split(r"[,;/]", assignee)[0].strip()
    short = re.sub(r"\s+", " ", short)
    return short[:40] if short else "Other"


def infer_topics(title: str, snippet: str) -> List[str]:
    blob = f"{title} {snippet}".lower()
    topics: List[str] = []
    for pattern, label in TOPIC_RULES:
        if re.search(pattern, blob, flags=re.I) and label not in topics:
            topics.append(label)
    return topics[:5]


def infer_status(rec: PatentRecord) -> str:
    pub = rec.publication_number.upper()
    if rec.grant_date or re.search(r"B\d$", pub):
        return "Granted"
    if pub.startswith("WO") or re.search(r"A\d?$", pub):
        fam = rec.family_country_status.upper()
        if "ACTIVE" in fam:
            return "Published / family active"
        return "Published application"
    if "ACTIVE" in (rec.family_country_status or "").upper():
        return "Active family member"
    return "Published"


def parse_inventors(raw: str) -> List[str]:
    if not raw:
        return []
    # Google often returns a single bolded inventor in search cards.
    parts = re.split(r"\s*;\s*|\s+and\s+", raw)
    names = [clean_text(p) for p in parts if clean_text(p)]
    # Ensure Matthias Wessling is listed.
    if names and not any("wessling" in n.lower() for n in names):
        names.append("Matthias Wessling")
    if not names:
        names = ["Matthias Wessling"]
    return names


def invent_slug(rec: PatentRecord) -> str:
    pub_slug = slugify(rec.publication_number)
    # Short descriptive stem from distinctive title tokens.
    stop = {
        "method",
        "process",
        "for",
        "the",
        "a",
        "an",
        "of",
        "and",
        "to",
        "in",
        "with",
        "by",
        "its",
        "thereof",
        "use",
        "using",
        "having",
        "comprising",
        "production",
        "producing",
        "preparation",
        "manufacturing",
        "manufacture",
    }
    words = [
        w
        for w in re.findall(r"[a-z0-9]+", (rec.title or "").lower())
        if w not in stop and len(w) > 2
    ][:6]
    stem = slugify("-".join(words)) if words else "patent"
    return f"{pub_slug}-{stem}"[:80]


def cdn_url(rel: str) -> str:
    return f"{IMAGE_CDN}/{rel.lstrip('/')}"


def download_bytes(url: str, *, timeout: int = 45) -> bytes:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Referer": "https://patents.google.com/",
            "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def is_cdn_rel_path(rel: str) -> bool:
    """Google Patents CDN figure paths look like aa/bb/cc/<hash>/<file>.png."""
    if not rel or rel.startswith("http"):
        return False
    parts = rel.strip("/").split("/")
    return len(parts) >= 4 and all(len(parts[i]) == 2 for i in range(3))


def render_pdf_preview(pdf_rel: str, image_dir: Path, *, max_pages: int = 4) -> Tuple[str, List[str]]:
    """Download a patent PDF and rasterize the first pages as preview images."""
    try:
        import fitz  # pymupdf
    except ImportError:
        print("  ! pymupdf not available; cannot render PDF preview")
        return "", []

    if not pdf_rel:
        return "", []

    image_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = image_dir / "source.pdf"
    try:
        pdf_path.write_bytes(download_bytes(cdn_url(pdf_rel), timeout=90))
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        print(f"  ! pdf download failed ({pdf_rel}): {exc}")
        return "", []

    try:
        doc = fitz.open(pdf_path)
    except Exception as exc:  # noqa: BLE001
        print(f"  ! pdf open failed: {exc}")
        return "", []

    index_rel = ""
    thumbs: List[str] = []
    page_count = min(max_pages, len(doc))
    for idx in range(page_count):
        page = doc[idx]
        # Moderate resolution for web previews.
        pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5), alpha=False)
        if idx == 0:
            out = image_dir / "index-figure.png"
            pix.save(out.as_posix())
            index_rel = f"/images/patents/{image_dir.name}/index-figure.png"
        out = image_dir / f"thumb-{idx + 1:02d}.png"
        pix.save(out.as_posix())
        thumbs.append(f"/images/patents/{image_dir.name}/thumb-{idx + 1:02d}.png")
    doc.close()
    return index_rel, thumbs


def save_figures(
    rec: PatentRecord,
    image_dir: Path,
    *,
    max_thumbs: int = 4,
    delay_s: float = 0.25,
) -> Tuple[str, List[str]]:
    """Download index figure + thumbnails. Returns (image_path, thumbnails)."""
    image_dir.mkdir(parents=True, exist_ok=True)
    figs = rec.figures or []
    rels: List[str] = []
    for fig in figs:
        full = (fig or {}).get("full") or (fig or {}).get("thumbnail") or ""
        if is_cdn_rel_path(full):
            rels.append(full)
    if not rels and is_cdn_rel_path(rec.thumbnail_path):
        rels.append(rec.thumbnail_path)

    index_rel = ""
    thumbs: List[str] = []
    for idx, rel in enumerate(rels[: max_thumbs + 1]):
        try:
            data = download_bytes(cdn_url(rel))
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            print(f"  ! figure download failed ({rel}): {exc}")
            continue
        if idx == 0:
            out = image_dir / "index-figure.png"
            out.write_bytes(data)
            index_rel = f"/images/patents/{image_dir.name}/index-figure.png"
        if idx < max_thumbs:
            out = image_dir / f"thumb-{idx + 1:02d}.png"
            out.write_bytes(data)
            thumbs.append(f"/images/patents/{image_dir.name}/thumb-{idx + 1:02d}.png")
        time.sleep(delay_s)

    if index_rel:
        return index_rel, thumbs

    # Fallback: rasterize PDF pages when drawing PNGs are unavailable.
    if rec.pdf_path:
        print(f"  → PDF preview fallback ({rec.pdf_path})")
        return render_pdf_preview(rec.pdf_path, image_dir, max_pages=max_thumbs)

    return "", []


def build_markdown(
    rec: PatentRecord,
    *,
    slug: str,
    image: str,
    thumbnails: List[str],
    organization: str,
    topics: List[str],
) -> str:
    title = title_case_safe(rec.title)
    summary = rec.snippet or title
    inventors = parse_inventors(rec.inventor)
    date = rec.publication_date or rec.priority_date or rec.filing_date or "1970-01-01"
    status = infer_status(rec)
    topics_toml = (
        "topics = []"
        if not topics
        else "topics = [" + ", ".join(toml_string(t) for t in topics) + "]"
    )
    inventors_toml = "inventors = [" + ", ".join(toml_string(n) for n in inventors) + "]"
    thumbs_toml = (
        "thumbnails = []"
        if not thumbnails
        else "thumbnails = [\n"
        + ",\n".join(f"  {toml_string(t)}" for t in thumbnails)
        + "\n]"
    )
    siblings = ", ".join(rec.siblings) if rec.siblings else ""

    body_links = [
        f"- [Google Patents]({rec.google_patents_url})",
        f"- [Espacenet search](https://worldwide.espacenet.com/patent/search?q=pn%3D{rec.publication_number})",
    ]
    if rec.pdf_path:
        body_links.append(f"- [PDF]({cdn_url(rec.pdf_path)})")

    overview_lines = [
        f"- **Publication:** {rec.publication_number}",
        f"- **Priority date:** {rec.priority_date or 'n/a'}",
        f"- **Filing date:** {rec.filing_date or 'n/a'}",
        f"- **Publication date:** {rec.publication_date or 'n/a'}",
    ]
    if rec.grant_date:
        overview_lines.append(f"- **Grant date:** {rec.grant_date}")
    if siblings:
        overview_lines.append(f"- **Related family publications:** {siblings}")
    if rec.family_country_status:
        overview_lines.append(f"- **Family status:** {rec.family_country_status}")

    return f"""+++
title = {toml_string(title)}
date = {date}
summary = {toml_string(summary)}
image = {toml_string(image)}
image_alt = {toml_string(f"Patent drawing from {rec.publication_number}" if image else "")}
publication_number = {toml_string(rec.publication_number)}
filing_date = {toml_string(rec.filing_date)}
publication_date = {toml_string(rec.publication_date)}
priority_date = {toml_string(rec.priority_date)}
grant_date = {toml_string(rec.grant_date)}
status = {toml_string(status)}
assignee = {toml_string(rec.assignee)}
organization = {toml_string(organization)}
{inventors_toml}
{topics_toml}
google_patents_url = {toml_string(rec.google_patents_url)}
family_publications = {toml_string(siblings)}
{thumbs_toml}
draft = false
featured = false
+++

## Patent overview

{chr(10).join(overview_lines)}

## Summary of the invention

{summary}

## Sources

{chr(10).join(body_links)}
"""


def should_skip(rec: PatentRecord, slug: str) -> Optional[str]:
    if slug in PRESERVE_SLUGS:
        return f"preserved curated slug {slug}"
    if rec.publication_number in PRESERVE_FAMILY_PUBS:
        return f"covered by curated page ({rec.publication_number})"
    if any(sib in PRESERVE_FAMILY_PUBS for sib in rec.siblings):
        return "family covered by curated page"
    return None


def write_index(out_dir: Path) -> None:
    index = out_dir / "_index.md"
    content = """+++
title = "Patents"
description = "Selected patents and patent applications with Matthias Wessling as inventor."
+++

Patents and patent applications across membrane science, electrochemical systems, and related process technology. Use the filters to browse by year, organization, or topic.
"""
    if not index.exists():
        index.write_text(content, encoding="utf-8")
    else:
        # Keep existing custom text if already present; only ensure title.
        pass


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--xhr-dir", type=Path, default=DEFAULT_XHR_DIR)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--image-root", type=Path, default=DEFAULT_IMAGE_ROOT)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--skip-images", action="store_true")
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()

    records = load_xhr_records(args.xhr_dir)
    reps = choose_representatives(records.values())
    print(f"Loaded {len(records)} publications -> {len(reps)} family representatives")

    if args.limit > 0:
        reps = reps[: args.limit]

    args.out_dir.mkdir(parents=True, exist_ok=True)
    if not args.dry_run:
        write_index(args.out_dir)

    written = 0
    skipped = 0
    for rec in reps:
        slug = invent_slug(rec)
        reason = should_skip(rec, slug)
        out_path = args.out_dir / f"{slug}.md"
        if reason:
            print(f"skip {rec.publication_number}: {reason}")
            skipped += 1
            continue
        if out_path.exists() and not args.overwrite:
            print(f"skip existing {out_path.name} (use --overwrite)")
            skipped += 1
            continue

        organization = normalize_organization(rec.assignee)
        topics = infer_topics(rec.title, rec.snippet)
        image = ""
        thumbs: List[str] = []
        if not args.skip_images and not args.dry_run:
            image_dir = args.image_root / slugify(rec.publication_number)
            print(f"figures {rec.publication_number} -> {image_dir.name} ({len(rec.figures)} available)")
            image, thumbs = save_figures(rec, image_dir)

        md = build_markdown(
            rec,
            slug=slug,
            image=image,
            thumbnails=thumbs,
            organization=organization,
            topics=topics,
        )
        print(
            f"{'DRY ' if args.dry_run else ''}write {out_path.name} | {organization} | "
            f"{rec.publication_number} | topics={topics}"
        )
        if not args.dry_run:
            out_path.write_text(md, encoding="utf-8")
        written += 1

    print(f"Done. wrote={written} skipped={skipped}")


if __name__ == "__main__":
    main()
