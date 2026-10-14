"""Next-move hints with human-readable explanations for Sudoku players.

`hint(cells)` inspects a partial board and returns the single most
instructive move, in the order a human teacher would try:

  1. Naked single -- an empty cell with exactly one candidate left.
  2. Hidden single -- a digit that can go in only one cell of some row,
     column, or box (that cell may still have other candidates).
  3. Guess (MRV) -- no forced move exists, so suggest the empty cell with
     the fewest candidates: the smallest branching factor for a trial.

Returns a `Hint` (0-based row/col, the forced `value` or None, `technique`,
and a plain-English `explanation`), or None when the board is already
solved, inconsistent, or at a dead end (an empty cell with zero
candidates -- no hint can rescue that).
"""

from __future__ import annotations

from dataclasses import dataclass

from .board import UNITS, is_consistent
from .solver import _bit, _candidates_from_scratch, _popcount


@dataclass
class Hint:
    row: int                 # 0-based
    col: int                 # 0-based
    value: int | None        # the forced digit, or None for a guess
    technique: str           # "naked single" | "hidden single" | "guess (MRV)"
    candidates: tuple[int, ...]  # candidates at the hinted cell
    explanation: str


def _unit_name(unit_no: int) -> str:
    if unit_no < 9:
        return f"row {unit_no + 1}"
    if unit_no < 18:
        return f"column {unit_no - 8}"
    return f"box {unit_no - 17}"


def _cell_name(i: int) -> str:
    return f"r{i // 9 + 1}c{i % 9 + 1}"


def hint(cells: list[int]) -> Hint | None:
    """Return the best next move for this board, or None if there isn't one."""
    if not is_consistent(cells):
        return None
    empties = [i for i in range(81) if cells[i] == 0]
    if not empties:
        return None  # already solved
    cands = _candidates_from_scratch(cells)
    if any(cands[i] == 0 for i in empties):
        return None  # dead end: some empty cell has no legal digit

    # 1. Naked singles: exactly one candidate left in the cell.
    for i in empties:
        if _popcount(cands[i]) == 1:
            v = cands[i].bit_length() - 1
            return Hint(
                row=i // 9, col=i % 9, value=v, technique="naked single",
                candidates=(v,),
                explanation=(
                    f"Naked single: {_cell_name(i)} must be {v} -- it is the "
                    f"only candidate left in that cell."
                ),
            )

    # 2. Hidden singles: a digit that fits in exactly one cell of a unit.
    for unit_no, unit in enumerate(UNITS):
        empt = [i for i in unit if cells[i] == 0]
        for v in range(1, 10):
            bit = _bit(v)
            if any(cells[i] == v for i in unit):
                continue
            spots = [i for i in empt if cands[i] & bit]
            if len(spots) == 1:
                i = spots[0]
                others = sorted(d for d in range(1, 10)
                                if d != v and cands[i] & _bit(d))
                extra = (f" (Its other candidates {others} get ruled out by "
                         f"the surrounding cells as you keep solving.)"
                         if others else "")
                return Hint(
                    row=i // 9, col=i % 9, value=v,
                    technique="hidden single",
                    candidates=tuple(sorted(
                        d for d in range(1, 10) if cands[i] & _bit(d))),
                    explanation=(
                        f"Hidden single: {v} can only go in {_cell_name(i)} "
                        f"within {_unit_name(unit_no)} -- every other empty "
                        f"cell there already rules it out.{extra}"
                    ),
                )

    # 3. No forced move: guess at the most constrained cell (MRV).
    best = min(empties, key=lambda i: (_popcount(cands[i]), i))
    vals = tuple(d for d in range(1, 10) if cands[best] & _bit(d))
    return Hint(
        row=best // 9, col=best % 9, value=None, technique="guess (MRV)",
        candidates=vals,
        explanation=(
            f"No forced move: try {_cell_name(best)} first -- with the "
            f"fewest candidates {list(vals)}, guessing there branches the "
            f"least."
        ),
    )
