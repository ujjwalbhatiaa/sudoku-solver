# sudoku-solver

Solve, validate, and generate Sudoku puzzles in pure Python — no dependencies.

## Usage

```bash
# Solve a puzzle (81 chars: digits, '.' or '0' for empty cells)
python sudoku.py solve "530070000600195000098000060800060003400803001700020006060000280000419005000080079"

# Validate a puzzle's givens
python sudoku.py validate "550070000600195000098000060800060003400803001700020006060000280000419005000080079"

# Generate a new puzzle with a guaranteed unique solution
python sudoku.py generate --difficulty medium
python sudoku.py generate --difficulty hard --seed 7
```

## How it works

- **Solver**: backtracking search with the minimum-remaining-values (MRV)
  heuristic and naked-single constraint propagation. Solves even notoriously
  hard puzzles (e.g. Arto Inkala's "AI Escargot") in well under a second.
- **Generator**: fills a complete grid with randomized backtracking, then digs
  holes while the puzzle keeps exactly one solution (checked by counting
  solutions capped at 2). Difficulty targets: easy 40, medium 32, hard 27 clues.
- **Validation**: rejects puzzles whose givens violate any row, column, or
  3×3 box constraint before searching.

## API

```python
from sudoku import parse_grid, solve, generate, is_valid, format_grid

puzzle = generate("medium", seed=42)
solution = solve(puzzle)
print(format_grid(solution))
```

## Tests

```bash
pytest
```

16 tests: parsing, validation, solving (easy + AI Escargot), uniqueness
counting, generation across difficulties, and edge cases.
