*This project has been created as part of the 42 curriculum by gustde-s.*

# A-Maze-ing — This is the way

## Description

**A-Maze-ing** is a modular, strictly typed Python maze generator, solver, and interactive terminal visualizer built for the 42 curriculum. Given a configuration file, the program generates either:

- **Perfect Mazes (`PERFECT=True`)**: Spanning-tree labyrinths with a unique path between any two cells and zero loops.
- **Pac-Man Playable Boards (`PERFECT=False`)**: Braided mazes with open corners and center corridors, multiple independent routes (loops), no dead-ends (except the two structural pockets inside the `'2'` of the central `"42"` emblem), and zero forbidden `3x3` open rooms.

Every generated maze embeds a visible `"42"` pattern made of fully closed cells (`0xF`) at its center (automatically omitted with a console warning when grid dimensions are smaller than `9x7`), computes the optimal shortest path from `ENTRY` to `EXIT` via Breadth-First Search (BFS), exports the result in the required hexadecimal format, and launches an interactive ANSI/Unicode terminal interface.

---

## Instructions

### Prerequisites

- **Python 3.10+** (uses only the Python standard library at runtime).
- Optional development tools for linting and packaging: `flake8`, `mypy`, `pytest`, `build`.

### Installation & Setup

```bash
# Install development dependencies and the editable mazegen package
make install
```

### Execution

```bash
# Run with the default configuration file (config.txt)
python3 a_maze_ing.py config.txt
# or via Makefile:
make run
```

### Makefile Targets

| Target | Description |
| :--- | :--- |
| `make install` | Install package and development dependencies (`flake8`, `mypy`, `build`). |
| `make run` | Run `python3 a_maze_ing.py config.txt`. |
| `make debug` | Run the main script inside Python's interactive debugger (`pdb`). |
| `make test` | Run the `unittest` test suite under `tests/`. |
| `make lint` | Run `flake8 .` and `mypy .` with the mandatory subject flags. |
| `make lint-strict` | Run `flake8 .` and `mypy . --strict`. |
| `make build` | Rebuild `mazegen-1.0.0-py3-none-any.whl` and `mazegen-1.0.0.tar.gz` at the repo root. |
| `make clean` | Remove `__pycache__`, `.mypy_cache`, build directories, and temporary caches. |

---

## Configuration File Format

The configuration file consists of `KEY=VALUE` pairs (one per line). Empty lines and lines starting with `#` are ignored.

```ini
# Mandatory keys
WIDTH=20
HEIGHT=15
ENTRY=0,0
EXIT=19,14
OUTPUT_FILE=maze.txt
PERFECT=True

# Optional keys
SEED=42
ALGORITHM=dfs
```

| Key | Required | Type / Format | Description |
| :--- | :---: | :--- | :--- |
| `WIDTH` | Yes | `int >= 2` | Number of columns in the maze grid. |
| `HEIGHT` | Yes | `int >= 2` | Number of rows in the maze grid. |
| `ENTRY` | Yes | `x,y` | 0-indexed coordinates of the starting cell. |
| `EXIT` | Yes | `x,y` | 0-indexed coordinates of the exit cell (must differ from `ENTRY`). |
| `OUTPUT_FILE` | Yes | `str` | Path where the hexadecimal maze and shortest path are written. |
| `PERFECT` | Yes | `True` / `False` | `True` for a spanning-tree perfect maze; `False` for a braided Pac-Man board. |
| `SEED` | No | `int` | Seed for deterministic, reproducible random generation. |
| `ALGORITHM` | No | `dfs` \| `prim` | Primary spanning-tree algorithm (`dfs` default, or `prim`). |

---

## Maze Generation Algorithms & Technical Choices

1. **4-Bit Bitmask Cell Representation (`Direction` IntFlag)**:
   - Each cell stores a 4-bit integer (`0..15` / `0x0..0xF`): `NORTH = 1` (bit 0), `EAST = 2` (bit 1), `SOUTH = 4` (bit 2), `WEST = 8` (bit 3).
   - Closed walls set the bit to `1`; open passages clear the bit to `0`.
   - `MazeGrid.remove_wall` and `MazeGrid.add_wall` atomically update both the target cell and its neighbor (`direction.opposite`) to guarantee 100% wall coherence.
2. **Primary Generation — Iterative DFS Backtracker & Randomized Prim**:
   - **Why chosen**: Iterative Depth-First Search (Recursive Backtracker) produces long, winding corridors with high aesthetic quality and challenging dead-ends in `PERFECT=True` mode. We implemented it iteratively using an explicit stack (`list[Coordinate]`) rather than call-stack recursion to prevent `RecursionError` on large grids.
   - As an advanced feature (bonus), we also implemented **Randomized Prim's Algorithm** (`ALGORITHM=prim`), which branches radially from a frontier list and produces more organic, short-branch topologies.
3. **Non-Perfect Braiding (`BraidedPacModifier`)**:
   - When `PERFECT=False`, the modifier opens the four corners and center corridor, then iteratively eliminates dead-ends (`degree <= 1`) while checking `creates_open_2x2` and `creates_open_3x3` to guarantee corridors never form forbidden `3x3` open rooms.
4. **Shortest-Path Resolution (`BFSSolver`)**:
   - Uses Breadth-First Search with a `collections.deque` FIFO queue and a `parent_map` dictionary (`child -> (parent, direction)`), guaranteeing the minimum-step path in $O(V + E)$ time.

---

## Visual Representation & Interactive Menu

The terminal interface uses a 2D TrueColor half-block (`▀`) canvas providing
2x vertical resolution and zero gaps between elements.

Interactive menu options:
1. **Re-generate a new maze**: Generates a new random maze with fresh entropy.
2. **Show / Hide the shortest path**: Toggles the continuous BFS solution line.
3. **Rotate the wall colours**: Cycles through 4 TrueColor 24-bit themes.
4. **Toggle algorithm**: Switches dynamically between DFS Backtracker and Prim.
5. **Animate maze generation**: Real-time snake trail and backtracking animation.
6. **Animate solution path**: BFS wavefront propagation and path lighting.
7. **Play maze**: Interactive navigation with WASD and final route trace.
8. **Quit**: Cleanly exits the program.

---

## Reusable Module (`mazegen`) Documentation

The entire generation and solving engine is packaged as a standalone distribution (`mazegen-1.0.0-py3-none-any.whl` and `mazegen-1.0.0.tar.gz`) at the root of the repository.

### Installing in Another Project

```bash
pip install mazegen-1.0.0-py3-none-any.whl
```

### Basic Usage Example

```python
from mazegen import MazeGenerator

# 1. Instantiate with custom parameters (size, entry/exit, mode, seed, algorithm)
generator = MazeGenerator(
    width=20,
    height=15,
    entry=(0, 0),
    exit_coord=(19, 14),
    perfect=False,
    seed=42,
    algorithm="dfs",
)

# 2. Generate the maze and compute the shortest path
grid = generator.generate()

# 3. Access the generated structure
matrix: list[list[int]] = generator.get_matrix()      # 2D list of 0..15 bitmasks
hex_rows: list[str] = generator.get_hex_rows()        # Hex strings per row

# 4. Access the shortest path solution
print("Shortest path (NESW):", generator.solution_str)
print("Visited coordinates:", generator.solution_coordinates)

# 5. Optionally export to the standard output file format
generator.save("output_maze.txt")
```

---

## Team and Project Management

- **Team Roles**:
  - `gustde-s`: Software architecture, domain modeling, iterative generation/braiding algorithms, BFS solver, terminal ANSI renderer, packaging, and unit testing.
- **Planning & Evolution**:
  - *Phase 1*: Domain modeling (`Direction` bitmasks, `MazeConfig`, `Protocol` interfaces).
  - *Phase 2*: Core `MazeGrid` with `"42"` pattern masking, wall coherence, and `3x3` open-area detection.
  - *Phase 3*: Iterative `DFSBacktracker`, `PrimGenerator`, `BraidedPacModifier`, and `BFSSolver`.
  - *Phase 4*: Terminal visual renderer, interactive CLI loop, packaging (`pyproject.toml`), and unit tests.
- **What Worked Well & Possible Improvements**:
  - Separating `domain`, `core`, `algorithms`, and `cli` via `typing.Protocol` kept static typing (`mypy --strict`) clean and prevented circular imports.
  - Future improvements could include an optional graphical renderer using MiniLibX alongside the terminal renderer.
- **Tools Used**:
  - Python 3.10+, `unittest`, `flake8`, `mypy --strict`, `setuptools` / `wheel`, Git, and GNU Make.

---

## Resources & AI Usage

### Classic References

- Jamis Buck, *Mazes for Programmers: Code Your Own Twisty Little Passages* (Pragmatic Bookshelf, 2015) — Reference for Recursive Backtracker, Prim's algorithm, and braiding (dead-end removal).
- Cormen et al., *Introduction to Algorithms (CLRS)* — Graph representations, spanning trees, and Breadth-First Search shortest paths.
- Python 3 Documentation (`enum.IntFlag`, `typing.Protocol`, `collections.deque`, `dataclasses`).

### AI Usage Disclosure

AI assistance was used as a pair-programming mentor during development for:
- Reviewing Clean Architecture boundaries and `typing.Protocol` interfaces to ensure 100% `mypy --strict` compliance without `Any`.
- Verifying `flake8` formatting constraints (79-character line limits and PEP 257 docstrings).
- Designing edge-case unit tests in `tests/` (validating `"42"` pattern boundaries, `3x3` room prevention, and spanning-tree invariants).
All generated code and algorithms were reviewed, tested, and validated against the project specification.

