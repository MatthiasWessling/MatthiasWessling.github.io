#!/usr/bin/env python3
"""
Crawl Google Patents for an inventor and write a review CSV.

Uses the public patents.google.com XHR query endpoint (same data the UI loads).

Examples:
  python scripts/crawl_google_patents.py
  python scripts/crawl_google_patents.py --inventor "Matthias Wessling"
  python scripts/crawl_google_patents.py --inventor "Matthias Wessling" \\
      --output data/patents_matthias_wessling.csv
"""

from __future__ import annotations

import argparse
import csv
import html
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)

CSV_FIELDS = [
    "include",
    "publication_number",
    "title",
    "inventor",
    "assignee",
    "priority_date",
    "filing_date",
    "publication_date",
    "grant_date",
    "language",
    "family_country_status",
    "snippet",
    "google_patents_url",
    "query_hit",
    "notes",
]


def clean_text(value: Optional[str]) -> str:
    if not value:
        return ""
    text = html.unescape(value)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text.replace("\u2026", "...")


def fetch_json(url: str, *, retries: int = 5, timeout: int = 30) -> Dict[str, Any]:
    last_err: Optional[BaseException] = None
    for attempt in range(retries):
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": USER_AGENT,
                "Accept": "application/json,text/plain,*/*",
                "Accept-Language": "en-US,en;q=0.9",
                "Referer": "https://patents.google.com/",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as err:
            last_err = err
            # Back off on rate limits / temporary outages.
            if err.code in {429, 500, 502, 503, 504} and attempt < retries - 1:
                time.sleep(1.5 * (attempt + 1))
                continue
            raise
        except urllib.error.URLError as err:
            last_err = err
            if attempt < retries - 1:
                time.sleep(1.5 * (attempt + 1))
                continue
            raise
    raise RuntimeError(f"Failed to fetch {url}: {last_err}")


def query_variants(inventor: str) -> List[str]:
    """Return complementary Google Patents inventor query strings.

    Unquoted and quoted forms can return different family representatives;
    merging them gives better coverage. Avoid ``Last, First`` forms — those
    are parsed poorly and return huge unrelated result sets.
    """
    inventor = inventor.strip()
    return [
        f"inventor={inventor.replace(' ', '+')}",
        f'inventor="{inventor}"',
    ]


def query_page(query_inner: str, page: int, *, num: int = 100) -> Dict[str, Any]:
    # Match the UI query form; request many results per page when possible.
    parts = [query_inner, f"num={num}"]
    if page:
        parts.append(f"page={page}")
    inner = "&".join(parts)
    url = "https://patents.google.com/xhr/query?" + urllib.parse.urlencode(
        {"url": inner, "exp": ""}
    )
    return fetch_json(url)


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


def patent_row(item: Dict[str, Any], *, query_hit: str = "") -> Optional[Dict[str, str]]:
    patent = item.get("patent") or {}
    pub = patent.get("publication_number") or ""
    if not pub:
        return None
    patent_id = item.get("id") or ""
    if patent_id:
        gp_url = f"https://patents.google.com/{patent_id}"
    else:
        gp_url = f"https://patents.google.com/patent/{pub}"
    return {
        "include": "",
        "publication_number": pub,
        "title": clean_text(patent.get("title")),
        "inventor": clean_text(patent.get("inventor")),
        "assignee": clean_text(patent.get("assignee")),
        "priority_date": patent.get("priority_date") or "",
        "filing_date": patent.get("filing_date") or "",
        "publication_date": patent.get("publication_date") or "",
        "grant_date": patent.get("grant_date") or "",
        "language": patent.get("language") or "",
        "family_country_status": family_status(patent),
        "snippet": clean_text(patent.get("snippet")),
        "google_patents_url": gp_url,
        "query_hit": query_hit,
        "notes": "",
    }


def crawl_query(query_inner: str, *, delay_s: float = 0.7) -> List[Dict[str, str]]:
    first = query_page(query_inner, 0)
    results = first.get("results") or {}
    if results.get("parse_error") or results.get("user_error"):
        raise RuntimeError(f"Google Patents query error: {results}")

    total = int(results.get("total_num_results") or 0)
    num_pages = int(results.get("total_num_pages") or 1)
    print(f"Query {query_inner!r}: {total} results across {num_pages} page(s)")

    rows: List[Dict[str, str]] = []
    seen = set()
    for page in range(num_pages):
        data = first if page == 0 else query_page(query_inner, page)
        clusters = (data.get("results") or {}).get("cluster") or []
        page_count = 0
        for cluster in clusters:
            for item in cluster.get("result") or []:
                row = patent_row(item, query_hit=query_inner)
                if not row:
                    continue
                pub = row["publication_number"]
                if pub in seen:
                    continue
                seen.add(pub)
                rows.append(row)
                page_count += 1
        print(f"  page {page}: +{page_count} (cumulative {len(rows)})")
        if page < num_pages - 1:
            time.sleep(delay_s)
    return rows


def crawl_inventor(inventor: str, *, delay_s: float = 0.7) -> List[Dict[str, str]]:
    merged: Dict[str, Dict[str, str]] = {}
    for query_inner in query_variants(inventor):
        for row in crawl_query(query_inner, delay_s=delay_s):
            pub = row["publication_number"]
            if pub not in merged:
                merged[pub] = row
            else:
                prev = merged[pub]["query_hit"]
                if row["query_hit"] and row["query_hit"] not in prev:
                    merged[pub]["query_hit"] = f"{prev} | {row['query_hit']}"
        time.sleep(delay_s)

    rows = list(merged.values())
    rows.sort(
        key=lambda r: (
            r["priority_date"] or "0000",
            r["publication_date"] or "0000",
            r["publication_number"],
        ),
        reverse=True,
    )
    print(f"Merged unique publications: {len(rows)}")
    return rows


def write_csv(path: Path, rows: List[Dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--inventor",
        default="Matthias Wessling",
        help='Inventor name for Google Patents search (default: "Matthias Wessling")',
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/patents_matthias_wessling.csv"),
        help="Output CSV path",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.8,
        help="Delay between page requests in seconds",
    )
    args = parser.parse_args()

    rows = crawl_inventor(args.inventor, delay_s=args.delay)
    write_csv(args.output, rows)
    print(f"Wrote {len(rows)} patents -> {args.output}")
    print("Assignees:")
    for assignee, count in Counter(r["assignee"] for r in rows).most_common():
        print(f"  {count:3d}  {assignee or '(empty)'}")


if __name__ == "__main__":
    main()
