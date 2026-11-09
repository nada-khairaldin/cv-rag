"""Recognize date lines in CV text.

Shared by cleaning (to avoid joining a date onto a job title) and by section
detection (to avoid treating a date as a heading). Standard library only.
"""

import re

# A month name, long or short, with an optional dot: "Jan", "Jan.", "January".
_MONTH = r"(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\.?"
# One end of a range: "2024", "Jan 2021" or "03/2021".
_DATE_POINT = rf"(?:(?:0?[1-9]|1[0-2])/\d{{4}}|(?:{_MONTH}\s+)?\d{{4}})"
# An open-ended range: "2024 - Present".
_OPEN_END = r"(?:present|current|now|today|ongoing)"
_RANGE_SEPARATOR = r"(?:\s*[-–—]\s*|\s+to\s+)"

# Date lines such as "2024 - Present", "Jan 2021 - Mar 2023", "03/2021 - 05/2023".
DATE_LINE_PATTERN = re.compile(
    rf"^{_DATE_POINT}(?:{_RANGE_SEPARATOR}(?:{_DATE_POINT}|{_OPEN_END}))?$",
    re.IGNORECASE,
)


def is_date_line(line: str) -> bool:
    """Tell whether a line holds only a date or a date range."""
    return DATE_LINE_PATTERN.match(line.strip()) is not None
