"""Versioned prompt templates for VLM page content extraction."""

EXTRACT_PAGE_CONTENT = """You are extracting structured content from a document page image for automated comparison.

## Instructions

Analyze the page and extract EVERY piece of content into a structured JSON format.

### Bounding Boxes
All coordinates must be **normalized fractions (0.0 to 1.0)** of the page dimensions:
- x=0.0 is the left edge, x=1.0 is the right edge
- y=0.0 is the top edge, y=1.0 is the bottom edge
- width and height are also fractions of page dimensions

### Content Types
- **text**: Regular paragraphs, body text, lists
- **table**: Tabular data with rows and columns
- **annotation**: Handwritten notes, stamps, highlights, strikethroughs
- **header**: Page headers (document title, revision numbers at top)
- **footer**: Page footers (page numbers, dates at bottom)

### Confidence
Rate your extraction confidence for each block:
- 1.0 = perfectly clear, no ambiguity
- 0.8 = mostly clear, minor uncertainty
- 0.5 = partially readable, some guessing
- 0.3 = barely readable, significant guessing
- 0.0 = illegible, cannot extract

### Rules
1. Extract EVERY visible text element, no matter how small
2. For tables: extract every cell including empty ones. Note merged cells with rowspan/colspan > 1
3. For handwritten annotations: transcribe if readable, mark confidence. If illegible, set confidence to 0.0 and transcription to ""
4. Mark header zones (top ~8% of page) as type "header"
5. Mark footer zones (bottom ~5% of page) as type "footer"
6. Reading order must follow natural document flow (left-to-right, top-to-bottom, respecting columns)
7. For multi-column layouts, read left column fully before right column

### Output Format
Return ONLY valid JSON (no markdown, no explanation):

{
  "blocks": [
    {
      "id": "blk_001",
      "type": "header",
      "bbox": {"x": 0.05, "y": 0.02, "width": 0.9, "height": 0.04},
      "text": "ACME Corp — Document Title Rev.3",
      "confidence": 0.95
    },
    {
      "id": "blk_002",
      "type": "text",
      "bbox": {"x": 0.08, "y": 0.12, "width": 0.84, "height": 0.06},
      "text": "1. Introduction",
      "confidence": 1.0,
      "section_level": 1,
      "section_title": "1. Introduction"
    },
    {
      "id": "blk_003",
      "type": "text",
      "bbox": {"x": 0.08, "y": 0.18, "width": 0.84, "height": 0.12},
      "text": "This document describes the technical specifications for...",
      "confidence": 0.98
    },
    {
      "id": "blk_004",
      "type": "table",
      "bbox": {"x": 0.06, "y": 0.35, "width": 0.88, "height": 0.25},
      "text": "",
      "confidence": 0.92,
      "table": {
        "rows": 4,
        "cols": 3,
        "cells": [
          {"row": 0, "col": 0, "rowspan": 1, "colspan": 1, "text": "Parameter"},
          {"row": 0, "col": 1, "rowspan": 1, "colspan": 1, "text": "Value"},
          {"row": 0, "col": 2, "rowspan": 1, "colspan": 1, "text": "Unit"},
          {"row": 1, "col": 0, "rowspan": 1, "colspan": 1, "text": "Temperature"},
          {"row": 1, "col": 1, "rowspan": 1, "colspan": 1, "text": "350"},
          {"row": 1, "col": 2, "rowspan": 1, "colspan": 1, "text": "°C"}
        ],
        "headers": ["Parameter", "Value", "Unit"]
      }
    },
    {
      "id": "blk_005",
      "type": "annotation",
      "bbox": {"x": 0.75, "y": 0.42, "width": 0.2, "height": 0.05},
      "text": "",
      "confidence": 0.6,
      "annotation": {
        "type": "handwriting",
        "transcription": "Check with supplier",
        "transcription_confidence": 0.6
      }
    },
    {
      "id": "blk_006",
      "type": "footer",
      "bbox": {"x": 0.3, "y": 0.95, "width": 0.4, "height": 0.03},
      "text": "Page 3 of 12",
      "confidence": 0.99
    }
  ],
  "reading_order": ["blk_001", "blk_002", "blk_003", "blk_004", "blk_005", "blk_006"],
  "sections": [
    {"title": "1. Introduction", "level": 1, "block_ids": ["blk_002", "blk_003"]}
  ]
}"""


EXTRACT_PAGE_ANTHROPIC = f"""<task>
{EXTRACT_PAGE_CONTENT}
</task>

<important>
Return ONLY the JSON object. No markdown code fences, no explanation text.
Bounding boxes MUST be normalized 0-1 fractions of page dimensions.
Include a "confidence" field (0.0-1.0) on every block.
</important>"""


EXTRACT_PAGE_GOOGLE = EXTRACT_PAGE_CONTENT + """

CRITICAL: Return ONLY the JSON object. No markdown formatting, no ```json blocks, no explanation.
Every block MUST have a "confidence" field (0.0-1.0)."""


def get_extract_prompt(provider: str) -> str:
    if provider == "anthropic":
        return EXTRACT_PAGE_ANTHROPIC
    if provider == "google":
        return EXTRACT_PAGE_GOOGLE
    return EXTRACT_PAGE_CONTENT
