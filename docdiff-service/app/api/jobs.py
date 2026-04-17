import os
import uuid

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.api.deps import CurrentUser, DbSession
from app.config import settings
from app.models.difference import DetectedDifference, Significance
from app.models.document import Document, DocumentRole
from app.models.job import ComparisonJob, JobStatus
from app.schemas.job import JobListResponse, JobResponse
from app.schemas.common import SuccessResponse

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("", response_model=SuccessResponse[JobResponse])
async def create_job(
    db: DbSession,
    user: CurrentUser,
    version_a: UploadFile = File(..., description="Version A PDF document"),
    version_b: UploadFile = File(..., description="Version B PDF document"),
    model_provider: str = Form(default=settings.default_provider),
    model_name: str = Form(default=settings.default_model),
    label_a: str = Form(default="Version A"),
    label_b: str = Form(default="Version B"),
    auto_confirm_threshold: float = Form(default=0.95),
):
    for f, label in [(version_a, "Version A"), (version_b, "Version B")]:
        if not f.filename or not f.filename.lower().endswith(".pdf"):
            raise HTTPException(400, f"{label} file must be a PDF")
        if f.size and f.size > settings.max_file_size_mb * 1024 * 1024:
            raise HTTPException(400, f"{label} file exceeds {settings.max_file_size_mb}MB limit")

    job = ComparisonJob(
        model_provider=model_provider,
        model_name=model_name,
        status=JobStatus.uploading,
        auto_confirm_threshold=auto_confirm_threshold,
        user_id=user.user_id,
        company_id=user.company_id,
        api_key_id=uuid.UUID(user.api_key_id) if user.api_key_id else None,
    )
    db.add(job)
    await db.flush()

    job_dir = os.path.join(settings.storage_path, "uploads", str(job.id))
    os.makedirs(job_dir, exist_ok=True)

    for upload, role, label in [
        (version_a, DocumentRole.version_a, label_a),
        (version_b, DocumentRole.version_b, label_b),
    ]:
        file_path = os.path.join(job_dir, f"{role.value}_{upload.filename}")
        content = await upload.read()
        with open(file_path, "wb") as f:
            f.write(content)

        doc = Document(
            job_id=job.id,
            role=role,
            label=label,
            filename=upload.filename or "unknown.pdf",
            file_path=file_path,
            file_size_bytes=len(content),
            page_count=0,
        )
        db.add(doc)

    await db.commit()
    await db.refresh(job)
    return SuccessResponse(data=JobResponse.model_validate(job), message="Job created")


@router.get("", response_model=SuccessResponse[list[JobListResponse]])
async def list_jobs(db: DbSession, user: CurrentUser):
    query = (
        select(ComparisonJob)
        .options(selectinload(ComparisonJob.documents))
        .order_by(ComparisonJob.created_at.desc())
    )
    if user.user_id:
        query = query.where(ComparisonJob.user_id == user.user_id)
    elif user.api_key_id:
        query = query.where(ComparisonJob.api_key_id == uuid.UUID(user.api_key_id))
    result = await db.execute(query)
    jobs = result.scalars().unique().all()

    response_list = []
    for j in jobs:
        docs = {d.role: d for d in j.documents}
        doc_a = docs.get(DocumentRole.version_a)
        doc_b = docs.get(DocumentRole.version_b)

        material_result = await db.execute(
            select(func.count()).select_from(DetectedDifference).where(
                DetectedDifference.job_id == j.id,
                DetectedDifference.significance == Significance.material,
            )
        )
        material_count = material_result.scalar() or 0

        response_list.append(JobListResponse(
            id=j.id,
            status=j.status,
            model_provider=j.model_provider,
            model_name=j.model_name,
            label_a=doc_a.label if doc_a else None,
            label_b=doc_b.label if doc_b else None,
            total_differences=j.total_differences,
            differences_verified=j.differences_verified,
            material_count=material_count,
            processing_time_ms=j.processing_time_ms,
            created_at=j.created_at,
        ))
    return SuccessResponse(data=response_list)


@router.get("/{job_id}", response_model=SuccessResponse[JobResponse])
async def get_job(job_id: uuid.UUID, db: DbSession, user: CurrentUser):
    result = await db.execute(select(ComparisonJob).where(ComparisonJob.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(404, "Job not found")
    return SuccessResponse(data=JobResponse.model_validate(job))


@router.delete("/{job_id}")
async def delete_job(job_id: uuid.UUID, db: DbSession, user: CurrentUser):
    result = await db.execute(select(ComparisonJob).where(ComparisonJob.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(404, "Job not found")
    await db.delete(job)
    await db.commit()
    return SuccessResponse(data=None, message="Job deleted")


@router.post("/{job_id}/start")
async def start_job(job_id: uuid.UUID, db: DbSession, user: CurrentUser):
    result = await db.execute(select(ComparisonJob).where(ComparisonJob.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(404, "Job not found")
    if job.status != JobStatus.uploading:
        raise HTTPException(400, f"Job cannot be started from status: {job.status}")

    job.status = JobStatus.parsing_version_a
    job.current_stage = 1
    job.stage_progress = {"1": "in_progress"}
    await db.commit()

    from app.workers.job_worker import enqueue_job
    await enqueue_job(str(job_id))

    await db.refresh(job)
    return SuccessResponse(data=JobResponse.model_validate(job), message="Processing started")
