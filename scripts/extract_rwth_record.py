#!/usr/bin/env python3
"""
Extract structured thesis metadata from an RWTH Publications record URL.

Example:
  python scripts/extract_rwth_record.py \
    --url "https://publications.rwth-aachen.de/record/1028159"

Optional:
  --output rwth_1028159.json   # write JSON to file
  --markdown                   # also print a Markdown summary
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


def validate_rwth_record_url(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("URL must start with http:// or https://")
    if "publications.rwth-aachen.de" not in parsed.netloc.lower():
        raise ValueError("URL must be on publications.rwth-aachen.de")
    if "/record/" not in parsed.path:
        raise ValueError("URL must look like .../record/<id>")
    return url


def fetch_html(url: str, timeout: int = 20) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        encoding = resp.headers.get_content_charset() or "utf-8"
        return resp.read().decode(encoding, errors="replace")


def strip_tags(raw_html: str) -> str:
    # Remove script/style first to reduce noise.
    cleaned = re.sub(r"<script.*?>.*?</script>", " ", raw_html, flags=re.I | re.S)
    cleaned = re.sub(r"<style.*?>.*?</style>", " ", cleaned, flags=re.I | re.S)
    # Strip remaining tags and collapse whitespace.
    text = re.sub(r"<[^>]+>", " ", cleaned)
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def strip_tags_fragment(fragment_html: str) -> str:
    text = re.sub(r"<[^>]+>", " ", fragment_html)
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def first_match(pattern: str, text: str, flags: int = 0) -> Optional[str]:
    match = re.search(pattern, text, flags)
    return match.group(1).strip() if match else None


def clean_title_candidate(value: str) -> str:
    cleaned = re.sub(r"\s+", " ", value).strip()
    if " - RWTH Publications" in cleaned:
        cleaned = cleaned.split(" - RWTH Publications", 1)[0].strip()
    if "png " in cleaned and " = " in cleaned:
        cleaned = cleaned.rsplit("png ", 1)[-1].strip()
    return cleaned


def extract_record_id(url: str, page_text: str) -> Optional[str]:
    from_url = first_match(r"/record/(\d+)", url)
    if from_url:
        return from_url
    return first_match(r"Datensatz-ID:\s*(\d+)", page_text)


def extract_title(raw_html: str, page_text: str) -> Optional[str]:
    # Most reliable: citation metadata if present.
    from_meta = first_match(
        r'<meta[^>]+name="citation_title"[^>]+content="([^"]+)"',
        raw_html,
        flags=re.I,
    )
    if from_meta:
        return clean_title_candidate(html.unescape(from_meta))

    from_og = first_match(
        r'<meta[^>]+property="og:title"[^>]+content="([^"]+)"',
        raw_html,
        flags=re.I,
    )
    if from_og:
        return clean_title_candidate(html.unescape(from_og))

    from_title_tag = first_match(r"<title[^>]*>(.*?)</title>", raw_html, flags=re.I | re.S)
    if from_title_tag:
        cleaned_title_tag = clean_title_candidate(strip_tags_fragment(from_title_tag))
        if cleaned_title_tag and cleaned_title_tag.lower() not in {"h1", "title"}:
            return cleaned_title_tag

    # Fallback to first h1 heading.
    h1 = first_match(r"<h1[^>]*>(.*?)</h1>", raw_html, flags=re.I | re.S)
    if h1:
        cleaned_h1 = strip_tags_fragment(h1)
        if cleaned_h1 and cleaned_h1.lower() not in {"h1", "title"}:
            return clean_title_candidate(cleaned_h1)

    # Fallback: bilingual title ending before the author token.
    bilingual = first_match(
        r"([A-Z][^\n]{30,}=\s*[A-ZÄÖÜ][^\n]{30,}?)\s+[A-Z][a-zA-Z\-']+,\s+[A-Z][a-zA-Z\-']+\s*RWTH",
        page_text,
        flags=re.I,
    )
    if bilingual:
        return clean_title_candidate(bilingual)

    # Last-resort text extraction around known separators.
    text_title = first_match(
        r"RWTH Publications\s+(.+?)\s+(?:\w+,\s+\w+RWTH|Dissertation|OpenAccess)",
        page_text,
        flags=re.I,
    )
    return clean_title_candidate(text_title) if text_title else None


def extract_author(page_text: str) -> Optional[str]:
    # Pattern seen in records: "Brosch, SebastianRWTH*"
    author = first_match(r"([A-Z][a-zA-Z\-']+,\s+[A-Z][a-zA-Z\-']+)\s*RWTH", page_text)
    if author:
        return author
    # Fallback from "vorgelegt von Sebastian Brosch"
    return first_match(r"vorgelegt von\s+([A-Z][a-zA-Z\-']+\s+[A-Z][a-zA-Z\-']+)", page_text, re.I)


def extract_year(page_text: str) -> Optional[int]:
    year_str = first_match(r"Dissertation.*?(\b20\d{2}\b)", page_text, flags=re.I)
    if not year_str:
        year_str = first_match(r"\b(20\d{2})\b", page_text)
    if not year_str:
        return None
    try:
        return int(year_str)
    except ValueError:
        return None


def extract_doi(page_text: str) -> Optional[str]:
    return first_match(r"DOI:\s*(10\.\d{4,9}/[A-Za-z0-9.\-_/]+)", page_text)


def extract_pdf_url(raw_html: str, page_text: str) -> Optional[str]:
    # Prefer explicit URL in rendered text, then fallback to href ending with .pdf.
    from_text = first_match(r"URL:\s*<?(https?://[^\s>]+\.pdf)>?", page_text, flags=re.I)
    if from_text:
        return from_text

    href = first_match(r'href="(https?://[^"]+\.pdf)"', raw_html, flags=re.I)
    if href:
        return html.unescape(href)

    return None


def extract_thesis_type(page_text: str) -> Optional[str]:
    return first_match(r"(Dissertation,\s*Rheinisch-Westfälische.*?Aachen,\s*\d{4})", page_text, re.I)


def extract_language(page_text: str) -> Optional[str]:
    return first_match(r"Sprache\s+([A-Za-z]+)", page_text, re.I)


def extract_advisors(page_text: str) -> Optional[str]:
    advisors = first_match(
        r"Hauptberichter/Gutachter\s+(.+?)(?:Tag der mündlichen Prüfung|Online\s+DOI:|Einrichtungen)",
        page_text,
        re.I,
    )
    if not advisors:
        return None
    # Some records repeat the same block; keep the first occurrence only.
    if "Hauptberichter/Gutachter" in advisors:
        advisors = advisors.split("Hauptberichter/Gutachter", 1)[0].strip()
    advisors = re.sub(r"\s*RWTH\s*\*?\s*", " ", advisors).strip()
    advisors = re.sub(r"\s{2,}", " ", advisors)
    return advisors


def extract_graduate_date(page_text: str) -> Optional[str]:
    return first_match(
        r"Tag der mündlichen Prüfung/Habilitation\s+(\d{4}-\d{2}-\d{2})",
        page_text,
        re.I,
    )


def split_sentences(text: str) -> List[str]:
    items = re.split(r"(?<=[.!?])\s+", text)
    cleaned: List[str] = []
    for item in items:
        sentence = re.sub(r"\s+", " ", item).strip()
        if sentence:
            cleaned.append(sentence)
    return cleaned


def shorten_sentence(sentence: str, width: int = 170) -> str:
    sentence = sentence.strip()
    if len(sentence) <= width:
        return sentence
    return textwrap.shorten(sentence, width=width, placeholder="...")


def extract_abstract_text(page_text: str) -> Optional[str]:
    # Capture the abstract block between "Kurzfassung" and "OpenAccess".
    block = first_match(r"Kurzfassung\s+(.+?)\s+OpenAccess:", page_text, flags=re.I)
    if not block:
        return None

    block = re.sub(r"\s+", " ", block).strip()
    sentences = split_sentences(block)
    if not sentences:
        return block

    # Known starts observed in RWTH bilingual abstracts.
    english_starts = [
        "Porous media plays a significant role",
        "Immiscible fluid-fluid displacement",
        "Gas diffusion electrodes",
        "This thesis",
    ]
    for marker in english_starts:
        marker_match = re.search(re.escape(marker), block, flags=re.I)
        if marker_match:
            return block[marker_match.start() :].strip()

    english_stopwords = {
        "the", "and", "of", "to", "in", "is", "for", "with", "this", "that",
        "from", "are", "as", "by", "on", "was", "were", "be", "or", "at",
    }
    german_markers = {
        "und", "der", "die", "das", "mit", "von", "für", "wird", "durch",
        "diese", "arbeit", "nicht", "sowie", "zeigt", "werden", "einer",
    }

    def sentence_score(sentence: str) -> int:
        words = re.findall(r"[a-zA-Z]+", sentence.lower())
        english_hits = sum(1 for word in words if word in english_stopwords)
        german_hits = sum(1 for word in words if word in german_markers)
        umlaut_penalty = 1 if re.search(r"[äöüÄÖÜß]", sentence) else 0
        return english_hits - german_hits - umlaut_penalty

    # Score sentence windows and cut to the most likely English start.
    best_idx = 0
    best_score = -10_000
    for idx in range(len(sentences)):
        window = sentences[idx : idx + 3]
        score = sum(sentence_score(item) for item in window)
        if score > best_score:
            best_score = score
            best_idx = idx

    if best_score > 0:
        return " ".join(sentences[best_idx:]).strip()
    return block


def condense_abstract_to_bullets(abstract_text: Optional[str], max_points: int = 5) -> List[str]:
    if not abstract_text:
        return []

    sentences = split_sentences(abstract_text)
    if not sentences:
        return []

    useful_sentences: List[str] = []
    for sentence in sentences:
        lower = sentence.lower()
        if len(sentence) < 45:
            continue
        if lower.startswith(("go ", "rate this document", "record created")):
            continue
        useful_sentences.append(sentence)

    if not useful_sentences:
        return []

    keyword_groups = [
        ("scope", ["porous media", "electrochemical co2 reduction", "gas diffusion electrodes", "two-phase flow"]),
        ("challenge", ["unclear", "hypothesized", "triple-phase boundary", "tpb", "challenge"]),
        ("method", ["microfluidics", "clsm", "flim", "developed", "transformer", "simulations"]),
        ("result", ["overall, it could be shown", "it was shown", "measurements showed"]),
        ("impact", ["tailor-made design", "optimize", "efficiency", "selectivity", "fundamentally shifting"]),
    ]

    selected: List[str] = []
    for _, keys in keyword_groups:
        for sentence in useful_sentences:
            lower = sentence.lower()
            if any(key in lower for key in keys):
                compact = shorten_sentence(sentence)
                if compact not in selected:
                    selected.append(compact)
                break
        if len(selected) >= max_points:
            return selected[:max_points]

    for sentence in useful_sentences:
        compact = shorten_sentence(sentence)
        if compact not in selected:
            selected.append(compact)
        if len(selected) >= max_points:
            break

    return selected[:max_points]


def extract_rwth_metadata(url: str) -> Dict[str, Any]:
    validated_url = validate_rwth_record_url(url)
    raw_html = fetch_html(validated_url)
    text = strip_tags(raw_html)

    thesis_title = extract_title(raw_html, text)
    abstract_text = extract_abstract_text(text)
    summary_bullets = condense_abstract_to_bullets(abstract_text, max_points=5)

    result: Dict[str, Any] = {
        "source_url": validated_url,
        "record_id": extract_record_id(validated_url, text),
        "title": thesis_title,
        "thesis_title": thesis_title,
        "author": extract_author(text),
        "year": extract_year(text),
        "graduate_date": extract_graduate_date(text),
        "thesis_type": extract_thesis_type(text),
        "doi": extract_doi(text),
        "pdf_url": extract_pdf_url(raw_html, text),
        "language": extract_language(text),
        "advisors": extract_advisors(text),
        "summary_bullets": summary_bullets,
    }
    return result


def to_markdown(data: Dict[str, Any]) -> str:
    rows = [
        ("Source URL", data.get("source_url")),
        ("Record ID", data.get("record_id")),
        ("Title", data.get("title")),
        ("Author", data.get("author")),
        ("Year", data.get("year")),
        ("Graduate Date", data.get("graduate_date")),
        ("Thesis Type", data.get("thesis_type")),
        ("DOI", data.get("doi")),
        ("PDF URL", data.get("pdf_url")),
        ("Language", data.get("language")),
        ("Advisors", data.get("advisors")),
    ]

    lines = ["## RWTH Record Extract", ""]
    for key, value in rows:
        if value:
            lines.append(f"- **{key}:** {value}")
    bullets = data.get("summary_bullets") or []
    if bullets:
        lines.append("- **Summary (condensed):**")
        for item in bullets:
            lines.append(f"  - {item}")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract structured data from RWTH Publications record pages."
    )
    parser.add_argument(
        "--url",
        required=True,
        help="RWTH Publications record URL (e.g. https://publications.rwth-aachen.de/record/1028159)",
    )
    parser.add_argument(
        "--output",
        default="",
        help="Optional JSON output file path",
    )
    parser.add_argument(
        "--markdown",
        action="store_true",
        help="Print a markdown summary after JSON output",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        data = extract_rwth_metadata(args.url)
    except Exception as exc:
        print(f"Error: {exc}")
        return 1

    json_blob = json.dumps(data, indent=2, ensure_ascii=False)
    print(json_blob)

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json_blob + "\n", encoding="utf-8")
        print(f"\nSaved JSON: {output_path}")

    if args.markdown:
        print("\n" + to_markdown(data))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
