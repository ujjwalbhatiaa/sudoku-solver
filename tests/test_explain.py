import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest

from sudoku.board import is_valid_complete, parse
from sudoku.explain import Step, explain_solve
from sudoku.solver import solve

SOLVED = (
    "534678912672195348198342567859761423426853791713924856"
    "961537284287419635345286179"
)

# Classic easy example (Wikipedia)
EASY = ("530070000600195000098000060800060003400803001700020006"
        "060000280000419005000080079")

# Hard puzzle (Arto Inkala's "AI Escargot") -- needs real guessing.
HARD = ("100007090030020008009600500005300900010080002600004000"
        "300000010040000007007000300")

# 36-clue board whose first forced move is the hidden single "3 at r1c2".
HIDDEN_SINGLE_PUZZLE = (
    "....7..12..219534...83.25..8.9..14.3.26..3.9..1392..5.9"
    "..53.2.4.8......53....6..."
)

# Consistent givens, but r1c9 has no legal digit (row wants 9, column and
# box already contain 9) -- unsolvable.
DEAD_END = "12345678." + "........9" + "." * 63


def _replay(cells, steps):
    work = cells[:]
    for s in steps:
        assert work[s.row * 9 + s.col] == 0, "each step must fill an empty cell"
        work[s.row * 9 + s.col] = s.value
    return work


def test_explain_easy_replays_to_solution():
    cells = parse(EASY)
    solution = solve(cells)
    assert solution is not None
    steps = explain_solve(cells)
    assert steps, "a non-trivial puzzle must produce steps"
    # Sequential 1-based numbering.
    assert [s.number for s in steps] == list(range(1, len(steps) + 1))
    # Replaying the trace reproduces the solution exactly.
    assert _replay(cells, steps) == solution
    assert is_valid_complete(_replay(cells, steps))


def test_explain_easy_uses_only_forced_moves():
    # The Wikipedia easy example is solvable by propagation alone, so the
    # trace should never need to guess.
    steps = explain_solve(parse(EASY))
    assert {s.technique for s in steps} <= {"naked single", "hidden single"}


def test_explain_starts_with_hidden_single():
    steps = explain_solve(parse(HIDDEN_SINGLE_PUZZLE))
    first = steps[0]
    assert first.technique == "hidden single"
    assert (first.row, first.col, first.value) == (0, 1, 3)
    assert "r1c2" in first.explanation


def test_explain_hard_puzzle_uses_guesses_but_stays_correct():
    cells = parse(HARD)
    steps = explain_solve(cells)
    assert any(s.technique == "guess (MRV)" for s in steps), \
        "Escargot cannot be solved by propagation alone"
    assert is_valid_complete(_replay(cells, steps))


def test_explain_guess_values_match_solution():
    cells = parse(HARD)
    solution = solve(cells)
    for s in explain_solve(cells):
        assert 1 <= s.value <= 9
        assert solution[s.row * 9 + s.col] == s.value


def test_explain_step_fields():
    steps = explain_solve(parse(EASY))
    for s in steps:
        assert isinstance(s, Step)
        assert 0 <= s.row < 9 and 0 <= s.col < 9
        assert isinstance(s.explanation, str) and s.explanation


def test_explain_solved_board_returns_no_steps():
    assert explain_solve(parse(SOLVED)) == []


def test_explain_invalid_givens_raise():
    with pytest.raises(ValueError):
        explain_solve(parse("55" + "." * 79))


def test_explain_unsolvable_board_raises():
    with pytest.raises(ValueError):
        explain_solve(parse(DEAD_END))
