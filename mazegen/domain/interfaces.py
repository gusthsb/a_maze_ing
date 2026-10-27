"""Domain interfaces and protocols for A-Maze-ing.

This module defines the structural contracts (Protocols) for the maze grid,
generation algorithms, and pathfinding solvers to ensure loose coupling and
strict static typing without circular imports.
"""

from collections.abc import Callable
from random import Random
from typing import Protocol, TypeAlias

from mazegen.domain.types import Coordinate, Direction

StepCallback: TypeAlias = Callable[
    ["GridProtocol", Coordinate, list[Coordinate]], None
]
SolveStepCallback: TypeAlias = Callable[[Coordinate, set[Coordinate]], None]


class GridProtocol(Protocol):
    """Structural interface representing the 2D maze grid."""

    @property
    def width(self) -> int:
        """Return the number of columns in the grid."""
        ...

    @property
    def height(self) -> int:
        """Return the number of rows in the grid."""
        ...

    @property
    def entry(self) -> Coordinate:
        """Return the (x, y) entry coordinate."""
        ...

    @property
    def exit(self) -> Coordinate:
        """Return the (x, y) exit coordinate."""
        ...

    @property
    def masked_cells(self) -> frozenset[Coordinate]:
        """Return coordinates reserved for the '42' pattern."""
        ...

    def in_bounds(self, coord: Coordinate) -> bool:
        """Check whether a coordinate lies within the grid boundaries."""
        ...

    def is_masked(self, coord: Coordinate) -> bool:
        """Check whether a coordinate belongs to the closed '42' pattern."""
        ...

    def get_walls(self, coord: Coordinate) -> int:
        """Return the 4-bit wall bitmask (0..15) for the given coordinate."""
        ...

    def has_wall(self, coord: Coordinate, direction: Direction) -> bool:
        """Return True if the wall in the given direction is closed."""
        ...

    def remove_wall(self, coord: Coordinate, direction: Direction) -> None:
        """Open the passage between coord and its neighbor in direction."""
        ...

    def neighbors(
        self,
        coord: Coordinate,
    ) -> list[tuple[Direction, Coordinate]]:
        """Return all in-bounds, non-masked (direction, neighbor) pairs."""
        ...

    def accessible_neighbors(
        self,
        coord: Coordinate,
    ) -> list[tuple[Direction, Coordinate]]:
        """Return neighbors reachable from coord through open passages."""
        ...

    def creates_open_2x2(
        self,
        coord: Coordinate,
        direction: Direction,
    ) -> bool:
        """Check if removing a wall would create a 2x2 fully open block."""
        ...

    def creates_open_3x3(
        self,
        coord: Coordinate,
        direction: Direction,
    ) -> bool:
        """Check if removing a wall would create a forbidden 3x3 open area."""
        ...


class GenerationStrategy(Protocol):
    """Interface for maze generation and topology modification algorithms."""

    def generate(
        self,
        grid: GridProtocol,
        rng: Random,
        step_callback: StepCallback | None = None,
    ) -> None:
        """Mutate the provided grid in-place to construct the maze topology.

        Args:
            grid: The maze grid instance to carve passages into.
            rng: Seeded random number generator for reproducibility.
            step_callback: Optional callback invoked after each carving step.
        """
        ...


class SolverStrategy(Protocol):
    """Interface for maze pathfinding algorithms."""

    def solve(
        self,
        grid: GridProtocol,
        step_callback: SolveStepCallback | None = None,
    ) -> list[Direction]:
        """Compute the shortest path from grid.entry to grid.exit.

        Args:
            grid: The generated maze grid to solve.
            step_callback: Optional callback invoked during wavefront search.

        Returns:
            list[Direction]: Ordered sequence of steps from entry to exit.
        """
        ...
