"""CV section headings: the single source of truth for heading knowledge.

Holds the canonical section names with their aliases, the normalization every
caller should use, and the shape rule for a line that looks like a heading
without being a known one. Standard library only.
"""

import re

SECTION_ALIASES: dict[str, list[str]] = {
    "summary": [
        "PROFESSIONAL SUMMARY",
        "SUMMARY",
        "PROFILE",
        "ABOUT ME",
        "OBJECTIVE",
        "CAREER OBJECTIVE",
    ],
    "skills": [
        "CORE SKILLS",
        "SKILLS",
        "TECHNICAL SKILLS",
        "KEY SKILLS",
        "COMPETENCIES",
        "CORE COMPETENCIES",
    ],
    "experience": [
        "EXPERIENCE",
        "WORK EXPERIENCE",
        "PROFESSIONAL EXPERIENCE",
        "WORK HISTORY",
        "EMPLOYMENT HISTORY",
    ],
    "education": [
        "EDUCATION",
        "ACADEMIC BACKGROUND",
    ],
    "projects": [
        "PROJECTS",
        "SELECTED PROJECTS",
        "KEY PROJECTS",
    ],
    "certifications": [
        "CERTIFICATIONS",
        "CERTIFICATES",
    ],
    "courses": [
        "COURSES",
        "TRAINING",
        "PROFESSIONAL DEVELOPMENT",
    ],
    "languages": [
        "LANGUAGES",
    ],
    "volunteering": [
        "VOLUNTEERING",
        "VOLUNTEER EXPERIENCE",
        "VOLUNTEER WORK",
    ],
    "awards": [
        "AWARDS",
        "HONORS",
        "AWARDS & HONORS",
        "ACHIEVEMENTS",
    ],
    "publications": [
        "PUBLICATIONS",
        "RESEARCH",
    ],
    "interests": [
        "INTERESTS",
        "HOBBIES",
    ],
    "references": [
        "REFERENCES",
    ],
    "memberships": [
        "MEMBERSHIPS",
        "AFFILIATIONS",
    ],
}

# An unknown line needs the shape of a heading: short, and written in capitals.
MAX_HEADING_WORDS = 5
MIN_HEADING_LETTERS = 3

MARKDOWN_MARK = "#"
HEADING_COLON = ":"
_WHITESPACE_RUN_PATTERN = re.compile(r"\s+")

# Built once: every alias, uppercased, pointing at its canonical section name.
_ALIAS_TO_SECTION = {
    alias.upper(): name for name, aliases in SECTION_ALIASES.items() for alias in aliases
}


def normalize_heading(line: str) -> str:
    """Strip markdown marks, a trailing colon and extra spaces from a line."""
    text = line.strip().lstrip(MARKDOWN_MARK).strip()
    if text.endswith(HEADING_COLON):
        text = text[: -len(HEADING_COLON)].rstrip()
    return _WHITESPACE_RUN_PATTERN.sub(" ", text)


def match_heading(line: str) -> str | None:
    """Return the canonical section name of a known heading line, or None."""
    return _ALIAS_TO_SECTION.get(normalize_heading(line).upper())


def looks_like_heading(line: str) -> bool:
    """Tell whether a line has the shape of a heading: short and all capitals."""
    text = normalize_heading(line)
    if not text or text != text.upper():
        return False
    letters = sum(1 for char in text if char.isalpha())
    return len(text.split()) <= MAX_HEADING_WORDS and letters >= MIN_HEADING_LETTERS
