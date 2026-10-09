#!/usr/bin/env python3
"""sudoku-solver: solve, validate, and generate Sudoku puzzles.

Backtracking search with minimum-remaining-values (MRV) heuristic and
naked-single constraint propagation. Pure standard library.

Usage:
    python sudoku.py solve "530070000600195000098000060800060003400803001700020006060000280000419005000080079"
    python sudoku.py generate --difficulty medium
    python sudoku.py validate "550070000600195000098000060800060003400803001700020006060000280000419005000080079"
"""

from __future__ import annotations

import argparse
import random
import sys

N = 9
CELLS = range(81)


def _peers() -> list[set[int]]:
    peers = []
    for i in CELLS:
        r, c = divmod(i, 9)
        box_r, box_c = 3 * (r // 3), 3 * (c // 3)
        s = set()
        for j in CELLS:
            r2, c2 = divmod(j, 9)
            if j != i and (r2 == r or c2 == c or
                           (box_r <= r2 < box_r + 3 and box_c <= c2 < box_c + 3)):
                s.add(j)
        peers.append(s)
    return peers


PEERS = _peers()
UNITS = (
    [[r * 9 + c for c in range(9)] for r in range(9)] +
    [[r * 9 + c for r in range(9)] for c in range(9)] +
    [[(br + r) * 9 + (bc + c) for r in range(3) for c in range(3)]
     for br in (0, 3, 6) for bc in (0, 3, 6)]
)


# ---------------------------------------------------------------------------
# Parsing / display
# ---------------------------------------------------------------------------

def parse_grid(text: str) -> list[int]:
    """Parse an 81-char puzzle: digits, '.' or '0' for empties."""
    chars = [ch for ch in text if ch.isdigit() or ch in ".0xX"]
    if len(chars) != 81:
        raise ValueError(f"expected 81 cells, got {len(chars)}")
    return [0 if ch in ".0xX" else int(ch) for ch in chars]


def format_grid(grid: list[int]) -> str:
    """Pretty-print a grid with 3x3 box separators."""
    lines = []
    for r in range(9):
        row = []
        for c in range(9):
            v = grid[r * 9 + c]
            row.append(str(v) if v else ".")
            if c in (2, 5):
                row.append("|")
        lines.append(" ".join(row))
        if r in (2, 5):
            lines.append("-" * 21)
    return "\n".join(lines)


def is_valid(grid: list[int]) -> bool:
    """True if the givens violate no Sudoku constraint."""
    for unit in UNITS:
        seen = [grid[i] for i in unit if grid[i] != 0]
        if len(seen) != len(set(seen)):
            return False
    return True


def is_solved(grid: list[int]) -> bool:
    return all(v != 0 for v in grid) and is_valid(grid)


# ---------------------------------------------------------------------------
# Solver
# ---------------------------------------------------------------------------

def _candidates(grid: list[int], i: int) -> set[int]:
    used = {grid[p] for p in PEERS[i]} | {grid[i]}
    return set(range(1, 10)) - used


def _propagate(grid: list[int]) -> bool:
    """Fill naked singles until fixpoint. False on contradiction."""
    progress = True
    while progress:
        progress = False
        for i in CELLS:
            if grid[i] == 0:
                cands = _candidates(grid, i)
                if not cands:
                    return False
                if len(cands) == 1:
                    grid[i] = next(iter(cands))
                    progress = True
    return True


def _search(grid: list[int], limit: int, solutions: list[list[int]]) -> None:
    if len(solutions) >= limit:
        return
    # Work on a private copy: propagation mutates the grid, and copying per
    # call makes backtracking implicit (a dead end just discards the copy).
    grid = list(grid)
    if not _propagate(grid):
        return
    # MRV: pick the empty cell with fewest candidates
    best, best_cands = -1, None
    for i in CELLS:
        if grid[i] == 0:
            cands = _candidates(grid, i)
            if best_cands is None or len(cands) < len(best_cands):
                best, best_cands = i, cands
    if best == -1:  # no empties: solved
        solutions.append(grid)
        return
    for v in sorted(best_cands):
        grid[best] = v
        _search(grid, limit, solutions)
        if len(solutions) >= limit:
            return


def count_solutions(grid: list[int], limit: int = 2) -> int:
    """Count solutions up to `limit` (default 2: enough for uniqueness)."""
    if not is_valid(grid):
        return 0
    solutions: list[list[int]] = []
    _search(list(grid), limit, solutions)
    return len(solutions)


def solve(grid: list[int]) -> list[int] | None:
    """Return the solved grid, or None if unsolvable / invalid."""
    solutions: list[list[int]] = []
    if not is_valid(grid):
        return None
    _search(list(grid), 1, solutions)
    return solutions[0] if solutions else None


# ---------------------------------------------------------------------------
# Generator
# ---------------------------------------------------------------------------

def _full_grid(rng: random.Random) -> list[int]:
    grid = [0] * 81
    solutions: list[list[int]] = []

    def fill(g: list[int]) -> bool:
        empties = [i for i in CELLS if g[i] == 0]
        if not empties:
            solutions.append(list(g))
            return True
        i = min(empties, key=lambda x: len(_candidates(g, x)))
        vals = list(_candidates(g, i))
        rng.shuffle(vals)
        for v in vals:
            g[i] = v
            if fill(g):
                return True
            g[i] = 0
        return False

    fill(grid)
    return solutions[0]


DIFFICULTY_CLUES = {"easy": 40, "medium": 32, "hard": 27}


def difficulty_of(grid: list[int]) -> str:
    givens = sum(1 for v in grid if v != 0)
    if givens >= 36:
        return "easy"
    if givens >= 30:
        return "medium"
    return "hard"


def generate(difficulty: str = "medium",
             seed: int | None = None) -> list[int]:
    """Generate a puzzle with a unique solution.

    Starts from a random complete grid and digs holes while the solution
    stays unique, down to the clue target for the difficulty.
    """
    if difficulty not in DIFFICULTY_CLUES:
        raise ValueError(f"difficulty must be one of {sorted(DIFFICULTY_CLUES)}")
    rng = random.Random(seed)
    grid = _full_grid(rng)
    target = DIFFICULTY_CLUES[difficulty]
    order = list(CELLS)
    rng.shuffle(order)
    for i in order:
        if sum(1 for v in grid if v != 0) <= target:
            break
        backup = grid[i]
        grid[i] = 0
        if count_solutions(grid, limit=2) != 1:
            grid[i] = backup  # digging here breaks uniqueness: restore
    return grid


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Solve, validate, and "
                                                 "generate Sudoku puzzles.")
    sub = parser.add_subparsers(dest="command", required=True)

    p_solve = sub.add_parser("solve", help="solve a puzzle")
    p_solve.add_argument("puzzle", help="81-char puzzle string "
                                        "(digits, '.' or '0' for empty)")

    p_val = sub.add_parser("validate", help="check a puzzle's givens")
    p_val.add_argument("puzzle", help="81-char puzzle string")

    p_gen = sub.add_parser("generate", help="generate a new puzzle")
    p_gen.add_argument("--difficulty", default="medium",
                       choices=sorted(DIFFICULTY_CLUES))
    p_gen.add_argument("--seed", type=int, default=None)

    args = parser.parse_args(argv)

    if args.command == "generate":
        puzzle = generate(args.difficulty, seed=args.seed)
        print(f"# difficulty: {difficulty_of(puzzle)} "
              f"({sum(1 for v in puzzle if v != 0)} clues)")
        print("".join(str(v) if v else "." for v in puzzle))
        print()
        print(format_grid(puzzle))
        return 0

    try:
        grid = parse_grid(args.puzzle)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.command == "validate":
        print("valid" if is_valid(grid) else "invalid: givens conflict")
        return 0 if is_valid(grid) else 1

    solved = solve(grid)
    if solved is None:
        print("no solution", file=sys.stderr)
        return 1
    print(format_grid(solved))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
