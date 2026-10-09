"""Tests for sudoku-solver. Run with: pytest"""

import pytest

from sudoku import (
    count_solutions,
    difficulty_of,
    format_grid,
    generate,
    is_solved,
    is_valid,
    parse_grid,
    solve,
)

# Classic easy example (Wikipedia)
EASY = ("530070000600195000098000060800060003400803001700020006"
        "060000280000419005000080079")
EASY_SOLUTION = ("534678912672195348198342567859761423426853791713924856"
                 "961537284287419635345286179")

# Hard puzzle (Arto Inkala's "AI Escargot")
HARD = ("100007090030020008009600500005300900010080002600004000"
        "300000010040000007007000300")


def test_parse_grid_digits_and_dots():
    g = parse_grid(EASY)
    assert len(g) == 81
    assert g[0] == 5 and g[2] == 0


def test_parse_grid_rejects_wrong_length():
    with pytest.raises(ValueError):
        parse_grid("123")


def test_parse_grid_accepts_zeros():
    g = parse_grid("0" * 81)
    assert g == [0] * 81


def test_is_valid_accepts_good_puzzle():
    assert is_valid(parse_grid(EASY))


def test_is_valid_rejects_conflict():
    g = parse_grid(EASY)
    g[1] = 5  # duplicate 5 in row 0
    assert not is_valid(g)


def test_solve_easy():
    solved = solve(parse_grid(EASY))
    assert solved is not None
    assert "".join(map(str, solved)) == EASY_SOLUTION
    assert is_solved(solved)


def test_solve_hard():
    solved = solve(parse_grid(HARD))
    assert solved is not None
    assert is_solved(solved)


def test_solve_invalid_returns_none():
    g = parse_grid(EASY)
    g[1] = 5
    assert solve(g) is None


def test_solve_empty_grid_gives_valid_solution():
    solved = solve([0] * 81)
    assert solved is not None
    assert is_solved(solved)


def test_count_solutions_unique():
    assert count_solutions(parse_grid(EASY), limit=2) == 1


def test_count_solutions_empty_capped():
    # empty grid has astronomically many solutions; limit caps the search
    assert count_solutions([0] * 81, limit=2) == 2


def test_generate_unique_solution():
    for difficulty in ("easy", "medium"):
        puzzle = generate(difficulty, seed=42)
        assert count_solutions(puzzle, limit=2) == 1
        assert difficulty_of(puzzle) == difficulty


def test_generate_hard_unique_solution():
    puzzle = generate("hard", seed=7)
    assert count_solutions(puzzle, limit=2) == 1


def test_generate_bad_difficulty():
    with pytest.raises(ValueError):
        generate("impossible")


def test_format_grid_shape():
    out = format_grid(parse_grid(EASY_SOLUTION)).splitlines()
    assert len(out) == 11  # 9 rows + 2 separators
    assert "|" in out[0]


def test_difficulty_of_thresholds():
    assert difficulty_of([1] * 40 + [0] * 41) == "easy"
    assert difficulty_of([1] * 32 + [0] * 49) == "medium"
    assert difficulty_of([1] * 27 + [0] * 54) == "hard"
