EXTRACT_PAGE_CONTENT = """Analyze this document page image and extract all content into structured JSON.

Extract:
1. **Text blocks**: Every paragraph, heading, and standalone text with reading order
2. **Tables**: Complete table structure with headers, rows, columns, merged cells
3. **Annotations**: Handwritten notes, highlights, stamps, sticky notes
4. **Section hierarchy**: Heading levels and section structure

Return JSON in this exact format:
```json
{{
  "blocks": [
    {{
      "id": "blk_001",
      "type": "text|table|image|annotation|header|footer",
      "bbox": {{"x": 0, "y": 0, "width": 100, "height": 20}},
      "text": "extracted text content",
      "table": {{
        "rows": 5,
        "cols": 3,
        "cells": [
          {{"row": 0, "col": 0, "rowspan": 1, "colspan": 1, "text": "cell text"}}
        ],
        "headers": ["Col A", "Col B", "Col C"]
      }},
      "annotation": {{
        "type": "handwriting|sticky_note|highlight|strikethrough|stamp|text_box",
        "transcription": "transcribed text if applicable",
        "transcription_confidence": 0.85
      }},
      "section_level": 2,
      "section_title": "Section Title"
    }}
  ],
  "reading_order": ["blk_001", "blk_002"],
  "sections": [
    {{"title": "Section Name", "level": 1, "block_ids": ["blk_001"]}}
  ]
}}
```

Rules:
- Include EVERY piece of text on the page, no matter how small
- For tables, extract EVERY cell including empty ones
- Bounding box coordinates should be approximate pixel positions
- Only include "table" field for table-type blocks
- Only include "annotation" field for annotation-type blocks
- section_level: 1=main heading, 2=subheading, 3=sub-subheading
- reading_order must list ALL block IDs in natural reading sequence
- If text is unclear, provide best guess and note low confidence in annotation field"""


EXTRACT_PAGE_ANTHROPIC = f"""<task>
{EXTRACT_PAGE_CONTENT}
</task>

<output_format>JSON only, no additional text</output_format>"""


EXTRACT_PAGE_GOOGLE = EXTRACT_PAGE_CONTENT + """

IMPORTANT: Return ONLY the JSON object. No markdown formatting, no explanation."""


def get_extract_prompt(provider: str) -> str:
    if provider == "anthropic":
        return EXTRACT_PAGE_ANTHROPIC
    if provider == "google":
        return EXTRACT_PAGE_GOOGLE
    return EXTRACT_PAGE_CONTENT
