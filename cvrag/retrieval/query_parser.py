from __future__ import annotations


def parse_query(question: str):
    """Parse the user question into retrieval-friendly search terms."""
    return {"question": question}
