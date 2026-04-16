import logging
import uuid

import fitz  # PyMuPDF
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document, DocumentPage, PageType, PageProcessingStatus
from app.models.job import ComparisonJob, JobStatus
from app.pdf.renderer import has_text_layer

logger = logging.getLogger("docdiff.pipeline")


def _page_has_annotations(pdf_path: str, page_number: int) -> bool:
    """Return True if the given page (0-indexed) has any PDF annotations."""
    doc = fitz.open(pdf_path)
    page = doc[page_number]
    annots = list(page.annots())
    doc.close()
    return len(annots) > 0


async def run_stage_2(job_id: uuid.UUID, db: AsyncSession) -> bool:
    """Stage 2: Page Classification.

    For each page of each document, determines whether the page is
    BORN_DIGITAL (has a text layer) or SCANNED (no text layer).
    Also detects PDF annotations and flags scanned pages as potentially
    containing handwriting.
    """
    # Load job
    result = await db.execute(select(ComparisonJob).where(ComparisonJob.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        logger.error(f"Stage 2: job {job_id} not found")
        return False

    # Load documents
    result = await db.execute(select(Document).where(Document.job_id == job_id))
    documents = result.scalars().all()
    if len(documents) != 2:
        job.status = JobStatus.failed
        job.error_message = f"Stage 2: Expected 2 documents, found {len(documents)}"
        await db.commit()
        logger.error(job.error_message)
        return False

    for doc in documents:
        logger.info(
            f"Stage 2: classifying pages for {doc.role} document '{doc.filename}' "
            f"(job {job_id})"
        )

        page_result = await db.execute(
            select(DocumentPage)
            .where(DocumentPage.document_id == doc.id)
            .order_by(DocumentPage.page_number)
        )
        pages = page_result.scalars().all()

        for page in pages:
            # Page number stored as 1-indexed; PyMuPDF uses 0-indexed
            zero_idx = page.page_number - 1

            # Classify as born_digital or scanned based on text layer presence
            text_present = has_text_layer(doc.file_path, zero_idx)
            page_type = PageType.born_digital if text_present else PageType.scanned
            page.page_type = page_type

            # Check for PDF annotations
            page.has_annotations = _page_has_annotations(doc.file_path, zero_idx)

            # Scanned pages may contain handwriting
            page.has_handwriting = page_type == PageType.scanned

            logger.debug(
                f"Stage 2: {doc.role} page {page.page_number} -> "
                f"type={page_type.value}, "
                f"annotations={page.has_annotations}, "
                f"handwriting={page.has_handwriting} "
                f"(job {job_id})"
            )

    await db.commit()
    logger.info(f"Stage 2 completed successfully for job {job_id}")
    return True
