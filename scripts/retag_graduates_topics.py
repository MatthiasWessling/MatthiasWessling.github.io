#!/usr/bin/env python3
"""
Retag graduates.csv topics with a small controlled vocabulary.

Sources: thesis title + English abstract from data/rwth_markdown/ (RWTH)
or data/ut_markdown/ (Twente Pure dumps).

Usage:
  python scripts/retag_graduates_topics.py --dry-run
  python scripts/retag_graduates_topics.py --write-csv
  python scripts/retag_graduates_topics.py --write-csv --import-md
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))
from enrich_graduates_summaries import record_id_from_url  # noqa: E402
from extract_rwth_record import (  # noqa: E402
    extract_abstract_text,
    is_mostly_german,
    short_webpage_summary,
)
from import_graduates_from_csv import import_rows  # noqa: E402


DEFAULT_CSV = "data/graduates.csv"
DEFAULT_MD_DIR = "data/rwth_markdown"
DEFAULT_UT_MD_DIR = "data/ut_markdown"

# Small controlled vocabulary for the graduates filter.
# Each entry: (canonical label, list of match patterns).
# More specific labels are listed before generic parents when both may fire.
VOCAB: List[Tuple[str, Sequence[str]]] = [
    ("gas diffusion electrodes", ("gas diffusion electrode", "gas-diffusion electrode", "gde")),
    ("bipolar membranes", ("bipolar membrane", "bipolar membranes")),
    ("hollow fiber membranes", ("hollow fiber", "hollow-fibre", "hollow fibre", "spinneret")),
    ("ion-exchange membranes", ("ion exchange membrane", "ion-exchange membrane", "ion exchange membranes", "iem")),
    ("layer-by-layer", ("layer-by-layer", "layer by layer", "lbl ", "polyelectrolyte multilayer")),
    ("organic solvent nanofiltration", ("organic solvent nanofiltration", "osn", "solvent nanofiltration")),
    ("forward osmosis", ("forward osmosis", "draw solution")),
    ("capacitive deionization", ("capacitive deionization", "flow-electrode capacitive", "fcdi", "deionization")),
    ("redox flow batteries", ("redox flow", "vanadium redox", "vrfb", "flow battery")),
    ("CO2 reduction", ("co2 reduction", "co₂ reduction", "co2 electroly", "co₂ electroly", "electroreduction of co", "co2 electro", "co₂ electro")),
    ("nitrogen reduction", ("nitrogen reduction", "ammonia synthesis", "n2 reduction", "n₂ reduction")),
    ("hydrogen", ("hydrogen compression", "hydrogen recovery", "biohydrogen", "water splitting", "hydrogen distribution")),
    ("biomass valorization", ("biomass", "lignin", "biorefiner", "furancarboxylic", "hmf", "fdca", "methanol oxidation")),
    ("tissue engineering", ("tissue engineering", "neuroregeneration", "cell expansion", "scaffold", "blood-contact", "blood compatible", "hemodynamic", "extracorporeal")),
    ("microgels", ("microgel",)),
    ("polyelectrolytes", ("polyelectrolyte", "pedot")),
    ("polymers", ("polymer particle", "polymer ", "polymeric", "silicone")),
    ("porous media", ("porous media", "porosity", "porous scaffold", "porous network", "porous electrode", "porous ion", "porous-wall", "porous wall")),
    ("microfluidics", ("microfluidic", "two-photon", "wet spinning", "microtube")),
    ("MRI", ("magnetic resonance", "flow-mri", "flow mri", " mri")),
    ("impedance spectroscopy", ("impedance spectroscopy", "electrical impedance")),
    ("plasma", ("plasma-coated", "plasma coating", "plasma gas", "argon plasma")),
    ("fouling", ("fouling", "antifouling")),
    ("modeling", ("mathematical process modeling", "process modeling", "process modelling", "numerical model", "modelling of", "modeling of", "model-based", "model based design")),
    ("simulation", ("simulation", "numerical insight", "computational framework", "computational model")),
    ("visualization", ("visualiz", "flow field", "wettability")),
    ("bioreactors", ("bioreactor", "gas fermentation", "fermentation")),
    ("water treatment", ("wastewater", "drinking water", "micropollutant", "activated carbon", "ozonation", "hydrothermal", "water purification", "water treatment")),
    ("gas separation", ("gas separation", "biogas", "siloxane", "propylene", "membrane distillation", "enthalpy exchanger")),
    ("electrochemistry", ("electrochem", "electrolysis", "electrode", "overlimiting", "neuromorphic", "charge transport")),
    ("filtration", ("filtration", "nanofiltration", "ultrafiltration", "diafiltration", "filter cake", "soft matter filtration", "colloid")),
    ("membranes", ("membrane", "membran")),
]

# Prefer at most this many labels per graduate.
MAX_TOPICS = 4


def normalize_text(value: str) -> str:
    text = (value or "").lower()
    text = text.replace("co$_{2}$", "co2").replace("co₂", "co2").replace("n$_{2}$", "n2")
    text = text.replace("$", "")
    text = re.sub(r"\s+", " ", text)
    return text


def load_abstract(md_dir: Path, record_url: str, ut_md_dir: Optional[Path] = None) -> str:
    # RWTH: data/rwth_markdown/<record_id>.md
    rid = record_id_from_url(record_url)
    if rid:
        path = md_dir / f"{rid}.md"
        if path.is_file():
            raw = path.read_text(encoding="utf-8", errors="replace")
            abstract = extract_abstract_text(raw) or ""
            if abstract and "online nicht verfügbar" not in abstract.lower():
                if not is_mostly_german(abstract):
                    return abstract

    # Twente: data/ut_markdown/<slug>.md with ## Abstract section
    if ut_md_dir and record_url and "utwente.nl" in record_url:
        from import_graduates_from_csv import slugify  # local import

        slug = slugify(Path(record_url.rstrip("/")).name)
        path = ut_md_dir / f"{slug}.md"
        if path.is_file():
            raw = path.read_text(encoding="utf-8", errors="replace")
            m = re.search(r"## Abstract\s*(.+)$", raw, flags=re.I | re.S)
            if m:
                abstract = re.sub(r"\s+", " ", m.group(1)).strip()
                if abstract and not abstract.startswith("_No abstract"):
                    return abstract
    return ""


def score_topics(title: str, abstract: str) -> List[Tuple[str, float]]:
    title_n = normalize_text(title)
    abs_n = normalize_text(abstract)
    scored: List[Tuple[str, float]] = []
    for label, patterns in VOCAB:
        score = 0.0
        for pattern in patterns:
            p = pattern.lower()
            if p in title_n:
                score += 3.0
            if abs_n and p in abs_n:
                score += 1.0
        if score > 0:
            scored.append((label, score))
    scored.sort(key=lambda item: (-item[1], item[0]))
    return scored


def select_topics(scored: Sequence[Tuple[str, float]], *, max_topics: int = MAX_TOPICS) -> List[str]:
    if not scored:
        return ["membranes"]  # safe fallback for this corpus; refined below by caller

    selected: List[str] = []
    for label, _score in scored:
        if label in selected:
            continue
        selected.append(label)
        if len(selected) >= max_topics:
            break
    return selected


def retag_rows(
    rows: List[Dict[str, str]],
    md_dir: Path,
    *,
    max_topics: int,
    ut_md_dir: Optional[Path] = None,
) -> Dict[str, int]:
    stats = {
        "retagged": 0,
        "unchanged": 0,
        "with_abstract": 0,
        "fallback": 0,
    }
    for row in rows:
        title = (row.get("thesis_title") or "").strip()
        record_url = (row.get("record_url") or row.get("rwth_url") or "").strip()
        abstract = load_abstract(md_dir, record_url, ut_md_dir=ut_md_dir)
        if abstract:
            stats["with_abstract"] += 1
        scored = score_topics(title, abstract)
        topics = select_topics(scored, max_topics=max_topics)
        if not scored:
            # Title-only generic fallback from coarse cues
            lower = normalize_text(title)
            topics = []
            if "electro" in lower:
                topics.append("electrochemistry")
            if "filter" in lower or "filtrat" in lower:
                topics.append("filtration")
            if "membrane" in lower:
                topics.append("membranes")
            if not topics:
                topics = ["membranes"]
            stats["fallback"] += 1

        new_topics = "; ".join(topics)
        old = (row.get("topics") or "").strip()
        if new_topics != old:
            stats["retagged"] += 1
        else:
            stats["unchanged"] += 1
        row["topics"] = new_topics
    return stats


def write_csv(path: Path, fieldnames: List[str], rows: List[Dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Retag graduates with controlled vocabulary.")
    parser.add_argument("--csv", default=DEFAULT_CSV)
    parser.add_argument("--markdown-dir", default=DEFAULT_MD_DIR)
    parser.add_argument("--ut-markdown-dir", default=DEFAULT_UT_MD_DIR)
    parser.add_argument("--max-topics", type=int, default=MAX_TOPICS)
    parser.add_argument("--write-csv", action="store_true")
    parser.add_argument("--import-md", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo = Path(__file__).resolve().parents[1]
    csv_path = Path(args.csv)
    md_dir = Path(args.markdown_dir)
    ut_md_dir = Path(args.ut_markdown_dir)
    if not csv_path.is_absolute():
        csv_path = repo / csv_path
    if not md_dir.is_absolute():
        md_dir = repo / md_dir
    if not ut_md_dir.is_absolute():
        ut_md_dir = repo / ut_md_dir

    with csv_path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        fieldnames = list(reader.fieldnames or [])
        rows = [dict(r) for r in reader]

    stats = retag_rows(
        rows,
        md_dir,
        max_topics=args.max_topics,
        ut_md_dir=ut_md_dir if ut_md_dir.is_dir() else None,
    )
    print(
        f"Retag complete: retagged={stats['retagged']} unchanged={stats['unchanged']} "
        f"with_abstract={stats['with_abstract']} fallback={stats['fallback']}"
    )

    # Vocabulary usage report
    from collections import Counter

    usage: Counter[str] = Counter()
    for row in rows:
        for part in re.split(r"[;|]", row.get("topics") or ""):
            label = part.strip()
            if label:
                usage[label] += 1
    print(f"Unique labels in use: {len(usage)}")
    for label, count in usage.most_common():
        print(f"  {count:3d}  {label}")

    if args.dry_run or not args.write_csv:
        print("Dry-run / no --write-csv: CSV not updated")
        if args.dry_run:
            for row in rows[:8]:
                print(f"  {row['name']}: {row['topics']}")
        return 0

    write_csv(csv_path, fieldnames, rows)
    print(f"Updated CSV: {csv_path}")

    if args.import_md:
        out_dir = repo / "content/graduates"
        import_rows(csv_path, out_dir, overwrite=True, dry_run=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
