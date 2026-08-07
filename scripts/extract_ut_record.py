#!/usr/bin/env python3
"""
Extract structured thesis metadata from a University of Twente Pure record URL.

Example:
  python scripts/extract_ut_record.py \
    --url "https://research.utwente.nl/en/publications/polymer-nanofoams/"

Optional:
  --output ut_krause.json
  --markdown
"""

from __future__ import annotations

import argparse
import html
import json
import re
import textwrap
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional


USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/123.0.0.0 Safari/537.36"
)


def validate_ut_record_url(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("URL must start with http:// or https://")
    host = parsed.netloc.lower()
    if "research.utwente.nl" not in host and "ris.utwente.nl" not in host:
        raise ValueError("URL must be on research.utwente.nl or ris.utwente.nl")
    if "/publications/" not in parsed.path and "/files/" not in parsed.path:
        raise ValueError("URL must look like .../publications/<slug>/")
    return url.rstrip("/") + ("/" if "/publications/" in parsed.path else "")


def fetch_html(url: str, timeout: int = 30) -> str:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-GB,en;q=0.9,nl;q=0.8",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        encoding = resp.headers.get_content_charset() or "utf-8"
        return resp.read().decode(encoding, errors="replace")


def first_match(pattern: str, text: str, flags: int = 0) -> Optional[str]:
    match = re.search(pattern, text, flags)
    return match.group(1).strip() if match else None


def meta_contents(raw_html: str, name: str) -> List[str]:
    pattern = rf'<meta[^>]+name="{re.escape(name)}"[^>]+content="([^"]+)"'
    return [html.unescape(m) for m in re.findall(pattern, raw_html, flags=re.I)]


def meta_content(raw_html: str, name: str) -> Optional[str]:
    values = meta_contents(raw_html, name)
    return values[0] if values else None


def strip_tags(raw_html: str) -> str:
    cleaned = re.sub(r"<script.*?>.*?</script>", " ", raw_html, flags=re.I | re.S)
    cleaned = re.sub(r"<style.*?>.*?</style>", " ", cleaned, flags=re.I | re.S)
    text = re.sub(r"<[^>]+>", " ", cleaned)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def normalize_date(raw: Optional[str]) -> str:
    if not raw:
        return ""
    raw = raw.strip()
    # YYYY-MM-DD or YYYY/MM/DD
    m = re.match(r"^(\d{4})[/-](\d{1,2})[/-](\d{1,2})$", raw)
    if m:
        return f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
    # YYYY only
    m = re.match(r"^(\d{4})$", raw)
    if m:
        return f"{m.group(1)}-01-01"
    return raw


def author_display_name(raw: str) -> str:
    """Prefer 'Given Family' over 'Family, Given'."""
    value = re.sub(r"\s+", " ", (raw or "").strip())
    if "," in value:
        family, given = [p.strip() for p in value.split(",", 1)]
        if family and given:
            return f"{given} {family}"
    return value


def extract_abstract(raw_html: str) -> str:
    # Prefer Pure thesis abstract portal rendering.
    patterns = [
        r'rendering_researchoutput_abstractportal[^"]*"[^>]*>\s*<div class="textblock">(.*?)</div>',
        r'class="textblock">(.*?)</div>\s*</div>\s*(?:<div|</section|</div>)',
        r"<h\d[^>]*>\s*Abstract\s*</h\d>\s*<div[^>]*>\s*<div class=\"textblock\">(.*?)</div>",
        r"<h\d[^>]*>\s*Abstract\s*</h\d>\s*<div[^>]*>(.*?)</div>",
        r'property="og:description"\s+content="([^"]+)"',
        r'name="description"\s+content="([^"]+)"',
    ]
    for pattern in patterns:
        m = re.search(pattern, raw_html, flags=re.I | re.S)
        if not m:
            continue
        fragment = m.group(1)
        text = strip_tags(fragment) if "<" in fragment else html.unescape(fragment)
        text = re.sub(r"\s+", " ", text).strip()
        if len(text) >= 80:
            return text
    return ""


def mentions_wessling(page_text: str) -> bool:
    return bool(re.search(r"\bWessling\b", page_text, flags=re.I))


def extract_ut_metadata(url: str, *, html_body: Optional[str] = None) -> Dict[str, Any]:
    url = validate_ut_record_url(url)
    raw_html = html_body if html_body is not None else fetch_html(url)
    page_text = strip_tags(raw_html)

    title = meta_content(raw_html, "citation_title")
    if not title:
        title = first_match(
            r'<meta[^>]+property="og:title"[^>]+content="([^"]+)"',
            raw_html,
            flags=re.I,
        )
        if title:
            title = html.unescape(title)

    authors = [author_display_name(a) for a in meta_contents(raw_html, "citation_author")]
    author = authors[0] if authors else ""

    graduate_date = normalize_date(meta_content(raw_html, "citation_publication_date"))
    doi = meta_content(raw_html, "citation_doi") or ""
    if not doi:
        doi_url = first_match(r"https?://doi\.org/(10\.3990/[^\s\"'<>]+)", raw_html, re.I)
        if doi_url:
            doi = doi_url
        else:
            doi = first_match(r"\b(10\.3990/[A-Za-z0-9.\-_]+)\b", page_text) or ""

    pdf = meta_content(raw_html, "citation_pdf_url") or ""
    if not pdf:
        rel = first_match(r'href="(/files/[^"]+\.pdf)"', raw_html, re.I)
        if rel:
            pdf = urllib.parse.urljoin("https://research.utwente.nl", html.unescape(rel))
        else:
            abs_pdf = first_match(
                r'href="(https?://research\.utwente\.nl/files/[^"]+\.pdf)"',
                raw_html,
                re.I,
            )
            if abs_pdf:
                pdf = html.unescape(abs_pdf)

    abstract = extract_abstract(raw_html)
    year = None
    if graduate_date[:4].isdigit():
        year = int(graduate_date[:4])

    return {
        "source_url": url,
        "title": (title or "").strip(),
        "author": author,
        "authors": authors,
        "graduate_date": graduate_date,
        "year": year,
        "doi": doi.strip(),
        "thesis_pdf": pdf.strip(),
        "abstract": abstract,
        "mentions_wessling": mentions_wessling(page_text),
        "institution": "Twente",
    }


def to_markdown(meta: Dict[str, Any]) -> str:
    lines = [
        f"# {meta.get('title') or 'Untitled'}",
        "",
        f"- Author: {meta.get('author') or ''}",
        f"- Graduate date: {meta.get('graduate_date') or ''}",
        f"- DOI: {meta.get('doi') or ''}",
        f"- PDF: {meta.get('thesis_pdf') or ''}",
        f"- Record: {meta.get('source_url') or ''}",
        f"- Mentions Wessling: {meta.get('mentions_wessling')}",
        "",
        "## Abstract",
        "",
        meta.get("abstract") or "_No abstract found._",
        "",
    ]
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract metadata from a University of Twente Pure thesis page."
    )
    parser.add_argument("--url", required=True, help="Pure publication URL")
    parser.add_argument("--output", help="Write JSON to this path")
    parser.add_argument(
        "--markdown",
        action="store_true",
        help="Also print a Markdown summary",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    meta = extract_ut_metadata(args.url)
    text = json.dumps(meta, indent=2, ensure_ascii=False)
    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text + "\n", encoding="utf-8")
        print(f"Wrote {out}")
    else:
        print(text)
    if args.markdown:
        print()
        print(to_markdown(meta))


if __name__ == "__main__":
    main()
