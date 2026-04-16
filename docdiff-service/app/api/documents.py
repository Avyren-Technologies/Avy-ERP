import uuid

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.deps import CurrentUser, DbSession
from app.models.document import Document, DocumentPage, DocumentRole
from app.models.job import ComparisonJob
from app.schemas.common import SuccessResponse
from app.schemas.document import PageContentResponse

router = APIRouter(prefix="/jobs", tags=["documents"])


@router.get("/{job_id}/documents/{role}/pages/{page_num}/image")
async def get_page_image(
    job_id: uuid.UUID,
    role: DocumentRole,
    page_num: int,
    db: DbSession,
    user: CurrentUser,
):
    # Verify job exists
    job_result = await db.execute(select(ComparisonJob).where(ComparisonJob.id == job_id))
    job = job_result.scalar_one_or_none()
    if not job:
        raise HTTPException(404, "Job not found")

    # Find the document for this role
    doc_result = await db.execute(
        select(Document)
        .options(selectinload(Document.pages))
        .where(Document.job_id == job_id, Document.role == role)
    )
    doc = doc_result.scalar_one_or_none()
    if not doc:
        raise HTTPException(404, f"Document '{role.value}' not found for this job")

    # Find the page
    page_result = await db.execute(
        select(DocumentPage).where(
            DocumentPage.document_id == doc.id,
            DocumentPage.page_number == page_num,
        )
    )
    page = page_result.scalar_one_or_none()
    if not page:
        raise HTTPException(404, f"Page {page_num} not found")

    if not page.image_path:
        raise HTTPException(404, f"Image for page {page_num} has not been rendered yet")

    return FileResponse(
        path=page.image_path,
        media_type="image/png",
        filename=f"page_{page_num:03d}.png",
    )


@router.get(
    "/{job_id}/documents/{role}/pages/{page_num}/content",
    response_model=SuccessResponse[PageContentResponse],
)
async def get_page_content(
    job_id: uuid.UUID,
    role: DocumentRole,
    page_num: int,
    db: DbSession,
    user: CurrentUser,
):
    # Verify job exists
    job_result = await db.execute(select(ComparisonJob).where(ComparisonJob.id == job_id))
    job = job_result.scalar_one_or_none()
    if not job:
        raise HTTPException(404, "Job not found")

    # Find the document for this role
    doc_result = await db.execute(
        select(Document).where(Document.job_id == job_id, Document.role == role)
    )
    doc = doc_result.scalar_one_or_none()
    if not doc:
        raise HTTPException(404, f"Document '{role.value}' not found for this job")

    # Find the page
    page_result = await db.execute(
        select(DocumentPage).where(
            DocumentPage.document_id == doc.id,
            DocumentPage.page_number == page_num,
        )
    )
    page = page_result.scalar_one_or_none()
    if not page:
        raise HTTPException(404, f"Page {page_num} not found")

    return SuccessResponse(data=PageContentResponse.model_validate(page))
