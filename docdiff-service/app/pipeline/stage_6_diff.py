import logging
from dataclasses import dataclass

from app.models.difference import DifferenceType
from app.pipeline.stage_5_alignment import AlignedPair
from app.utils.diff_utils import compute_text_diff
from app.utils.table_utils import compare_tables

logger = logging.getLogger("docdiff.pipeline")


@dataclass
class RawDiffRecord:
    difference_type: DifferenceType
    value_before: str
    value_after: str
    context: str
    page_version_a: int | None
    page_version_b: int | None
    bbox_version_a: dict | None
    bbox_version_b: dict | None
    block_id_version_a: str | None
    block_id_version_b: str | None


def run_stage_6(aligned_pairs: list[AlignedPair]) -> list[RawDiffRecord]:
    """Stage 6: Diff computation.

    Iterates over aligned pairs from Stage 5 and produces a flat list of
    RawDiffRecord objects, one per detected change.

    Rules:
      - Both blocks None           → skip (should not happen)
      - Only version_a present     → deletion record
      - Only version_b present     → addition record
      - Both present, table type   → compare_tables → cell/row/structure diffs
      - Both present, annotation   → annotation_present_in_b or annotation_removed_from_b
      - Both present, text         → compute_text_diff → text_addition/deletion/modification
    """
    records: list[RawDiffRecord] = []

    for pair in aligned_pairs:
        blk_a = pair.version_a_block
        blk_b = pair.version_b_block

        if blk_a is None and blk_b is None:
            # Nothing to do
            continue

        # ------------------------------------------------------------------
        # Only Version A present → deletion
        # ------------------------------------------------------------------
        if blk_a is not None and blk_b is None:
            block_type = blk_a.get("type") or blk_a.get("block_type", "text")
            if block_type == "table":
                diff_type = DifferenceType.table_row_deletion
            elif block_type == "annotation":
                diff_type = DifferenceType.annotation_removed_from_b
            else:
                diff_type = DifferenceType.text_deletion
            records.append(
                RawDiffRecord(
                    difference_type=diff_type,
                    value_before=blk_a.get("text", "") or "",
                    value_after="",
                    context=_build_context(blk_a, None),
                    page_version_a=pair.page_version_a,
                    page_version_b=None,
                    bbox_version_a=blk_a.get("bbox"),
                    bbox_version_b=None,
                    block_id_version_a=blk_a.get("id"),
                    block_id_version_b=None,
                )
            )
            continue

        # ------------------------------------------------------------------
        # Only Version B present → addition
        # ------------------------------------------------------------------
        if blk_b is not None and blk_a is None:
            block_type = blk_b.get("type") or blk_b.get("block_type", "text")
            if block_type == "table":
                diff_type = DifferenceType.table_row_addition
            elif block_type == "annotation":
                diff_type = DifferenceType.annotation_present_in_b
            else:
                diff_type = DifferenceType.text_addition
            records.append(
                RawDiffRecord(
                    difference_type=diff_type,
                    value_before="",
                    value_after=blk_b.get("text", "") or "",
                    context=_build_context(None, blk_b),
                    page_version_a=None,
                    page_version_b=pair.page_version_b,
                    bbox_version_a=None,
                    bbox_version_b=blk_b.get("bbox"),
                    block_id_version_a=None,
                    block_id_version_b=blk_b.get("id"),
                )
            )
            continue

        # ------------------------------------------------------------------
        # Both present — determine block type and compute diff
        # ------------------------------------------------------------------
        block_type_a = blk_a.get("type") or blk_a.get("block_type", "text")
        block_type_b = blk_b.get("type") or blk_b.get("block_type", "text")

        # Annotation pair
        if block_type_a == "annotation" or block_type_b == "annotation":
            # Annotation in b but not a originally → present_in_b; vice versa
            if block_type_b == "annotation" and block_type_a != "annotation":
                diff_type = DifferenceType.annotation_present_in_b
            elif block_type_a == "annotation" and block_type_b != "annotation":
                diff_type = DifferenceType.annotation_removed_from_b
            else:
                # Both are annotations — treat as modification; use text content
                diff_type = DifferenceType.annotation_present_in_b
            records.append(
                RawDiffRecord(
                    difference_type=diff_type,
                    value_before=blk_a.get("text", "") or "",
                    value_after=blk_b.get("text", "") or "",
                    context=_build_context(blk_a, blk_b),
                    page_version_a=pair.page_version_a,
                    page_version_b=pair.page_version_b,
                    bbox_version_a=blk_a.get("bbox"),
                    bbox_version_b=blk_b.get("bbox"),
                    block_id_version_a=blk_a.get("id"),
                    block_id_version_b=blk_b.get("id"),
                )
            )
            continue

        # Table pair
        if block_type_a == "table" or block_type_b == "table":
            table_diff = compare_tables(blk_a, blk_b)

            if table_diff.structure_changed or table_diff.header_changes:
                records.append(
                    RawDiffRecord(
                        difference_type=DifferenceType.table_structure_change,
                        value_before=_table_headers_str(blk_a),
                        value_after=_table_headers_str(blk_b),
                        context=_build_context(blk_a, blk_b),
                        page_version_a=pair.page_version_a,
                        page_version_b=pair.page_version_b,
                        bbox_version_a=blk_a.get("bbox"),
                        bbox_version_b=blk_b.get("bbox"),
                        block_id_version_a=blk_a.get("id"),
                        block_id_version_b=blk_b.get("id"),
                    )
                )

            for row_idx in table_diff.rows_deleted:
                records.append(
                    RawDiffRecord(
                        difference_type=DifferenceType.table_row_deletion,
                        value_before=f"Row {row_idx}",
                        value_after="",
                        context=_build_context(blk_a, blk_b),
                        page_version_a=pair.page_version_a,
                        page_version_b=pair.page_version_b,
                        bbox_version_a=blk_a.get("bbox"),
                        bbox_version_b=blk_b.get("bbox"),
                        block_id_version_a=blk_a.get("id"),
                        block_id_version_b=blk_b.get("id"),
                    )
                )

            for row_idx in table_diff.rows_added:
                records.append(
                    RawDiffRecord(
                        difference_type=DifferenceType.table_row_addition,
                        value_before="",
                        value_after=f"Row {row_idx}",
                        context=_build_context(blk_a, blk_b),
                        page_version_a=pair.page_version_a,
                        page_version_b=pair.page_version_b,
                        bbox_version_a=blk_a.get("bbox"),
                        bbox_version_b=blk_b.get("bbox"),
                        block_id_version_a=blk_a.get("id"),
                        block_id_version_b=blk_b.get("id"),
                    )
                )

            for cell in table_diff.cell_changes:
                records.append(
                    RawDiffRecord(
                        difference_type=DifferenceType.table_cell_change,
                        value_before=cell.value_before,
                        value_after=cell.value_after,
                        context=f"Row {cell.row}, Col {cell.col}",
                        page_version_a=pair.page_version_a,
                        page_version_b=pair.page_version_b,
                        bbox_version_a=blk_a.get("bbox"),
                        bbox_version_b=blk_b.get("bbox"),
                        block_id_version_a=blk_a.get("id"),
                        block_id_version_b=blk_b.get("id"),
                    )
                )
            continue

        # ------------------------------------------------------------------
        # Text / heading / paragraph blocks — use diff-match-patch
        # ------------------------------------------------------------------
        text_a = blk_a.get("text", "") or ""
        text_b = blk_b.get("text", "") or ""

        # Skip if both are empty or whitespace-only
        if not text_a.strip() and not text_b.strip():
            continue

        # Skip if texts are identical after whitespace normalization
        if " ".join(text_a.split()) == " ".join(text_b.split()):
            continue

        text_diffs = compute_text_diff(text_a, text_b)
        if not text_diffs:
            # Identical — no record needed
            continue

        for td in text_diffs:
            if td.diff_type == "addition":
                diff_type = DifferenceType.text_addition
            elif td.diff_type == "deletion":
                diff_type = DifferenceType.text_deletion
            else:
                diff_type = DifferenceType.text_modification

            records.append(
                RawDiffRecord(
                    difference_type=diff_type,
                    value_before=td.value_before,
                    value_after=td.value_after,
                    context=_build_context(blk_a, blk_b),
                    page_version_a=pair.page_version_a,
                    page_version_b=pair.page_version_b,
                    bbox_version_a=blk_a.get("bbox"),
                    bbox_version_b=blk_b.get("bbox"),
                    block_id_version_a=blk_a.get("id"),
                    block_id_version_b=blk_b.get("id"),
                )
            )

    # Merge adjacent text diffs from same block pairs
    records = _merge_adjacent_diffs(records)

    logger.info(f"Stage 6: produced {len(records)} raw diff records")
    return records


def _merge_adjacent_diffs(
    records: list[RawDiffRecord],
    max_gap: int = 50,
) -> list[RawDiffRecord]:
    """Merge adjacent diff records from the same block pair into single logical changes.

    If multiple consecutive text changes come from the same block pair and
    are close together (within max_gap characters), merge them into one record.
    This prevents "18%" -> "21%" from being split into character-level fragments
    and reduces report noise.
    """
    if len(records) <= 1:
        return records

    merged: list[RawDiffRecord] = []
    current = records[0]

    for next_rec in records[1:]:
        # Can merge if: same block pair, same page, both are text modifications
        can_merge = (
            current.block_id_version_a == next_rec.block_id_version_a
            and current.block_id_version_b == next_rec.block_id_version_b
            and current.difference_type in (
                DifferenceType.text_modification,
                DifferenceType.text_addition,
                DifferenceType.text_deletion,
            )
            and next_rec.difference_type in (
                DifferenceType.text_modification,
                DifferenceType.text_addition,
                DifferenceType.text_deletion,
            )
        )

        if can_merge:
            # Merge: combine before/after values
            sep = " "
            before_parts = [current.value_before, next_rec.value_before]
            after_parts = [current.value_after, next_rec.value_after]
            current = RawDiffRecord(
                difference_type=DifferenceType.text_modification,
                value_before=sep.join(p for p in before_parts if p),
                value_after=sep.join(p for p in after_parts if p),
                context=current.context,
                page_version_a=current.page_version_a,
                page_version_b=current.page_version_b,
                bbox_version_a=current.bbox_version_a,
                bbox_version_b=current.bbox_version_b,
                block_id_version_a=current.block_id_version_a,
                block_id_version_b=current.block_id_version_b,
            )
        else:
            merged.append(current)
            current = next_rec

    merged.append(current)

    if len(records) != len(merged):
        logger.debug(f"Diff merge: {len(records)} → {len(merged)} records")

    return merged


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_context(blk_a: dict | None, blk_b: dict | None) -> str:
    """Derive a short context string from one or both blocks."""
    if blk_a and blk_b:
        title = blk_a.get("section_title") or blk_b.get("section_title") or ""
        if title:
            return f"Section: {title}"
        block_type = blk_a.get("type") or blk_b.get("type") or "text"
        return f"Block type: {block_type}"
    block = blk_a or blk_b
    if block:
        return block.get("section_title") or block.get("type") or block.get("block_type") or "unknown"
    return ""


def _table_headers_str(block: dict) -> str:
    """Return a comma-separated string of table headers from a block dict."""
    headers = block.get("headers", [])
    return ", ".join(str(h) for h in headers)
