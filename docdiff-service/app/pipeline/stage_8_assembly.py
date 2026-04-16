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
