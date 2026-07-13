import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sudoku.board import (
    box_of,
    col_of,
    is_consistent,
    is_valid_complete,
    parse,
    peers,
    pretty,
    row_of,
    to_string,
)

EASY = (
    "53..7....6..195....98....6.8...6...34..8.3..17...2...6.6....28....419..5....8..79"
)


def test_parse_compact_string_roundtrip():
    cells = parse(EASY)
    assert len(cells) == 81
    assert to_string(cells) == EASY


def test_parse_grid_with_dots():
    grid = "\n".join(EASY[r * 9 : r * 9 + 9] for r in range(9))
    cells = parse(grid)
    assert to_string(cells) == EASY


def test_parse_rejects_wrong_length():
    try:
        parse("123")
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError")


def test_row_col_box_indices():
    # cell 0 -> row 0, col 0, box 0
    assert row_of(0) == 0 and col_of(0) == 0 and box_of(0) == 0
    # cell 80 (row 8, col 8) -> box 8
    assert row_of(80) == 8 and col_of(80) == 8 and box_of(80) == 8
    # cell 40 (row 4, col 4) -> box 4 (center box)
    assert row_of(40) == 4 and col_of(40) == 4 and box_of(40) == 4


def test_peers_count_and_symmetry():
    for i in (0, 40, 80):
        p = peers(i)
        # A cell shares its row (8 others), col (8 others), box (8 others,
        # but 4 already counted via row+col overlap) -> 20 unique peers.
        assert len(p) == 20
        assert i not in p
    # Peer relation is symmetric.
    assert 5 in peers(0)
    assert 0 in peers(5)


def test_is_consistent_detects_duplicate():
    cells = [0] * 81
    cells[0] = 5
    cells[1] = 5  # same row, duplicate
    assert not is_consistent(cells)


def test_is_consistent_allows_partial():
    cells = [0] * 81
    cells[0] = 5
    assert is_consistent(cells)


def test_is_valid_complete_requires_full_board():
    cells = [0] * 81
    cells[0] = 5
    assert not is_valid_complete(cells)


def test_pretty_has_box_dividers():
    cells = parse(EASY)
    text = pretty(cells)
    assert text.count("\n") == 10  # 9 rows + 2 divider lines
    assert "------+-------+------" in text
