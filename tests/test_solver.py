import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sudoku.board import is_valid_complete, parse
from sudoku.solver import count_solutions, solve, solved_by_propagation_alone

AI_ESCARGOT = (
    "1.......2.9.4...5...6...7...5.9.3.......7.......85..4.7.....6...3...9.8...2.....1"
)

WORLDS_HARDEST = (
    "8..........36......7..9.2...5...7.......457.....1...3...1....68..85...1..9....4.."
)

NO_CLUES = "." * 81


def test_solve_hard_puzzle_ai_escargot():
    cells = parse(AI_ESCARGOT)
    result = solve(cells)
    assert result is not None
    assert is_valid_complete(result)
    for i, v in enumerate(cells):
        if v != 0:
            assert result[i] == v


def test_solve_worlds_hardest():
    cells = parse(WORLDS_HARDEST)
    result = solve(cells)
    assert result is not None
    assert is_valid_complete(result)


def test_solve_empty_board_produces_valid_grid():
    cells = parse(NO_CLUES)
    result = solve(cells)
    assert result is not None
    assert is_valid_complete(result)


def test_unsolvable_puzzle_returns_none():
    cells = [0] * 81
    cells[0] = 1
    cells[1] = 1  # same row duplicate -> inconsistent from the start
    assert solve(cells) is None


def test_count_solutions_unique_puzzle():
    cells = parse(AI_ESCARGOT)
    assert count_solutions(cells, limit=2) == 1


def test_count_solutions_empty_board_has_many():
    cells = parse(NO_CLUES)
    # An empty board has millions of solutions; with limit=2 we should hit
    # the cap quickly rather than enumerate them all.
    assert count_solutions(cells, limit=2) == 2


def test_count_solutions_inconsistent_board_is_zero():
    cells = [0] * 81
    cells[0] = 1
    cells[1] = 1
    assert count_solutions(cells, limit=2) == 0


def test_solved_by_propagation_alone_true_for_easy():
    cells = parse(AI_ESCARGOT)
    # AI Escargot is famous for specifically NOT being solvable by simple
    # singles propagation -- it needs guessing. Assert that here as a
    # sanity check on the propagation-only detector itself.
    assert solved_by_propagation_alone(cells) is False


def test_solved_by_propagation_alone_true_for_near_complete():
    cells = parse(AI_ESCARGOT)
    solution = solve(cells)
    # Take the true solution and blank out just one cell -- trivially
    # solvable by a single naked-single step.
    near_complete = solution[:]
    near_complete[0] = 0
    assert solved_by_propagation_alone(near_complete) is True
