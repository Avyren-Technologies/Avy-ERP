import logging
import re
import unicodedata
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document, DocumentPage, PageProcessingStatus
from app.models.job import ComparisonJob, JobStatus

logger = logging.getLogger("docdiff.pipeline")


def normalize_text(text: str) -> str:
    """Apply Unicode NFKC normalization and collapse runs of whitespace."""
    normalized = unicodedata.normalize("NFKC", text)
    collapsed = re.sub(r"\s+", " ", normalized).strip()
    return collapsed


async def run_stage_4(job_id: uuid.UUID, db: AsyncSession) -> bool:
    """Stage 4: Normalization.

    For every page that completed extraction:
    - Applies Unicode NFKC normalization + whitespace collapsing to all block
      text values.
    - Re-assigns stable unique block IDs in the format:
        ``{doc.role}_{page_number:03d}_blk_{counter:04d}``
      e.g. ``version_a_001_blk_0001`` for the first block on page 1 of Version A.
    - Rewrites content.reading_order to use the new IDs.
    """
    # Load job
    result = await db.execute(select(ComparisonJob).where(ComparisonJob.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        logger.error(f"Stage 4: job {job_id} not found")
        return False

    # Load documents
    result = await db.execute(select(Document).where(Document.job_id == job_id))
    documents = result.scalars().all()
    if len(documents) != 2:
        job.status = JobStatus.failed
        job.error_message = f"Stage 4: Expected 2 documents, found {len(documents)}"
        await db.commit()
        logger.error(job.error_message)
        return False

    for doc in documents:
        logger.info(
            f"Stage 4: normalizing {doc.role} document '{doc.filename}' "
            f"(job {job_id})"
        )

        page_result = await db.execute(
            select(DocumentPage)
            .where(DocumentPage.document_id == doc.id)
            .order_by(DocumentPage.page_number)
        )
        pages = page_result.scalars().all()

        for page in pages:
            if page.processing_status != PageProcessingStatus.completed:
                logger.debug(
                    f"Stage 4: skipping {doc.role} page {page.page_number} "
                    f"(status={page.processing_status.value}) (job {job_id})"
                )
                continue

            content = page.content
            if not content or not isinstance(content, dict):
                logger.debug(
                    f"Stage 4: {doc.role} page {page.page_number} has no content dict — skipping"
                )
                continue

            blocks: list[dict] = content.get("blocks", [])
            old_to_new: dict[str, str] = {}

            for counter, block in enumerate(blocks, start=1):
                # Build new stable ID
                new_id = (
                    f"{doc.role}_{page.page_number:03d}_blk_{counter:04d}"
                )
                old_id = block.get("id", "")
                old_to_new[old_id] = new_id
                block["id"] = new_id

                # Normalize text field
                if "text" in block and isinstance(block["text"], str):
                    block["text"] = normalize_text(block["text"])

                # Normalize table cell text
                table = block.get("table")
                if isinstance(table, dict):
                    for cell in table.get("cells", []):
                        if isinstance(cell.get("text"), str):
                            cell["text"] = normalize_text(cell["text"])
                    # Normalize header strings
                    if isinstance(table.get("headers"), list):
                        table["headers"] = [
                            normalize_text(h) if isinstance(h, str) else h
                            for h in table["headers"]
                        ]

                # Normalize annotation transcription
                annotation = block.get("annotation")
                if isinstance(annotation, dict) and isinstance(
                    annotation.get("transcription"), str
                ):
                    annotation["transcription"] = normalize_text(
                        annotation["transcription"]
                    )

            # Rewrite reading_order with new block IDs
            old_reading_order: list[str] = content.get("reading_order", [])
            content["reading_order"] = [
                old_to_new.get(old_id, old_id) for old_id in old_reading_order
            ]

            content["blocks"] = blocks
            page.content = content

            logger.debug(
                f"Stage 4: {doc.role} page {page.page_number} — "
                f"{len(blocks)} block(s) normalized (job {job_id})"
            )

    await db.commit()
    logger.info(f"Stage 4 completed successfully for job {job_id}")
    return True
