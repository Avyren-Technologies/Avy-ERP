import logging
import os
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document, DocumentPage, PageType
from app.models.job import ComparisonJob, JobStatus
from app.pdf.metadata import extract_metadata, validate_pdf
from app.pdf.renderer import render_all_pages
from app.config import settings

logger = logging.getLogger("docdiff.pipeline")


async def run_stage_1(job_id: uuid.UUID, db: AsyncSession) -> bool:
    """Stage 1: Ingestion & Validation.

    Loads each document, validates the PDF, extracts metadata, creates
    DocumentPage records, and renders page images. Returns True on success,
    False on failure (job.status is set to FAILED with an error_message).
    """
    # Load job
    result = await db.execute(select(ComparisonJob).where(ComparisonJob.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        logger.error(f"Stage 1: job {job_id} not found")
        return False

    # Load documents
    result = await db.execute(select(Document).where(Document.job_id == job_id))
    documents = result.scalars().all()
    if len(documents) != 2:
        job.status = JobStatus.failed
        job.error_message = f"Expected 2 documents, found {len(documents)}"
        await db.commit()
        logger.error(f"Stage 1: {job.error_message} for job {job_id}")
        return False

    for doc in documents:
        logger.info(f"Stage 1: validating {doc.role} document '{doc.filename}' (job {job_id})")

        # Validate PDF
        is_valid, error = validate_pdf(doc.file_path, settings.max_pages, settings.max_file_size_mb)
        if not is_valid:
            job.status = JobStatus.failed
            job.error_message = f"Validation failed for {doc.label}: {error}"
            await db.commit()
            logger.error(f"Stage 1: {job.error_message} (job {job_id})")
            return False

        # Extract metadata
        meta = extract_metadata(doc.file_path)
        doc.page_count = meta.page_count
        doc.pdf_metadata = {
            "title": meta.title,
            "author": meta.author,
            "creator": meta.creator,
            "producer": meta.producer,
            "creation_date": meta.creation_date,
            "pdf_version": meta.pdf_version,
        }
        logger.info(
            f"Stage 1: {doc.role} has {meta.page_count} page(s) "
            f"(job {job_id})"
        )

        # Create DocumentPage records
        for page_num in range(meta.page_count):
            page = DocumentPage(
                document_id=doc.id,
                page_number=page_num + 1,
                page_type=PageType.mixed,
            )
            db.add(page)

        # Render page images
        image_dir = os.path.join(
            settings.storage_path,
            "uploads",
            str(job_id),
            f"{doc.role}_pages",
        )
        logger.info(f"Stage 1: rendering {doc.role} pages to {image_dir} (job {job_id})")
        image_paths = render_all_pages(doc.file_path, image_dir)

        # Flush so the newly added pages get their IDs and are queryable
        await db.flush()

        page_result = await db.execute(
            select(DocumentPage)
            .where(DocumentPage.document_id == doc.id)
            .order_by(DocumentPage.page_number)
        )
        pages = page_result.scalars().all()
        for page, img_path in zip(pages, image_paths):
            page.image_path = img_path
            logger.debug(
                f"Stage 1: page {page.page_number} image -> {img_path} (job {job_id})"
            )

    await db.commit()
    logger.info(f"Stage 1 completed successfully for job {job_id}")
    return True
