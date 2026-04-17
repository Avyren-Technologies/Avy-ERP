import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import func, select

from app.api.deps import CurrentUser, DbSession
from app.models.difference import (
    DetectedDifference,
    DifferenceType,
    Significance,
    VerificationStatus,
)
from app.models.job import ComparisonJob
from app.schemas.common import PaginatedResponse, SuccessResponse
from app.schemas.difference import (
    BulkVerificationAction,
    DifferenceResponse,
    ManualDifferenceCreate,
    VerificationAction,
)

router = APIRouter(prefix="/jobs", tags=["differences"])

_VERIFIED_STATUSES = {
    VerificationStatus.confirmed,
    VerificationStatus.dismissed,
    VerificationStatus.corrected,
    VerificationStatus.flagged,
}


@router.get("/{job_id}/differences", response_model=PaginatedResponse[DifferenceResponse])
async def list_differences(
    job_id: uuid.UUID,
    db: DbSession,
    user: CurrentUser,
    difference_type: DifferenceType | None = Query(default=None),
    significance: Significance | None = Query(default=None),
    verification_status: VerificationStatus | None = Query(default=None),
    needs_verification: bool | None = Query(default=None),
    confidence_min: float | None = Query(default=None, ge=0.0, le=1.0),
    confidence_max: float | None = Query(default=None, ge=0.0, le=1.0),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=50, ge=1, le=200),
):
    # Verify job exists
    job_result = await db.execute(select(ComparisonJob).where(ComparisonJob.id == job_id))
    job = job_result.scalar_one_or_none()
    if not job:
        raise HTTPException(404, "Job not found")

    query = select(DetectedDifference).where(DetectedDifference.job_id == job_id)

    if difference_type is not None:
        query = query.where(DetectedDifference.difference_type == difference_type)
    if significance is not None:
        query = query.where(DetectedDifference.significance == significance)
    if verification_status is not None:
        query = query.where(DetectedDifference.verification_status == verification_status)
    if needs_verification is not None:
        query = query.where(DetectedDifference.needs_verification == needs_verification)
    if confidence_min is not None:
        query = query.where(DetectedDifference.confidence >= confidence_min)
    if confidence_max is not None:
        query = query.where(DetectedDifference.confidence <= confidence_max)

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0

    # Paginate
    query = (
        query.order_by(DetectedDifference.difference_number)
        .offset((page - 1) * limit)
        .limit(limit)
    )
    result = await db.execute(query)
    differences = result.scalars().all()

    total_pages = max(1, (total + limit - 1) // limit)
    return PaginatedResponse(
        data=[DifferenceResponse.model_validate(d) for d in differences],
        meta={"page": page, "limit": limit, "total": total, "totalPages": total_pages},
    )


@router.get(
    "/{job_id}/differences/{difference_id}",
    response_model=SuccessResponse[DifferenceResponse],
)
async def get_difference(
    job_id: uuid.UUID,
    difference_id: uuid.UUID,
    db: DbSession,
    user: CurrentUser,
):
    result = await db.execute(
        select(DetectedDifference).where(
            DetectedDifference.job_id == job_id,
            DetectedDifference.id == difference_id,
        )
    )
    diff = result.scalar_one_or_none()
    if not diff:
        raise HTTPException(404, "Difference not found")
    return SuccessResponse(data=DifferenceResponse.model_validate(diff))


@router.patch(
    "/{job_id}/differences/{difference_id}",
    response_model=SuccessResponse[DifferenceResponse],
)
async def verify_difference(
    job_id: uuid.UUID,
    difference_id: uuid.UUID,
    body: VerificationAction,
    db: DbSession,
    user: CurrentUser,
):
    result = await db.execute(
        select(DetectedDifference).where(
            DetectedDifference.job_id == job_id,
            DetectedDifference.id == difference_id,
        )
    )
    diff = result.scalar_one_or_none()
    if not diff:
        raise HTTPException(404, "Difference not found")

    was_verified = diff.verification_status in _VERIFIED_STATUSES
    original_significance = diff.significance

    diff.verification_status = body.action
    diff.verified_at = datetime.now(tz=timezone.utc)

    if body.comment is not None:
        diff.verifier_comment = body.comment
    if body.corrected_description is not None:
        diff.corrected_description = body.corrected_description
    if body.corrected_significance is not None:
        diff.significance = body.corrected_significance
    if body.corrected_value_after is not None:
        diff.value_after = body.corrected_value_after

    # Log correction for future learning if significance was changed
    if body.corrected_significance is not None:
        from app.models.correction import ReviewerCorrection
        correction = ReviewerCorrection(
            value_before=diff.value_before or "",
            value_after=diff.value_after or "",
            difference_type=diff.difference_type.value if diff.difference_type else "",
            original_significance=original_significance.value if original_significance else "",
            corrected_significance=body.corrected_significance.value,
            verifier_comment=body.comment,
            context=diff.context,
        )
        db.add(correction)

    # Update job.differences_verified count
    is_now_verified = body.action in _VERIFIED_STATUSES
    if is_now_verified and not was_verified:
        job_result = await db.execute(
            select(ComparisonJob).where(ComparisonJob.id == job_id)
        )
        job = job_result.scalar_one_or_none()
        if job:
            job.differences_verified = (job.differences_verified or 0) + 1

    await db.commit()
    await db.refresh(diff)
    return SuccessResponse(
        data=DifferenceResponse.model_validate(diff),
        message="Difference updated",
    )


@router.patch(
    "/{job_id}/differences/bulk",
    response_model=SuccessResponse[list[DifferenceResponse]],
)
async def bulk_verify_differences(
    job_id: uuid.UUID,
    body: BulkVerificationAction,
    db: DbSession,
    user: CurrentUser,
):
    # Verify job exists
    job_result = await db.execute(select(ComparisonJob).where(ComparisonJob.id == job_id))
    job = job_result.scalar_one_or_none()
    if not job:
        raise HTTPException(404, "Job not found")

    result = await db.execute(
        select(DetectedDifference).where(
            DetectedDifference.job_id == job_id,
            DetectedDifference.id.in_(body.difference_ids),
        )
    )
    differences = result.scalars().all()

    newly_verified_count = 0
    is_now_verified = body.action in _VERIFIED_STATUSES
    now = datetime.now(tz=timezone.utc)

    for diff in differences:
        was_verified = diff.verification_status in _VERIFIED_STATUSES
        diff.verification_status = body.action
        diff.verified_at = now
        if body.comment is not None:
            diff.verifier_comment = body.comment
        if is_now_verified and not was_verified:
            newly_verified_count += 1

    if newly_verified_count > 0:
        job.differences_verified = (job.differences_verified or 0) + newly_verified_count

    await db.commit()
    for diff in differences:
        await db.refresh(diff)

    return SuccessResponse(
        data=[DifferenceResponse.model_validate(d) for d in differences],
        message=f"{len(differences)} differences updated",
    )


@router.post(
    "/{job_id}/differences",
    response_model=SuccessResponse[DifferenceResponse],
    status_code=201,
)
async def create_manual_difference(
    job_id: uuid.UUID,
    body: ManualDifferenceCreate,
    db: DbSession,
    user: CurrentUser,
):
    # Verify job exists
    job_result = await db.execute(select(ComparisonJob).where(ComparisonJob.id == job_id))
    job = job_result.scalar_one_or_none()
    if not job:
        raise HTTPException(404, "Job not found")

    # Determine next difference_number
    count_result = await db.execute(
        select(DetectedDifference).where(DetectedDifference.job_id == job_id)
    )
    existing = count_result.scalars().all()
    next_number = max((d.difference_number for d in existing), default=0) + 1

    diff = DetectedDifference(
        job_id=job_id,
        difference_number=next_number,
        difference_type=body.difference_type,
        significance=body.significance,
        confidence=1.0,
        page_version_a=body.page_version_a,
        page_version_b=body.page_version_b,
        value_before=body.value_before,
        value_after=body.value_after,
        summary=body.summary,
        verification_status=VerificationStatus.pending,
        auto_confirmed=False,
        needs_verification=True,
    )
    db.add(diff)

    job.total_differences = (job.total_differences or 0) + 1
    await db.commit()
    await db.refresh(diff)

    return SuccessResponse(
        data=DifferenceResponse.model_validate(diff),
        message="Manual difference created",
    )
