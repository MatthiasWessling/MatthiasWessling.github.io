#!/usr/bin/env python3
"""
Build a DOI/title → keywords lookup from a Scopus RIS export for Hugo search.

Writes data/scopus_keywords.json used by themes/custom/layouts/index.json.

Usage:
  python scripts/build_scopus_keywords.py
  python scripts/build_scopus_keywords.py --ris data/scopus_export_2026-08-07.ris
"""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from pathlib import Path
from typing import Dict, List, Optional, Tuple


DEFAULT_RIS = "data/scopus_export_2026-08-07.ris"
DEFAULT_OUT = "themes/custom/data/scopus_keywords.json"


def fold(text: str) -> str:
    text = (text or "").strip().lower()
    text = (
        text.replace("ä", "ae")
        .replace("ö", "oe")
        .replace("ü", "ue")
        .replace("ß", "ss")
    )
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def normalize_doi(doi: str) -> str:
    doi = (doi or "").strip()
    doi = re.sub(r"^https?://(dx\.)?doi\.org/", "", doi, flags=re.I)
    return doi.strip().rstrip(".").lower()


def hugo_title_key(text: str) -> str:
    """Title key reproducible in Hugo templates (lower + non-alnum → space)."""
    text = (text or "").lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def parse_ris_keywords(path: Path) -> Tuple[Dict[str, List[str]], Dict[str, List[str]], Dict[str, List[str]]]:
    by_doi: Dict[str, List[str]] = {}
    by_title: Dict[str, List[str]] = {}
    by_title_simple: Dict[str, List[str]] = {}

    cur_doi: Optional[str] = None
    cur_title: Optional[str] = None
    cur_kw: List[str] = []

    def flush() -> None:
        nonlocal cur_doi, cur_title, cur_kw
        # Preserve order, drop empties/duplicates (case-insensitive)
        seen = set()
        cleaned: List[str] = []
        for kw in cur_kw:
            k = kw.strip()
            if not k:
                continue
            key = k.lower()
            if key in seen:
                continue
            seen.add(key)
            cleaned.append(k)

        if cleaned:
            if cur_doi:
                by_doi[cur_doi] = cleaned
            if cur_title:
                title_key = fold(cur_title)
                if title_key and title_key not in by_title:
                    by_title[title_key] = cleaned
                simple_key = hugo_title_key(cur_title)
                if simple_key and simple_key not in by_title_simple:
                    by_title_simple[simple_key] = cleaned

        cur_doi = None
        cur_title = None
        cur_kw = []

    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.rstrip("\n")
        if line.startswith("TY  -"):
            flush()
            continue
        if line.startswith("ER  -"):
            flush()
            continue
        if line.startswith("DO  -"):
            cur_doi = normalize_doi(line[6:])
            continue
        if line.startswith("TI  -"):
            cur_title = line[6:].strip()
            continue
        if line.startswith("KW  -"):
            cur_kw.append(line[6:].strip())
            continue

    flush()
    return by_doi, by_title, by_title_simple


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ris", default=DEFAULT_RIS, help="Scopus RIS export path")
    parser.add_argument("--out", default=DEFAULT_OUT, help="Output JSON path")
    args = parser.parse_args()

    repo = Path(__file__).resolve().parents[1]
    ris_path = Path(args.ris)
    out_path = Path(args.out)
    if not ris_path.is_absolute():
        ris_path = repo / ris_path
    if not out_path.is_absolute():
        out_path = repo / out_path

    if not ris_path.exists():
        raise SystemExit(f"RIS not found: {ris_path}")

    by_doi, by_title, by_title_simple = parse_ris_keywords(ris_path)
    payload = {
        "source": str(ris_path.relative_to(repo)),
        "doi_count": len(by_doi),
        "title_count": len(by_title),
        "title_simple_count": len(by_title_simple),
        "by_doi": by_doi,
        "by_title": by_title,
        "by_title_simple": by_title_simple,
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        f"Wrote {out_path.relative_to(repo)} "
        f"(dois={len(by_doi)} titles={len(by_title)} title_simple={len(by_title_simple)})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
