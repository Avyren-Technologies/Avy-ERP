import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.difference import DetectedDifference, VerificationStatus
from app.models.job import ComparisonJob, JobStatus

logger = logging.getLogger("docdiff.pipeline")


async def run_stage_8(
    job_id: uuid.UUID,
    scored_differences: list[dict],
    db: AsyncSession,
) -> bool:
    """Stage 8: Persist scored differences and finalise the job.

    For every scored difference dict produced by Stage 7:
      - Creates a DetectedDifference row.
      - Sets verification_status to CONFIRMED if auto_confirmed, else PENDING.

    After persisting all differences:
      - Updates job.total_differences with the total count.
      - Updates job.differences_verified with the count of auto-confirmed ones.
      - Sets job.status to READY_FOR_REVIEW.
      - Commits and returns True.

    Returns False (without raising) if the job cannot be found.
    """
    result = await db.execute(select(ComparisonJob).where(ComparisonJob.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        logger.error(f"Stage 8: job {job_id} not found")
        return False

    # Deduplicate before saving
    scored_differences = _deduplicate_differences(scored_differences)

    # Re-number after dedup
    for i, diff in enumerate(scored_differences, start=1):
        diff["difference_number"] = i

    auto_confirmed_count = 0

    for scored in scored_differences:
        is_auto_confirmed: bool = scored.get("auto_confirmed", False)

        verification_status = (
            VerificationStatus.confirmed if is_auto_confirmed else VerificationStatus.pending
        )

        if is_auto_confirmed:
            auto_confirmed_count += 1

        difference = DetectedDifference(
            job_id=job_id,
            difference_number=scored["difference_number"],
            difference_type=scored["difference_type"],
            significance=scored["significance"],
            confidence=scored["confidence"],
            page_version_a=scored.get("page_version_a"),
            page_version_b=scored.get("page_version_b"),
            bbox_version_a=scored.get("bbox_version_a"),
            bbox_version_b=scored.get("bbox_version_b"),
            value_before=scored.get("value_before"),
            value_after=scored.get("value_after"),
            context=scored.get("context"),
            summary=scored.get("summary", ""),
            block_id_version_a=scored.get("block_id_version_a"),
            block_id_version_b=scored.get("block_id_version_b"),
            verification_status=verification_status,
            auto_confirmed=is_auto_confirmed,
            needs_verification=scored.get("needs_verification", False),
        )
        db.add(difference)

    job.total_differences = len(scored_differences)
    job.differences_verified = auto_confirmed_count
    job.status = JobStatus.ready_for_review

    await db.commit()

    logger.info(
        f"Stage 8: saved {len(scored_differences)} differences for job {job_id} — "
        f"{auto_confirmed_count} auto-confirmed; job status → ready_for_review"
    )
    return True


def _deduplicate_differences(scored: list[dict]) -> list[dict]:
    """Enhanced deduplication and noise reduction.

    Applies these filters in order:
    1. Remove OCR garbage entries
    2. Collapse header/footer changes repeated across pages into single entries
    3. Remove page number pattern changes
    4. Remove duplicate same-value changes on same page
    """
    from collections import defaultdict

    from app.utils.diff_utils import is_ocr_garbage, is_page_number_text

    # Pass 1: Filter OCR garbage
    clean: list[dict] = []
    ocr_removed = 0
    for diff in scored:
        before = (diff.get("value_before") or "").strip()
        after = (diff.get("value_after") or "").strip()
        if is_ocr_garbage(before) or is_ocr_garbage(after):
            ocr_removed += 1
            continue
        clean.append(diff)
    if ocr_removed:
        logger.info(f"Dedup: removed {ocr_removed} OCR garbage entries")

    # Pass 2: Collapse header/footer repeats across pages
    # Group by (before, after, diff_type) ignoring page numbers
    content_groups: dict[tuple, list[dict]] = defaultdict(list)
    for diff in clean:
        before = (diff.get("value_before") or "").strip()
        after = (diff.get("value_after") or "").strip()
        key = (before, after, str(diff.get("difference_type")))
        content_groups[key].append(diff)

    collapsed: list[dict] = []
    collapsed_count = 0
    seen_keys: set[tuple] = set()

    for diff in clean:
        before = (diff.get("value_before") or "").strip()
        after = (diff.get("value_after") or "").strip()
        key = (before, after, str(diff.get("difference_type")))

        if key in seen_keys:
            continue
        seen_keys.add(key)

        group = content_groups[key]
        if len(group) >= 3:
            # This change appears on 3+ pages -- it's a header/footer/repeated element
            pages = sorted(set(
                d.get("page_version_a") or d.get("page_version_b") or 0 for d in group
            ))
            representative = group[0].copy()
            representative["summary"] = (
                f"{representative.get('summary', '')} "
                f"(found on {len(group)} pages: {', '.join(str(p) for p in pages[:5])}"
                f"{'...' if len(pages) > 5 else ''})"
            )
            # Downgrade repeated header/footer changes to cosmetic
            from app.models.difference import Significance
            representative["significance"] = Significance.cosmetic
            representative["auto_confirmed"] = True
            representative["confidence"] = 0.98
            collapsed.append(representative)
            collapsed_count += len(group) - 1
        else:
            collapsed.append(diff)

    if collapsed_count:
        logger.info(f"Dedup: collapsed {collapsed_count} repeated header/footer entries")

    # Pass 3: Filter page number changes
    filtered: list[dict] = []
    page_num_removed = 0
    for diff in collapsed:
        before = (diff.get("value_before") or "").strip()
        after = (diff.get("value_after") or "").strip()
        if is_page_number_text(before) or is_page_number_text(after):
            page_num_removed += 1
            continue
        filtered.append(diff)
    if page_num_removed:
        logger.info(f"Dedup: removed {page_num_removed} page number entries")

    # Pass 4: Same-value dedup on same page (existing logic)
    seen: set[tuple] = set()
    final: list[dict] = []
    for diff in filtered:
        before = (diff.get("value_before") or "").strip()
        after = (diff.get("value_after") or "").strip()
        if len(before) <= 1 and len(after) <= 1:
            final.append(diff)
            continue
        page_a = diff.get("page_version_a")
        page_b = diff.get("page_version_b")
        key = (before, after, page_a, page_b, str(diff.get("difference_type")))
        if key in seen:
            continue
        seen.add(key)
        final.append(diff)

    total_removed = len(scored) - len(final)
    if total_removed:
        logger.info(
            f"Dedup total: {len(scored)} -> {len(final)} "
            f"({total_removed} entries removed: {ocr_removed} OCR, "
            f"{collapsed_count} header/footer, {page_num_removed} page numbers, "
            f"{len(scored) - len(final) - ocr_removed - collapsed_count - page_num_removed} same-value)"
        )
    return final
