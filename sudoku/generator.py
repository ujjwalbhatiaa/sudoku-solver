"""Puzzle generation: full-grid generation, hole-digging, and difficulty rating.

Approach:
1. Generate a complete, valid 9x9 grid by backtracking with randomized value
   order (this is the same search as the solver's, but shuffled so repeated
   calls give different grids instead of always the same one).
2. "Dig holes": visit cells in random order and try clearing each one,
   keeping the removal only if the puzzle still has exactly one solution
   (checked with `solver.count_solutions(..., limit=2) == 1`). This is the
   standard technique for generating uniquely-solvable Sudoku puzzles -- the
   alternative (removing cells without checking) can silently produce
   multi-solution puzzles.
3. Rate the resulting puzzle's difficulty from two signals: whether pure
   constraint propagation (no guessing) solves it, and how many clues remain.
   This is a heuristic, not a formal proof of difficulty, and is documented
   as such in the README.
"""

from __future__ import annotations

import random

from .board import PEERS
from .solver import count_solutions, solved_by_propagation_alone

DIFFICULTY_TARGET_CLUES = {
    "easy": 40,
    "medium": 33,
    "hard": 28,
    "expert": 24,
}


def _bit(v: int) -> int:
    return 1 << v


def generate_full_grid(rng: random.Random) -> list[int]:
    """Return a complete, randomly-generated valid 9x9 solution grid."""
    cells = [0] * 81

    def backtrack(pos: int) -> bool:
        if pos == 81:
            return True
        if cells[pos] != 0:
            return backtrack(pos + 1)
        candidates = list(range(1, 10))
        rng.shuffle(candidates)
        used = {cells[p] for p in PEERS[pos] if cells[p] != 0}
        for v in candidates:
            if v in used:
                continue
            cells[pos] = v
            if backtrack(pos + 1):
                return True
            cells[pos] = 0
        return False

    ok = backtrack(0)
    assert ok, "full-grid generation should always succeed"
    return cells


def dig_holes(solution: list[int], rng: random.Random, target_clues: int, max_attempts: int | None = None) -> list[int]:
    """Remove cells from a complete grid while keeping a unique solution.

    Stops when either `target_clues` is reached or no more cells can be
    removed without breaking uniqueness (common for very low targets like
    'expert' -- true minimum-clue puzzles are a hard research problem in
    their own right, so this is a best-effort dig, not a guarantee of
    hitting the exact target).
    """
    puzzle = solution[:]
    order = list(range(81))
    rng.shuffle(order)
    clues = 81

    for i in order:
        if clues <= target_clues:
            break
        if puzzle[i] == 0:
            continue
        saved = puzzle[i]
        puzzle[i] = 0
        if count_solutions(puzzle, limit=2) == 1:
            clues -= 1
        else:
            puzzle[i] = saved  # removing this cell broke uniqueness, restore

    return puzzle


def rate_difficulty(puzzle: list[int]) -> str:
    """Heuristic difficulty rating from clue count + whether propagation alone
    (no backtracking/guessing) solves it. See module docstring for caveats."""
    clues = sum(1 for v in puzzle if v != 0)
    propagation_only = solved_by_propagation_alone(puzzle)

    if propagation_only and clues >= 36:
        return "easy"
    if propagation_only:
        return "medium"
    if clues >= 26:
        return "hard"
    return "expert"


def generate_puzzle(difficulty: str = "medium", seed: int | None = None) -> tuple[list[int], list[int], str]:
    """Generate a (puzzle, solution, actual_difficulty) tuple.

    `difficulty` selects a target clue count to dig towards; the returned
    `actual_difficulty` is independently measured from the resulting puzzle
    (it may differ slightly from the requested tier since digging is
    randomized and clue count alone doesn't perfectly determine difficulty).
    """
    if difficulty not in DIFFICULTY_TARGET_CLUES:
        raise ValueError(f"unknown difficulty {difficulty!r}, expected one of {list(DIFFICULTY_TARGET_CLUES)}")

    rng = random.Random(seed)
    solution = generate_full_grid(rng)
    target = DIFFICULTY_TARGET_CLUES[difficulty]
    puzzle = dig_holes(solution, rng, target_clues=target)
    actual = rate_difficulty(puzzle)
    return puzzle, solution, actual
