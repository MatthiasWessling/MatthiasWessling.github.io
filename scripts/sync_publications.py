#!/usr/bin/env python3
"""
Sync journal publications from OpenAlex into content/publications/.

Source of truth for *machine* metadata: OpenAlex works for ORCID
0000-0002-7874-5315 (author A5031459065). LinkedIn remains a human cue for
what is new; this script does not scrape LinkedIn.

Usage:
  python scripts/sync_publications.py --dry-run
  python scripts/sync_publications.py
  python scripts/sync_publications.py --since-year 2024
  python scripts/sync_publications.py --overwrite
  python scripts/sync_publications.py --limit 20

Default import covers the full career (from 1990). Pass --since-year for a narrower window.
"""

from __future__ import annotations

import argparse
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT_DIR = ROOT / "content" / "publications"
DEFAULT_REPORT = ROOT / "data" / "publications_sync_report.json"

# Canonical OpenAlex identity for Matthias Wessling (DWI / RWTH).
DEFAULT_ORCID = "0000-0002-7874-5315"
DEFAULT_OPENALEX_AUTHOR = "A5031459065"

USER_AGENT = (
    "MatthiasWesslingWebsite/1.0 "
    "(https://matthiaswessling.github.io; ORCID "
    f"{DEFAULT_ORCID})"
)

# Work types to import (OpenAlex type filter; OR within one field).
DEFAULT_TYPES = ("article", "review")

# Never overwrite these slugs (hand-curated pages).
PRESERVE_SLUGS: Set[str] = set()


@dataclass
class Publication:
    openalex_id: str
    title: str
    doi: str
    publication_year: int
    publication_date: str
    journal: str
    authors: List[str] = field(default_factory=list)
    abstract: str = ""
    paper_url: str = ""
    cited_by_count: int = 0
    tags: List[str] = field(default_factory=list)
    work_type: str = "article"

    @property
    def slug(self) -> str:
        if self.doi:
            return slugify(self.doi.replace("/", "-"))
        return slugify(f"{self.publication_year}-{self.title}")[:80]


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
    return value or "publication"


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


def toml_string_list(values: Sequence[str]) -> str:
    if not values:
        return "[]"
    return "[" + ", ".join(toml_string(v) for v in values) + "]"


def reconstruct_abstract(inverted: Optional[Dict[str, List[int]]]) -> str:
    if not inverted:
        return ""
    positions: List[Tuple[int, str]] = []
    for word, idxs in inverted.items():
        for i in idxs:
            positions.append((i, word))
    if not positions:
        return ""
    positions.sort(key=lambda x: x[0])
    text = " ".join(w for _, w in positions)
    text = re.sub(r"\s+([,.;:!?])", r"\1", text)
    return text.strip()


def http_get_json(url: str, *, retries: int = 3) -> Dict[str, Any]:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    last_err: Optional[Exception] = None
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as exc:
            last_err = exc
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"OpenAlex request failed after {retries} tries: {url}") from last_err


def openalex_id_short(value: str) -> str:
    # https://openalex.org/W123 -> W123
    return value.rstrip("/").rsplit("/", 1)[-1]


def normalize_doi(value: Optional[str]) -> str:
    if not value:
        return ""
    doi = value.strip()
    doi = re.sub(r"^https?://(dx\.)?doi\.org/", "", doi, flags=re.I)
    return doi.strip()


def normalize_author_name(name: str) -> str:
    """Prefer ASCII Wessling spelling for site-facing author lists."""
    return (name or "").replace("Weßling", "Wessling").replace("weßling", "wessling").strip()


def parse_work(raw: Dict[str, Any]) -> Optional[Publication]:
    title = (raw.get("title") or raw.get("display_name") or "").strip()
    if not title:
        return None

    doi = normalize_doi(raw.get("doi"))
    year = int(raw.get("publication_year") or 0)
    pub_date = (raw.get("publication_date") or "").strip()
    if not pub_date and year:
        pub_date = f"{year}-01-01"

    loc = raw.get("primary_location") or {}
    source = loc.get("source") or {}
    journal = (source.get("display_name") or loc.get("raw_source_name") or "").strip()
    paper_url = (
        (loc.get("landing_page_url") or "").strip()
        or (f"https://doi.org/{doi}" if doi else "")
        or (raw.get("id") or "")
    )

    authors: List[str] = []
    for authorship in raw.get("authorships") or []:
        author = authorship.get("author") or {}
        name = normalize_author_name(author.get("display_name") or "")
        if name and name not in authors:
            authors.append(name)

    concepts = raw.get("concepts") or []
    tags: List[str] = []
    for concept in sorted(concepts, key=lambda c: float(c.get("score") or 0), reverse=True):
        name = (concept.get("display_name") or "").strip()
        level = concept.get("level")
        if name and level in (1, 2) and name not in tags:
            tags.append(name)
        if len(tags) >= 6:
            break

    return Publication(
        openalex_id=openalex_id_short(raw.get("id") or ""),
        title=title,
        doi=doi,
        publication_year=year,
        publication_date=pub_date,
        journal=journal,
        authors=authors,
        abstract=reconstruct_abstract(raw.get("abstract_inverted_index")),
        paper_url=paper_url,
        cited_by_count=int(raw.get("cited_by_count") or 0),
        tags=tags,
        work_type=(raw.get("type") or "article").strip(),
    )


def fetch_works(
    *,
    author_id: str,
    since_year: Optional[int],
    types: Sequence[str],
    limit: Optional[int],
) -> List[Publication]:
    type_filter = "|".join(types)
    filters = [
        f"author.id:{author_id}",
        f"type:{type_filter}",
    ]
    if since_year is not None:
        filters.append(f"from_publication_date:{since_year}-01-01")
    base = "https://api.openalex.org/works"
    per_page = 50
    cursor = "*"
    pubs: List[Publication] = []

    while cursor:
        params = {
            "filter": ",".join(filters),
            "sort": "publication_date:desc",
            "per_page": str(per_page),
            "cursor": cursor,
        }
        url = f"{base}?{urllib.parse.urlencode(params)}"
        payload = http_get_json(url)
        for raw in payload.get("results") or []:
            pub = parse_work(raw)
            if pub:
                pubs.append(pub)
            if limit is not None and len(pubs) >= limit:
                return pubs
        cursor = (payload.get("meta") or {}).get("next_cursor")
        if not cursor:
            break
        time.sleep(0.2)
    return pubs


def existing_source(path: Path) -> str:
    if not path.exists():
        return ""
    text = path.read_text(encoding="utf-8")
    m = re.search(r'(?m)^source\s*=\s*"([^"]+)"\s*$', text)
    return (m.group(1) if m else "").strip()


def existing_openalex_ids(out_dir: Path) -> Dict[str, Path]:
    found: Dict[str, Path] = {}
    for path in out_dir.glob("*.md"):
        if path.name == "_index.md":
            continue
        text = path.read_text(encoding="utf-8")
        m = re.search(r'(?m)^openalex_id\s*=\s*"([^"]+)"\s*$', text)
        if m:
            found[m.group(1)] = path
    return found


def build_markdown(pub: Publication) -> str:
    date = pub.publication_date or f"{pub.publication_year or 1970}-01-01"
    summary = pub.abstract[:280].rsplit(" ", 1)[0] + "…" if len(pub.abstract) > 280 else pub.abstract
    abstract_body = pub.abstract or "_No abstract available from OpenAlex._"

    lines = [
        "+++",
        f"title = {toml_string(pub.title)}",
        f"date = {toml_string(date)}",
        "draft = false",
        f"summary = {toml_string(summary)}",
        f"abstract = {toml_string(pub.abstract)}",
        f"authors = {toml_string_list(pub.authors)}",
        f"publication = {toml_string(pub.journal)}",
        f"publication_year = {toml_string(str(pub.publication_year or ''))}",
        f"doi = {toml_string(pub.doi)}",
        f"paper_url = {toml_string(pub.paper_url)}",
        f"openalex_id = {toml_string(pub.openalex_id)}",
        f"cited_by_count = {pub.cited_by_count}",
        f'work_type = {toml_string(pub.work_type)}',
        'source = "openalex"',
        f"tags = {toml_string_list(pub.tags)}",
        "+++",
        "",
        "## Abstract",
        "",
        abstract_body,
        "",
        "## Links",
        "",
    ]
    if pub.doi:
        lines.append(f"- DOI: [{pub.doi}](https://doi.org/{pub.doi})")
    if pub.paper_url:
        lines.append(f"- Publisher / landing page: [{pub.paper_url}]({pub.paper_url})")
    if pub.openalex_id:
        lines.append(
            f"- OpenAlex: [{pub.openalex_id}](https://openalex.org/{pub.openalex_id})"
        )
    lines.append("")
    return "\n".join(lines)


def write_publications(
    pubs: Iterable[Publication],
    out_dir: Path,
    *,
    overwrite: bool,
    dry_run: bool,
) -> Dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    by_id = existing_openalex_ids(out_dir)
    created = updated = skipped = preserved = 0
    actions: List[Dict[str, str]] = []

    for pub in pubs:
        path = out_dir / f"{pub.slug}.md"
        # Prefer updating the file already keyed by this OpenAlex id.
        if pub.openalex_id in by_id:
            path = by_id[pub.openalex_id]

        if path.name == "_index.md":
            skipped += 1
            continue
        if pub.slug in PRESERVE_SLUGS or path.stem in PRESERVE_SLUGS:
            preserved += 1
            actions.append({"action": "preserve", "slug": path.stem, "title": pub.title})
            continue

        src = existing_source(path)
        if path.exists() and src == "manual":
            preserved += 1
            actions.append({"action": "preserve-manual", "slug": path.stem, "title": pub.title})
            continue

        if path.exists() and not overwrite:
            skipped += 1
            actions.append({"action": "skip-exists", "slug": path.stem, "title": pub.title})
            continue

        md = build_markdown(pub)
        action = "update" if path.exists() else "create"
        if dry_run:
            actions.append({"action": f"dry-{action}", "slug": path.stem, "title": pub.title})
            if action == "create":
                created += 1
            else:
                updated += 1
            continue

        path.write_text(md, encoding="utf-8")
        actions.append({"action": action, "slug": path.stem, "title": pub.title})
        if action == "create":
            created += 1
        else:
            updated += 1

    return {
        "created": created,
        "updated": updated,
        "skipped": skipped,
        "preserved": preserved,
        "actions": actions,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync publications from OpenAlex into Hugo content.")
    parser.add_argument("--orcid", default=DEFAULT_ORCID, help="ORCID iD (documentation / User-Agent)")
    parser.add_argument(
        "--author-id",
        default=DEFAULT_OPENALEX_AUTHOR,
        help="OpenAlex author id (e.g. A5031459065)",
    )
    parser.add_argument(
        "--since-year",
        type=int,
        default=1990,
        help="Import works from this year onward (default: 1990, full career)",
    )
    parser.add_argument(
        "--types",
        default=",".join(DEFAULT_TYPES),
        help="Comma-separated OpenAlex work types (default: article,review)",
    )
    parser.add_argument("--limit", type=int, default=None, help="Max works to import")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--overwrite", action="store_true", help="Refresh existing openalex-sourced pages")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    types = [t.strip() for t in args.types.split(",") if t.strip()]
    print(
        f"Fetching OpenAlex works for {args.author_id} "
        f"(ORCID {args.orcid}) since {args.since_year}, types={types}"
    )
    pubs = fetch_works(
        author_id=args.author_id,
        since_year=args.since_year,
        types=types,
        limit=args.limit,
    )
    print(f"Fetched {len(pubs)} works")

    stats = write_publications(
        pubs,
        args.out_dir,
        overwrite=args.overwrite,
        dry_run=args.dry_run,
    )
    # Keep the report lean (no full abstracts) so Hugo's data/ JSON mount stays light.
    report = {
        "author_id": args.author_id,
        "orcid": args.orcid,
        "since_year": args.since_year,
        "types": types,
        "fetched": len(pubs),
        "dry_run": args.dry_run,
        "overwrite": args.overwrite,
        **{k: stats[k] for k in ("created", "updated", "skipped", "preserved")},
        "publications": [
            {
                "openalex_id": p.openalex_id,
                "doi": p.doi,
                "title": p.title,
                "publication_year": p.publication_year,
                "journal": p.journal,
                "slug": p.slug,
            }
            for p in pubs
        ],
        "actions": stats["actions"],
    }
    if not args.dry_run:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"Wrote report {args.report}")

    print(
        f"created={stats['created']} updated={stats['updated']} "
        f"skipped={stats['skipped']} preserved={stats['preserved']}"
        + (" (dry-run)" if args.dry_run else "")
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
