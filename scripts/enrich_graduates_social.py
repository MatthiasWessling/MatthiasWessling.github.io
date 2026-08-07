#!/usr/bin/env python3
"""
Enrich graduates.csv with social / professional profile URLs.

Primary target: LinkedIn (written into the `linkedin` column).
Also supports ORCID (optional `orcid` column).

Backends:
  1) OpenAlex author search → ORCID (reliable; no LinkedIn)
  2) Bing / DuckDuckGo via crawl_bing_linkedin.py (often captcha-blocked)
  3) Apply a precomputed map from data/graduates_social_found.json

Usage:
  python scripts/enrich_graduates_social.py --openalex-only --write-csv
  python scripts/enrich_graduates_social.py --apply-found data/graduates_social_found.json --write-csv
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
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))
from crawl_bing_linkedin import (  # noqa: E402
    crawl,
    normalize_linkedin_profile_url,
)


DEFAULT_CSV = "data/graduates.csv"
DEFAULT_CANDIDATES = "data/graduates_social_candidates.json"

ORCID_RE = re.compile(r"https?://(?:www\.)?orcid\.org/\d{4}-\d{4}-\d{4}-\d{3}[\dX]", re.I)
SCHOLAR_RE = re.compile(
    r"https?://scholar\.google\.[^/\s\"']+/citations\?[^\s\"']*user=[A-Za-z0-9_-]+",
    re.I,
)
RESEARCHGATE_RE = re.compile(
    r"https?://(?:www\.)?researchgate\.net/profile/[A-Za-z0-9_-]+",
    re.I,
)
TWITTER_RE = re.compile(
    r"https?://(?:www\.)?(?:twitter|x)\.com/(?!share|intent|home|search)[A-Za-z0-9_]+/?",
    re.I,
)

POSITIVE_HINTS = (
    "rwth",
    "aachen",
    "avt",
    "verfahrenstechnik",
    "wessling",
    "dissertation",
    "phd",
    "promotion",
    "membrane",
    "electrochem",
    "chemical engineering",
)
NEGATIVE_HINTS = ("pub/dir", "directory", "namesake", "homonym")
USER_AGENT = "graduates-social-enrich/1.0 (mailto:pub.nachweis@ub.rwth-aachen.de)"


@dataclass
class ScoredProfile:
    url: str
    score: float
    title: str = ""
    snippet: str = ""
    reasons: List[str] = field(default_factory=list)


def name_tokens(name: str) -> List[str]:
    tokens = re.findall(r"[A-Za-zÄÖÜäöüß]{2,}", name.lower())
    stop = {"von", "van", "de", "da", "der", "den", "la", "le"}
    return [t for t in tokens if t not in stop]


def slug_tokens(url: str) -> List[str]:
    path = urlparse(url).path.lower()
    slug = path.rstrip("/").split("/")[-1]
    return [t for t in re.split(r"[-_.]+", slug) if len(t) >= 2]


def score_linkedin(name: str, thesis_title: str, hit: Dict[str, Any]) -> ScoredProfile:
    url = hit.get("url") or ""
    title = hit.get("title") or ""
    snippet = hit.get("snippet") or ""
    blob = f"{title} {snippet} {url}".lower()
    reasons: List[str] = []
    score = 0.0
    tokens = name_tokens(name)
    if not tokens:
        return ScoredProfile(url=url, score=-100, title=title, snippet=snippet)

    matched = sum(1 for t in tokens if t in blob)
    score += matched * 2.5
    reasons.append(f"name_hits={matched}/{len(tokens)}")

    slug = slug_tokens(url)
    slug_hits = sum(1 for t in tokens if t in slug or any(t.startswith(s) for s in slug))
    score += slug_hits * 1.5
    if slug_hits:
        reasons.append(f"slug_hits={slug_hits}")

    for hint in POSITIVE_HINTS:
        if hint in blob:
            score += 1.2
            reasons.append(f"+{hint}")

    thesis_words = [
        w
        for w in re.findall(r"[A-Za-zÄÖÜäöüß]{5,}", (thesis_title or "").lower())
        if w not in {"based", "using", "systems", "process", "processes"}
    ]
    thesis_hits = sum(1 for w in thesis_words[:8] if w in blob)
    if thesis_hits:
        score += thesis_hits * 0.8
        reasons.append(f"thesis_hits={thesis_hits}")

    for hint in NEGATIVE_HINTS:
        if hint in blob:
            score -= 4.0
            reasons.append(f"-{hint}")

    if "/pub/dir/" in url.lower() or "/search/" in url.lower():
        score -= 10.0
        reasons.append("-directory")

    if tokens and tokens[-1] not in blob and tokens[-1] not in " ".join(slug):
        score -= 3.0
        reasons.append("-missing_surname")

    return ScoredProfile(url=url, score=score, title=title, snippet=snippet, reasons=reasons)


def pick_best_linkedin(
    name: str,
    thesis_title: str,
    profiles: Sequence[Dict[str, Any]],
    *,
    min_score: float,
    min_margin: float,
) -> Tuple[Optional[ScoredProfile], List[ScoredProfile]]:
    scored = [score_linkedin(name, thesis_title, hit) for hit in profiles]
    scored = [s for s in scored if s.url]
    scored.sort(key=lambda s: s.score, reverse=True)
    if not scored:
        return None, []
    best = scored[0]
    second = scored[1].score if len(scored) > 1 else -999.0
    if best.score >= min_score and (best.score - second) >= min_margin:
        return best, scored
    return None, scored


def extract_other_profiles(web_results: Sequence[Dict[str, Any]]) -> Dict[str, List[str]]:
    found: Dict[str, List[str]] = {
        "orcid": [],
        "google_scholar": [],
        "researchgate": [],
        "twitter": [],
    }
    seen = {k: set() for k in found}

    def add(kind: str, url: str) -> None:
        url = url.rstrip(".,;)")
        if url in seen[kind]:
            return
        seen[kind].add(url)
        found[kind].append(url)

    for hit in web_results:
        blob = " ".join([hit.get("url") or "", hit.get("title") or "", hit.get("snippet") or ""])
        for m in ORCID_RE.findall(blob):
            add("orcid", m)
        for m in SCHOLAR_RE.findall(blob):
            add("google_scholar", m.split("&")[0])
        for m in RESEARCHGATE_RE.findall(blob):
            add("researchgate", m)
        for m in TWITTER_RE.findall(blob):
            add("twitter", m)
    return found


def normalize_orcid(value: str) -> str:
    value = (value or "").strip()
    if not value:
        return ""
    m = ORCID_RE.search(value)
    if m:
        return m.group(0).replace("http://", "https://")
    m = re.search(r"(\d{4}-\d{4}-\d{4}-\d{3}[\dX])", value)
    if m:
        return f"https://orcid.org/{m.group(1)}"
    return ""


def openalex_lookup(name: str) -> Dict[str, str]:
    query = urllib.parse.quote(name)
    url = f"https://api.openalex.org/authors?search={query}&per_page=5"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            data = json.loads(resp.read().decode("utf-8", errors="replace"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        return {}

    tokens = set(name_tokens(name))
    best = None
    best_score = -1
    for author in data.get("results") or []:
        display = (author.get("display_name") or "").lower()
        score = sum(1 for t in tokens if t in display)
        inst_blob = " ".join(
            (i.get("display_name") or "").lower()
            for i in (author.get("last_known_institutions") or [])
        )
        aff_blob = " ".join(
            ((a.get("institution") or {}).get("display_name") or "").lower()
            for a in (author.get("affiliations") or [])[:5]
        )
        blob = f"{inst_blob} {aff_blob}"
        if "aachen" in blob or "rwth" in blob:
            score += 3
        if score > best_score:
            best_score = score
            best = author
    if not best or best_score < max(2, len(tokens) - 1):
        return {}
    return {
        "orcid": normalize_orcid(best.get("orcid") or ""),
        "openalex_id": best.get("id") or "",
        "display_name": best.get("display_name") or "",
    }


def load_csv(path: Path) -> Tuple[List[str], List[Dict[str, str]]]:
    with path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        fieldnames = list(reader.fieldnames or [])
        rows = [dict(row) for row in reader]
    return fieldnames, rows


def write_csv(path: Path, fieldnames: List[str], rows: List[Dict[str, str]]) -> None:
    if "orcid" not in fieldnames:
        if "linkedin" in fieldnames:
            i = fieldnames.index("linkedin") + 1
            fieldnames = fieldnames[:i] + ["orcid"] + fieldnames[i:]
        else:
            fieldnames = fieldnames + ["orcid"]
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            row.setdefault("orcid", "")
            writer.writerow(row)


def search_person(name: str, thesis_title: str, *, prefer: str, pause: float) -> dict:
    result = crawl(
        name=name,
        affiliation="RWTH Aachen",
        linkedin_only=False,
        also_thesis=bool(thesis_title),
        max_results=8,
        pause_seconds=pause,
        prefer=prefer,
    )
    profiles = []
    seen = set()
    for hit in result.get("linkedin_profiles") or []:
        url = normalize_linkedin_profile_url(hit.get("url") or "")
        if not url or url in seen:
            continue
        seen.add(url)
        hit = dict(hit)
        hit["url"] = url
        profiles.append(hit)
    for hit in result.get("web_results") or []:
        url = normalize_linkedin_profile_url(
            " ".join([hit.get("url") or "", hit.get("title") or "", hit.get("snippet") or ""])
        )
        if not url or url in seen:
            continue
        seen.add(url)
        profiles.append(
            {
                "title": hit.get("title") or "",
                "url": url,
                "snippet": hit.get("snippet") or "",
                "source": "linkedin",
            }
        )
    result["linkedin_profiles"] = profiles
    return result


def apply_found_json(
    rows: List[Dict[str, str]],
    found_path: Path,
    *,
    min_confidence: str,
) -> Tuple[int, int]:
    data = json.loads(found_path.read_text(encoding="utf-8"))
    people = data.get("people") or []
    by_name = {(p.get("name") or "").strip().lower(): p for p in people}
    rank = {"high": 3, "medium": 2, "low": 1, "none": 0}
    min_rank = rank.get(min_confidence, 2)
    li_n = 0
    orcid_n = 0
    for row in rows:
        name = (row.get("name") or "").strip()
        hit = by_name.get(name.lower())
        if not hit:
            continue
        conf = (hit.get("confidence") or "none").lower()
        if rank.get(conf, 0) < min_rank:
            continue
        linkedin = normalize_linkedin_profile_url(hit.get("linkedin") or "") or ""
        if linkedin and not (row.get("linkedin") or "").strip():
            row["linkedin"] = linkedin
            li_n += 1
        orcid = normalize_orcid(hit.get("orcid") or "")
        if orcid and not (row.get("orcid") or "").strip():
            row["orcid"] = orcid
            orcid_n += 1
    return li_n, orcid_n


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Search social/professional profiles for graduates.csv rows."
    )
    parser.add_argument("--csv", default=DEFAULT_CSV)
    parser.add_argument("--candidates-out", default=DEFAULT_CANDIDATES)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument(
        "--prefer", choices=("bing", "duckduckgo", "bing-api"), default="duckduckgo"
    )
    parser.add_argument("--pause", type=float, default=1.2)
    parser.add_argument("--person-pause", type=float, default=2.0)
    parser.add_argument("--min-score", type=float, default=6.0)
    parser.add_argument("--min-margin", type=float, default=1.5)
    parser.add_argument("--openalex-only", action="store_true")
    parser.add_argument("--apply-found", default="")
    parser.add_argument(
        "--min-confidence", choices=("high", "medium", "low"), default="medium"
    )
    parser.add_argument("--write-csv", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo = Path(__file__).resolve().parents[1]
    csv_path = Path(args.csv)
    cand_path = Path(args.candidates_out)
    if not csv_path.is_absolute():
        csv_path = repo / csv_path
    if not cand_path.is_absolute():
        cand_path = repo / cand_path

    fieldnames, rows = load_csv(csv_path)

    if args.apply_found:
        found_path = Path(args.apply_found)
        if not found_path.is_absolute():
            found_path = repo / found_path
        li_n, orcid_n = apply_found_json(
            rows, found_path, min_confidence=args.min_confidence
        )
        print(
            f"Applied from {found_path}: linkedin={li_n} orcid={orcid_n} "
            f"(min_confidence={args.min_confidence})"
        )
        if args.write_csv and not args.dry_run:
            write_csv(csv_path, fieldnames, rows)
            print(f"Updated CSV: {csv_path}")
        elif args.dry_run:
            print("Dry-run: CSV not written")
        else:
            print("CSV unchanged (pass --write-csv to apply)")
        return 0

    only_missing = not args.all
    targets: List[Tuple[int, Dict[str, str]]] = []
    for idx, row in enumerate(rows):
        name = (row.get("name") or "").strip()
        if not name:
            continue
        linkedin = (row.get("linkedin") or "").strip()
        if only_missing and linkedin and not args.openalex_only:
            continue
        if args.openalex_only and (row.get("orcid") or "").strip() and only_missing:
            continue
        targets.append((idx, row))
    if args.limit and args.limit > 0:
        targets = targets[: args.limit]

    print(f"Processing {len(targets)} graduates (csv={csv_path})")
    accepted = ambiguous = empty = orcid_hits = 0
    review: Dict[str, Any] = {
        "generated_for": str(csv_path),
        "settings": {
            "prefer": args.prefer,
            "min_score": args.min_score,
            "min_margin": args.min_margin,
            "openalex_only": args.openalex_only,
        },
        "people": [],
    }

    for n, (idx, row) in enumerate(targets, start=1):
        name = (row.get("name") or "").strip()
        thesis = (row.get("thesis_title") or "").strip()
        print(f"[{n}/{len(targets)}] {name}")

        oa = openalex_lookup(name)
        if oa.get("orcid") and not (row.get("orcid") or "").strip():
            if args.write_csv and not args.dry_run:
                rows[idx]["orcid"] = oa["orcid"]
            orcid_hits += 1
            print(f"  ORCID {oa['orcid']} (OpenAlex: {oa.get('display_name')})")

        if args.openalex_only:
            review["people"].append({"name": name, "row_index": idx, "openalex": oa})
            time.sleep(0.2)
            continue

        try:
            result = search_person(name, thesis, prefer=args.prefer, pause=args.pause)
        except Exception as exc:
            print(f"  ERROR: {exc}")
            review["people"].append(
                {"name": name, "row_index": idx, "error": str(exc), "openalex": oa}
            )
            time.sleep(args.person_pause)
            continue

        profiles = result.get("linkedin_profiles") or []
        best, scored = pick_best_linkedin(
            name,
            thesis,
            profiles,
            min_score=args.min_score,
            min_margin=args.min_margin,
        )
        others = extract_other_profiles(result.get("web_results") or [])
        if oa.get("orcid"):
            others.setdefault("orcid", [])
            if oa["orcid"] not in others["orcid"]:
                others["orcid"].insert(0, oa["orcid"])

        entry = {
            "name": name,
            "row_index": idx,
            "graduate_date": row.get("graduate_date") or "",
            "rwth_url": row.get("rwth_url") or "",
            "accepted_linkedin": best.url if best else "",
            "accepted_score": best.score if best else None,
            "linkedin_candidates": [asdict(s) for s in scored[:5]],
            "other_profiles": others,
            "openalex": oa,
            "notes": result.get("notes") or [],
        }

        if best:
            accepted += 1
            print(f"  ACCEPT {best.url} (score={best.score:.1f})")
            if args.write_csv and not args.dry_run:
                rows[idx]["linkedin"] = best.url
        elif scored:
            ambiguous += 1
            top = scored[0]
            print(f"  AMBIGUOUS top={top.url} score={top.score:.1f}")
        else:
            empty += 1
            print("  NONE found")

        review["people"].append(entry)
        if n < len(targets) and args.person_pause > 0:
            time.sleep(args.person_pause)

    review["summary"] = {
        "processed": len(targets),
        "accepted": accepted,
        "ambiguous": ambiguous,
        "none": empty,
        "orcid_hits": orcid_hits,
    }
    print(
        f"Done. accepted={accepted} ambiguous={ambiguous} none={empty} "
        f"orcid={orcid_hits} processed={len(targets)}"
    )

    if args.dry_run:
        print("Dry-run: no files written")
        return 0

    cand_path.parent.mkdir(parents=True, exist_ok=True)
    cand_path.write_text(json.dumps(review, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote candidates: {cand_path}")

    if args.write_csv:
        write_csv(csv_path, fieldnames, rows)
        print(f"Updated CSV: {csv_path}")
    else:
        print("CSV unchanged (pass --write-csv to apply)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
