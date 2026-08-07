#!/usr/bin/env python3
"""
Match Scopus RIS authors to graduate detail pages and attach publications.

Usage:
  python scripts/enrich_graduates_publications.py --ris PATH/to/export.ris
  python scripts/enrich_graduates_publications.py --ris PATH --dry-run
  python scripts/enrich_graduates_publications.py --ris PATH --report data/graduates_publications_report.json
"""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


DEFAULT_GRADUATES_DIR = "content/graduates"
DEFAULT_REPORT = "data/graduates_publications_report.json"

PARTICLES = {
    "van",
    "von",
    "de",
    "der",
    "den",
    "ter",
    "ten",
    "te",
    "di",
    "da",
    "do",
    "dos",
    "das",
    "la",
    "le",
    "el",
    "al",
    "af",
    "zu",
    "zum",
    "zur",
}

# When the same AU string maps to multiple graduates, assign by title keywords.
# First matching rule wins; unmatched ambiguous pubs stay unassigned.
AMBIGUOUS_TITLE_RULES: Dict[str, List[Tuple[str, Tuple[str, ...]]]] = {
    # Martin = Flow-MRI; Monika = responsive / enzymatically active membranes
    "Wiese, M.": [
        (
            "martin-wiese",
            (
                "mri",
                "velocimetry",
                "flow and filtration imaging",
                "chaotic flow",
                "shell and lumen",
                "microstructured spacer",
                "helically microstructured",
                "parahydrogen",
                "hyperpolarization",
                "cell density",
                "cell viability",
            ),
        ),
        (
            "monika-t-wiese",
            (
                "microgel",
                "mikrogel",
                "enzyme",
                "catalytically",
                "metal–organic",
                "metal-organic",
                "tunable permeability",
                "switchable",
                "sorption behavior",
                "poly(poss",
            ),
        ),
    ],
    # Scopus lists tissue-engineering / microgel work as Lohaus, T. (not S.)
    "Lohaus, T.": [
        (
            "suzana-lohaus",
            (
                "tissue",
                "mini-tissue",
                "microgel",
                "cell adhesion",
                "scaffold-free",
                "bioreactor",
                "fouling prevention",
                "direct membrane heating",
                "rayleigh",
                "mobility and molecular",
            ),
        ),
    ],
}

# Manual surname / AU overrides when automatic parsing is insufficient.
# Prefer author_aliases in each graduate's front matter for name changes;
# this dict remains for typos / one-off Scopus forms.
# Keys are graduate markdown filenames (without .md).
MANUAL_ALIASES: Dict[str, List[str]] = {
    # CSV typo "KorcnPercin" / page "korcan-percin"
    "korcan-percin": ["Percin, K."],
    # CSV "RobertFemmer"
    "robert-femmer": ["Femmer, R."],
    # Elizaveta Evdochenko page vs Lisa Evdochenko in CSV
    "elizaveta-evdochenko": ["Evdochenko, E."],
    # Therese / Theresa Krahnstöver
    "therese-krahnstoever": ["Krahnstöver, T.", "Krahnstoever, T.", "Krahnstover, T."],
    "theresa-b-m-roesener": ["Rösener, T.", "Roesener, T.", "Rosener, T."],
    "sven-lyko": ["Lyko, S."],
    "jonas-loewenberg": ["Löwenberg, J.", "Loewenberg, J.", "Lowenberg, J."],
    "tobias-luelf": ["Lülf, T.", "Luelf, T.", "Lulf, T."],
    "lars-i-e-peters": ["Peters, L."],
    "marina-lazar": ["Lazar, M."],
    "gerrald-bargeman": ["Bargeman, G."],
    "jo-o-miguel-de-sousa-andre": ["André, J.", "Andre, J.", "de Sousa André, J."],
    "piotr-edward-dlugolecki": ["Długołęcki, P.", "Dlugolecki, P.", "Dlugolecki, P.E."],
    "l-de-geeter": ["De Geeter, B.A.", "de Geeter, L.", "De Geeter, L."],
    # Saiful often appears as "Saiful" or "Saiful, S."
    "saiful": ["Saiful", "Saiful, S."],
}


def fold(text: str) -> str:
    """Lowercase ASCII-ish fold for comparison (ä→ae style then strip accents)."""
    text = (text or "").strip().lower()
    for src, dst in (
        ("ä", "ae"),
        ("ö", "oe"),
        ("ü", "ue"),
        ("ß", "ss"),
        ("æ", "ae"),
        ("ø", "o"),
        ("å", "a"),
        ("ł", "l"),
        ("ń", "n"),
        ("ś", "s"),
        ("ź", "z"),
        ("ż", "z"),
        ("ć", "c"),
        ("ę", "e"),
        ("ą", "a"),
    ):
        text = text.replace(src, dst)
    normalized = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in normalized if not unicodedata.combining(ch))


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


def split_given_surname(full_name: str) -> Tuple[List[str], List[str]]:
    """
    Split a graduate display name into given-name tokens and surname tokens.
    Handles particles (van der, de, di) and glued typos like RobertFemmer.
    """
    name = re.sub(r"\s+", " ", (full_name or "").strip())
    # Insert space before capital runs in glued CamelCase surnames/names.
    name = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", name)
    # Drop trailing credentials-like tokens already uncommon here.
    tokens = [t for t in re.split(r"[ \u00a0]+", name) if t and t not in {"-", "–"}]
    # Strip punctuation around tokens but keep hyphens inside (Jan-Bernd).
    cleaned: List[str] = []
    for tok in tokens:
        tok = tok.strip(".,;")
        if not tok:
            continue
        # Expand initials like "K.E." already split; keep single letters.
        cleaned.append(tok)

    if not cleaned:
        return [], []

    # Surname: trailing particle chain + final non-particle word(s).
    # Prefer last token as surname core; pull preceding particles into surname.
    surname: List[str] = [cleaned[-1]]
    i = len(cleaned) - 2
    while i >= 0 and fold(cleaned[i]).rstrip(".") in PARTICLES:
        surname.insert(0, cleaned[i])
        i -= 1
    # Two-part Hispanic-style surnames without particles (Restrepo Toro)
    if i >= 0 and fold(cleaned[i]).rstrip(".") not in PARTICLES:
        # Only treat as double surname when the penultimate is capitalized word
        # and not a clear given name with middle initials already taken.
        # Heuristic: if total tokens >= 3 and penultimate has length > 2, include it
        # only when the last two tokens are both longer given-looking surnames
        # known patterns: Restrepo Toro.
        if len(cleaned) >= 3 and len(cleaned[-2]) > 3 and "." not in cleaned[-2]:
            # Conservative: only if no particles and penultimate is not a single letter
            if fold(cleaned[-2]) not in PARTICLES:
                # Check if penultimate looks like surname (not particle); include
                # for names with 3+ parts where first is given.
                pass
    given = cleaned[: i + 1] if i >= 0 else []

    # Special-case known double surnames.
    joined = " ".join(fold(t) for t in cleaned)
    if "restrepo toro" in joined:
        # Maria Adelaida Restrepo Toro
        surname = ["Restrepo", "Toro"]
        given = [t for t in cleaned if fold(t) not in {"restrepo", "toro"}]
    if "di marino" in joined:
        surname = ["Di", "Marino"]
        given = [t for t in cleaned if fold(t) not in {"di", "marino"}]
    if "van der vegt" in joined:
        surname = ["van", "der", "Vegt"]
        given = [t for t in cleaned if fold(t) not in {"van", "der", "vegt"}]
    if "van de ven" in joined:
        surname = ["van", "de", "Ven"]
        given = [t for t in cleaned if fold(t) not in {"van", "de", "ven"}]
    if "de geeter" in joined:
        surname = ["de", "Geeter"]
        given = [t for t in cleaned if fold(t) not in {"de", "geeter", "l"}]
    if "de jong" in joined:
        surname = ["de", "Jong"]
        given = [t for t in cleaned if fold(t) not in {"de", "jong"}]
    if "de sousa" in joined or "miguel de sousa" in joined:
        surname = [cleaned[-1]]
        given = cleaned[:-1]

    return given, surname


def initials_from_given(given: Sequence[str]) -> str:
    """Return concatenated initials like 'CB' or 'AKE' (letters only, upper)."""
    letters: List[str] = []
    for tok in given:
        # Token may be "K." or "Jan-Bernd" or "Maria"
        parts = re.split(r"[-.]+", tok)
        for part in parts:
            part = part.strip()
            if not part:
                continue
            if len(part) == 1:
                letters.append(part.upper())
            else:
                letters.append(part[0].upper())
    return "".join(letters)


def parse_ris_author(au: str) -> Tuple[str, str]:
    """
    Parse 'Surname, F.M.' or 'Surname Particles, F.' into (folded_surname, initials).
    Returns initials as uppercase letters only.
    """
    au = au.strip()
    if "," in au:
        surname, rest = au.split(",", 1)
    else:
        # Rare: 'Saiful'
        surname, rest = au, ""
    surname_key = fold(re.sub(r"\s+", " ", surname).strip())
    initials = "".join(ch.upper() for ch in rest if ch.isalpha())
    return surname_key, initials


def surname_keys_for_graduate(surname_tokens: Sequence[str]) -> List[str]:
    """Candidate folded surname strings to match against RIS AU surnames."""
    if not surname_tokens:
        return []
    folded_tokens = [fold(t).rstrip(".") for t in surname_tokens]
    keys = set()
    keys.add(" ".join(folded_tokens))
    # Without particles
    core = [t for t in folded_tokens if t not in PARTICLES]
    if core:
        keys.add(" ".join(core))
        keys.add(core[-1])
    # Full last token always
    keys.add(folded_tokens[-1])
    return [k for k in keys if k]


def initials_compatible(grad_initials: str, au_initials: str) -> bool:
    """True if graduate and AU initials are compatible.

    Accepts:
    - prefix either way (AKE vs A, NSR vs N)
    - same letters in any order (CB vs BC for Clara Berinike / B.C.)
    - a single AU initial that appears among the graduate's initials
      (Bräsel, B. for Clara Berinike Bräsel)
    """
    g = (grad_initials or "").upper()
    a = (au_initials or "").upper()
    if not g or not a:
        return False
    if a.startswith(g) or g.startswith(a):
        return True
    if len(a) > 1 and sorted(a) == sorted(g):
        return True
    if len(a) == 1 and a in g:
        return True
    return False


@dataclass
class Publication:
    title: str
    year: str = ""
    journal: str = ""
    doi: str = ""
    url: str = ""
    authors: List[str] = field(default_factory=list)
    typ: str = ""

    @property
    def key(self) -> str:
        if self.doi:
            return fold(self.doi)
        return fold(f"{self.year}|{self.title}")

    def doi_url(self) -> str:
        if self.doi:
            return f"https://doi.org/{self.doi}"
        return self.url


@dataclass
class Graduate:
    path: Path
    title: str
    slug: str
    given: List[str]
    surname: List[str]
    initials: str
    surname_keys: List[str]
    aliases: List[str] = field(default_factory=list)
    former_names: List[str] = field(default_factory=list)


def parse_toml_string_list(front: str, key: str) -> List[str]:
    """Parse a simple TOML string array: key = ["a", "b"]."""
    m = re.search(
        rf'^{re.escape(key)}\s*=\s*\[(.*?)\]\s*$',
        front,
        re.M | re.S,
    )
    if not m:
        return []
    return [s.replace('\\"', '"') for s in re.findall(r'"((?:\\.|[^"\\])*)"', m.group(1))]


def parse_ris(path: Path) -> List[Publication]:
    text = path.read_text(encoding="utf-8", errors="replace")
    pubs: List[Publication] = []
    cur: Optional[dict] = None
    for raw in text.splitlines():
        line = raw.rstrip("\n")
        if line.startswith("TY  -"):
            cur = {"TY": line[6:].strip(), "AU": []}
            continue
        if cur is None:
            continue
        if line.startswith("ER  -"):
            authors = cur.get("AU") or []
            pubs.append(
                Publication(
                    title=(cur.get("TI") or "").strip(),
                    year=(cur.get("PY") or "").strip(),
                    journal=(cur.get("T2") or cur.get("JO") or cur.get("JF") or "").strip(),
                    doi=(cur.get("DO") or "").strip(),
                    url=(cur.get("UR") or "").strip(),
                    authors=authors,
                    typ=(cur.get("TY") or "").strip(),
                )
            )
            cur = None
            continue
        if line.startswith("AU  -"):
            cur.setdefault("AU", []).append(line[6:].strip())
            continue
        m = re.match(r"^([A-Z0-9]{2})  - (.*)$", line)
        if m:
            tag, val = m.group(1), m.group(2).strip()
            # Keep first value for repeated tags except AU
            if tag not in cur:
                cur[tag] = val
    return pubs


def load_graduates(graduates_dir: Path) -> List[Graduate]:
    grads: List[Graduate] = []
    for path in sorted(graduates_dir.glob("*.md")):
        if path.name == "_index.md":
            continue
        text = path.read_text(encoding="utf-8")
        if not text.startswith("+++"):
            continue
        end = text.find("+++", 3)
        front = text[3:end] if end > 0 else text
        m = re.search(r'^title\s*=\s*"(.*)"\s*$', front, re.M)
        if not m:
            continue
        title = m.group(1).replace('\\"', '"')
        given, surname = split_given_surname(title)
        initials = initials_from_given(given)
        slug = path.stem
        aliases = list(MANUAL_ALIASES.get(slug, []))
        for alias in parse_toml_string_list(front, "author_aliases"):
            if alias not in aliases:
                aliases.append(alias)
        former_names = parse_toml_string_list(front, "former_names")
        grads.append(
            Graduate(
                path=path,
                title=title,
                slug=slug,
                given=given,
                surname=surname,
                initials=initials,
                surname_keys=surname_keys_for_graduate(surname),
                aliases=aliases,
                former_names=former_names,
            )
        )
    return grads


def match_publications(
    graduates: Sequence[Graduate],
    publications: Sequence[Publication],
) -> Tuple[Dict[str, List[Publication]], dict]:
    """
    Return mapping slug -> publications and a report dict.
    Ambiguous AU strings (multiple graduates, same specificity) are skipped.
    """
    # Build AU-string -> best graduate matches with score
    # First, index graduates by surname key
    by_surname: Dict[str, List[Graduate]] = {}
    for g in graduates:
        for key in g.surname_keys:
            by_surname.setdefault(key, []).append(g)

    # Collect all AU strings from pubs
    au_strings = sorted({a for p in publications for a in p.authors})

    au_owner: Dict[str, Optional[Graduate]] = {}
    ambiguous_aus: List[dict] = []
    unmatched_aus_samples: List[str] = []

    for au in au_strings:
        surname_key, au_initials = parse_ris_author(au)
        candidates = by_surname.get(surname_key, [])
        # Also try last token only
        if not candidates and " " in surname_key:
            candidates = by_surname.get(surname_key.split()[-1], [])

        scored: List[Tuple[int, Graduate]] = []
        for g in candidates:
            # Manual exact alias wins hard
            if any(fold(au) == fold(alias) for alias in g.aliases):
                scored.append((1000, g))
                continue
            if not initials_compatible(g.initials, au_initials):
                continue
            # Score: longer shared initial prefix is better; fuller AU initials better
            shared = 0
            for gc, ac in zip(g.initials, au_initials):
                if gc == ac:
                    shared += 1
                else:
                    break
            score = shared * 10 + len(au_initials) + (5 if surname_key in g.surname_keys[:1] else 0)
            # Prefer exact surname-key equality with full form
            if surname_key == fold(" ".join(g.surname)):
                score += 3
            scored.append((score, g))

        # Alias-only graduates with no surname index hit
        for g in graduates:
            if g in [s[1] for s in scored]:
                continue
            if any(fold(au) == fold(alias) for alias in g.aliases):
                scored.append((1000, g))

        if not scored:
            continue

        scored.sort(key=lambda x: (-x[0], x[1].slug))
        best_score = scored[0][0]
        top = [g for s, g in scored if s == best_score]
        if len(top) > 1:
            au_owner[au] = None
            ambiguous_aus.append(
                {
                    "au": au,
                    "candidates": [g.title for g in top],
                    "score": best_score,
                }
            )
        else:
            au_owner[au] = top[0]

    by_slug = {g.slug: g for g in graduates}
    ambiguous_au_set = {item["au"] for item in ambiguous_aus}

    # Assign pubs
    assigned: Dict[str, List[Publication]] = {g.slug: [] for g in graduates}
    seen: Dict[str, set] = {g.slug: set() for g in graduates}
    ambiguous_resolved = 0
    ambiguous_unresolved = 0

    for pub in publications:
        if not pub.title:
            continue
        owners: List[Graduate] = []
        for au in pub.authors:
            owner = au_owner.get(au)
            if owner is not None:
                if owner not in owners:
                    owners.append(owner)
                continue
            if au in AMBIGUOUS_TITLE_RULES:
                title_fold = fold(pub.title)
                resolved = None
                for slug, keywords in AMBIGUOUS_TITLE_RULES[au]:
                    if any(fold(k) in title_fold for k in keywords):
                        resolved = by_slug.get(slug)
                        break
                if resolved is not None:
                    ambiguous_resolved += 1
                    if resolved not in owners:
                        owners.append(resolved)
                elif au in ambiguous_au_set:
                    ambiguous_unresolved += 1
        for owner in owners:
            if pub.key in seen[owner.slug]:
                continue
            seen[owner.slug].add(pub.key)
            assigned[owner.slug].append(pub)

    # Sort each list by year desc, title
    for slug, pubs in assigned.items():
        pubs.sort(key=lambda p: (p.year or "", p.title), reverse=True)

    matched_grads = sum(1 for pubs in assigned.values() if pubs)
    report = {
        "publications_in_ris": len(publications),
        "graduates": len(graduates),
        "graduates_with_publications": matched_grads,
        "ambiguous_author_strings": ambiguous_aus,
        "ambiguous_title_resolved": ambiguous_resolved,
        "ambiguous_title_unresolved": ambiguous_unresolved,
        "per_graduate_counts": {
            g.slug: {
                "name": g.title,
                "initials": g.initials,
                "surname_keys": g.surname_keys,
                "count": len(assigned[g.slug]),
            }
            for g in graduates
        },
        "graduates_without_publications": [
            {"slug": g.slug, "name": g.title, "initials": g.initials}
            for g in graduates
            if not assigned[g.slug]
        ],
    }
    return assigned, report


PUBLICATIONS_SECTION_RE = re.compile(
    r"\n## Publications\n.*?(?=\n## |\Z)",
    re.S,
)
PUBLICATIONS_TOML_RE = re.compile(
    r"\n\[\[publications\]\]\n(?:.*?\n)*?(?=(?:\n\[\[|\n[a-zA-Z0-9_]+\s*=|\n\+\+\+))",
    re.S,
)


def strip_existing_publications_toml(front: str) -> str:
    """Remove prior [[publications]] tables from TOML front matter body."""
    lines = front.splitlines()
    out: List[str] = []
    i = 0
    while i < len(lines):
        if lines[i].strip() == "[[publications]]":
            i += 1
            while i < len(lines):
                s = lines[i].strip()
                if s.startswith("[[") or (s and not s.startswith("#") and "=" not in s and s != ""):
                    # next table or unexpected — stop without consuming
                    if s.startswith("[["):
                        break
                if s.startswith("[["):
                    break
                # End of this table entry: blank line followed by non-key? Keep consuming
                # key = value lines and blanks until next [[ or end
                if s.startswith("[["):
                    break
                # Stop before a non-publication top-level key that is not indented
                # Publication keys use title/year/journal/doi/url/authors
                if (
                    s
                    and "=" in s
                    and not s.startswith(
                        (
                            "title",
                            "year",
                            "journal",
                            "doi",
                            "url",
                            "authors",
                            "type",
                        )
                    )
                    and not s.startswith("[[")
                ):
                    # Could be next top-level key — but only if previous was blank?
                    # Safer: publications keys only; any other key ends the block.
                    key = s.split("=", 1)[0].strip()
                    if key not in {
                        "title",
                        "year",
                        "journal",
                        "doi",
                        "url",
                        "authors",
                        "type",
                    }:
                        break
                i += 1
            continue
        out.append(lines[i])
        i += 1
    # Collapse excess blank lines at end
    text = "\n".join(out).rstrip() + "\n"
    return text


def publications_toml(pubs: Sequence[Publication]) -> str:
    blocks: List[str] = []
    for p in pubs:
        authors = "; ".join(p.authors)
        blocks.append(
            "\n".join(
                [
                    "[[publications]]",
                    f"title = {toml_string(p.title)}",
                    f"year = {toml_string(p.year)}",
                    f"journal = {toml_string(p.journal)}",
                    f"doi = {toml_string(p.doi)}",
                    f"url = {toml_string(p.doi_url())}",
                    f"authors = {toml_string(authors)}",
                ]
            )
        )
    return ("\n" + "\n\n".join(blocks) + "\n") if blocks else ""


def publications_markdown(pubs: Sequence[Publication]) -> str:
    if not pubs:
        return ""
    lines = ["## Publications", ""]
    for p in pubs:
        cite_bits = []
        if p.year:
            cite_bits.append(p.year)
        if p.journal:
            cite_bits.append(p.journal)
        meta = f" ({', '.join(cite_bits)})" if cite_bits else ""
        link = p.doi_url()
        if link:
            lines.append(f"- [{p.title}]({link}){meta}")
        else:
            lines.append(f"- {p.title}{meta}")
        if p.authors:
            lines.append(f"  - Authors: {'; '.join(p.authors)}")
        if p.doi:
            lines.append(f"  - DOI: `{p.doi}`")
    lines.append("")
    return "\n".join(lines)


def update_graduate_file(path: Path, pubs: Sequence[Publication], *, dry_run: bool) -> bool:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("+++"):
        raise ValueError(f"Missing TOML front matter: {path}")
    end = text.find("+++", 3)
    if end < 0:
        raise ValueError(f"Unclosed front matter: {path}")
    front = text[3:end]
    body = text[end + 3 :]

    front_clean = strip_existing_publications_toml(front)
    if not front_clean.endswith("\n"):
        front_clean += "\n"
    new_front = front_clean.rstrip() + "\n" + publications_toml(pubs)

    # Drop any previously written markdown Publications section; the single
    # template renders .Params.publications instead.
    body_no_pubs = PUBLICATIONS_SECTION_RE.sub("\n", body).rstrip() + "\n"

    new_text = f"+++{new_front}+++\n{body_no_pubs}"
    if not new_text.endswith("\n"):
        new_text += "\n"

    if new_text == text:
        return False
    if dry_run:
        return True
    path.write_text(new_text, encoding="utf-8")
    return True


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--ris", required=True, help="Path to Scopus RIS export")
    p.add_argument(
        "--graduates-dir",
        default=DEFAULT_GRADUATES_DIR,
        help=f"Graduates content dir (default: {DEFAULT_GRADUATES_DIR})",
    )
    p.add_argument(
        "--report",
        default=DEFAULT_REPORT,
        help=f"Write JSON match report (default: {DEFAULT_REPORT})",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Do not write graduate markdown files",
    )
    p.add_argument(
        "--clear-unmatched",
        action="store_true",
        help="Remove publications sections from graduates with zero matches",
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()
    repo = Path(__file__).resolve().parents[1]
    ris_path = Path(args.ris)
    graduates_dir = Path(args.graduates_dir)
    report_path = Path(args.report)
    if not ris_path.is_absolute():
        ris_path = repo / ris_path
    if not graduates_dir.is_absolute():
        graduates_dir = repo / graduates_dir
    if not report_path.is_absolute():
        report_path = repo / report_path

    publications = parse_ris(ris_path)
    graduates = load_graduates(graduates_dir)
    assigned, report = match_publications(graduates, publications)

    updated = 0
    for g in graduates:
        pubs = assigned.get(g.slug, [])
        if not pubs and not args.clear_unmatched:
            continue
        if update_graduate_file(g.path, pubs, dry_run=args.dry_run):
            updated += 1

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(
        f"RIS pubs={len(publications)} graduates={len(graduates)} "
        f"with_pubs={report['graduates_with_publications']} "
        f"ambiguous_aus={len(report['ambiguous_author_strings'])} "
        f"files_touched={updated} dry_run={args.dry_run}"
    )
    print(f"Report: {report_path}")
    # Show top counts
    counts = sorted(
        (
            (v["count"], v["name"], k)
            for k, v in report["per_graduate_counts"].items()
            if v["count"]
        ),
        reverse=True,
    )
    print("Top matches:")
    for count, name, slug in counts[:15]:
        print(f"  {count:3d}  {name} ({slug})")
    if report["ambiguous_author_strings"]:
        print("Ambiguous AU strings (skipped):")
        for item in report["ambiguous_author_strings"][:20]:
            print(f"  {item['au']} -> {item['candidates']}")
    none = report["graduates_without_publications"]
    print(f"Without publications: {len(none)}")
    for item in none[:25]:
        print(f"  - {item['name']} ({item['slug']})")


if __name__ == "__main__":
    main()
