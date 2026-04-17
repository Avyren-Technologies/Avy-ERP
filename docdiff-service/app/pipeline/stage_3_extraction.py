"""
stage_3_extraction.py — Content Extraction

Strategy (fast path first):
  1. Born-digital pages  → PyMuPDF fast_parser  (< 50 ms/page, no ML models)
  2. Scanned/failed pages → VLM via ai_provider  (Gemini vision call)

Both documents are processed CONCURRENTLY via asyncio.gather(), halving the
elapsed time for the extraction stage.

Compared to the previous Docling-based approach this typically reduces Stage 3
from 10–15 minutes to under 30 seconds for born-digital documents, and from
~15 minutes to ~2–3 minutes for fully scanned documents.
"""

import asyncio
import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.base import AIProvider
from app.ai.response_parser import safe_parse_or_flag
from app.models.document import Document, DocumentPage, PageType, PageProcessingStatus
from app.models.job import ComparisonJob, JobStatus
from app.pdf.fast_parser import extract_all_pages
from app.prompts.extract_page import get_extract_prompt

logger = logging.getLogger("docdiff.pipeline")

# Seconds to sleep between VLM calls to respect provider rate limits.
# Gemini paid-tier: ~60 RPM — 1 second is conservative but safe.
# Bump to 4 if you see 429 errors on free-tier keys.
_VLM_INTER_CALL_SLEEP = 1.0


async def run_stage_3(
    job_id: uuid.UUID,
    db: AsyncSession,
    ai_provider: AIProvider,
) -> bool:
    """Stage 3: Content Extraction.

    For each document, PyMuPDF handles born-digital pages instantly (no API
    cost, no ML models).  Scanned pages fall back to the VLM.

    Both documents are processed in parallel.  Individual page failures set
    the page to FAILED but do NOT abort the whole job.
    Returns True when all documents have been processed, False only if the
    job itself cannot be loaded.
    """
    result = await db.execute(select(ComparisonJob).where(ComparisonJob.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        logger.error(f"Stage 3: job {job_id} not found")
        return False

    result = await db.execute(select(Document).where(Document.job_id == job_id))
    documents = result.scalars().all()
    if len(documents) != 2:
        job.status = JobStatus.failed
        job.error_message = f"Stage 3: Expected 2 documents, found {len(documents)}"
        await db.commit()
        logger.error(job.error_message)
        return False

    extract_prompt = get_extract_prompt(ai_provider.provider_name)

    # ----------------------------------------------------------------
    # Process both documents concurrently
    # ----------------------------------------------------------------
    tasks = [
        _process_document(doc, job_id, db, ai_provider, extract_prompt)
        for doc in documents
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    for doc, outcome in zip(documents, results):
        if isinstance(outcome, Exception):
            logger.error(
                f"Stage 3: document {doc.role} processing raised an exception: "
                f"{outcome} (job {job_id})"
            )

    await db.commit()
    logger.info(f"Stage 3 completed for job {job_id}")
    return True


# ---------------------------------------------------------------------------
# Per-document processing (runs concurrently for both docs)
# ---------------------------------------------------------------------------

async def _process_document(
    doc: Document,
    job_id: uuid.UUID,
    db: AsyncSession,
    ai_provider: AIProvider,
    extract_prompt: str,
) -> None:
    logger.info(
        f"Stage 3: extracting '{doc.filename}' ({doc.role}) "
        f"via fast_parser + VLM fallback (job {job_id})"
    )

    # ---- Fast path: extract all born-digital pages with PyMuPDF --------
    # Run synchronous PyMuPDF in a thread pool so we don't block the loop.
    fast_pages: list[dict] = []
    try:
        loop = asyncio.get_event_loop()
        fast_pages = await loop.run_in_executor(None, extract_all_pages, doc.file_path)
        logger.info(
            f"Stage 3: fast_parser extracted {len(fast_pages)} page(s) "
            f"for {doc.role} (job {job_id})"
        )
    except Exception as exc:
        logger.warning(
            f"Stage 3: fast_parser failed for {doc.role} ({exc}); "
            f"all pages will fall back to VLM (job {job_id})"
        )

    # ---- Load page records from DB -------------------------------------
    page_result = await db.execute(
        select(DocumentPage)
        .where(DocumentPage.document_id == doc.id)
        .order_by(DocumentPage.page_number)
    )
    pages = page_result.scalars().all()

    vlm_call_count = 0

    for page in pages:
        page_idx = page.page_number - 1  # 0-based

        # ---- Born-digital: use PyMuPDF result if available ---------------
        if (
            page.page_type == PageType.born_digital
            and fast_pages
            and page_idx < len(fast_pages)
        ):
            fast_content = fast_pages[page_idx]
            if fast_content.get("blocks"):
                page.content = fast_content
                page.extraction_method = "pymupdf"
                page.extraction_confidence = 0.95
                page.processing_status = PageProcessingStatus.completed
                logger.debug(
                    f"Stage 3: {doc.role} page {page.page_number} "
                    f"→ pymupdf (job {job_id})"
                )
                continue
            # Empty page (no blocks) — fall through to VLM if image exists

        # ---- Scanned / no fast-parser output: use VLM -------------------
        if not page.image_path:
            page.processing_status = PageProcessingStatus.failed
            page.error_message = "No rendered image available for VLM extraction"
            logger.warning(
                f"Stage 3: {doc.role} page {page.page_number} — "
                f"skipping VLM (no image_path) (job {job_id})"
            )
            continue

        # Rate-limit guard between consecutive VLM calls
        if vlm_call_count > 0:
            await asyncio.sleep(_VLM_INTER_CALL_SLEEP)

        try:
            with open(page.image_path, "rb") as f:
                image_bytes = f.read()

            ai_response = await ai_provider.extract_page_content(image_bytes, extract_prompt)
            vlm_call_count += 1

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
                f"Stage 3: {doc.role} page {page.page_number} "
                f"→ vlm (job {job_id})"
            )

        except Exception as exc:
            page.processing_status = PageProcessingStatus.failed
            page.error_message = f"VLM extraction error: {exc}"
            logger.error(
                f"Stage 3: {doc.role} page {page.page_number} — "
                f"VLM error: {exc} (job {job_id})"
            )

    logger.info(
        f"Stage 3: {doc.role} done — "
        f"{sum(1 for p in pages if p.processing_status == PageProcessingStatus.completed)} "
        f"pages extracted, {vlm_call_count} VLM call(s) (job {job_id})"
    )
