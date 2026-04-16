import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document, DocumentPage, PageType, PageProcessingStatus
from app.models.job import ComparisonJob, JobStatus
from app.pdf.parser import parse_document_with_docling
from app.ai.base import AIProvider
from app.ai.response_parser import safe_parse_or_flag
from app.prompts.extract_page import get_extract_prompt

logger = logging.getLogger("docdiff.pipeline")


async def run_stage_3(
    job_id: uuid.UUID,
    db: AsyncSession,
    ai_provider: AIProvider,
) -> bool:
    """Stage 3: Content Extraction.

    For each document, tries Docling parsing first. Born-digital pages with
    Docling output are stored directly (confidence 0.95, method "docling").
    Scanned pages and any page where Docling failed fall back to the VLM via
    ai_provider.extract_page_content().

    Individual page failures set the page's processing_status to FAILED with
    an error_message but do NOT abort the whole job — other pages continue.
    Returns True when all documents have been processed (even with partial
    page failures), False only if the job itself cannot be loaded.
    """
    # Load job
    result = await db.execute(select(ComparisonJob).where(ComparisonJob.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        logger.error(f"Stage 3: job {job_id} not found")
        return False

    # Load documents
    result = await db.execute(select(Document).where(Document.job_id == job_id))
    documents = result.scalars().all()
    if len(documents) != 2:
        job.status = JobStatus.failed
        job.error_message = f"Stage 3: Expected 2 documents, found {len(documents)}"
        await db.commit()
        logger.error(job.error_message)
        return False

    extract_prompt = get_extract_prompt(ai_provider.provider_name)

    for doc in documents:
        logger.info(
            f"Stage 3: extracting content for {doc.role} document '{doc.filename}' "
            f"(job {job_id})"
        )

        # Attempt Docling on the whole document once
        docling_pages: list[dict] = []
        try:
            docling_pages = parse_document_with_docling(doc.file_path)
            logger.info(
                f"Stage 3: Docling succeeded for {doc.role} — "
                f"{len(docling_pages)} page(s) parsed (job {job_id})"
            )
        except Exception as exc:
            logger.warning(
                f"Stage 3: Docling failed for {doc.role} ({exc}); "
                f"will use VLM for all pages (job {job_id})"
            )

        page_result = await db.execute(
            select(DocumentPage)
            .where(DocumentPage.document_id == doc.id)
            .order_by(DocumentPage.page_number)
        )
        pages = page_result.scalars().all()

        for page in pages:
            page_idx = page.page_number - 1  # 0-based index

            # --- Try Docling result for born-digital pages ---
            if (
                page.page_type == PageType.born_digital
                and docling_pages
                and page_idx < len(docling_pages)
            ):
                docling_content = docling_pages[page_idx]
                if docling_content.get("blocks"):
                    page.content = docling_content
                    page.extraction_method = "docling"
                    page.extraction_confidence = 0.95
                    page.processing_status = PageProcessingStatus.completed
                    logger.debug(
                        f"Stage 3: {doc.role} page {page.page_number} -> "
                        f"docling (confidence=0.95) (job {job_id})"
                    )
                    continue

            # --- Fall back to VLM for scanned / no-Docling-output pages ---
            if not page.image_path:
                page.processing_status = PageProcessingStatus.failed
                page.error_message = "No rendered image available for VLM extraction"
                logger.warning(
                    f"Stage 3: {doc.role} page {page.page_number} — "
                    f"skipping VLM (no image_path) (job {job_id})"
                )
                continue

            try:
                with open(page.image_path, "rb") as f:
                    image_bytes = f.read()

                ai_response = await ai_provider.extract_page_content(
                    image_bytes, extract_prompt
                )
                parsed_content, flagged = safe_parse_or_flag(ai_response.content)

                if flagged or parsed_content is None:
                    page.processing_status = PageProcessingStatus.failed
                    page.error_message = "VLM returned unparseable response"
                    logger.warning(
                        f"Stage 3: {doc.role} page {page.page_number} — "
                        f"VLM parse failed (job {job_id})"
                    )
                    continue

                page.content = parsed_content
                page.extraction_method = "vlm"
                page.extraction_confidence = 0.80
                page.processing_status = PageProcessingStatus.completed
                logger.debug(
                    f"Stage 3: {doc.role} page {page.page_number} -> "
                    f"vlm (confidence=0.80) (job {job_id})"
                )

            except Exception as exc:
                page.processing_status = PageProcessingStatus.failed
                page.error_message = f"VLM extraction error: {exc}"
                logger.error(
                    f"Stage 3: {doc.role} page {page.page_number} — "
                    f"VLM error: {exc} (job {job_id})"
                )

    await db.commit()
    logger.info(f"Stage 3 completed for job {job_id}")
    return True
