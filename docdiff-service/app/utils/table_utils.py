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


def _normalize_cell_value(text: str) -> str:
    """Normalize cell value for comparison.

    - Strip whitespace
    - Normalize numbers: "2.0" -> "2", "1,000" -> "1000"
    - Preserve non-numeric text as-is
    """
    text = text.strip()
    if not text:
        return text

    # Try to parse as number and normalize
    try:
        # Remove commas from numbers
        cleaned = text.replace(",", "").replace(" ", "")
        # Try float conversion
        num = float(cleaned)
        # If it's a whole number, show without decimal
        if num == int(num):
            return str(int(num))
        return str(num)
    except ValueError:
        return text


def _unwrap_table(block: dict) -> dict:
    """Unwrap table data from block dict.

    fast_parser nests table data under a "table" key, while some other code
    passes the table dict directly. This handles both cases.
    """
    if "table" in block and isinstance(block["table"], dict):
        return block["table"]
    return block


def compare_tables(table_a: dict, table_b: dict) -> TableDiff:
    # Unwrap nested table structure (fast_parser nests under "table" key)
    ta = _unwrap_table(table_a)
    tb = _unwrap_table(table_b)

    cells_a = _build_cell_map(ta.get("cells", []))
    cells_b = _build_cell_map(tb.get("cells", []))
    headers_a = ta.get("headers", [])
    headers_b = tb.get("headers", [])

    cell_changes: list[CellDiff] = []
    structure_changed = (
        ta.get("rows") != tb.get("rows")
        or ta.get("cols") != tb.get("cols")
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
        raw_a = cells_a.get(key, None)
        raw_b = cells_b.get(key, None)
        val_a = _normalize_cell_value(raw_a) if raw_a is not None else None
        val_b = _normalize_cell_value(raw_b) if raw_b is not None else None
        row, col = key
        if val_a is None and val_b is not None:
            cell_changes.append(CellDiff(row=row, col=col, value_before="", value_after=raw_b, diff_type="added"))
        elif val_a is not None and val_b is None:
            cell_changes.append(CellDiff(row=row, col=col, value_before=raw_a, value_after="", diff_type="deleted"))
        elif val_a != val_b:
            cell_changes.append(CellDiff(row=row, col=col, value_before=raw_a or "", value_after=raw_b or "", diff_type="modified"))

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
    ta = _unwrap_table(table_a)
    tb = _unwrap_table(table_b)
    headers_a = " ".join(ta.get("headers", []))
    headers_b = " ".join(tb.get("headers", []))
    header_sim = compute_similarity(headers_a, headers_b)
    size_a = ta.get("rows", 0) * ta.get("cols", 0)
    size_b = tb.get("rows", 0) * tb.get("cols", 0)
    if max(size_a, size_b) == 0:
        size_sim = 1.0
    else:
        size_sim = 1.0 - abs(size_a - size_b) / max(size_a, size_b)
    return 0.7 * header_sim + 0.3 * size_sim
