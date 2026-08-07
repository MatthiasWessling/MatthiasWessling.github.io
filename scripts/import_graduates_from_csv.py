#!/usr/bin/env python3
"""
Bulk-import Graduates entries from data/graduates.csv into content/graduates/.

CSV columns (header required):
  name, graduate_date, thesis_title, topics, institution, record_url, doi,
  thesis_pdf, linkedin, orcid, image, summary

Backward compatible:
  - `rwth_url` is accepted as an alias for `record_url`
  - missing `institution` defaults to RWTH when record_url is an RWTH host,
    Twente when it is research.utwente.nl, else empty

topics: semicolon-separated keywords, e.g. "membranes; CO2 reduction"

Usage:
  python scripts/import_graduates_from_csv.py
  python scripts/import_graduates_from_csv.py --dry-run
  python scripts/import_graduates_from_csv.py --overwrite
  python scripts/import_graduates_from_csv.py --csv data/graduates.csv
"""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path
from typing import List


DEFAULT_CSV = "data/graduates.csv"
DEFAULT_OUT_DIR = "content/graduates"


def slugify(value: str) -> str:
    value = value.lower().strip()
    replacements = {
        "ä": "ae",
        "ö": "oe",
        "ü": "ue",
        "ß": "ss",
        "á": "a",
        "à": "a",
        "é": "e",
        "è": "e",
        "í": "i",
        "ó": "o",
        "ú": "u",
        "ñ": "n",
    }
    for src, dst in replacements.items():
        value = value.replace(src, dst)
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-{2,}", "-", value).strip("-")
    return value or "graduate"


def toml_string(value: str) -> str:
    """Serialize a Python string as a double-quoted TOML basic string."""
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


def parse_topics(raw: str) -> List[str]:
    if not raw or not raw.strip():
        return []
    parts = re.split(r"[;|]", raw)
    return [part.strip() for part in parts if part.strip()]


def topics_toml(topics: List[str]) -> str:
    if not topics:
        return "topics = []"
    quoted = ", ".join(toml_string(t) for t in topics)
    return f"topics = [{quoted}]"


def resolve_record_url(row: dict) -> str:
    return (row.get("record_url") or row.get("rwth_url") or "").strip()


def resolve_institution(row: dict, record_url: str) -> str:
    explicit = (row.get("institution") or "").strip()
    if explicit:
        return explicit
    host = record_url.lower()
    if "publications.rwth-aachen.de" in host:
        return "RWTH"
    if "research.utwente.nl" in host or "ris.utwente.nl" in host:
        return "Twente"
    return ""


def record_label(institution: str) -> str:
    inst = institution.strip().lower()
    if inst == "twente":
        return "UT Record"
    if inst == "rwth":
        return "RWTH Record"
    return "Repository Record"


def build_markdown(row: dict) -> str:
    name = (row.get("name") or "").strip()
    if not name:
        raise ValueError("Row is missing required 'name'")

    graduate_date = (row.get("graduate_date") or "").strip()
    thesis_title = (row.get("thesis_title") or "").strip()
    topics = parse_topics(row.get("topics") or "")
    record_url = resolve_record_url(row)
    institution = resolve_institution(row, record_url)
    doi = (row.get("doi") or "").strip()
    thesis_pdf = (row.get("thesis_pdf") or "").strip()
    linkedin = (row.get("linkedin") or "").strip()
    orcid = (row.get("orcid") or "").strip()
    image = (row.get("image") or "").strip()
    summary = (row.get("summary") or "").strip()
    image_alt = f"Portrait of {name}" if image else ""

    # Prefer real defense date; undated entries sort last without inventing a year.
    date_str = graduate_date or "1900-01-01"

    front = [
        "+++",
        f"title = {toml_string(name)}",
        f"date = {toml_string(date_str)}",
        f"graduate_date = {toml_string(graduate_date)}",
        f"thesis_title = {toml_string(thesis_title)}",
        topics_toml(topics),
        "draft = false",
        f"summary = {toml_string(summary)}",
        f"image = {toml_string(image)}",
        f"image_alt = {toml_string(image_alt)}",
        f"institution = {toml_string(institution)}",
        f"record_url = {toml_string(record_url)}",
        # Keep rwth_url for older templates/scripts that still read it.
        f"rwth_url = {toml_string(record_url if institution == 'RWTH' else '')}",
        f"doi = {toml_string(doi)}",
        f"thesis_pdf = {toml_string(thesis_pdf)}",
        f"linkedin = {toml_string(linkedin)}",
        f"orcid = {toml_string(orcid)}",
        "featured = false",
        "+++",
        "",
    ]

    body: List[str] = ["## Thesis", ""]
    if thesis_title:
        body.append(f"- Title: {thesis_title}")
    if graduate_date:
        body.append(f"- Graduate Date: {graduate_date}")
    if institution:
        body.append(f"- Institution: {institution}")
    if topics:
        body.append(f"- Topics: {', '.join(topics)}")
    body.append("")
    body.append("## Links")
    body.append("")
    if thesis_pdf:
        body.append(f"- Thesis: [{thesis_pdf}]({thesis_pdf})")
    if linkedin:
        body.append(f"- LinkedIn: [{linkedin}]({linkedin})")
    if orcid:
        body.append(f"- ORCID: [{orcid}]({orcid})")
    if record_url:
        label = record_label(institution)
        body.append(f"- {label}: [{record_url}]({record_url})")
    if doi:
        body.append(f"- DOI: `{doi}`")
    if not any([thesis_pdf, linkedin, orcid, record_url, doi]):
        body.append(
            "- _Add thesis, repository, DOI, LinkedIn, or ORCID links when available._"
        )
    body.append("")

    return "\n".join(front + body)


def import_rows(
    csv_path: Path,
    out_dir: Path,
    *,
    overwrite: bool,
    dry_run: bool,
) -> None:
    if not csv_path.is_file():
        raise FileNotFoundError(f"CSV not found: {csv_path}")

    out_dir.mkdir(parents=True, exist_ok=True)

    with csv_path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        required = {"name"}
        if not reader.fieldnames or not required.issubset(set(reader.fieldnames)):
            raise ValueError(
                f"CSV must include at least columns: {sorted(required)}. "
                f"Found: {reader.fieldnames}"
            )

        created = 0
        skipped = 0
        updated = 0

        for i, row in enumerate(reader, start=2):
            name = (row.get("name") or "").strip()
            if not name:
                print(f"Row {i}: skip (empty name)")
                skipped += 1
                continue

            out_file = out_dir / f"{slugify(name)}.md"
            content = build_markdown(row)

            if out_file.exists() and not overwrite:
                print(f"SKIP  {out_file} (exists; use --overwrite)")
                skipped += 1
                continue

            action = "UPDATE" if out_file.exists() else "CREATE"
            if dry_run:
                print(f"{action} {out_file} [dry-run]")
                print(content)
                print("---")
            else:
                out_file.write_text(content, encoding="utf-8")
                print(f"{action} {out_file}")

            if action == "UPDATE":
                updated += 1
            else:
                created += 1

    print(
        f"Done. created={created} updated={updated} skipped={skipped} "
        f"dry_run={dry_run}"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Import Graduates Hugo pages from a CSV spreadsheet."
    )
    parser.add_argument(
        "--csv",
        default=DEFAULT_CSV,
        help=f"Path to graduates CSV (default: {DEFAULT_CSV})",
    )
    parser.add_argument(
        "--out-dir",
        default=DEFAULT_OUT_DIR,
        help=f"Output directory (default: {DEFAULT_OUT_DIR})",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing graduate markdown files",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print generated markdown without writing files",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repo_root = Path(__file__).resolve().parents[1]
    csv_path = Path(args.csv)
    out_dir = Path(args.out_dir)
    if not csv_path.is_absolute():
        csv_path = repo_root / csv_path
    if not out_dir.is_absolute():
        out_dir = repo_root / out_dir

    import_rows(
        csv_path,
        out_dir,
        overwrite=args.overwrite,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
