"""Tests for sudoku-solver: parsing, solving, generation, rating. Run with: pytest"""

import pytest

from sudoku.board import is_consistent, is_valid_complete, parse, pretty
from sudoku.generator import generate_puzzle, rate_difficulty
from sudoku.solver import count_solutions, solve, solved_by_propagation_alone

# Classic easy example (Wikipedia)
EASY = ("530070000600195000098000060800060003400803001700020006"
        "060000280000419005000080079")
EASY_SOLUTION = ("534678912672195348198342567859761423426853791713924856"
                 "961537284287419635345286179")

# Hard puzzle (Arto Inkala's "AI Escargot")
HARD = ("100007090030020008009600500005300900010080002600004000"
        "300000010040000007007000300")

# 36-clue board solvable by propagation alone (first move: hidden single).
PROPAGATION_SOLVABLE_36 = (
    "....7..12..219534...83.25..8.9..14.3.26..3.9..1392..5.9"
    "..53.2.4.8......53....6..."
)


def test_parse_digits_and_dots():
    g = parse(EASY)
    assert len(g) == 81
    assert g[0] == 5 and g[2] == 0


def test_parse_rejects_wrong_length():
    with pytest.raises(ValueError):
        parse("123")


def test_parse_accepts_zeros():
    assert parse("0" * 81) == [0] * 81


def test_is_consistent_accepts_good_puzzle():
    assert is_consistent(parse(EASY))


def test_is_consistent_rejects_conflict():
    g = parse(EASY)
    g[1] = 5  # duplicate 5 in row 0
    assert not is_consistent(g)


def test_solve_easy():
    solved = solve(parse(EASY))
    assert solved is not None
    assert "".join(map(str, solved)) == EASY_SOLUTION
    assert is_valid_complete(solved)


def test_solve_hard():
    solved = solve(parse(HARD))
    assert solved is not None
    assert is_valid_complete(solved)


def test_solve_invalid_returns_none():
    g = parse(EASY)
    g[1] = 5
    assert solve(g) is None


def test_solve_empty_grid_gives_valid_solution():
    solved = solve([0] * 81)
    assert solved is not None
    assert is_valid_complete(solved)


def test_count_solutions_unique():
    assert count_solutions(parse(EASY), limit=2) == 1


def test_count_solutions_empty_capped():
    # empty grid has astronomically many solutions; limit caps the search
    assert count_solutions([0] * 81, limit=2) == 2


def test_generate_unique_solution_and_rating():
    for difficulty in ("easy", "medium"):
        puzzle, solution, actual = generate_puzzle(difficulty, seed=42)
        assert count_solutions(puzzle, limit=2) == 1
        assert is_valid_complete(solution)
        assert actual == difficulty


def test_generate_hard_unique_solution():
    puzzle, solution, actual = generate_puzzle("hard", seed=7)
    assert count_solutions(puzzle, limit=2) == 1
    assert is_valid_complete(solution)
    assert actual in ("easy", "medium", "hard", "expert")


def test_generate_bad_difficulty():
    with pytest.raises(ValueError):
        generate_puzzle("impossible")


def test_pretty_grid_shape():
    out = pretty(parse(EASY_SOLUTION)).splitlines()
    assert len(out) == 11  # 9 rows + 2 separators
    assert "|" in out[0]


def test_rate_difficulty_easy():
    # 36 clues and solvable by propagation alone -> easy
    cells = parse(PROPAGATION_SOLVABLE_36)
    assert solved_by_propagation_alone(cells)
    assert rate_difficulty(cells) == "easy"


def test_rate_difficulty_medium():
    # propagation-solvable but under 36 clues -> medium
    puzzle, _, _ = generate_puzzle("medium", seed=42)
    assert sum(1 for v in puzzle if v != 0) < 36
    assert solved_by_propagation_alone(puzzle)
    assert rate_difficulty(puzzle) == "medium"


def test_rate_difficulty_hard():
    # needs backtracking, but still 26+ clues -> hard
    cells = parse(EASY_SOLUTION)
    for i in range(30):
        cells[i] = 0
    assert not solved_by_propagation_alone(cells)
    assert rate_difficulty(cells) == "hard"


def test_rate_difficulty_expert():
    # Escargot: needs search and has few clues -> expert
    cells = parse(HARD)
    assert not solved_by_propagation_alone(cells)
    assert rate_difficulty(cells) == "expert"
