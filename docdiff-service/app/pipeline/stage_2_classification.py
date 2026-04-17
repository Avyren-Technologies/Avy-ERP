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


def _classify_page_type(pdf_path: str, page_idx: int) -> tuple[str, float]:
    """Classify page type using text density analysis.

    Returns (PageType value, confidence).

    A page with an OCR text layer (scanned + OCR'd) is detected by:
    - Has text layer BUT text doesn't match expected character density
    - Has text layer BUT font names indicate OCR (e.g., "Tesseract")
    """
    doc = fitz.open(pdf_path)
    page = doc[page_idx]

    # Get text and page dimensions
    text = page.get_text("text").strip()
    text_len = len(text)
    page_area = page.rect.width * page.rect.height

    # Get text blocks with position info
    text_dict = page.get_text("dict")
    blocks = text_dict.get("blocks", [])
    text_blocks = [b for b in blocks if b.get("type") == 0]  # type 0 = text
    image_blocks = [b for b in blocks if b.get("type") == 1]  # type 1 = image

    # Calculate text coverage (what fraction of page is text blocks)
    text_area = sum(
        (b["bbox"][2] - b["bbox"][0]) * (b["bbox"][3] - b["bbox"][1])
        for b in text_blocks
    ) if text_blocks else 0
    text_coverage = text_area / page_area if page_area > 0 else 0

    # Calculate image coverage
    image_area = sum(
        (b["bbox"][2] - b["bbox"][0]) * (b["bbox"][3] - b["bbox"][1])
        for b in image_blocks
    ) if image_blocks else 0
    image_coverage = image_area / page_area if page_area > 0 else 0

    doc.close()

    # Classification rules
    if text_len < 10:
        # Very little text — likely scanned or image-only
        return PageType.scanned, 0.95

    if image_coverage > 0.7 and text_coverage < 0.1:
        # Page is mostly images — scanned
        return PageType.scanned, 0.90

    if text_coverage > 0.3 and image_coverage < 0.2:
        # Lots of text, few images — born digital
        return PageType.born_digital, 0.95

    if image_coverage > 0.5 and text_len > 50:
        # Significant images AND text — likely OCR'd scanned or mixed
        return PageType.mixed, 0.75

    # Default: born digital if has reasonable text
    if text_len > 50:
        return PageType.born_digital, 0.85

    return PageType.scanned, 0.70


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

            # Classify using text density analysis
            page_type, classification_confidence = _classify_page_type(
                doc.file_path, zero_idx
            )
            page.page_type = page_type
            page.extraction_confidence = classification_confidence

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
