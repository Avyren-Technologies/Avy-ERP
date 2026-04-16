import logging

from app.ai.base import AIProvider
from app.ai.response_parser import safe_parse_or_flag
from app.models.difference import DifferenceType, Significance
from app.pipeline.stage_6_diff import RawDiffRecord
from app.prompts.classify_difference import get_classify_prompt

logger = logging.getLogger("docdiff.pipeline")

# Heuristic confidence values per difference type
_TYPE_BASE_CONFIDENCE: dict[DifferenceType, float] = {
    DifferenceType.text_addition: 0.9,
    DifferenceType.text_deletion: 0.9,
    DifferenceType.text_modification: 0.85,
    DifferenceType.table_cell_change: 0.92,
    DifferenceType.table_row_addition: 0.92,
    DifferenceType.table_row_deletion: 0.92,
    DifferenceType.table_structure_change: 0.88,
    DifferenceType.annotation_present_in_b: 0.85,
    DifferenceType.annotation_removed_from_b: 0.85,
    DifferenceType.section_moved: 0.75,
    DifferenceType.formatting_change: 0.80,
}

# Heuristic significance per difference type (before AI refinement)
_TYPE_HEURISTIC_SIGNIFICANCE: dict[DifferenceType, Significance] = {
    DifferenceType.text_addition: Significance.substantive,
    DifferenceType.text_deletion: Significance.substantive,
    DifferenceType.text_modification: Significance.uncertain,
    DifferenceType.table_cell_change: Significance.material,
    DifferenceType.table_row_addition: Significance.material,
    DifferenceType.table_row_deletion: Significance.material,
    DifferenceType.table_structure_change: Significance.material,
    DifferenceType.annotation_present_in_b: Significance.cosmetic,
    DifferenceType.annotation_removed_from_b: Significance.cosmetic,
    DifferenceType.section_moved: Significance.substantive,
    DifferenceType.formatting_change: Significance.cosmetic,
}


async def run_stage_7(
    diff_records: list[RawDiffRecord],
    ai_provider: AIProvider,
    confidence_threshold: float = 0.75,
    auto_confirm_threshold: float = 0.95,
) -> list[dict]:
    """Stage 7: Confidence scoring and significance classification.

    For each RawDiffRecord:
      1. Assign base confidence from heuristic table.
      2. Assign heuristic significance.
      3. If significance is uncertain, call the AI to classify.
      4. Mark needs_verification = True when confidence < confidence_threshold.
      5. Mark auto_confirmed = True when confidence >= auto_confirm_threshold
         AND significance is not uncertain.

    Returns a list of scored dicts ready for Stage 8 (DetectedDifference creation).
    """
    scored: list[dict] = []

    for idx, record in enumerate(diff_records, start=1):
        difference_number = idx
        diff_type = record.difference_type

        # Step 1: base confidence
        confidence = _TYPE_BASE_CONFIDENCE.get(diff_type, 0.80)

        # Step 2: heuristic significance
        significance = _TYPE_HEURISTIC_SIGNIFICANCE.get(diff_type, Significance.uncertain)

        summary = _build_summary(record)

        # Step 3: AI classification for uncertain significance or low confidence
        if significance == Significance.uncertain or confidence < confidence_threshold:
            try:
                prompt = get_classify_prompt(
                    provider=ai_provider.provider_name,
                    difference_type=diff_type.value,
                    value_before=record.value_before,
                    value_after=record.value_after,
                    context=record.context,
                )
                ai_response = await ai_provider.classify_difference(
                    context=record.context or "",
                    prompt=prompt,
                )
                parsed, flagged = safe_parse_or_flag(ai_response.content)

                if not flagged and parsed:
                    ai_significance_raw = parsed.get("significance", "")
                    ai_confidence = parsed.get("confidence", confidence)
                    ai_reasoning = parsed.get("reasoning", "")

                    try:
                        significance = Significance(ai_significance_raw)
                    except ValueError:
                        logger.warning(
                            f"Stage 7: unknown significance value '{ai_significance_raw}' "
                            f"from AI for diff #{difference_number}; keeping heuristic"
                        )

                    if isinstance(ai_confidence, (int, float)):
                        confidence = float(ai_confidence)

                    if ai_reasoning:
                        summary = ai_reasoning

                else:
                    logger.warning(
                        f"Stage 7: AI classification flagged/failed for diff "
                        f"#{difference_number}; keeping heuristics"
                    )
                    # If AI failed and significance is still uncertain, lower confidence
                    if significance == Significance.uncertain:
                        confidence = min(confidence, confidence_threshold - 0.01)

            except Exception as exc:
                logger.error(
                    f"Stage 7: AI call failed for diff #{difference_number}: {exc}",
                    exc_info=True,
                )
                # Degraded confidence on AI failure
                if significance == Significance.uncertain:
                    confidence = min(confidence, confidence_threshold - 0.01)

        # Step 4 & 5: verification flags
        needs_verification = confidence < confidence_threshold
        auto_confirmed = (
            confidence >= auto_confirm_threshold and significance != Significance.uncertain
        )

        scored.append(
            {
                "difference_number": difference_number,
                "difference_type": diff_type,
                "significance": significance,
                "confidence": confidence,
                "page_version_a": record.page_version_a,
                "page_version_b": record.page_version_b,
                "bbox_version_a": record.bbox_version_a,
                "bbox_version_b": record.bbox_version_b,
                "value_before": record.value_before,
                "value_after": record.value_after,
                "context": record.context,
                "summary": summary,
                "block_id_version_a": record.block_id_version_a,
                "block_id_version_b": record.block_id_version_b,
                "needs_verification": needs_verification,
                "auto_confirmed": auto_confirmed,
            }
        )

    auto_count = sum(1 for s in scored if s["auto_confirmed"])
    verify_count = sum(1 for s in scored if s["needs_verification"])
    logger.info(
        f"Stage 7: scored {len(scored)} differences — "
        f"{auto_count} auto-confirmed, {verify_count} need verification"
    )
    return scored


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_summary(record: RawDiffRecord) -> str:
    """Build a human-readable one-line summary for the difference."""
    diff_type = record.difference_type

    if diff_type == DifferenceType.text_addition:
        preview = _truncate(record.value_after, 60)
        return f"Text added: \"{preview}\""

    if diff_type == DifferenceType.text_deletion:
        preview = _truncate(record.value_before, 60)
        return f"Text deleted: \"{preview}\""

    if diff_type == DifferenceType.text_modification:
        before = _truncate(record.value_before, 40)
        after = _truncate(record.value_after, 40)
        return f"Text changed from \"{before}\" to \"{after}\""

    if diff_type == DifferenceType.table_cell_change:
        return f"Table cell changed: \"{_truncate(record.value_before, 30)}\" → \"{_truncate(record.value_after, 30)}\""

    if diff_type == DifferenceType.table_row_addition:
        return f"Table row added: {record.value_after}"

    if diff_type == DifferenceType.table_row_deletion:
        return f"Table row deleted: {record.value_before}"

    if diff_type == DifferenceType.table_structure_change:
        return "Table structure changed (columns or dimensions differ)"

    if diff_type == DifferenceType.annotation_present_in_b:
        return "Annotation present in Version B"

    if diff_type == DifferenceType.annotation_removed_from_b:
        return "Annotation removed (present in Version A only)"

    if diff_type == DifferenceType.section_moved:
        return f"Section moved: \"{_truncate(record.value_before, 60)}\""

    if diff_type == DifferenceType.formatting_change:
        return "Formatting difference detected"

    return f"{diff_type.value} detected"


def _truncate(text: str, max_len: int) -> str:
    if not text:
        return ""
    text = text.strip()
    if len(text) <= max_len:
        return text
    return text[:max_len] + "…"
