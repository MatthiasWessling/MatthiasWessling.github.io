#!/usr/bin/env python3
"""
Create a Graduates entry from a LinkedIn profile URL.

What this script does:
1) Accepts a LinkedIn profile URL.
2) Tries to discover a thesis/dissertation URL from public web results.
3) Writes a new Hugo markdown file into content/graduates/.

Usage examples:
  python scripts/add_graduate_from_linkedin.py \
    --linkedin "https://www.linkedin.com/in/jane-doe-123456/"

  python scripts/add_graduate_from_linkedin.py \
    --linkedin "https://www.linkedin.com/in/jane-doe-123456/" \
    --name "Jane Doe" \
    --thesis "https://example.edu/thesis.pdf"
"""

from __future__ import annotations

import argparse
import datetime as dt
import html
import re
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from extract_rwth_record import extract_rwth_metadata


DEFAULT_OUTPUT_DIR = "content/graduates"
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/123.0.0.0 Safari/537.36"
)


def extract_name_from_linkedin(linkedin_url: str) -> str:
    """Best-effort person name from LinkedIn profile slug."""
    parsed = urllib.parse.urlparse(linkedin_url)
    path = parsed.path.strip("/")
    if not path.startswith("in/"):
        return "Unknown Graduate"

    slug = path.split("/", 1)[1]
    slug = re.sub(r"[-_]+", " ", slug)
    slug = re.sub(r"\d+", " ", slug)
    slug = re.sub(r"\s+", " ", slug).strip()
    if not slug:
        return "Unknown Graduate"
    return " ".join(token.capitalize() for token in slug.split())


def slugify(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-{2,}", "-", value).strip("-")
    return value or "graduate"


def normalize_rwth_author(author: str) -> str:
    """
    Convert author from "Lastname, Firstname" to "Firstname Lastname".
    """
    cleaned = re.sub(r"\s+", " ", author).strip()
    if "," not in cleaned:
        return cleaned
    last, first = [part.strip() for part in cleaned.split(",", 1)]
    if not first:
        return cleaned
    return f"{first} {last}".strip()


def fetch_html(url: str, timeout: int = 15) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        encoding = resp.headers.get_content_charset() or "utf-8"
        return resp.read().decode(encoding, errors="replace")


def duckduckgo_search_links(query: str, max_results: int = 10) -> List[str]:
    """
    Return candidate links from DuckDuckGo HTML results.
    Using the HTML endpoint keeps dependencies minimal.
    """
    search_url = "https://html.duckduckgo.com/html/?q=" + urllib.parse.quote_plus(query)
    page = fetch_html(search_url)

    # Match links in result anchors; decode HTML entities.
    hrefs = re.findall(r'<a[^>]+class="[^"]*result__a[^"]*"[^>]+href="([^"]+)"', page)
    clean_links: List[str] = []
    for href in hrefs:
        link = html.unescape(href)
        if link.startswith("http://") or link.startswith("https://"):
            clean_links.append(link)
        if len(clean_links) >= max_results:
            break
    return clean_links


def score_thesis_url(url: str) -> int:
    lower = url.lower()
    score = 0
    keywords = [
        "thesis",
        "dissertation",
        "doctoral",
        "phd",
        "master",
        "repository",
        ".edu",
        ".ac.",
        ".pdf",
    ]
    for kw in keywords:
        if kw in lower:
            score += 1
    # Slight penalty for obvious non-thesis destinations.
    if any(bad in lower for bad in ["linkedin.com", "facebook.com", "instagram.com", "youtube.com"]):
        score -= 3
    return score


def discover_thesis_url(person_name: str) -> Optional[str]:
    queries = [
        f'"{person_name}" thesis',
        f'"{person_name}" dissertation',
        f'"{person_name}" phd thesis filetype:pdf',
        f'"{person_name}" masters thesis',
    ]

    candidates: List[Tuple[int, str]] = []
    for query in queries:
        try:
            for link in duckduckgo_search_links(query, max_results=8):
                candidates.append((score_thesis_url(link), link))
        except Exception:
            # Search can fail due to rate limits/network. Continue with next query.
            continue

    if not candidates:
        return None

    candidates.sort(key=lambda item: item[0], reverse=True)
    best_score, best_url = candidates[0]
    if best_score <= 0:
        return None
    return best_url


def build_markdown(
    title: str,
    linkedin_url: str,
    thesis_url: Optional[str],
    summary: str,
    rwth_data: Optional[Dict[str, Any]] = None,
) -> str:
    date_str = dt.date.today().isoformat()
    safe_title = title.replace("'", "\\'")
    safe_summary = summary.replace("'", "\\'")

    thesis_line = (
        f"- Thesis: [{thesis_url}]({thesis_url})"
        if thesis_url
        else "- Thesis: _Not found automatically. Add manually._"
    )
    body = (
        "## Links\n\n"
        f"{thesis_line}\n"
        f"- LinkedIn: [{linkedin_url}]({linkedin_url})\n"
    )
    if rwth_data:
        record_url = rwth_data.get("source_url")
        doi = rwth_data.get("doi")
        if record_url:
            body += f"- RWTH Record: [{record_url}]({record_url})\n"
        if doi:
            body += f"- DOI: `{doi}`\n"

    return (
        "+++\n"
        f"title = '{safe_title}'\n"
        f"date = '{date_str}'\n"
        "draft = false\n"
        f"summary = '{safe_summary}'\n"
        "image = ''\n"
        "image_alt = ''\n"
        "featured = false\n"
        "+++\n\n"
        f"{body}"
    )


def write_graduate_entry(
    output_dir: Path,
    name: str,
    linkedin_url: str,
    thesis_url: Optional[str],
    rwth_data: Optional[Dict[str, Any]],
    overwrite: bool,
    dry_run: bool,
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    filename = slugify(name) + ".md"
    out_file = output_dir / filename

    summary = "Graduate profile with thesis and LinkedIn references."
    content = build_markdown(name, linkedin_url, thesis_url, summary, rwth_data)

    if out_file.exists() and not overwrite:
        raise FileExistsError(
            f"File already exists: {out_file}. Use --overwrite to replace it."
        )

    if dry_run:
        print(content)
    else:
        out_file.write_text(content, encoding="utf-8")
    return out_file


def validate_linkedin_url(linkedin_url: str) -> None:
    parsed = urllib.parse.urlparse(linkedin_url)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("LinkedIn URL must start with http:// or https://")
    if "linkedin.com" not in parsed.netloc.lower():
        raise ValueError("URL does not look like a LinkedIn URL.")


def validate_rwth_record_url(rwth_url: str) -> None:
    parsed = urllib.parse.urlparse(rwth_url)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("RWTH URL must start with http:// or https://")
    if "publications.rwth-aachen.de" not in parsed.netloc.lower():
        raise ValueError("RWTH URL must be on publications.rwth-aachen.de")
    if "/record/" not in parsed.path:
        raise ValueError("RWTH URL must look like .../record/<id>")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a Hugo Graduates entry from a LinkedIn URL."
    )
    parser.add_argument("--linkedin", required=True, help="LinkedIn profile URL")
    parser.add_argument(
        "--name",
        default="",
        help="Graduate name (optional; auto-derived from LinkedIn URL when omitted)",
    )
    parser.add_argument(
        "--thesis",
        default="",
        help="Thesis URL (optional; skips auto-discovery when provided)",
    )
    parser.add_argument(
        "--rwth-url",
        default="",
        help="RWTH Publications record URL (optional; used to extract thesis/PDF metadata)",
    )
    parser.add_argument(
        "--out-dir",
        default=DEFAULT_OUTPUT_DIR,
        help=f"Output directory (default: {DEFAULT_OUTPUT_DIR})",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing file if it already exists",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print generated markdown without writing file",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        validate_linkedin_url(args.linkedin)
    except ValueError as exc:
        print(f"Error: {exc}")
        return 2

    if args.rwth_url.strip():
        try:
            validate_rwth_record_url(args.rwth_url.strip())
        except ValueError as exc:
            print(f"Error: {exc}")
            return 2

    name = args.name.strip() or extract_name_from_linkedin(args.linkedin)
    thesis_url = args.thesis.strip() or None
    rwth_data: Optional[Dict[str, Any]] = None

    if args.rwth_url.strip():
        print("Extracting metadata from RWTH record...")
        try:
            rwth_data = extract_rwth_metadata(args.rwth_url.strip())
        except Exception as exc:
            print(f"Warning: could not extract RWTH metadata ({exc}).")
        else:
            rwth_author = (rwth_data.get("author") or "").strip()
            if rwth_author and not args.name.strip():
                name = normalize_rwth_author(rwth_author)
                print(f"Using name from RWTH author field: {name}")
            if not thesis_url:
                thesis_url = rwth_data.get("pdf_url") or rwth_data.get("source_url")
                if thesis_url:
                    print(f"Using thesis URL from RWTH metadata: {thesis_url}")

    if not thesis_url:
        print("Searching for thesis URL from public web results...")
        thesis_url = discover_thesis_url(name)
        if thesis_url:
            print(f"Found thesis candidate: {thesis_url}")
        else:
            print("No thesis URL found automatically.")

    out_dir = Path(args.out_dir)
    try:
        out_file = write_graduate_entry(
            output_dir=out_dir,
            name=name,
            linkedin_url=args.linkedin,
            thesis_url=thesis_url,
            rwth_data=rwth_data,
            overwrite=args.overwrite,
            dry_run=args.dry_run,
        )
    except FileExistsError as exc:
        print(f"Error: {exc}")
        return 3

    if args.dry_run:
        print("\nDry run complete. No file written.")
    else:
        print(f"Created: {out_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
