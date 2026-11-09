from __future__ import annotations


def clean_text(raw_text: str) -> str:
    """Normalize extracted text before metadata or chunking."""
    return raw_text.strip()
