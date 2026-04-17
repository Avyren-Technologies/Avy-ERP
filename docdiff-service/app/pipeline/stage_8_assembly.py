import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.difference import DetectedDifference, VerificationStatus
from app.models.job import ComparisonJob, JobStatus

logger = logging.getLogger("docdiff.pipeline")


async def run_stage_8(
    job_id: uuid.UUID,
    scored_differences: list[dict],
    db: AsyncSession,
) -> bool:
    """Stage 8: Persist scored differences and finalise the job.

    For every scored difference dict produced by Stage 7:
      - Creates a DetectedDifference row.
      - Sets verification_status to CONFIRMED if auto_confirmed, else PENDING.

    After persisting all differences:
      - Updates job.total_differences with the total count.
      - Updates job.differences_verified with the count of auto-confirmed ones.
      - Sets job.status to READY_FOR_REVIEW.
      - Commits and returns True.

    Returns False (without raising) if the job cannot be found.
    """
    result = await db.execute(select(ComparisonJob).where(ComparisonJob.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        logger.error(f"Stage 8: job {job_id} not found")
        return False

    # Deduplicate before saving
    scored_differences = _deduplicate_differences(scored_differences)

    # Re-number after dedup
    for i, diff in enumerate(scored_differences, start=1):
        diff["difference_number"] = i

    auto_confirmed_count = 0

    for scored in scored_differences:
        is_auto_confirmed: bool = scored.get("auto_confirmed", False)

        verification_status = (
            VerificationStatus.confirmed if is_auto_confirmed else VerificationStatus.pending
        )

        if is_auto_confirmed:
            auto_confirmed_count += 1

        difference = DetectedDifference(
            job_id=job_id,
            difference_number=scored["difference_number"],
            difference_type=scored["difference_type"],
            significance=scored["significance"],
            confidence=scored["confidence"],
            page_version_a=scored.get("page_version_a"),
            page_version_b=scored.get("page_version_b"),
            bbox_version_a=scored.get("bbox_version_a"),
            bbox_version_b=scored.get("bbox_version_b"),
            value_before=scored.get("value_before"),
            value_after=scored.get("value_after"),
            context=scored.get("context"),
            summary=scored.get("summary", ""),
            block_id_version_a=scored.get("block_id_version_a"),
            block_id_version_b=scored.get("block_id_version_b"),
            verification_status=verification_status,
            auto_confirmed=is_auto_confirmed,
            needs_verification=scored.get("needs_verification", False),
        )
        db.add(difference)

    job.total_differences = len(scored_differences)
    job.differences_verified = auto_confirmed_count
    job.status = JobStatus.ready_for_review

    await db.commit()

    logger.info(
        f"Stage 8: saved {len(scored_differences)} differences for job {job_id} — "
        f"{auto_confirmed_count} auto-confirmed; job status → ready_for_review"
    )
    return True


def _deduplicate_differences(scored: list[dict]) -> list[dict]:
    """Enhanced deduplication and noise reduction.

    Applies these filters in order:
    1. Remove OCR garbage entries
    2. Collapse header/footer changes repeated across pages into single entries
    3. Remove page number pattern changes
    4. Remove duplicate same-value changes on same page
    """
    from collections import defaultdict

    from app.utils.diff_utils import is_ocr_garbage, is_page_number_text

    # Pass 1: Filter OCR garbage
    clean: list[dict] = []
    ocr_removed = 0
    for diff in scored:
        before = (diff.get("value_before") or "").strip()
        after = (diff.get("value_after") or "").strip()
        if is_ocr_garbage(before) or is_ocr_garbage(after):
            ocr_removed += 1
            continue
        clean.append(diff)
    if ocr_removed:
        logger.info(f"Dedup: removed {ocr_removed} OCR garbage entries")

    # Pass 2: Collapse ONLY header/footer zone repeats across pages
    # Body text diffs with same values are kept as separate entries
    # (e.g., "001A→001B" in body paragraph is different from same in footer)
    collapsed: list[dict] = []
    collapsed_count = 0

    # Identify header/footer diffs: blocks with type "header" or "footer",
    # or blocks positioned in header/footer zones (top 8%, bottom 5%)
    header_footer_groups: dict[tuple, list[dict]] = defaultdict(list)
    body_diffs: list[dict] = []

    for diff in clean:
        before = (diff.get("value_before") or "").strip()
        after = (diff.get("value_after") or "").strip()

        # Check if this diff is from a header/footer zone
        is_hf = _is_header_footer_diff(diff)

        if is_hf:
            key = (before, after, str(diff.get("difference_type")))
            header_footer_groups[key].append(diff)
        else:
            body_diffs.append(diff)

    # Collapse header/footer groups that appear on 2+ pages (lower threshold for headers)
    seen_hf_keys: set[tuple] = set()
    for diff in clean:
        before = (diff.get("value_before") or "").strip()
        after = (diff.get("value_after") or "").strip()
        key = (before, after, str(diff.get("difference_type")))

        if not _is_header_footer_diff(diff):
            collapsed.append(diff)
            continue

        if key in seen_hf_keys:
            continue
        seen_hf_keys.add(key)

        group = header_footer_groups[key]
        if len(group) >= 2:  # 2+ pages for header/footer (not 3)
            pages = sorted(set(
                d.get("page_version_a") or d.get("page_version_b") or 0 for d in group
            ))
            representative = group[0].copy()
            representative["summary"] = (
                f"{representative.get('summary', '')} "
                f"(repeated on {len(group)} pages)"
            )
            from app.models.difference import Significance
            representative["significance"] = Significance.cosmetic
            representative["auto_confirmed"] = True
            representative["confidence"] = 0.98
            collapsed.append(representative)
            collapsed_count += len(group) - 1
        else:
            collapsed.append(diff)

    if collapsed_count:
        logger.info(f"Dedup: collapsed {collapsed_count} repeated header/footer entries")

    # Pass 3: Filter page number changes
    filtered: list[dict] = []
    page_num_removed = 0
    for diff in collapsed:
        before = (diff.get("value_before") or "").strip()
        after = (diff.get("value_after") or "").strip()
        if is_page_number_text(before) or is_page_number_text(after):
            page_num_removed += 1
            continue
        filtered.append(diff)
    if page_num_removed:
        logger.info(f"Dedup: removed {page_num_removed} page number entries")

    # Pass 4: Same-value dedup on same page
    # EXCLUDE table_cell_change — each cell is an independent change
    seen: set[tuple] = set()
    final: list[dict] = []
    for diff in filtered:
        before = (diff.get("value_before") or "").strip()
        after = (diff.get("value_after") or "").strip()

        # Never dedup single-char diffs or table cell changes
        dt = diff.get("difference_type")
        dt_val = dt.value if hasattr(dt, "value") else str(dt)
        if (len(before) <= 1 and len(after) <= 1) or dt_val == "table_cell_change":
            final.append(diff)
            continue

        page_a = diff.get("page_version_a")
        page_b = diff.get("page_version_b")
        key = (before, after, page_a, page_b, str(diff.get("difference_type")))
        if key in seen:
            continue
        seen.add(key)
        final.append(diff)

    # Pass 5: Merge delete+add pairs into modifications
    # When a text_deletion and text_addition appear on the same page
    # with similar context, they likely represent a modified block
    final = _merge_delete_add_pairs(final)

    total_removed = len(scored) - len(final)
    if total_removed:
        logger.info(
            f"Dedup total: {len(scored)} -> {len(final)} "
            f"({total_removed} entries removed: {ocr_removed} OCR, "
            f"{collapsed_count} header/footer, {page_num_removed} page numbers, "
            f"{len(scored) - len(final) - ocr_removed - collapsed_count - page_num_removed} same-value)"
        )
    return final


def _is_header_footer_diff(diff: dict) -> bool:
    """Check if a diff originates from a header/footer zone block."""
    # Check bbox position (header = top 8%, footer = bottom 5%)
    for bbox_key in ("bbox_version_a", "bbox_version_b"):
        bbox = diff.get(bbox_key)
        if bbox and isinstance(bbox, dict):
            y = bbox.get("y", 0.5)
            y_end = y + bbox.get("height", 0)
            if y < 0.08 or y_end > 0.95:
                return True

    # Check context for header/footer indicators
    context = (diff.get("context") or "").lower()
    summary = (diff.get("summary") or "").lower()
    if any(kw in context or kw in summary for kw in ("header", "footer", "page number")):
        return True

    return False


def _merge_delete_add_pairs(diffs: list[dict]) -> list[dict]:
    """Merge text_deletion + text_addition pairs on the same page into text_modification.

    When the alignment stage fails to match blocks (e.g., handwritten notes),
    a modified block appears as separate deletion + addition entries.
    This merges them when they're on the same page.
    """
    from app.models.difference import DifferenceType
    from app.utils.diff_utils import compute_similarity

    deletions: list[tuple[int, dict]] = []
    additions: list[tuple[int, dict]] = []

    for i, diff in enumerate(diffs):
        dt = diff.get("difference_type")
        dt_val = dt.value if hasattr(dt, "value") else str(dt)
        if dt_val == "text_deletion":
            deletions.append((i, diff))
        elif dt_val == "text_addition":
            additions.append((i, diff))

    merged_indices: set[int] = set()
    merged_diffs: list[dict] = []

    for del_idx, del_diff in deletions:
        if del_idx in merged_indices:
            continue

        del_page = del_diff.get("page_version_a") or del_diff.get("page_version_b")
        del_text = (del_diff.get("value_before") or "").strip()

        if not del_text or not del_page:
            continue

        # Find a matching addition on the same page
        best_add_idx = -1
        best_add_diff = None
        best_similarity = 0.0

        for add_idx, add_diff in additions:
            if add_idx in merged_indices:
                continue

            add_page = add_diff.get("page_version_b") or add_diff.get("page_version_a")
            if add_page != del_page:
                continue

            add_text = (add_diff.get("value_after") or "").strip()
            if not add_text:
                continue

            # Check if they're related (some text similarity or same context)
            sim = compute_similarity(del_text[:200], add_text[:200])

            if sim > best_similarity and sim >= 0.15:  # Very low threshold — just needs SOME relation
                best_similarity = sim
                best_add_idx = add_idx
                best_add_diff = add_diff

        if best_add_diff is not None:
            # Merge into a modification
            merged_diff = del_diff.copy()
            merged_diff["difference_type"] = DifferenceType.text_modification
            merged_diff["value_before"] = del_text
            merged_diff["value_after"] = (best_add_diff.get("value_after") or "").strip()
            merged_diff["page_version_b"] = best_add_diff.get("page_version_b")
            merged_diff["bbox_version_b"] = best_add_diff.get("bbox_version_b")
            merged_diff["summary"] = (
                f"Text modified: \"{del_text[:50]}\" → \"{merged_diff['value_after'][:50]}\""
            )
            merged_diffs.append(merged_diff)
            merged_indices.add(del_idx)
            merged_indices.add(best_add_idx)

    # Build final list: unmerged originals + merged
    result: list[dict] = []
    for i, diff in enumerate(diffs):
        if i not in merged_indices:
            result.append(diff)
    result.extend(merged_diffs)

    merge_count = len(merged_diffs)
    if merge_count:
        logger.info(f"Dedup: merged {merge_count} delete+add pairs into modifications")

    return result
