import logging
import os

import fitz  # PyMuPDF

from app.config import settings

logger = logging.getLogger("docdiff.pdf")


def render_page_to_image(
    pdf_path: str,
    page_number: int,
    output_dir: str,
    dpi: int | None = None,
) -> str:
    if dpi is None:
        dpi = settings.page_render_dpi
    doc = fitz.open(pdf_path)
    page = doc[page_number]
    zoom = dpi / 72.0
    matrix = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=matrix)
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"page_{page_number + 1:03d}.png")
    pix.save(output_path)
    doc.close()
    logger.debug(f"Rendered page {page_number + 1} at {dpi} DPI -> {output_path}")
    return output_path


def render_all_pages(pdf_path: str, output_dir: str, dpi: int | None = None) -> list[str]:
    if dpi is None:
        dpi = settings.page_render_dpi
    os.makedirs(output_dir, exist_ok=True)
    zoom = dpi / 72.0
    matrix = fitz.Matrix(zoom, zoom)

    doc = fitz.open(pdf_path)
    paths: list[str] = []
    for i in range(doc.page_count):
        page = doc[i]
        pix = page.get_pixmap(matrix=matrix)
        output_path = os.path.join(output_dir, f"page_{i + 1:03d}.png")
        pix.save(output_path)
        paths.append(output_path)
        logger.debug(f"Rendered page {i + 1} at {dpi} DPI → {output_path}")
    doc.close()
    return paths


def has_text_layer(pdf_path: str, page_number: int) -> bool:
    doc = fitz.open(pdf_path)
    page = doc[page_number]
    text = page.get_text("text").strip()
    doc.close()
    return len(text) > 10


def get_optimal_dpi(pdf_path: str, page_number: int) -> int:
    """Determine optimal rendering DPI based on page content.

    - Born-digital pages with text layer: 150 DPI (sufficient for overlays)
    - Scanned pages without text layer: 300 DPI (better OCR accuracy)
    - Pages with small text or fine detail: 300 DPI
    """
    if has_text_layer(pdf_path, page_number):
        return 150  # Text is already extractable, just need visual
    return 300  # Need high quality for VLM OCR


def render_all_pages_adaptive(pdf_path: str, output_dir: str) -> list[tuple[str, int]]:
    """Render all pages with adaptive DPI based on content type.

    Returns list of (image_path, dpi_used) tuples.
    """
    doc = fitz.open(pdf_path)
    page_count = doc.page_count
    doc.close()

    results = []
    for i in range(page_count):
        dpi = get_optimal_dpi(pdf_path, i)
        path = render_page_to_image(pdf_path, i, output_dir, dpi)
        results.append((path, dpi))

    return results
