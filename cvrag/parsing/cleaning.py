"""Clean raw parser text before section detection, metadata or chunking.

Works on the page-separated text produced by a parser: pages are split by
PAGE_BREAK and the separators are kept in the output. Standard library only.
"""

import re

from . import PAGE_BREAK
from .dates import is_date_line
from .headings import looks_like_heading, match_heading

# --- Step 1: characters -------------------------------------------------------

# Zero-width and direction marks that PDF extraction often leaves behind.
INVISIBLE_CHARS = ("﻿", "​", "‌", "‍", "‎", "‏")
NON_BREAKING_SPACE = " "

# --- Step 2: noise lines ------------------------------------------------------

# Boilerplate lines, matched case-insensitively against the stripped line.
NOISE_PATTERNS = [
    re.compile(r"^synthetic cv for training/demo purposes$", re.IGNORECASE),
    re.compile(r"^page \d+( of \d+)?$", re.IGNORECASE),
]

# How many lines at the top and at the bottom of a page count as header/footer.
HEADER_FOOTER_ZONE = 3

# --- Step 3: whitespace -------------------------------------------------------

SPACE_RUN_PATTERN = re.compile(r"[ \t]+")

# --- Step 4: bullets ----------------------------------------------------------

# A bullet character plus whitespace at the start of a line. Only this prefix is
# replaced, so separators inside a line ("HubSpot - Mailchimp") stay untouched.
BULLET_PREFIX_PATTERN = re.compile(
    r"^[ \t]*[•▪●◦‣∙·*–-][ \t]+"
)
BULLET_MARKER = "- "

# --- Step 5: wrapped lines ----------------------------------------------------

# Headings come from headings.py and date lines from dates.py, so the same rules
# serve section detection later on.

# A line ending in one of these looks finished, so the next line is not a wrap.
SENTENCE_END_CHARS = (".", "!", "?", ":")
# A line ending in one of these is clearly unfinished.
TRAILING_JOIN_CHARS = (",", "&", "/", "-")
CONTINUATION_WORDS = frozenset({
    "and", "or", "of", "in", "with", "for", "to", "the", "a", "an", "on", "at", "by",
})
LAST_WORD_PATTERN = re.compile(r"([A-Za-z]+)$")


# --- Public API ---------------------------------------------------------------


def clean_text(raw: str) -> str:
    """Clean raw parser text and return only the cleaned text."""
    cleaned, _ = clean_text_with_report(raw)
    return cleaned


def clean_text_with_report(raw: str) -> tuple[str, dict]:
    """Clean raw parser text and return it with a report of what changed.

    The report holds "removed_lines" (the stripped lines dropped as noise),
    "joined_lines" (the (A, B) pairs that were merged) and
    "bullets_normalized" (how many bullet prefixes were rewritten).
    """
    report: dict = {"removed_lines": [], "joined_lines": [], "bullets_normalized": 0}

    text = _normalize_characters(raw)
    pages = [page.split("\n") for page in text.split(PAGE_BREAK)]
    pages = _remove_noise_lines(pages, report)
    pages = _clean_whitespace(pages)
    pages = _normalize_bullets(pages, report)
    pages = _join_wrapped_lines(pages, report)
    pages = _final_tidy(pages)

    return PAGE_BREAK.join("\n".join(page) for page in pages), report


# --- Step 1: normalize characters ---------------------------------------------


def _normalize_characters(raw: str) -> str:
    """Convert line endings, drop invisible characters, unify spaces."""
    text = raw.replace("\r\n", "\n").replace("\r", "\n")
    for char in INVISIBLE_CHARS:
        text = text.replace(char, "")
    return text.replace(NON_BREAKING_SPACE, " ")


# --- Step 2: remove noise lines -----------------------------------------------


def _remove_noise_lines(pages: list[list[str]], report: dict) -> list[list[str]]:
    """Drop boilerplate lines and repeated page headers/footers."""
    kept = []
    for page in pages:
        lines = []
        for line in page:
            if _is_noise_line(line):
                report["removed_lines"].append(line.strip())
            else:
                lines.append(line)
        kept.append(lines)
    return _remove_repeated_headers(kept, report)


def _is_noise_line(line: str) -> bool:
    """Tell whether a line matches one of the boilerplate patterns."""
    text = line.strip()
    return any(pattern.match(text) for pattern in NOISE_PATTERNS)


def _remove_repeated_headers(pages: list[list[str]], report: dict) -> list[list[str]]:
    """Keep only the first occurrence of a line repeated on every page edge."""
    if len(pages) < 2:
        return pages

    zones = [_zone_indices(page) for page in pages]
    repeated = set.intersection(*[
        {page[index].strip() for index in zone} for page, zone in zip(pages, zones)
    ])
    repeated.discard("")
    if not repeated:
        return pages

    seen: set[str] = set()
    kept = []
    for page, zone in zip(pages, zones):
        lines = []
        for index, line in enumerate(page):
            text = line.strip()
            if index in zone and text in repeated:
                if text in seen:
                    report["removed_lines"].append(text)
                    continue
                seen.add(text)
            lines.append(line)
        kept.append(lines)
    return kept


def _zone_indices(page: list[str]) -> set[int]:
    """Return the indices of the first and last non-empty lines of a page."""
    filled = [index for index, line in enumerate(page) if line.strip()]
    return set(filled[:HEADER_FOOTER_ZONE] + filled[-HEADER_FOOTER_ZONE:])


# --- Step 3: clean whitespace -------------------------------------------------


def _clean_whitespace(pages: list[list[str]]) -> list[list[str]]:
    """Collapse runs of spaces/tabs and strip trailing spaces on every line."""
    return [[SPACE_RUN_PATTERN.sub(" ", line).rstrip() for line in page] for page in pages]


# --- Step 4: normalize bullets ------------------------------------------------


def _normalize_bullets(pages: list[list[str]], report: dict) -> list[list[str]]:
    """Rewrite a bullet character at the start of a line as a dash marker."""
    normalized = 0
    kept = []
    for page in pages:
        lines = []
        for line in page:
            bulleted = BULLET_PREFIX_PATTERN.sub(BULLET_MARKER, line, count=1)
            if bulleted != line:
                normalized += 1
            lines.append(bulleted)
        kept.append(lines)
    report["bullets_normalized"] = normalized
    return kept


# --- Step 5: join wrapped lines -----------------------------------------------


def _join_wrapped_lines(pages: list[list[str]], report: dict) -> list[list[str]]:
    """Merge continuation lines, page by page, never across a page break."""
    kept = []
    for page in pages:
        lines: list[str] = []
        for line in page:
            if lines and _should_join(lines[-1], line):
                report["joined_lines"].append((lines[-1], line.strip()))
                lines[-1] = _join_two(lines[-1], line)
            else:
                lines.append(line)
        kept.append(lines)
    return kept


def _should_join(line_a: str, line_b: str) -> bool:
    """Tell whether line_b is the wrapped continuation of line_a."""
    first, second = line_a.strip(), line_b.strip()

    # Never join across these.
    if not first or not second:
        return False
    if _is_heading(first) or _is_heading(second):
        return False
    if second.startswith(BULLET_MARKER):
        return False
    if is_date_line(second):
        return False
    if first.endswith(SENTENCE_END_CHARS):
        return False

    # Join only on a strong signal: a missed join is better than a wrong one.
    if first.endswith(TRAILING_JOIN_CHARS):
        return True
    if _last_word(first) in CONTINUATION_WORDS:
        return True
    return second[0].islower()


def _join_two(line_a: str, line_b: str) -> str:
    """Merge two lines, without a space on a hyphenated word break."""
    first, second = line_a.rstrip(), line_b.strip()
    if first.endswith("-") and second[0].islower():
        return first + second
    return f"{first} {second}"


def _is_heading(line: str) -> bool:
    """Tell whether a line is a section heading."""
    text = line.strip()
    if not text:
        return False
    if match_heading(text) is not None or text.startswith("#"):
        return True
    return looks_like_heading(text)


def _last_word(line: str) -> str:
    """Return the last alphabetic word of a line, lowercased."""
    match = LAST_WORD_PATTERN.search(line)
    return match.group(1).lower() if match else ""


# --- Step 6: final tidy -------------------------------------------------------


def _final_tidy(pages: list[list[str]]) -> list[list[str]]:
    """Collapse repeated empty lines and trim blank lines around each page."""
    kept = []
    for page in pages:
        lines: list[str] = []
        for line in page:
            if not line.strip() and lines and not lines[-1].strip():
                continue
            lines.append(line)
        while lines and not lines[0].strip():
            lines.pop(0)
        while lines and not lines[-1].strip():
            lines.pop()
        kept.append(lines)
    return kept
