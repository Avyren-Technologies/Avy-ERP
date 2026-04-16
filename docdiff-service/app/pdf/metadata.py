import logging
from dataclasses import dataclass
from pathlib import Path

import fitz  # PyMuPDF

logger = logging.getLogger("docdiff.pdf")


@dataclass
class PDFMetadata:
    page_count: int
    file_size_bytes: int
    title: str | None
    author: str | None
    creator: str | None
    producer: str | None
    creation_date: str | None
    pdf_version: str | None
    is_encrypted: bool


def extract_metadata(file_path: str) -> PDFMetadata:
    path = Path(file_path)
    doc = fitz.open(file_path)
    meta = doc.metadata or {}
    result = PDFMetadata(
        page_count=doc.page_count,
        file_size_bytes=path.stat().st_size,
        title=meta.get("title") or None,
        author=meta.get("author") or None,
        creator=meta.get("creator") or None,
        producer=meta.get("producer") or None,
        creation_date=meta.get("creationDate") or None,
        pdf_version=meta.get("format") or None,
        is_encrypted=doc.is_encrypted,
    )
    doc.close()
    return result


def validate_pdf(file_path: str, max_pages: int, max_size_mb: int) -> tuple[bool, str]:
    path = Path(file_path)
    if not path.exists():
        return False, "File not found"
    size_mb = path.stat().st_size / (1024 * 1024)
    if size_mb > max_size_mb:
        return False, f"File size ({size_mb:.1f}MB) exceeds {max_size_mb}MB limit"
    try:
        doc = fitz.open(file_path)
    except Exception as e:
        return False, f"Invalid PDF file: {e}"
    if doc.is_encrypted:
        doc.close()
        return False, "PDF is password-protected or encrypted"
    if doc.page_count > max_pages:
        doc.close()
        return False, f"Page count ({doc.page_count}) exceeds {max_pages} page limit"
    if doc.page_count == 0:
        doc.close()
        return False, "PDF has no pages"
    doc.close()
    return True, ""
