import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sudoku.board import is_valid_complete
from sudoku.generator import DIFFICULTY_TARGET_CLUES, dig_holes, generate_full_grid, generate_puzzle, rate_difficulty
from sudoku.solver import count_solutions, solve
import random


def test_generate_full_grid_is_valid_and_deterministic_with_seed():
    grid_a = generate_full_grid(random.Random(1))
    assert is_valid_complete(grid_a)

    grid_b = generate_full_grid(random.Random(1))
    assert grid_a == grid_b  # same seed -> same grid

    grid_c = generate_full_grid(random.Random(2))
    assert grid_c != grid_a  # different seed -> (overwhelmingly likely) different grid


def test_dig_holes_preserves_unique_solution():
    rng = random.Random(7)
    solution = generate_full_grid(rng)
    puzzle = dig_holes(solution, rng, target_clues=32)
    assert count_solutions(puzzle, limit=2) == 1
    # The unique solution must match the original grid it was dug from.
    assert solve(puzzle) == solution


def test_dig_holes_reduces_clue_count():
    rng = random.Random(3)
    solution = generate_full_grid(rng)
    puzzle = dig_holes(solution, rng, target_clues=30)
    clues = sum(1 for v in puzzle if v != 0)
    assert clues <= 40  # started at 81, should be well reduced
    assert clues >= 17  # 17 is the proven minimum for a unique-solution puzzle


def test_generate_puzzle_all_difficulties_produce_unique_solvable_puzzles():
    for difficulty in DIFFICULTY_TARGET_CLUES:
        puzzle, solution, actual = generate_puzzle(difficulty=difficulty, seed=42)
        assert is_valid_complete(solution)
        assert count_solutions(puzzle, limit=2) == 1
        assert solve(puzzle) == solution
        assert actual in DIFFICULTY_TARGET_CLUES


def test_generate_puzzle_reproducible_with_seed():
    p1, s1, d1 = generate_puzzle(difficulty="medium", seed=99)
    p2, s2, d2 = generate_puzzle(difficulty="medium", seed=99)
    assert p1 == p2
    assert s1 == s2
    assert d1 == d2


def test_generate_puzzle_rejects_unknown_difficulty():
    try:
        generate_puzzle(difficulty="nightmare")
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError")


def test_rate_difficulty_harder_puzzles_have_fewer_clues_on_average():
    # Not a strict guarantee for any single puzzle (digging is randomized),
    # but averaged over several seeds, higher difficulty tiers should trend
    # toward fewer clues.
    def avg_clues(difficulty, seeds):
        totals = []
        for s in seeds:
            puzzle, _, _ = generate_puzzle(difficulty=difficulty, seed=s)
            totals.append(sum(1 for v in puzzle if v != 0))
        return sum(totals) / len(totals)

    seeds = range(5)
    easy_avg = avg_clues("easy", seeds)
    expert_avg = avg_clues("expert", seeds)
    assert expert_avg <= easy_avg
