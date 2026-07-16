"""Sudoku solver: constraint propagation + backtracking with MRV.

Design:
- Each empty cell tracks a `candidates` bitmask (bits 1-9) of values not yet
  ruled out by its row/col/box peers.
- Constraint propagation does three passes to a fixed point before any
  guessing:
    1. Naked singles: a cell with exactly one candidate -> forced.
    2. Hidden singles: a unit where a value fits in only one remaining cell
       -> forced there even if that cell has other candidates too.
    3. Naked pairs: two cells in a unit sharing an identical 2-candidate set
       -> those two values are eliminated from every other cell in the unit.
  This alone solves "easy"/"medium" puzzles with zero backtracking, which is
  also how the difficulty rater in generator.py decides a puzzle is easy.
  Naked pairs was added specifically to shrink candidate sets on puzzles
  that naked+hidden singles alone can't fully crack, reducing how much the
  backtracker has to search on "medium"/"hard" tiers (see README).
- Backtracking picks the empty cell with the Minimum Remaining Values (MRV)
  -- fewest candidates -- which prunes the search tree far more aggressively
  than picking cells in row-major order, and is the standard technique for
  this problem (same idea as variable ordering in general CSP solving).
- `count_solutions(..., limit=2)` reuses the same search but stops as soon as
  it finds `limit` solutions -- used by the generator to confirm a puzzle has
  exactly one solution without paying for an exhaustive search.
"""

from __future__ import annotations

from .board import PEERS, is_consistent

FULL_MASK = 0b1111111110  # bits 1..9 set, bit 0 unused


def _popcount(x: int) -> int:
    return bin(x).count("1")


def _bit(v: int) -> int:
    return 1 << v


def _candidates_from_scratch(cells: list[int]) -> list[int]:
    """Compute the candidate bitmask for every empty cell from the current board."""
    cands = [0] * 81
    for i in range(81):
        if cells[i] != 0:
            continue
        used = 0
        for p in PEERS[i]:
            if cells[p] != 0:
                used |= _bit(cells[p])
        cands[i] = FULL_MASK & ~used
    return cands


def _propagate(cells: list[int], cands: list[int]) -> bool:
    """Apply naked-singles + hidden-singles to a fixed point.

    Mutates `cells` and `cands` in place. Returns False if a contradiction is
    found (some empty cell has zero candidates, or a unit can't place some
    value anywhere) -- meaning the current partial assignment is a dead end.
    """
    from .board import UNITS

    changed = True
    while changed:
        changed = False

        # Naked singles.
        for i in range(81):
            if cells[i] != 0:
                continue
            c = cands[i]
            if c == 0:
                return False
            if _popcount(c) == 1:
                v = c.bit_length() - 1
                cells[i] = v
                cands[i] = 0
                for p in PEERS[i]:
                    if cells[p] == 0 and (cands[p] & _bit(v)):
                        cands[p] &= ~_bit(v)
                changed = True

        # Hidden singles: for each unit, a value that appears in exactly one
        # cell's candidate set among the unit's empty cells must go there.
        for unit in UNITS:
            empties = [i for i in unit if cells[i] == 0]
            for v in range(1, 10):
                bit = _bit(v)
                spots = [i for i in empties if cands[i] & bit]
                if len(spots) == 0:
                    # Only a genuine contradiction if v isn't already placed
                    # elsewhere in the unit.
                    if not any(cells[i] == v for i in unit):
                        return False
                elif len(spots) == 1:
                    i = spots[0]
                    if cands[i] != bit:
                        cands[i] = bit
                        changed = True

        # Naked pairs: if two cells in the same unit both have exactly the
        # same 2 candidates, neither cell can end up as anything else, which
        # means no *other* cell in that unit can hold either of those two
        # values either. Eliminating them shrinks candidate sets elsewhere in
        # the unit, which can in turn trigger more naked/hidden singles on
        # the next pass. This is the one advanced technique the solver
        # previously lacked (see README "Known limitations").
        for unit in UNITS:
            empties = [i for i in unit if cells[i] == 0]
            pair_cells = [i for i in empties if _popcount(cands[i]) == 2]
            for a_idx in range(len(pair_cells)):
                a = pair_cells[a_idx]
                for b in pair_cells[a_idx + 1:]:
                    if cands[a] != cands[b]:
                        continue
                    pair_mask = cands[a]
                    for i in empties:
                        if i == a or i == b:
                            continue
                        if cands[i] & pair_mask:
                            cands[i] &= ~pair_mask
                            changed = True

    return True


def _search(cells: list[int], cands: list[int], limit: int, count: list[int], solutions: list[list[int]] | None) -> None:
    """Backtracking search with MRV. Appends completed boards to `solutions`
    (if provided) and increments count[0] for each one found, stopping once
    count[0] reaches `limit`."""
    if count[0] >= limit:
        return

    # Copy-on-write propagation at this node.
    work_cells = cells[:]
    work_cands = cands[:]
    if not _propagate(work_cells, work_cands):
        return

    # Find MRV empty cell.
    best_i, best_n = -1, 10
    for i in range(81):
        if work_cells[i] == 0:
            n = _popcount(work_cands[i])
            if n < best_n:
                best_i, best_n = i, n
                if n <= 1:
                    break

    if best_i == -1:
        # No empty cells left -> solved.
        count[0] += 1
        if solutions is not None:
            solutions.append(work_cells[:])
        return

    if best_n == 0:
        return  # dead end

    for v in range(1, 10):
        if not (work_cands[best_i] & _bit(v)):
            continue
        next_cells = work_cells[:]
        next_cands = work_cands[:]
        next_cells[best_i] = v
        next_cands[best_i] = 0
        for p in PEERS[best_i]:
            next_cands[p] &= ~_bit(v)
        _search(next_cells, next_cands, limit, count, solutions)
        if count[0] >= limit:
            return


def solve(cells: list[int]) -> list[int] | None:
    """Return a solved board, or None if unsolvable. If multiple solutions
    exist, returns one of them (undefined which)."""
    if not is_consistent(cells):
        return None
    cands = _candidates_from_scratch(cells)
    solutions: list[list[int]] = []
    count = [0]
    _search(cells, cands, limit=1, count=count, solutions=solutions)
    return solutions[0] if solutions else None


def count_solutions(cells: list[int], limit: int = 2) -> int:
    """Count solutions up to `limit` (default 2, i.e. just enough to know if
    the puzzle is uniquely solvable). Used by the generator."""
    if not is_consistent(cells):
        return 0
    cands = _candidates_from_scratch(cells)
    count = [0]
    _search(cells, cands, limit=limit, count=count, solutions=None)
    return count[0]


def solved_by_propagation_alone(cells: list[int]) -> bool:
    """True if naked+hidden singles alone (no guessing) solve the puzzle.
    Used by the generator's difficulty rater: puzzles solvable this way are
    'easy'; puzzles that need backtracking are harder."""
    work_cells = cells[:]
    work_cands = _candidates_from_scratch(work_cells)
    if not _propagate(work_cells, work_cands):
        return False
    return all(v != 0 for v in work_cells)
