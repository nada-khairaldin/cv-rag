def embed_documents(texts: list[str], titles: list[str] | None = None) -> list[list[float]]:
    """Embed CV chunks (at ingestion time)."""
    ...

def embed_query(text: str) -> list[float]:
    """Embed a user question (at search time)."""
    ...