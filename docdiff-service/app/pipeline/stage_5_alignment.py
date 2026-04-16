import logging
import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document, DocumentPage, DocumentRole, PageProcessingStatus
from app.utils.diff_utils import compute_similarity
from app.utils.table_utils import compute_table_similarity

logger = logging.getLogger("docdiff.pipeline")

TITLE_MATCH_THRESHOLD = 0.7
TABLE_MATCH_THRESHOLD = 0.5
TEXT_MATCH_THRESHOLD = 0.4


@dataclass
class AlignedPair:
    version_a_block: dict | None
    version_b_block: dict | None
    page_version_a: int | None
    page_version_b: int | None
    alignment_score: float


async def run_stage_5(job_id: uuid.UUID, db: AsyncSession) -> list[AlignedPair]:
    """Stage 5: Section alignment between Version A and Version B documents.

    Uses a 3-pass matching strategy:
      Pass 1 — Match by section title similarity (>= 0.7)
      Pass 2 — Match tables by structural similarity (>= 0.5)
      Pass 3 — Match remaining text blocks by content similarity (>= 0.4)

    Unmatched Version A blocks become deletions; unmatched Version B blocks
    become additions. Returns the full list of AlignedPair objects.
    """
    # Load both documents
    result = await db.execute(select(Document).where(Document.job_id == job_id))
    documents = result.scalars().all()

    doc_a = next((d for d in documents if d.role == DocumentRole.version_a), None)
    doc_b = next((d for d in documents if d.role == DocumentRole.version_b), None)

    if doc_a is None or doc_b is None:
        logger.error(
            f"Stage 5: could not find both Version A and Version B documents for job {job_id}"
        )
        return []

    blocks_a = await _get_all_blocks(doc_a.id, db)
    blocks_b = await _get_all_blocks(doc_b.id, db)

    logger.info(
        f"Stage 5: aligning {len(blocks_a)} Version A blocks with "
        f"{len(blocks_b)} Version B blocks (job {job_id})"
    )

    aligned: list[AlignedPair] = []
    used_a: set[int] = set()
    used_b: set[int] = set()

    # ------------------------------------------------------------------
    # Pass 1: Match by section title similarity
    # ------------------------------------------------------------------
    title_blocks_a = [
        (i, b) for i, b in enumerate(blocks_a) if b.get("block_type") in ("heading", "title")
    ]
    title_blocks_b = [
        (i, b) for i, b in enumerate(blocks_b) if b.get("block_type") in ("heading", "title")
    ]

    for idx_a, blk_a in title_blocks_a:
        if idx_a in used_a:
            continue
        title_a = blk_a.get("text", "") or ""
        best_score = 0.0
        best_idx_b = -1
        for idx_b, blk_b in title_blocks_b:
            if idx_b in used_b:
                continue
            title_b = blk_b.get("text", "") or ""
            score = compute_similarity(title_a, title_b)
            if score >= TITLE_MATCH_THRESHOLD and score > best_score:
                best_score = score
                best_idx_b = idx_b
        if best_idx_b >= 0:
            blk_b = blocks_b[best_idx_b]
            aligned.append(
                AlignedPair(
                    version_a_block=blk_a,
                    version_b_block=blk_b,
                    page_version_a=blk_a.get("_page_number"),
                    page_version_b=blk_b.get("_page_number"),
                    alignment_score=best_score,
                )
            )
            used_a.add(idx_a)
            used_b.add(best_idx_b)

    # ------------------------------------------------------------------
    # Pass 2: Match tables by structural similarity
    # ------------------------------------------------------------------
    table_blocks_a = [
        (i, b) for i, b in enumerate(blocks_a) if b.get("block_type") == "table" and i not in used_a
    ]
    table_blocks_b = [
        (i, b) for i, b in enumerate(blocks_b) if b.get("block_type") == "table" and i not in used_b
    ]

    for idx_a, blk_a in table_blocks_a:
        best_score = 0.0
        best_idx_b = -1
        for idx_b, blk_b in table_blocks_b:
            if idx_b in used_b:
                continue
            score = compute_table_similarity(blk_a, blk_b)
            if score >= TABLE_MATCH_THRESHOLD and score > best_score:
                best_score = score
                best_idx_b = idx_b
        if best_idx_b >= 0:
            blk_b = blocks_b[best_idx_b]
            aligned.append(
                AlignedPair(
                    version_a_block=blk_a,
                    version_b_block=blk_b,
                    page_version_a=blk_a.get("_page_number"),
                    page_version_b=blk_b.get("_page_number"),
                    alignment_score=best_score,
                )
            )
            used_a.add(idx_a)
            used_b.add(best_idx_b)

    # ------------------------------------------------------------------
    # Pass 3: Match remaining text blocks by content similarity
    # ------------------------------------------------------------------
    remaining_a = [(i, b) for i, b in enumerate(blocks_a) if i not in used_a]
    remaining_b = [(i, b) for i, b in enumerate(blocks_b) if i not in used_b]

    for idx_a, blk_a in remaining_a:
        text_a = blk_a.get("text", "") or ""
        best_score = 0.0
        best_idx_b = -1
        for idx_b, blk_b in remaining_b:
            if idx_b in used_b:
                continue
            text_b = blk_b.get("text", "") or ""
            score = compute_similarity(text_a, text_b)
            if score >= TEXT_MATCH_THRESHOLD and score > best_score:
                best_score = score
                best_idx_b = idx_b
        if best_idx_b >= 0:
            blk_b = blocks_b[best_idx_b]
            aligned.append(
                AlignedPair(
                    version_a_block=blk_a,
                    version_b_block=blk_b,
                    page_version_a=blk_a.get("_page_number"),
                    page_version_b=blk_b.get("_page_number"),
                    alignment_score=best_score,
                )
            )
            used_a.add(idx_a)
            used_b.add(best_idx_b)

    # ------------------------------------------------------------------
    # Unmatched Version A blocks → deletions
    # ------------------------------------------------------------------
    for idx_a, blk_a in enumerate(blocks_a):
        if idx_a not in used_a:
            aligned.append(
                AlignedPair(
                    version_a_block=blk_a,
                    version_b_block=None,
                    page_version_a=blk_a.get("_page_number"),
                    page_version_b=None,
                    alignment_score=0.0,
                )
            )

    # ------------------------------------------------------------------
    # Unmatched Version B blocks → additions
    # ------------------------------------------------------------------
    for idx_b, blk_b in enumerate(blocks_b):
        if idx_b not in used_b:
            aligned.append(
                AlignedPair(
                    version_a_block=None,
                    version_b_block=blk_b,
                    page_version_a=None,
                    page_version_b=blk_b.get("_page_number"),
                    alignment_score=0.0,
                )
            )

    matched = sum(1 for p in aligned if p.version_a_block and p.version_b_block)
    deletions = sum(1 for p in aligned if p.version_a_block and not p.version_b_block)
    additions = sum(1 for p in aligned if not p.version_a_block and p.version_b_block)
    logger.info(
        f"Stage 5: {matched} matched pairs, {deletions} deletions, "
        f"{additions} additions (job {job_id})"
    )
    return aligned


async def _get_all_blocks(document_id: uuid.UUID, db: AsyncSession) -> list[dict]:
    """Load all content blocks from completed pages of a document, in page order."""
    result = await db.execute(
        select(DocumentPage)
        .where(
            DocumentPage.document_id == document_id,
            DocumentPage.processing_status == PageProcessingStatus.completed,
        )
        .order_by(DocumentPage.page_number)
    )
    pages = result.scalars().all()
    all_blocks: list[dict] = []
    for page in pages:
        if not page.content or "blocks" not in page.content:
            continue
        for block in page.content["blocks"]:
            block["_page_number"] = page.page_number
            all_blocks.append(block)
    return all_blocks
