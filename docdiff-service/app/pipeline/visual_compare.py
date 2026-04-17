"""Visual page comparison — sends both pages to LLM for direct diff detection.

Used for scanned/mixed pages where OCR-based extraction is unreliable.
The LLM sees both page images simultaneously and identifies differences
directly, bypassing the text extraction pipeline entirely.

This produces higher accuracy on scanned PDFs at higher cost per page.
"""
import logging

from app.ai.base import AIProvider, AIResponse
from app.ai.response_parser import parse_ai_response
from app.prompts.system_prompts import VISUAL_COMPARISON_SYSTEM_PROMPT

logger = logging.getLogger("docdiff.pipeline")

VISUAL_COMPARE_PROMPT = """Compare these two document pages and identify ALL differences.

The FIRST image is Version A (original). The SECOND image is Version B (revised).

For each difference found, provide:
- type: text_modification, text_addition, text_deletion, table_cell_change, table_row_addition, table_row_deletion, table_structure_change, annotation_present_in_b, annotation_removed_from_b, formatting_change
- bbox_version_a: {x, y, width, height} normalized 0-1 fractions on Version A page (null if addition)
- bbox_version_b: {x, y, width, height} normalized 0-1 fractions on Version B page (null if deletion)
- value_before: exact text from Version A (empty string if addition)
- value_after: exact text from Version B (empty string if deletion)
- significance: material, substantive, or cosmetic
- confidence: 0.0-1.0
- summary: brief description of the change

Return JSON:
{
  "differences": [
    {
      "type": "table_cell_change",
      "bbox_version_a": {"x": 0.55, "y": 0.45, "width": 0.12, "height": 0.03},
      "bbox_version_b": {"x": 0.55, "y": 0.45, "width": 0.12, "height": 0.03},
      "value_before": "18%",
      "value_after": "21%",
      "significance": "material",
      "confidence": 0.98,
      "summary": "Revenue growth changed from 18% to 21%"
    }
  ],
  "page_summary": "3 material differences, 1 substantive, 0 cosmetic found on this page pair"
}

IMPORTANT:
- Report EVERY difference, no matter how small
- Numbers must be exact (18% not ~18%)
- Do NOT report rendering/quality differences between the two images
- If no differences exist, return {"differences": [], "page_summary": "No differences found"}"""


async def visual_compare_pages(
    image_a: bytes,
    image_b: bytes,
    ai_provider: AIProvider,
    page_num_a: int,
    page_num_b: int,
) -> list[dict]:
    """Compare two page images using VLM visual comparison.

    Sends both images to the LLM simultaneously. The LLM identifies
    differences directly from the visual content, bypassing text extraction.

    Returns list of difference dicts ready for stage 7 scoring.
    """
    try:
        response: AIResponse = await ai_provider.call(
            prompt=VISUAL_COMPARE_PROMPT,
            images=[image_a, image_b],
            system=VISUAL_COMPARISON_SYSTEM_PROMPT,
        )
    except Exception as e:
        logger.error(f"Visual comparison failed for pages {page_num_a}/{page_num_b}: {e}")
        return []

    parsed = parse_ai_response(response.content)
    if not parsed or not isinstance(parsed, dict):
        logger.warning(f"Visual comparison returned unparseable response for pages {page_num_a}/{page_num_b}")
        return []

    raw_diffs = parsed.get("differences", [])
    if not isinstance(raw_diffs, list):
        return []

    # Convert to pipeline-compatible format
    results: list[dict] = []
    for i, d in enumerate(raw_diffs, start=1):
        if not isinstance(d, dict):
            continue
        results.append({
            "difference_number": i,
            "difference_type": d.get("type", "text_modification"),
            "significance": d.get("significance", "uncertain"),
            "confidence": d.get("confidence", 0.80),
            "page_version_a": page_num_a,
            "page_version_b": page_num_b,
            "bbox_version_a": d.get("bbox_version_a"),
            "bbox_version_b": d.get("bbox_version_b"),
            "value_before": d.get("value_before", ""),
            "value_after": d.get("value_after", ""),
            "context": d.get("summary", ""),
            "summary": d.get("summary", ""),
            "block_id_version_a": None,
            "block_id_version_b": None,
            "needs_verification": d.get("confidence", 0.80) < 0.75,
            "auto_confirmed": d.get("confidence", 0.80) >= 0.95,
            "source": "visual_comparison",
        })

    logger.info(
        f"Visual comparison: {len(results)} differences found on pages "
        f"{page_num_a}/{page_num_b} (summary: {parsed.get('page_summary', 'N/A')})"
    )
    return results
