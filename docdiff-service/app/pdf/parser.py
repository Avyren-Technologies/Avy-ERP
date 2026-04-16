import logging

logger = logging.getLogger("docdiff.pdf")


def parse_document_with_docling(file_path: str) -> list[dict]:
    try:
        from docling.document_converter import DocumentConverter
    except ImportError:
        logger.error("Docling not installed. Install with: pip install docling")
        raise

    converter = DocumentConverter()
    result = converter.convert(file_path)
    doc = result.document

    pages: list[dict] = []
    page_blocks: dict[int, list[dict]] = {}

    block_counter = 0
    for item in doc.iterate_items():
        element = item
        page_num = 1
        bbox = {"x": 0, "y": 0, "width": 0, "height": 0}

        if hasattr(element, "prov") and element.prov:
            prov = element.prov[0] if isinstance(element.prov, list) else element.prov
            if hasattr(prov, "page_no"):
                page_num = prov.page_no
            if hasattr(prov, "bbox"):
                b = prov.bbox
                bbox = {
                    "x": getattr(b, "l", 0),
                    "y": getattr(b, "t", 0),
                    "width": getattr(b, "r", 0) - getattr(b, "l", 0),
                    "height": getattr(b, "b", 0) - getattr(b, "t", 0),
                }

        block_counter += 1
        block_id = f"blk_{block_counter:03d}"

        block: dict = {
            "id": block_id,
            "type": "text",
            "bbox": bbox,
            "text": "",
        }

        element_type = type(element).__name__.lower()

        if "table" in element_type:
            block["type"] = "table"
            table_data = _extract_table_data(element)
            if table_data:
                block["table"] = table_data
                block["text"] = ""
        elif "heading" in element_type or "title" in element_type:
            block["type"] = "text"
            block["text"] = element.text if hasattr(element, "text") else str(element)
            level = getattr(element, "level", 1)
            block["section_level"] = level
            block["section_title"] = block["text"]
        elif "picture" in element_type or "figure" in element_type:
            block["type"] = "image"
            block["text"] = getattr(element, "caption", "") or ""
        else:
            block["text"] = element.text if hasattr(element, "text") else str(element)

        if page_num not in page_blocks:
            page_blocks[page_num] = []
        page_blocks[page_num].append(block)

    max_page = max(page_blocks.keys()) if page_blocks else 0
    for p in range(1, max_page + 1):
        blocks = page_blocks.get(p, [])
        sections = [
            {
                "title": b.get("section_title", ""),
                "level": b.get("section_level", 1),
                "block_ids": [b["id"]],
            }
            for b in blocks
            if b.get("section_level")
        ]
        pages.append({
            "blocks": blocks,
            "reading_order": [b["id"] for b in blocks],
            "sections": sections,
        })

    return pages


def _extract_table_data(element) -> dict | None:
    try:
        if hasattr(element, "export_to_dataframe"):
            df = element.export_to_dataframe()
            headers = list(df.columns)
            cells = []
            for row_idx, row in df.iterrows():
                for col_idx, val in enumerate(row):
                    cells.append({
                        "row": int(row_idx) + 1,
                        "col": col_idx,
                        "rowspan": 1,
                        "colspan": 1,
                        "text": str(val) if val is not None else "",
                    })
            header_cells = [
                {"row": 0, "col": i, "rowspan": 1, "colspan": 1, "text": h}
                for i, h in enumerate(headers)
            ]
            return {
                "rows": len(df) + 1,
                "cols": len(headers),
                "cells": header_cells + cells,
                "headers": headers,
            }
    except Exception as e:
        logger.warning(f"Failed to extract table data: {e}")
    return None
