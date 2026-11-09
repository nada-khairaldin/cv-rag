import time

import pymupdf

from . import PAGE_BREAK


# Page separator:
# "\f" is the form feed character, traditionally meaning "new page". It is invisible in text.
# We join the text of all pages into one string, with "\f" between every two pages:
#     "page 1 text" + "\f" + "page 2 text"
# Why? After chunking, we can find which page a chunk came from by counting
# the "\f" characters before its start position:
#     page = text.count("\f", 0, chunk_start) + 1
# If a chunk starts on one page and ends on the next, we store pages = [1, 2].
# Note: "\f" only marks page numbers. It is NOT a chunk boundary.
# Chunking follows CV sections, even when a section continues onto the next page.



def parse_pdf(pdf_bytes: bytes) -> dict:
    """Extract raw text from a PDF using PyMuPDF."""
    start = time.perf_counter()

    with pymupdf.open(stream=pdf_bytes, filetype="pdf") as doc:
        pages = [page.get_text() for page in doc]
        page_count = doc.page_count

    return {
        "parser": "pymupdf",
        "text": PAGE_BREAK.join(pages),
        "page_count": page_count,
        "parse_seconds": time.perf_counter() - start,
    }