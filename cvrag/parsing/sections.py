"""Split cleaned CV text into labelled sections.

Input is the output of cleaning.clean_text, where pages are separated by
PAGE_BREAK. Offsets refer to that input, so concatenating text[start:end] for
every section in order reproduces it exactly. Standard library only.
"""

from dataclasses import dataclass

from . import PAGE_BREAK
from .dates import is_date_line
from .headings import MARKDOWN_MARK, looks_like_heading, match_heading, normalize_heading

# Section names that are not canonical headings.
HEADER_NAME = "header"  # name, title and contact details above the first heading
BODY_NAME = "body"  # the whole document, when it has no known heading at all
UNKNOWN_NAME = "other"  # an unknown heading that still starts its own section

# Sections we hope to find in every CV. Their absence is information, not an error.
EXPECTED_SECTIONS = ["summary", "skills", "experience", "education"]

# A heading never holds these: they mark job lines, contact details and dates.
FORBIDDEN_HEADING_CHARS = ("|", "@")

# A line ends at a newline or at a page break.
LINE_SEPARATORS = ("\n", PAGE_BREAK)


@dataclass
class Section:
    """One labelled part of a CV, with its offsets in the cleaned text."""

    name: str
    heading: str
    start: int
    content_start: int
    end: int
    text: str
    pages: list[int]


# --- Public API ---------------------------------------------------------------


def detect_sections(text: str) -> list[Section]:
    """Split cleaned CV text into sections."""
    sections, _ = detect_sections_with_report(text)
    return sections


def detect_sections_with_report(text: str) -> tuple[list[Section], dict]:
    """Split cleaned CV text into sections and report what stayed unclear.

    The report holds "unknown_heading_candidates" (lines that look like a
    heading without being a known one), "missing_expected" (EXPECTED_SECTIONS
    that were not found) and "empty_sections" (sections without content).
    """
    report: dict = {
        "unknown_heading_candidates": [],
        "missing_expected": [],
        "empty_sections": [],
    }

    lines = _split_lines(text)
    starts = _find_section_starts(lines, report)
    sections = _build_sections(text, starts)

    found = {section.name for section in sections}
    report["missing_expected"] = [name for name in EXPECTED_SECTIONS if name not in found]
    report["empty_sections"] = [section.name for section in sections if not section.text]
    return sections, report


# --- Lines --------------------------------------------------------------------


def _split_lines(text: str) -> list[tuple[int, str]]:
    """Return (offset, line) for every line, splitting on newlines and breaks."""
    lines = []
    start = 0
    for index, char in enumerate(text):
        if char in LINE_SEPARATORS:
            lines.append((start, text[start:index]))
            start = index + 1
    lines.append((start, text[start:]))
    return lines


def _next_non_empty(lines: list[tuple[int, str]], index: int) -> str | None:
    """Return the first non-empty line at or after index, or None."""
    for _, line in lines[index:]:
        if line.strip():
            return line
    return None


# --- Section starts -----------------------------------------------------------


def _find_section_starts(
    lines: list[tuple[int, str]], report: dict
) -> list[tuple[int, str, str]]:
    """Return (offset, heading line, canonical name) for every section start."""
    starts = []
    seen_known = False

    for index, (offset, line) in enumerate(lines):
        name = match_heading(line)
        if name is not None:
            starts.append((offset, line, name))
            seen_known = True
            continue

        # Unknown headings only exist below the first known one, never in the header.
        if not seen_known:
            continue

        if _starts_unknown_section(line, lines, index):
            starts.append((offset, line, UNKNOWN_NAME))
            report["unknown_heading_candidates"].append(line)
        elif _is_reportable_markdown(line):
            report["unknown_heading_candidates"].append(line)

    return starts


def _starts_unknown_section(line: str, lines: list[tuple[int, str]], index: int) -> bool:
    """Tell whether an unknown line is a heading that starts its own section."""
    if not _looks_like_unknown_heading(line):
        return False

    # A heading needs content below it, and the last line of a CV has none.
    following = _next_non_empty(lines, index + 1)
    if following is None:
        return False
    return not _is_any_heading(following)


def _looks_like_unknown_heading(line: str) -> bool:
    """Apply the shape rules an unknown heading has to satisfy."""
    if not looks_like_heading(line):
        return False
    text = normalize_heading(line)
    return _has_no_forbidden_chars(text) and not is_date_line(text)


def _is_any_heading(line: str) -> bool:
    """Tell whether a line is a known heading or looks like an unknown one."""
    return match_heading(line) is not None or _looks_like_unknown_heading(line)


def _is_reportable_markdown(line: str) -> bool:
    """Tell whether a markdown heading is worth reporting as an unknown one."""
    text = line.strip()
    if not text.startswith(MARKDOWN_MARK):
        return False
    return _has_no_forbidden_chars(normalize_heading(text))


def _has_no_forbidden_chars(text: str) -> bool:
    """Tell whether a candidate is free of job line and contact markers."""
    if any(char in text for char in FORBIDDEN_HEADING_CHARS):
        return False
    return not any(char.isdigit() for char in text)


# --- Sections -----------------------------------------------------------------


def _build_sections(text: str, starts: list[tuple[int, str, str]]) -> list[Section]:
    """Turn section starts into sections that cover the whole text."""
    if not starts:
        return [_make_section(text, BODY_NAME, "", 0, 0, len(text))]

    sections = []
    first_start = starts[0][0]
    if text[:first_start].strip():
        sections.append(_make_section(text, HEADER_NAME, "", 0, 0, first_start))

    for position, (offset, heading, name) in enumerate(starts):
        is_last = position + 1 == len(starts)
        end = len(text) if is_last else starts[position + 1][0]
        content_start = _content_start(text, offset, heading, end)
        sections.append(_make_section(text, name, heading, offset, content_start, end))
    return sections


def _content_start(text: str, offset: int, heading: str, end: int) -> int:
    """Return the offset just after the heading line and its separator."""
    position = offset + len(heading)
    if position < len(text) and text[position] in LINE_SEPARATORS:
        position += 1
    return min(position, end)


def _make_section(
    text: str, name: str, heading: str, start: int, content_start: int, end: int
) -> Section:
    """Build one section with its content text and page span."""
    return Section(
        name=name,
        heading=heading,
        start=start,
        content_start=content_start,
        end=end,
        text=text[content_start:end].replace(PAGE_BREAK, "\n").strip(),
        pages=_page_span(text, start, end),
    )


def _page_span(text: str, start: int, end: int) -> list[int]:
    """Return the 1-based page numbers a section spans."""
    # rstrip keeps a trailing page break out, so a section does not claim the
    # next page just because one begins right after it.
    content = text[start:end].rstrip()
    last = start + len(content) - 1 if content else start
    return list(range(_page_of(text, start), _page_of(text, last) + 1))


def _page_of(text: str, position: int) -> int:
    """Return the 1-based page number of an offset."""
    return text.count(PAGE_BREAK, 0, position) + 1
