import time

from llama_cloud import LlamaCloud

from .. import config
from . import PAGE_BREAK

# Parsing tier: fast | cost_effective | agentic | agentic_plus
# Higher tiers understand complex layouts better, but cost more credits per page.
TIER = "cost_effective"


def parse_pdf(pdf_bytes: bytes, file_name: str = "cv.pdf") -> dict:
    """Extract Markdown text from a PDF using LlamaParse (cloud service)."""
    if not config.LLAMA_CLOUD_API_KEY:
        raise RuntimeError("Missing LLAMA_CLOUD_API_KEY in .env")

    start = time.perf_counter()

    client = LlamaCloud(api_key=config.LLAMA_CLOUD_API_KEY)
    result = client.parsing.parse(
        tier=TIER,
        version="latest",
        upload_file=(file_name, pdf_bytes, "application/pdf"),
        expand=["markdown"],
    )

    pages = result.markdown.pages if result.markdown else []
    texts = [getattr(page, "markdown", "") for page in pages]

    return {
        "parser": "llamaparse",
        "text": PAGE_BREAK.join(texts),
        "page_count": len(texts),
        "parse_seconds": time.perf_counter() - start,
    }