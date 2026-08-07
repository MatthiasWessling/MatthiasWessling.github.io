#!/usr/bin/env python3
"""
Crawl Bing (and DuckDuckGo fallback) to discover LinkedIn profile URLs.

LinkedIn profiles are not scraped directly (login walls / bot blocking).
This tool searches the open web for public LinkedIn /in/ URLs and other
candidate links (thesis, RWTH publications, etc.).

Backends:
  1. Bing HTML search (primary). Often blocked by captcha from datacenter IPs.
  2. DuckDuckGo HTML search (automatic fallback when Bing returns captcha/empty).
  3. Optional Azure Bing Web Search API if BING_SEARCH_KEY is set.

Examples:
  python scripts/crawl_bing_linkedin.py --query "Anna Maria Kalde RWTH"

  python scripts/crawl_bing_linkedin.py \
    --name "Florian Wiesner" \
    --affiliation "RWTH" \
    --linkedin-only

  python scripts/crawl_bing_linkedin.py \
    --name "Sebastian Brosch" \
    --also-thesis \
    --output data/brosch_search.json
"""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from typing import List, Optional, Sequence, Tuple


USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)

LINKEDIN_PROFILE_RE = re.compile(
    r"https?://(?:[\w.-]+\.)?linkedin\.com/in/[\w%\-./]+",
    flags=re.I,
)


@dataclass
class SearchHit:
    title: str
    url: str
    snippet: str
    source: str  # "bing", "duckduckgo", "bing-api", "linkedin"


class BingBlockedError(RuntimeError):
    """Raised when Bing returns a captcha/challenge page instead of results."""


def fetch_html(url: str, timeout: int = 20, data: Optional[bytes] = None) -> str:
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        },
        method="POST" if data is not None else "GET",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        encoding = resp.headers.get_content_charset() or "utf-8"
        return resp.read().decode(encoding, errors="replace")


def clean_text(value: str) -> str:
    value = html.unescape(value)
    value = re.sub(r"<[^>]+>", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def normalize_url(url: str) -> str:
    url = html.unescape(url).strip()
    if url.startswith("//"):
        url = "https:" + url

    # DuckDuckGo redirect wrapper: /l/?uddg=<encoded>
    if "duckduckgo.com/l/?" in url or url.startswith("/l/?"):
        parsed = urllib.parse.urlparse(url if "://" in url else "https://duckduckgo.com" + url)
        query = urllib.parse.parse_qs(parsed.query)
        if "uddg" in query and query["uddg"]:
            return urllib.parse.unquote(query["uddg"][0])

    # Bing often wraps destinations as /ck/a?...&u=a1... encoded URL.
    if "bing.com/ck/" in url or "bing.com/aclick" in url:
        parsed = urllib.parse.urlparse(url)
        query = urllib.parse.parse_qs(parsed.query)
        for key in ("u", "url", "r"):
            if key in query and query[key]:
                candidate = query[key][0]
                if candidate.startswith("a1"):
                    candidate = candidate[2:]
                try:
                    decoded = urllib.parse.unquote(candidate)
                    if decoded.startswith("http"):
                        return decoded
                except Exception:
                    pass
    return url


def normalize_linkedin_profile_url(url: str) -> Optional[str]:
    match = LINKEDIN_PROFILE_RE.search(url)
    if not match:
        return None
    profile = match.group(0)
    profile = profile.split("?")[0].split("#")[0].rstrip("/.,;)")
    parsed = urllib.parse.urlparse(profile)
    parts = [part for part in parsed.path.split("/") if part]
    if len(parts) < 2 or parts[0].lower() != "in":
        return None
    slug = urllib.parse.unquote(parts[1])
    return f"https://www.linkedin.com/in/{slug}/"


def is_bing_challenge(page: str) -> bool:
    lower = page.lower()
    markers = (
        "challenge/verify",
        "captchasuccesspostmessage",
        "please complete the security check",
        "id=\"challenge-form\"",
    )
    return any(marker in lower for marker in markers)


def bing_search_html(query: str, max_results: int = 10) -> List[SearchHit]:
    """Query Bing HTML search and parse organic result blocks."""
    search_url = (
        "https://www.bing.com/search?q="
        + urllib.parse.quote_plus(query)
        + "&setlang=en-US&cc=US"
    )
    page = fetch_html(search_url)
    if is_bing_challenge(page):
        raise BingBlockedError("Bing returned a captcha/challenge page")

    hits: List[SearchHit] = []
    blocks = re.findall(r'<li class="b_algo".*?</li>', page, flags=re.I | re.S)
    for block in blocks:
        href = re.search(r'<h2[^>]*>\s*<a[^>]+href="([^"]+)"', block, flags=re.I | re.S)
        title = re.search(r"<h2[^>]*>\s*<a[^>]*>(.*?)</a>", block, flags=re.I | re.S)
        snippet = re.search(
            r'<p[^>]*class="[^"]*b_lineclamp[^"]*"[^>]*>(.*?)</p>|<p>(.*?)</p>',
            block,
            flags=re.I | re.S,
        )
        if not href:
            continue
        url = normalize_url(href.group(1))
        title_text = clean_text(title.group(1)) if title else ""
        snippet_text = ""
        if snippet:
            snippet_text = clean_text(snippet.group(1) or snippet.group(2) or "")
        hits.append(
            SearchHit(
                title=title_text,
                url=url,
                snippet=snippet_text,
                source="bing",
            )
        )
        if len(hits) >= max_results:
            break
    return hits


def bing_search_api(query: str, max_results: int = 10, api_key: str = "") -> List[SearchHit]:
    """Azure Bing Web Search API (optional; needs BING_SEARCH_KEY)."""
    endpoint = "https://api.bing.microsoft.com/v7.0/search"
    params = urllib.parse.urlencode({"q": query, "count": max(1, min(max_results, 50))})
    req = urllib.request.Request(
        f"{endpoint}?{params}",
        headers={
            "Ocp-Apim-Subscription-Key": api_key,
            "User-Agent": USER_AGENT,
        },
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        payload = json.loads(resp.read().decode("utf-8"))

    hits: List[SearchHit] = []
    for item in payload.get("webPages", {}).get("value", []):
        hits.append(
            SearchHit(
                title=item.get("name", ""),
                url=item.get("url", ""),
                snippet=item.get("snippet", ""),
                source="bing-api",
            )
        )
        if len(hits) >= max_results:
            break
    return hits


def is_duckduckgo_blocked(page: str) -> bool:
    lower = page.lower()
    return "anomaly.js" in lower or "cc=botnet" in lower or "Unfortunately, bots use DuckDuckGo too".lower() in lower


def duckduckgo_search(query: str, max_results: int = 10) -> List[SearchHit]:
    """Query DuckDuckGo HTML endpoint and parse result cards."""
    # Prefer GET; POST is used by some DDG clients but both work when not blocked.
    search_url = "https://html.duckduckgo.com/html/?q=" + urllib.parse.quote_plus(query)
    page = fetch_html(search_url)
    if is_duckduckgo_blocked(page):
        raise RuntimeError("DuckDuckGo bot-check blocked this IP (anomaly.js)")

    hits: List[SearchHit] = []
    anchors = re.findall(
        r'<a[^>]+class="[^"]*result__a[^"]*"[^>]+href="([^"]+)"[^>]*>(.*?)</a>',
        page,
        flags=re.I | re.S,
    )
    snippets = re.findall(
        r'<a[^>]+class="[^"]*result__snippet[^"]*"[^>]*>(.*?)</a>',
        page,
        flags=re.I | re.S,
    )
    for idx, (href, title) in enumerate(anchors):
        snippet = clean_text(snippets[idx]) if idx < len(snippets) else ""
        hits.append(
            SearchHit(
                title=clean_text(title),
                url=normalize_url(href),
                snippet=snippet,
                source="duckduckgo",
            )
        )
        if len(hits) >= max_results:
            break
    return hits


def extract_linkedin_profiles(hits: Sequence[SearchHit]) -> List[SearchHit]:
    profiles: List[SearchHit] = []
    seen = set()
    for hit in hits:
        profile = normalize_linkedin_profile_url(hit.url)
        if not profile:
            profile = normalize_linkedin_profile_url(f"{hit.title} {hit.snippet} {hit.url}")
        if not profile or profile in seen:
            continue
        seen.add(profile)
        profiles.append(
            SearchHit(
                title=hit.title or "LinkedIn profile",
                url=profile,
                snippet=hit.snippet,
                source="linkedin",
            )
        )
    return profiles


def build_queries(
    query: str,
    name: str,
    affiliation: str,
    linkedin_only: bool,
    also_thesis: bool,
) -> List[str]:
    queries: List[str] = []
    base = query.strip()
    person = name.strip()
    aff = affiliation.strip()

    if base:
        queries.append(base)
        queries.append(f"site:linkedin.com/in {base}")
    if person:
        person_q = f'"{person}"'
        if aff:
            person_q = f'{person_q} "{aff}"'
        if not linkedin_only:
            queries.append(person_q)
        queries.append(f"site:linkedin.com/in {person_q}")
        if also_thesis and not linkedin_only:
            queries.append(f"{person_q} thesis OR dissertation")
            queries.append(f"{person_q} site:publications.rwth-aachen.de")

    unique: List[str] = []
    seen = set()
    for item in queries:
        key = item.lower()
        if key in seen:
            continue
        seen.add(key)
        unique.append(item)
    return unique


def search_one(
    query: str,
    max_results: int,
    prefer: str,
    api_key: str,
) -> Tuple[List[SearchHit], List[str]]:
    """
    Run one query against preferred backend + fallbacks.
    Returns (hits, notes).
    """
    notes: List[str] = []
    order: List[str]
    if prefer == "duckduckgo":
        order = ["duckduckgo", "bing", "bing-api"]
    elif prefer == "bing-api":
        order = ["bing-api", "bing", "duckduckgo"]
    else:
        order = ["bing", "bing-api", "duckduckgo"]

    for backend in order:
        try:
            if backend == "bing":
                hits = bing_search_html(query, max_results=max_results)
                if hits:
                    if backend != prefer:
                        notes.append("Fell back to Bing HTML")
                    return hits, notes
                notes.append("Bing HTML returned 0 organic results")
            elif backend == "bing-api":
                if not api_key:
                    continue
                hits = bing_search_api(query, max_results=max_results, api_key=api_key)
                if hits:
                    if backend != prefer:
                        notes.append("Fell back to Bing API")
                    return hits, notes
                notes.append("Bing API returned 0 results")
            elif backend == "duckduckgo":
                hits = duckduckgo_search(query, max_results=max_results)
                if hits:
                    if backend != prefer:
                        notes.append("Fell back to DuckDuckGo (Bing blocked or empty)")
                    return hits, notes
                notes.append("DuckDuckGo returned 0 results")
        except BingBlockedError as exc:
            notes.append(str(exc))
        except urllib.error.HTTPError as exc:
            notes.append(f"{backend} HTTP {exc.code}")
        except Exception as exc:
            notes.append(f"{backend} error: {exc}")
    return [], notes


def crawl(
    query: str = "",
    name: str = "",
    affiliation: str = "",
    linkedin_only: bool = False,
    also_thesis: bool = False,
    max_results: int = 10,
    pause_seconds: float = 0.8,
    prefer: str = "bing",
    api_key: str = "",
) -> dict:
    queries = build_queries(query, name, affiliation, linkedin_only, also_thesis)
    if not queries:
        raise ValueError("Provide --query and/or --name")

    api_key = api_key or os.environ.get("BING_SEARCH_KEY", "").strip()
    all_hits: List[SearchHit] = []
    notes: List[str] = []

    for idx, q in enumerate(queries):
        hits, query_notes = search_one(
            q,
            max_results=max_results,
            prefer=prefer,
            api_key=api_key,
        )
        all_hits.extend(hits)
        for note in query_notes:
            notes.append(f"[{q}] {note}")
        if idx < len(queries) - 1 and pause_seconds > 0:
            time.sleep(pause_seconds)

    deduped: List[SearchHit] = []
    seen_urls = set()
    for hit in all_hits:
        key = hit.url.lower().rstrip("/")
        if not key or key in seen_urls:
            continue
        seen_urls.add(key)
        deduped.append(hit)

    linkedin_profiles = extract_linkedin_profiles(deduped)
    if linkedin_only:
        web_results = [
            hit for hit in deduped if "linkedin.com/in/" in hit.url.lower()
        ]
    else:
        web_results = deduped

    return {
        "queries": queries,
        "backend_preference": prefer,
        "notes": notes,
        "web_results": [asdict(hit) for hit in web_results],
        "linkedin_profiles": [asdict(hit) for hit in linkedin_profiles],
        "counts": {
            "queries": len(queries),
            "web_results": len(web_results),
            "linkedin_profiles": len(linkedin_profiles),
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Search Bing/DuckDuckGo and discover LinkedIn profile URLs."
    )
    parser.add_argument("--query", default="", help="Free-text search query")
    parser.add_argument("--name", default="", help="Person name to search")
    parser.add_argument(
        "--affiliation",
        default="",
        help="Optional affiliation/context (e.g. RWTH, Aachen)",
    )
    parser.add_argument(
        "--linkedin-only",
        action="store_true",
        help="Return only LinkedIn profile-style results",
    )
    parser.add_argument(
        "--also-thesis",
        action="store_true",
        help="Also search for thesis/RWTH publication links",
    )
    parser.add_argument(
        "--prefer",
        choices=("bing", "duckduckgo", "bing-api"),
        default="bing",
        help=(
            "Preferred search backend (default: bing). "
            "Falls back automatically. Set BING_SEARCH_KEY for Azure Bing API."
        ),
    )
    parser.add_argument(
        "--max-results",
        type=int,
        default=10,
        help="Max organic results per query (default: 10)",
    )
    parser.add_argument(
        "--pause",
        type=float,
        default=0.8,
        help="Pause seconds between queries (default: 0.8)",
    )
    parser.add_argument(
        "--output",
        default="",
        help="Optional JSON output path",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        result = crawl(
            query=args.query,
            name=args.name,
            affiliation=args.affiliation,
            linkedin_only=args.linkedin_only,
            also_thesis=args.also_thesis,
            max_results=args.max_results,
            pause_seconds=args.pause,
            prefer=args.prefer,
        )
    except Exception as exc:
        print(f"Error: {exc}")
        return 1

    blob = json.dumps(result, indent=2, ensure_ascii=False)
    print(blob)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as handle:
            handle.write(blob + "\n")
        print(f"\nSaved JSON: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
