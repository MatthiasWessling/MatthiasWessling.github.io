#!/usr/bin/env python3
"""
Enrich graduates.csv `summary` from RWTH Publications abstracts.

For each row with an `rwth_url`, fetch the record, extract the English abstract,
and write a short 1–2 sentence webpage blurb into `summary`.

Caches raw HTML under data/rwth_cache/ so runs can resume after rate limits.

Usage:
  python scripts/enrich_graduates_summaries.py --limit 5 --dry-run
  python scripts/enrich_graduates_summaries.py --write-csv
  python scripts/enrich_graduates_summaries.py --from-markdown-dir data/rwth_markdown --write-csv
  python scripts/import_graduates_from_csv.py --overwrite
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import time
import urllib.error
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))
from extract_rwth_record import (  # noqa: E402
    extract_abstract_text,
    extract_rwth_metadata,
    fetch_html,
    short_webpage_summary,
    strip_tags,
    validate_rwth_record_url,
)


DEFAULT_CSV = "data/graduates.csv"
DEFAULT_CACHE = "data/rwth_cache"
DEFAULT_REPORT = "data/graduates_summaries_report.json"


def record_id_from_url(url: str) -> str:
    m = re.search(r"/record/(\d+)", url)
    return m.group(1) if m else ""


def load_csv(path: Path) -> Tuple[List[str], List[Dict[str, str]]]:
    with path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        return list(reader.fieldnames or []), [dict(r) for r in reader]


def write_csv(path: Path, fieldnames: List[str], rows: List[Dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def fetch_with_retry(
    url: str,
    cache_dir: Path,
    *,
    retries: int,
    pause: float,
) -> str:
    rid = record_id_from_url(url)
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_file = cache_dir / f"{rid}.html" if rid else None
    if cache_file and cache_file.is_file() and cache_file.stat().st_size > 500:
        return cache_file.read_text(encoding="utf-8", errors="replace")

    delay = pause
    last_err: Optional[Exception] = None
    for attempt in range(1, retries + 1):
        try:
            html = fetch_html(url, timeout=40)
            if "fast-challenge" in html and len(html) < 1000:
                raise RuntimeError("RWTH bot challenge page returned")
            if cache_file:
                cache_file.write_text(html, encoding="utf-8")
            return html
        except urllib.error.HTTPError as exc:
            last_err = exc
            if exc.code == 429:
                time.sleep(delay)
                delay = min(delay * 2, 120)
                continue
            raise
        except Exception as exc:  # noqa: BLE001
            last_err = exc
            time.sleep(delay)
            delay = min(delay * 1.5, 60)
    raise RuntimeError(f"Failed to fetch {url}: {last_err}")


def summary_from_html(html: str, url: str) -> Dict[str, Any]:
    text = strip_tags(html)
    abstract = extract_abstract_text(text)
    summary = short_webpage_summary(abstract)
    return {
        "source_url": url,
        "abstract": abstract or "",
        "summary": summary,
    }


def summary_from_markdown(md: str, url: str) -> Dict[str, Any]:
    # WebFetch markdown still contains Kurzfassung … OpenAccess blocks.
    abstract = extract_abstract_text(md)
    if not abstract:
        # Looser markdown capture
        m = re.search(
            r"Kurzfassung\s*(.+?)(?:OpenAccess|Dokumenttyp|Format\b)",
            md,
            flags=re.I | re.S,
        )
        if m:
            from extract_rwth_record import prefer_english_abstract

            abstract = prefer_english_abstract(re.sub(r"\s+", " ", m.group(1)).strip())
    summary = short_webpage_summary(abstract)
    return {
        "source_url": url,
        "abstract": abstract or "",
        "summary": summary,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Write short webpage summaries from RWTH thesis abstracts."
    )
    parser.add_argument("--csv", default=DEFAULT_CSV)
    parser.add_argument("--cache-dir", default=DEFAULT_CACHE)
    parser.add_argument("--report", default=DEFAULT_REPORT)
    parser.add_argument(
        "--from-markdown-dir",
        default="",
        help="Optional dir of {record_id}.md dumps (e.g. from WebFetch) instead of live HTTP",
    )
    parser.add_argument("--only-missing", action="store_true", default=True)
    parser.add_argument(
        "--all",
        action="store_true",
        help="Overwrite existing summaries",
    )
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--pause", type=float, default=2.5)
    parser.add_argument("--retries", type=int, default=5)
    parser.add_argument("--write-csv", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo = Path(__file__).resolve().parents[1]
    csv_path = Path(args.csv)
    cache_dir = Path(args.cache_dir)
    report_path = Path(args.report)
    md_dir = Path(args.from_markdown_dir) if args.from_markdown_dir else None
    if not csv_path.is_absolute():
        csv_path = repo / csv_path
    if not cache_dir.is_absolute():
        cache_dir = repo / cache_dir
    if not report_path.is_absolute():
        report_path = repo / report_path
    if md_dir and not md_dir.is_absolute():
        md_dir = repo / md_dir

    fieldnames, rows = load_csv(csv_path)
    only_missing = not args.all

    targets: List[Tuple[int, Dict[str, str]]] = []
    for idx, row in enumerate(rows):
        url = (row.get("rwth_url") or "").strip()
        if not url:
            continue
        if only_missing and (row.get("summary") or "").strip():
            continue
        targets.append((idx, row))
    if args.limit and args.limit > 0:
        targets = targets[: args.limit]

    print(f"Enriching summaries for {len(targets)} graduates")
    filled = 0
    failed = 0
    report: Dict[str, Any] = {"people": [], "summary": {}}

    for n, (idx, row) in enumerate(targets, start=1):
        name = (row.get("name") or "").strip()
        url = (row.get("rwth_url") or "").strip()
        rid = record_id_from_url(url)
        print(f"[{n}/{len(targets)}] {name} ({rid})")
        try:
            if md_dir:
                md_file = md_dir / f"{rid}.md"
                if not md_file.is_file():
                    raise FileNotFoundError(f"Missing markdown dump: {md_file}")
                payload = summary_from_markdown(
                    md_file.read_text(encoding="utf-8", errors="replace"), url
                )
            else:
                # Prefer metadata helper when live fetch works; fall back to cached HTML parser.
                try:
                    html = fetch_with_retry(
                        url,
                        cache_dir,
                        retries=args.retries,
                        pause=args.pause,
                    )
                    # If cache hit, parse locally; else extract_rwth_metadata would re-fetch.
                    payload = summary_from_html(html, url)
                    if not payload["summary"]:
                        meta = extract_rwth_metadata(validate_rwth_record_url(url))
                        payload["summary"] = meta.get("summary") or ""
                        payload["abstract"] = meta.get("abstract") or payload["abstract"]
                except Exception:
                    meta = extract_rwth_metadata(validate_rwth_record_url(url))
                    payload = {
                        "source_url": url,
                        "abstract": meta.get("abstract") or "",
                        "summary": meta.get("summary") or "",
                    }

            summary = (payload.get("summary") or "").strip()
            if not summary:
                raise RuntimeError("No English abstract/summary extracted")

            print(f"  {summary[:120]}…")
            if args.write_csv and not args.dry_run:
                rows[idx]["summary"] = summary
            filled += 1
            report["people"].append(
                {
                    "name": name,
                    "rwth_url": url,
                    "summary": summary,
                    "abstract_chars": len(payload.get("abstract") or ""),
                }
            )
        except Exception as exc:  # noqa: BLE001
            failed += 1
            print(f"  FAIL: {exc}")
            if args.all and args.write_csv and not args.dry_run:
                # Clear stale / non-English summaries on full refresh.
                rows[idx]["summary"] = ""
            report["people"].append(
                {"name": name, "rwth_url": url, "error": str(exc)}
            )

        if n < len(targets) and not md_dir:
            time.sleep(args.pause)

    report["summary"] = {"filled": filled, "failed": failed, "processed": len(targets)}
    print(f"Done. filled={filled} failed={failed}")

    if args.dry_run:
        print("Dry-run: no files written")
        return 0 if failed == 0 or filled > 0 else 1

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"Wrote report: {report_path}")

    if args.write_csv:
        write_csv(csv_path, fieldnames, rows)
        print(f"Updated CSV: {csv_path}")
    else:
        print("CSV unchanged (pass --write-csv to apply)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
