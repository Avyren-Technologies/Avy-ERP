"""Corrections library — learns from reviewer feedback.

Queries the reviewer_corrections table for recent corrections matching
the current difference type, and formats them as few-shot examples
for the AI classification prompt.
"""
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.correction import ReviewerCorrection

logger = logging.getLogger("docdiff.prompts")


async def get_relevant_corrections(
    difference_type: str,
    db: AsyncSession,
    limit: int = 5,
) -> list[dict]:
    """Get recent corrections for a given difference type.

    Returns the most recent corrections as dicts for prompt injection.
    """
    result = await db.execute(
        select(ReviewerCorrection)
        .where(ReviewerCorrection.difference_type == difference_type)
        .order_by(ReviewerCorrection.created_at.desc())
        .limit(limit)
    )
    corrections = result.scalars().all()
    return [
        {
            "before": c.value_before,
            "after": c.value_after,
            "was": c.original_significance,
            "corrected_to": c.corrected_significance,
            "reason": c.verifier_comment or "",
        }
        for c in corrections
    ]


def format_corrections_for_prompt(corrections: list[dict]) -> str:
    """Format corrections as few-shot examples for the classification prompt."""
    if not corrections:
        return ""

    lines = ["\n## Previous Reviewer Corrections (learn from these):\n"]
    for i, c in enumerate(corrections, 1):
        lines.append(
            f"{i}. '{c['before']}' -> '{c['after']}' was classified as {c['was']}, "
            f"reviewer corrected to {c['corrected_to']}"
            + (f" (reason: {c['reason']})" if c['reason'] else "")
        )
    lines.append("\nUse these corrections to inform your classification.\n")
    return "\n".join(lines)
