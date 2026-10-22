"""Step-by-step solution explanations for Sudoku puzzles.

`explain_solve(cells)` replays a puzzle's solution as an ordered list of
human-readable steps: it repeatedly asks `hint()` for the single most
instructive next move and applies it, recording what was done and why.

When no forced move exists, `hint()` suggests a guess at the most
constrained cell (MRV). The guess is resolved against a precomputed
solution, so the trace always shows the *successful* path -- like the
worked solution in a textbook, not a trial-and-error log. This is only
well-defined because every forced move (naked/hidden single) is logically
entailed by the givens and therefore holds in every solution; the guess
simply picks which solution's path to follow.

Raises ValueError for inconsistent givens or unsolvable puzzles.
Each step fills exactly one cell, so a trace has at most 81 steps.
"""

from __future__ import annotations

from dataclasses import dataclass

from .board import is_consistent, is_valid_complete
from .hint import hint
from .solver import solve


@dataclass
class Step:
    number: int        # 1-based position in the trace
    technique: str     # "naked single" | "hidden single" | "guess (MRV)"
    row: int           # 0-based
    col: int           # 0-based
    value: int         # digit placed (for guesses: the solution's digit)
    explanation: str   # plain-English reasoning for this step


def _cell_name(row: int, col: int) -> str:
    return f"r{row + 1}c{col + 1}"


def explain_solve(cells: list[int]) -> list[Step]:
    """Return the ordered steps that solve this puzzle.

    Every step's `value` agrees with the puzzle's solution (for guesses,
    the value is taken from the precomputed solution so the trace follows
    the successful path). Replaying the steps on the input board reproduces
    the solution exactly.
    """
    if not is_consistent(cells):
        raise ValueError("puzzle givens violate a Sudoku constraint")
    solution = solve(cells)
    if solution is None:
        raise ValueError("puzzle has no solution")

    work = cells[:]
    steps: list[Step] = []
    while not is_valid_complete(work):
        h = hint(work)
        if h is None:
            # A consistent, solvable board always yields a hint here (every
            # prefix of the true solution is itself consistent), so reaching
            # this branch means something went wrong -- fail loudly rather
            # than looping forever.
            raise ValueError("reached a dead end while explaining the solution")
        idx = h.row * 9 + h.col
        if h.value is not None:
            # Forced move: the digit is logically entailed, apply it as-is.
            work[idx] = h.value
            steps.append(Step(len(steps) + 1, h.technique,
                              h.row, h.col, h.value, h.explanation))
        else:
            # Guess: follow the known solution so the trace shows the
            # successful path instead of a backtracking search log.
            v = solution[idx]
            work[idx] = v
            steps.append(Step(
                number=len(steps) + 1,
                technique="guess (MRV)",
                row=h.row, col=h.col, value=v,
                explanation=(
                    f"Guess: no forced move, so try {_cell_name(h.row, h.col)} = {v} "
                    f"-- the most constrained cell, with candidates {list(h.candidates)}. "
                    f"(Following the puzzle's solution; a wrong guess here would backtrack.)"
                ),
            ))
    return steps
