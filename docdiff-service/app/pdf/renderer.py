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
