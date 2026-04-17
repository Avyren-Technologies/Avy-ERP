"""
fast_parser.py — PyMuPDF-based content extractor for born-digital PDF pages.

Extracts text blocks, headings and tables from a born-digital PDF page in
milliseconds, producing the same block-dict format used by the Docling/VLM
path so the rest of the pipeline is completely unchanged.

Why not Docling for born-digital?
  Docling loads ~770 ML model weights and runs layout analysis, taking
  5–15 minutes per document.  For born-digital PDFs PyMuPDF already has
  the text layer — extraction takes < 50 ms per page with zero ML overhead.
"""

import logging

import fitz  # PyMuPDF — already a project dependency

logger = logging.getLogger("docdiff.pdf")

# Font-size thresholds for heading detection
_H1_MIN_SIZE = 15.0
_H2_MIN_SIZE = 12.0
_BOLD_FLAG = 2 ** 4          # PyMuPDF span flag bit for bold


def extract_all_pages(pdf_path: str) -> list[dict]:
    """
    Extract every page of a born-digital PDF using PyMuPDF.

    Returns a list of page dicts (one per page) in the format:
      {
        "blocks": [ {id, type, bbox, text, [section_level, section_title],
                     [table: {rows, cols, cells, headers}] }, ... ],
        "reading_order": ["blk_001", ...],
        "sections":      [ {title, level, block_ids}, ... ],
      }

    This is the same shape produced by parse_document_with_docling() and by
    the VLM extraction path, so Stage 4+ requires zero changes.
    """
    doc = fitz.open(pdf_path)
    pages: list[dict] = []

    for page_idx in range(len(doc)):
        page = doc[page_idx]
        pages.append(_extract_page(page))

    doc.close()
    logger.debug(f"fast_parser: extracted {len(pages)} page(s) from {pdf_path}")
    return pages


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _extract_page(page: fitz.Page) -> dict:
    blocks_raw = page.get_text(
        "dict",
        flags=fitz.TEXT_PRESERVE_WHITESPACE | fitz.TEXT_PRESERVE_LIGATURES,
    )["blocks"]

    # Page dimensions for normalizing bboxes to 0-1 fractions
    page_w = page.rect.width
    page_h = page.rect.height

    result_blocks: list[dict] = []
    reading_order: list[str] = []
    sections: list[dict] = []
    block_counter = 0

    # ------------------------------------------------------------------
    # Text blocks
    # ------------------------------------------------------------------
    for raw in blocks_raw:
        if raw.get("type") != 0:        # type 1 = image — skip
            continue

        text = _block_text(raw).strip()
        if not text:
            continue

        block_counter += 1
        block_id = f"blk_{block_counter:03d}"
        bbox = _bbox_normalized(raw, page_w, page_h)

        block: dict = {
            "id": block_id,
            "block_type": "text",           # align with pipeline expectations
            "type": "text",
            "bbox": bbox,
            "text": text,
        }

        # Heading / section detection via font metrics
        first_span = _first_span(raw)
        if first_span:
            size: float = first_span.get("size", 12.0)
            flags: int = first_span.get("flags", 0)
            is_bold = bool(flags & _BOLD_FLAG)

            if size >= _H1_MIN_SIZE or (size >= _H2_MIN_SIZE and is_bold):
                level = 1 if size >= _H1_MIN_SIZE else 2
                block["section_level"] = level
                block["section_title"] = text[:120]
                sections.append(
                    {"title": text[:120], "level": level, "block_ids": [block_id]}
                )

        # Detect header/footer zones using normalized bbox
        bbox_y = bbox.get("y", 0)
        bbox_y_end = bbox_y + bbox.get("height", 0)

        if bbox_y < 0.08:  # Top 8% of page
            block["type"] = "header"
            block["block_type"] = "header"
        elif bbox_y_end > 0.95:  # Bottom 5% of page
            block["type"] = "footer"
            block["block_type"] = "footer"

        result_blocks.append(block)
        reading_order.append(block_id)

    # ------------------------------------------------------------------
    # Table extraction  (PyMuPDF ≥ 1.23.0)
    # ------------------------------------------------------------------
    try:
        for table in page.find_tables():
            df = table.to_pandas()
            if df.empty:
                continue

            block_counter += 1
            block_id = f"blk_{block_counter:03d}"
            headers = list(df.columns)

            header_cells = [
                {"row": 0, "col": i, "rowspan": 1, "colspan": 1, "text": str(h)}
                for i, h in enumerate(headers)
            ]
            data_cells = [
                {
                    "row": int(r_idx) + 1,
                    "col": c_idx,
                    "rowspan": 1,
                    "colspan": 1,
                    "text": str(val) if val is not None else "",
                }
                for r_idx, row in df.iterrows()
                for c_idx, val in enumerate(row)
            ]

            tb = table.bbox
            result_blocks.append(
                {
                    "id": block_id,
                    "block_type": "table",
                    "type": "table",
                    "bbox": {
                        "x": tb[0] / page_w if page_w else 0,
                        "y": tb[1] / page_h if page_h else 0,
                        "width": (tb[2] - tb[0]) / page_w if page_w else 0,
                        "height": (tb[3] - tb[1]) / page_h if page_h else 0,
                    },
                    "text": "",
                    "table": {
                        "rows": len(df) + 1,
                        "cols": len(headers),
                        "cells": header_cells + data_cells,
                        "headers": headers,
                    },
                }
            )
            reading_order.append(block_id)
    except Exception as exc:
        # find_tables() not available in this PyMuPDF build — graceful fallback
        logger.debug(f"fast_parser: table extraction skipped ({exc})")

    return {
        "blocks": result_blocks,
        "reading_order": reading_order,
        "sections": sections,
    }


def _block_text(raw: dict) -> str:
    """Concatenate all span text in a raw block dict."""
    lines = []
    for line in raw.get("lines", []):
        line_text = "".join(s.get("text", "") for s in line.get("spans", []))
        if line_text.strip():
            lines.append(line_text)
    return "\n".join(lines)


def _first_span(raw: dict) -> dict | None:
    lines = raw.get("lines", [])
    if lines:
        spans = lines[0].get("spans", [])
        if spans:
            return spans[0]
    return None


def _bbox_normalized(raw: dict, page_w: float, page_h: float) -> dict:
    """Convert PyMuPDF bbox (PDF points) to normalized 0-1 fractions of page size."""
    b = raw.get("bbox", (0, 0, 0, 0))
    return {
        "x": b[0] / page_w if page_w else 0,
        "y": b[1] / page_h if page_h else 0,
        "width": (b[2] - b[0]) / page_w if page_w else 0,
        "height": (b[3] - b[1]) / page_h if page_h else 0,
    }
