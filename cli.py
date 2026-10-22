#!/usr/bin/env python3
"""CLI for the Sudoku solver/generator.

Usage:
    python cli.py solve puzzle.txt
    python cli.py solve "53..7....6..195....98....6.8...6...34..8.3..17...2...6.6....28....419..5....8..79"
    python cli.py hint "53..7....6..195....98....6.8...6...34..8.3..17...2...6.6....28....419..5....8..79"
    python cli.py explain "53..7....6..195....98....6.8...6...34..8.3..17...2...6.6....28....419..5....8..79"
    python cli.py generate --difficulty medium
    python cli.py generate --difficulty hard --seed 42
"""

from __future__ import annotations

import argparse
import sys
import time
from collections import Counter

from sudoku.board import is_valid_complete, parse, pretty, to_string
from sudoku.explain import explain_solve
from sudoku.generator import generate_puzzle
from sudoku.hint import hint
from sudoku.solver import solve


def _load_puzzle(spec: str) -> list[int]:
    if spec.endswith(".txt") or "\n" not in spec and len(spec) != 81:
        try:
            with open(spec) as f:
                return parse(f.read())
        except FileNotFoundError:
            pass
    return parse(spec)


def cmd_solve(args: argparse.Namespace) -> int:
    if args.puzzle.endswith(".txt") or "\n" not in args.puzzle and len(args.puzzle) != 81:
        try:
            with open(args.puzzle) as f:
                text = f.read()
        except FileNotFoundError:
            text = args.puzzle
    else:
        text = args.puzzle

    cells = parse(text)
    print("Puzzle:")
    print(pretty(cells))
    print()

    start = time.perf_counter()
    result = solve(cells)
    elapsed = time.perf_counter() - start

    if result is None:
        print("No solution exists for this puzzle.")
        return 1

    print(f"Solved in {elapsed * 1000:.2f} ms:")
    print(pretty(result))
    assert is_valid_complete(result)
    return 0


def cmd_hint(args: argparse.Namespace) -> int:
    cells = _load_puzzle(args.puzzle)
    h = hint(cells)
    if h is None:
        print("No hint available: the board is solved, invalid, or stuck.")
        return 1
    print(h.explanation)
    print()
    print("Board:")
    print(pretty(cells))
    return 0


def cmd_explain(args: argparse.Namespace) -> int:
    cells = _load_puzzle(args.puzzle)
    try:
        steps = explain_solve(cells)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    if not steps:
        print("Already solved -- no steps needed.")
        return 0
    for s in steps:
        print(f"Step {s.number} [{s.technique}]: {s.explanation}")
    counts = Counter(s.technique for s in steps)
    summary = ", ".join(f"{n} {t}" for t, n in counts.most_common())
    print()
    print(f"Solved in {len(steps)} steps: {summary}.")
    return 0


def cmd_generate(args: argparse.Namespace) -> int:
    puzzle, solution, actual_difficulty = generate_puzzle(difficulty=args.difficulty, seed=args.seed)
    clues = sum(1 for v in puzzle if v != 0)

    print(f"Generated puzzle (requested={args.difficulty}, rated={actual_difficulty}, clues={clues}):")
    print(pretty(puzzle))
    print()
    print("Compact string:", to_string(puzzle))

    if args.show_solution:
        print()
        print("Solution:")
        print(pretty(solution))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Sudoku solver & puzzle generator")
    sub = parser.add_subparsers(dest="command", required=True)

    p_solve = sub.add_parser("solve", help="solve a puzzle from a file or inline string")
    p_solve.add_argument("puzzle", help="path to a .txt puzzle file, or an inline 81-char/9-line puzzle")
    p_solve.set_defaults(func=cmd_solve)

    p_hint = sub.add_parser("hint", help="suggest the next move, with an explanation")
    p_hint.add_argument("puzzle", help="path to a .txt puzzle file, or an inline 81-char/9-line puzzle")
    p_hint.set_defaults(func=cmd_hint)

    p_explain = sub.add_parser("explain", help="print the full step-by-step solution")
    p_explain.add_argument("puzzle", help="path to a .txt puzzle file, or an inline 81-char/9-line puzzle")
    p_explain.set_defaults(func=cmd_explain)

    p_gen = sub.add_parser("generate", help="generate a new puzzle")
    p_gen.add_argument("--difficulty", choices=["easy", "medium", "hard", "expert"], default="medium")
    p_gen.add_argument("--seed", type=int, default=None, help="RNG seed for reproducible generation")
    p_gen.add_argument("--show-solution", action="store_true")
    p_gen.set_defaults(func=cmd_generate)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
