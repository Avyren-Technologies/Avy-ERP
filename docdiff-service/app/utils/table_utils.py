import logging
from dataclasses import dataclass

from app.utils.diff_utils import compute_similarity

logger = logging.getLogger("docdiff.utils")


@dataclass
class CellDiff:
    row: int
    col: int
    value_before: str
    value_after: str
    diff_type: str  # "modified", "added", "deleted"


@dataclass
class TableDiff:
    cell_changes: list[CellDiff]
    rows_added: list[int]
    rows_deleted: list[int]
    structure_changed: bool
    header_changes: list[CellDiff]


def compare_tables(table_a: dict, table_b: dict) -> TableDiff:
    cells_a = _build_cell_map(table_a.get("cells", []))
    cells_b = _build_cell_map(table_b.get("cells", []))
    headers_a = table_a.get("headers", [])
    headers_b = table_b.get("headers", [])

    cell_changes: list[CellDiff] = []
    structure_changed = (
        table_a.get("rows") != table_b.get("rows")
        or table_a.get("cols") != table_b.get("cols")
    )

    header_changes: list[CellDiff] = []
    max_headers = max(len(headers_a), len(headers_b))
    for i in range(max_headers):
        ha = headers_a[i] if i < len(headers_a) else ""
        hb = headers_b[i] if i < len(headers_b) else ""
        if ha != hb:
            header_changes.append(CellDiff(row=0, col=i, value_before=ha, value_after=hb, diff_type="modified"))

    all_keys = set(cells_a.keys()) | set(cells_b.keys())
    for key in sorted(all_keys):
        val_a = cells_a.get(key, None)
        val_b = cells_b.get(key, None)
        row, col = key
        if val_a is None and val_b is not None:
            cell_changes.append(CellDiff(row=row, col=col, value_before="", value_after=val_b, diff_type="added"))
        elif val_a is not None and val_b is None:
            cell_changes.append(CellDiff(row=row, col=col, value_before=val_a, value_after="", diff_type="deleted"))
        elif val_a != val_b:
            cell_changes.append(CellDiff(row=row, col=col, value_before=val_a or "", value_after=val_b or "", diff_type="modified"))

    rows_in_a = {key[0] for key in cells_a.keys()}
    rows_in_b = {key[0] for key in cells_b.keys()}
    rows_added = sorted(rows_in_b - rows_in_a)
    rows_deleted = sorted(rows_in_a - rows_in_b)

    return TableDiff(
        cell_changes=cell_changes,
        rows_added=rows_added,
        rows_deleted=rows_deleted,
        structure_changed=structure_changed,
        header_changes=header_changes,
    )


def _build_cell_map(cells: list[dict]) -> dict[tuple[int, int], str]:
    cell_map: dict[tuple[int, int], str] = {}
    for cell in cells:
        key = (cell["row"], cell["col"])
        cell_map[key] = cell.get("text", "")
    return cell_map


def compute_table_similarity(table_a: dict, table_b: dict) -> float:
    headers_a = " ".join(table_a.get("headers", []))
    headers_b = " ".join(table_b.get("headers", []))
    header_sim = compute_similarity(headers_a, headers_b)
    size_a = table_a.get("rows", 0) * table_a.get("cols", 0)
    size_b = table_b.get("rows", 0) * table_b.get("cols", 0)
    if max(size_a, size_b) == 0:
        size_sim = 1.0
    else:
        size_sim = 1.0 - abs(size_a - size_b) / max(size_a, size_b)
    return 0.7 * header_sim + 0.3 * size_sim
