"""Board representation, parsing, and printing for 9x9 Sudoku.

A board is stored as a flat list of 81 ints, 0 = empty, 1-9 = filled.
Row-major order: index = row * 9 + col.
"""

from __future__ import annotations

BOX = 3
SIZE = 9


def parse(text: str) -> list[int]:
    """Parse a puzzle from a string.

    Accepts either an 81-character string (digits, with '.', '0', or '_' for
    blanks) or a 9-line grid (any non-digit character in a line is treated as
    blank; lines of pure formatting like '-----' are ignored).
    """
    digits: list[int] = []
    stripped = text.strip()

    if "\n" not in stripped and len(stripped.replace(" ", "")) == 81:
        for ch in stripped.replace(" ", ""):
            digits.append(0 if ch in ".0_" else int(ch))
    else:
        for line in stripped.splitlines():
            line = line.strip()
            if not line or set(line) <= set("-+| "):
                continue
            for ch in line:
                if ch in " |+-":
                    continue
                digits.append(0 if ch in ".0_" else int(ch))

    if len(digits) != 81:
        raise ValueError(f"expected 81 cells, got {len(digits)}")
    return digits


def to_string(cells: list[int]) -> str:
    """Serialize to the compact 81-char format ('.' for blanks)."""
    return "".join(str(v) if v else "." for v in cells)


def pretty(cells: list[int]) -> str:
    """Render as a human-readable 9x9 grid with box dividers."""
    lines = []
    for r in range(SIZE):
        if r % BOX == 0 and r != 0:
            lines.append("------+-------+------")
        row_parts = []
        for c in range(SIZE):
            if c % BOX == 0 and c != 0:
                row_parts.append("|")
            v = cells[r * SIZE + c]
            row_parts.append(str(v) if v else ".")
        lines.append(" ".join(row_parts))
    return "\n".join(lines)


def row_of(i: int) -> int:
    return i // SIZE


def col_of(i: int) -> int:
    return i % SIZE


def box_of(i: int) -> int:
    r, c = row_of(i), col_of(i)
    return (r // BOX) * BOX + (c // BOX)


def peers(i: int) -> set[int]:
    """All cell indices sharing a row, column, or box with i (excluding i)."""
    r, c, b = row_of(i), col_of(i), box_of(i)
    result = set()
    for j in range(81):
        if j == i:
            continue
        if row_of(j) == r or col_of(j) == c or box_of(j) == b:
            result.add(j)
    return result


# Precomputed once at import time -- used heavily by the solver's hot loop.
PEERS: list[frozenset[int]] = [frozenset(peers(i)) for i in range(81)]

# Index groups (row/col/box) as tuples of 9 cell indices each, used for
# hidden-singles / hidden-pairs style reasoning and for validity checks.
ROWS = [tuple(r * SIZE + c for c in range(SIZE)) for r in range(SIZE)]
COLS = [tuple(r * SIZE + c for r in range(SIZE)) for c in range(SIZE)]
BOXES = [
    tuple(
        (br * BOX + dr) * SIZE + (bc * BOX + dc)
        for dr in range(BOX)
        for dc in range(BOX)
    )
    for br in range(BOX)
    for bc in range(BOX)
]
UNITS = ROWS + COLS + BOXES


def is_valid_complete(cells: list[int]) -> bool:
    """True iff every cell is filled and every row/col/box is a permutation of 1-9."""
    if any(v == 0 for v in cells):
        return False
    return all(sorted(cells[i] for i in unit) == list(range(1, 10)) for unit in UNITS)


def is_consistent(cells: list[int]) -> bool:
    """True iff no row/col/box has a duplicate among its filled cells (partial ok)."""
    for unit in UNITS:
        seen = set()
        for i in unit:
            v = cells[i]
            if v == 0:
                continue
            if v in seen:
                return False
            seen.add(v)
    return True
