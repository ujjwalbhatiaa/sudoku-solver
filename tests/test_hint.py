import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sudoku.board import is_consistent, parse
from sudoku.hint import Hint, hint
from sudoku.solver import solve

SOLVED = (
    "534678912672195348198342567859761423426853791713924856"
    "961537284287419635345286179"
)

# 36-clue board with no naked singles: the first forced move is the hidden
# single "3 at r1c2 within row 1".
HIDDEN_SINGLE_PUZZLE = (
    "....7..12..219534...83.25..8.9..14.3.26..3.9..1392..5.9"
    "..53.2.4.8......53....6..."
)


def test_hint_naked_single():
    cells = parse(SOLVED)
    cells[4 * 9 + 4] = 0  # erase the 5 at r5c5
    h = hint(cells)
    assert isinstance(h, Hint)
    assert h.technique == "naked single"
    assert (h.row, h.col, h.value) == (4, 4, 5)
    assert h.candidates == (5,)
    assert "r5c5" in h.explanation and "5" in h.explanation


def test_hint_hidden_single():
    cells = parse(HIDDEN_SINGLE_PUZZLE)
    assert is_consistent(cells)
    h = hint(cells)
    assert h.technique == "hidden single"
    assert (h.row, h.col, h.value) == (0, 1, 3)
    assert "r1c2" in h.explanation and "row 1" in h.explanation
    # The hinted digit must agree with the true solution.
    solution = solve(cells)
    assert solution is not None
    assert solution[0 * 9 + 1] == 3


def test_hint_guess_fallback_on_empty_board():
    h = hint(parse("." * 81))
    assert h.technique == "guess (MRV)"
    assert h.value is None
    assert h.candidates == tuple(range(1, 10))
    assert (h.row, h.col) == (0, 0)
    assert "r1c1" in h.explanation


def test_hint_none_when_solved():
    assert hint(parse(SOLVED)) is None


def test_hint_none_when_inconsistent():
    assert hint(parse("55" + "." * 79)) is None


def test_hint_none_at_dead_end():
    # r1c9 is empty but every digit 1-9 already appears among its peers.
    cells = parse("12345678." + "........9" + "." * 63)
    assert is_consistent(cells)
    assert hint(cells) is None
