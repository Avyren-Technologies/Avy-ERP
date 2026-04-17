"""
stage_7_scoring.py — Confidence Scoring & Significance Classification

Strategy (cost-first, AI-last):

  1. Deterministic rule engine handles ~80% of diffs in microseconds (zero cost).
  2. Only diffs that the rule engine cannot resolve with high confidence are sent
     to the AI — typically <10% of all diffs.
  3. The AI call uses tight generation config (JSON mode, max 150 tokens,
     temperature 0.1) so it can't ramble.

This reduces AI calls from O(N_diffs) → O(0.1 × N_diffs) and cuts output
tokens by ~80% per call, dramatically lowering cost and latency.
"""

import logging
import re

from app.ai.base import AIProvider
from app.ai.response_parser import safe_parse_or_flag
from app.models.difference import DifferenceType, Significance
from app.pipeline.stage_6_diff import RawDiffRecord
from app.prompts.classify_difference import get_classify_prompt
from app.prompts.system_prompts import CLASSIFICATION_SYSTEM_PROMPT

logger = logging.getLogger("docdiff.pipeline")

# ---------------------------------------------------------------------------
# Base confidence per difference type (heuristic, before rule engine)
# ---------------------------------------------------------------------------
_TYPE_BASE_CONFIDENCE: dict[DifferenceType, float] = {
    DifferenceType.text_addition:           0.92,
    DifferenceType.text_deletion:           0.92,
    DifferenceType.text_modification:       0.80,
    DifferenceType.table_cell_change:       0.95,
    DifferenceType.table_row_addition:      0.95,
    DifferenceType.table_row_deletion:      0.95,
    DifferenceType.table_structure_change:  0.90,
    DifferenceType.annotation_present_in_b: 0.88,
    DifferenceType.annotation_removed_from_b: 0.88,
    DifferenceType.section_moved:           0.78,
    DifferenceType.formatting_change:       0.85,
}


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

async def run_stage_7(
    diff_records: list[RawDiffRecord],
    ai_provider: AIProvider,
    confidence_threshold: float = 0.75,
    auto_confirm_threshold: float = 0.95,
) -> list[dict]:
    """
    Stage 7: confidence scoring + significance classification.

    For each RawDiffRecord:
      1. Deterministic rule engine → significance + confidence (no API cost).
      2. If rule engine is uncertain (confidence < 0.72) → AI classify.
      3. Set needs_verification / auto_confirmed flags.
    """
    scored: list[dict] = []

    ai_call_count = 0
    rule_resolved_count = 0

    for idx, record in enumerate(diff_records, start=1):
        diff_type = record.difference_type
        base_confidence = _TYPE_BASE_CONFIDENCE.get(diff_type, 0.80)

        # ── Step 1: deterministic rule engine ─────────────────────────────
        rule_significance, rule_confidence, rule_summary = _rule_engine(record)

        significance = rule_significance
        confidence = rule_confidence
        summary = rule_summary or _build_summary(record)

        # ── Step 2: AI only if rule engine is genuinely uncertain ─────────
        # Threshold of 0.72 means: "rule engine gives < 72% certainty" → ask AI
        if rule_confidence < 0.72:
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
                    system=CLASSIFICATION_SYSTEM_PROMPT,
                )
                ai_call_count += 1
                parsed, flagged = safe_parse_or_flag(ai_response.content)

                if not flagged and parsed:
                    ai_sig_raw = parsed.get("significance", "")
                    ai_conf = parsed.get("confidence", confidence)
                    ai_reason = parsed.get("reasoning", "")

                    try:
                        significance = Significance(ai_sig_raw)
                    except ValueError:
                        logger.debug(
                            f"Stage 7: unknown AI significance '{ai_sig_raw}' "
                            f"for diff #{idx}; keeping rule result"
                        )

                    if isinstance(ai_conf, (int, float)):
                        confidence = float(ai_conf)

                    if ai_reason:
                        summary = ai_reason
                else:
                    logger.debug(f"Stage 7: diff #{idx} AI parse failed; using rule result")
                    if significance == Significance.uncertain:
                        confidence = min(confidence, confidence_threshold - 0.01)

            except Exception as exc:
                logger.error(f"Stage 7: AI call failed for diff #{idx}: {exc}")
                if significance == Significance.uncertain:
                    confidence = min(confidence, confidence_threshold - 0.01)
        else:
            rule_resolved_count += 1

        # ── Step 3: verification flags ────────────────────────────────────
        needs_verification = confidence < confidence_threshold
        auto_confirmed = (
            confidence >= auto_confirm_threshold
            and significance != Significance.uncertain
        )

        scored.append({
            "difference_number":    idx,
            "difference_type":      diff_type,
            "significance":         significance,
            "confidence":           confidence,
            "page_version_a":       record.page_version_a,
            "page_version_b":       record.page_version_b,
            "bbox_version_a":       record.bbox_version_a,
            "bbox_version_b":       record.bbox_version_b,
            "value_before":         record.value_before,
            "value_after":          record.value_after,
            "context":              record.context,
            "summary":              summary,
            "block_id_version_a":   record.block_id_version_a,
            "block_id_version_b":   record.block_id_version_b,
            "needs_verification":   needs_verification,
            "auto_confirmed":       auto_confirmed,
        })

    auto_count   = sum(1 for s in scored if s["auto_confirmed"])
    verify_count = sum(1 for s in scored if s["needs_verification"])
    logger.info(
        f"Stage 7: {len(scored)} diffs — "
        f"{rule_resolved_count} rule-resolved (0 AI cost), "
        f"{ai_call_count} AI call(s) — "
        f"{auto_count} auto-confirmed, {verify_count} need verification"
    )
    return scored


# ---------------------------------------------------------------------------
# Deterministic rule engine  (no AI, no cost)
# ---------------------------------------------------------------------------

def _rule_engine(
    record: RawDiffRecord,
) -> tuple[Significance, float, str | None]:
    """
    Returns (significance, confidence, summary_or_None).
    confidence < 0.72 → caller should escalate to AI.
    """
    diff_type = record.difference_type
    before = (record.value_before or "").strip()
    after  = (record.value_after  or "").strip()

    # ── Non-text types: already well-defined ─────────────────────────────
    if diff_type == DifferenceType.formatting_change:
        return Significance.cosmetic, 0.95, "Formatting difference detected"

    if diff_type in (
        DifferenceType.annotation_present_in_b,
        DifferenceType.annotation_removed_from_b,
    ):
        return Significance.substantive, 0.85, _build_summary(record)

    if diff_type in (
        DifferenceType.table_cell_change,
        DifferenceType.table_row_addition,
        DifferenceType.table_row_deletion,
        DifferenceType.table_structure_change,
    ):
        return Significance.material, 0.95, _build_summary(record)

    if diff_type in (DifferenceType.text_addition, DifferenceType.text_deletion):
        # Whitespace / empty additions → cosmetic
        if not (before or after).strip():
            return Significance.cosmetic, 0.97, "Whitespace-only change"
        # Short filler words → cosmetic
        if _is_filler_only(before or after):
            return Significance.cosmetic, 0.88, "Minor filler-word change"
        return Significance.substantive, 0.92, _build_summary(record)

    if diff_type == DifferenceType.section_moved:
        return Significance.substantive, 0.80, _build_summary(record)

    # ── text_modification: most complex — apply fine-grained rules ────────
    if diff_type == DifferenceType.text_modification:
        return _classify_text_modification(before, after)

    # Unknown type: send to AI
    return Significance.uncertain, 0.50, None


def _classify_text_modification(before: str, after: str) -> tuple[Significance, float, str | None]:
    """Rule-based classifier for text_modification diffs."""

    # Identical after strip → cosmetic
    if before == after:
        return Significance.cosmetic, 0.99, "No substantive change"

    # Whitespace / punctuation only
    if _text_equal_ignoring_whitespace(before, after):
        return Significance.cosmetic, 0.97, "Whitespace normalisation only"

    if _punctuation_only_diff(before, after):
        return Significance.cosmetic, 0.92, "Punctuation-only change"

    # Case-only difference
    if before.lower() == after.lower():
        return Significance.cosmetic, 0.95, "Capitalisation change only"

    # Version/revision identifiers -> cosmetic
    if re.search(r"(?:rev\.?\s*\d|version\s+\d|v\d+|rev\s*\.?\s*\d)", before, re.IGNORECASE) or \
       re.search(r"(?:rev\.?\s*\d|version\s+\d|v\d+|rev\s*\.?\s*\d)", after, re.IGNORECASE):
        return Significance.cosmetic, 0.93, (
            f"Version/revision identifier changed: \"{_truncate(before, 50)}\" -> \"{_truncate(after, 50)}\""
        )

    # Document reference IDs (RPT-xxxx, DOC-xxxx, 6-44-0052, etc.) -> cosmetic
    if re.search(r"[A-Z]{2,4}-\d{3,}", before) and re.search(r"[A-Z]{2,4}-\d{3,}", after):
        # Both contain doc reference patterns -- check if only the suffix changed
        before_stripped = re.sub(r"[A-Z]{2,4}-[\d-]+[A-Z]?", "", before).strip()
        after_stripped = re.sub(r"[A-Z]{2,4}-[\d-]+[A-Z]?", "", after).strip()
        if before_stripped == after_stripped:
            return Significance.cosmetic, 0.92, (
                f"Document reference ID changed: \"{_truncate(before, 50)}\" -> \"{_truncate(after, 50)}\""
            )

    # Number / date / amount changes -> MATERIAL (high stakes)
    if _contains_number(before) or _contains_number(after):
        if _numbers_changed(before, after):
            return Significance.material, 0.92, (
                f"Numerical value changed: \"{_truncate(before, 50)}\" → \"{_truncate(after, 50)}\""
            )

    if _contains_date(before) or _contains_date(after):
        # Document metadata dates (report date, prepared date) → cosmetic
        context_lower = before.lower() + " " + after.lower()
        if any(kw in context_lower for kw in ["date:", "prepared", "report", "revision", "version", "issued"]):
            return Significance.cosmetic, 0.88, (
                f"Document date changed: \"{_truncate(before, 50)}\" → \"{_truncate(after, 50)}\""
            )
        # Other dates (delivery, deadline) → substantive (not material unless numeric)
        return Significance.substantive, 0.85, (
            f"Date changed: \"{_truncate(before, 50)}\" → \"{_truncate(after, 50)}\""
        )

    # Currency / monetary
    if _contains_currency(before) or _contains_currency(after):
        return Significance.material, 0.93, (
            f"Monetary value changed: \"{_truncate(before, 50)}\" → \"{_truncate(after, 50)}\""
        )

    # Legal / obligation keywords
    if _contains_legal_keyword(before) or _contains_legal_keyword(after):
        return Significance.material, 0.85, (
            f"Legal/obligation term changed: \"{_truncate(before, 50)}\" → \"{_truncate(after, 50)}\""
        )

    # Very short change (≤3 chars) with no numbers → likely minor
    if len(before) <= 3 and len(after) <= 3:
        return Significance.cosmetic, 0.82, f"Minor text change: \"{before}\" → \"{after}\""

    # Small edit ratio (Jaccard similarity > 0.85) → likely minor rewording
    if _jaccard_similarity(before, after) > 0.85:
        return Significance.cosmetic, 0.78, "Minor rewording, high similarity"

    # Medium-confidence substantive: ~30% of words changed
    if _jaccard_similarity(before, after) < 0.50:
        return Significance.substantive, 0.80, (
            f"Significant text changed: \"{_truncate(before, 40)}\" → \"{_truncate(after, 40)}\""
        )

    # Falls through: genuine uncertainty — escalate to AI
    return Significance.uncertain, 0.65, None


# ---------------------------------------------------------------------------
# Pattern helpers
# ---------------------------------------------------------------------------

_RE_NUMBER   = re.compile(r"\b\d[\d,._]*\b")
_RE_DATE     = re.compile(
    r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}"
    r"|\d{4}[/-]\d{1,2}[/-]\d{1,2}"
    r"|\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{4}"
    r"|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},?\s+\d{4})\b",
    re.IGNORECASE,
)
_RE_CURRENCY = re.compile(r"[\$\€\£\₹\¥]|\b(usd|eur|gbp|inr|rs\.?)\b", re.IGNORECASE)
_LEGAL_KEYWORDS = re.compile(
    r"\b(shall|must|will|may not|cannot|liable|obligation|warranty|indemnif|terminat"
    r"|penalt|forfeit|breach|default|notwithstanding|whereas|herein|thereof)\b",
    re.IGNORECASE,
)
_FILLER = re.compile(
    r"^(the|a|an|and|or|but|in|on|at|to|for|of|with|by|from|is|are|was|were|be|been)\b$",
    re.IGNORECASE,
)


def _contains_number(text: str) -> bool:
    return bool(_RE_NUMBER.search(text))


def _numbers_changed(before: str, after: str) -> bool:
    nums_b = set(_RE_NUMBER.findall(before))
    nums_a = set(_RE_NUMBER.findall(after))
    return nums_b != nums_a


def _contains_date(text: str) -> bool:
    return bool(_RE_DATE.search(text))


def _contains_currency(text: str) -> bool:
    return bool(_RE_CURRENCY.search(text))


def _contains_legal_keyword(text: str) -> bool:
    return bool(_LEGAL_KEYWORDS.search(text))


def _is_filler_only(text: str) -> bool:
    words = text.split()
    return bool(words) and all(_FILLER.match(w) for w in words)


def _text_equal_ignoring_whitespace(a: str, b: str) -> bool:
    return " ".join(a.split()) == " ".join(b.split())


def _punctuation_only_diff(a: str, b: str) -> bool:
    _strip = re.compile(r"[^\w\s]")
    return _strip.sub("", a).strip() == _strip.sub("", b).strip()


def _jaccard_similarity(a: str, b: str) -> float:
    set_a = set(a.lower().split())
    set_b = set(b.lower().split())
    if not set_a and not set_b:
        return 1.0
    if not set_a or not set_b:
        return 0.0
    return len(set_a & set_b) / len(set_a | set_b)


# ---------------------------------------------------------------------------
# Summary helpers
# ---------------------------------------------------------------------------

def _build_summary(record: RawDiffRecord) -> str:
    diff_type = record.difference_type

    if diff_type == DifferenceType.text_addition:
        return f"Text added: \"{_truncate(record.value_after, 60)}\""
    if diff_type == DifferenceType.text_deletion:
        return f"Text deleted: \"{_truncate(record.value_before, 60)}\""
    if diff_type == DifferenceType.text_modification:
        return (
            f"Text changed from \"{_truncate(record.value_before, 40)}\" "
            f"to \"{_truncate(record.value_after, 40)}\""
        )
    if diff_type == DifferenceType.table_cell_change:
        return (
            f"Table cell changed: \"{_truncate(record.value_before, 30)}\" "
            f"→ \"{_truncate(record.value_after, 30)}\""
        )
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
    return text if len(text) <= max_len else text[:max_len] + "…"
