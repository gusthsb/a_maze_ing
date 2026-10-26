"""Domain types, enumerations, data structures, and exceptions for A-Maze-ing.

This module defines the fundamental building blocks used across the maze
generator and solver, including bitmask wall directions, coordinates,
immutable configuration, and custom domain exceptions.
"""

from dataclasses import dataclass
from enum import IntFlag
from typing import TypeAlias

Coordinate: TypeAlias = tuple[int, int]


class Direction(IntFlag):
    """Bitmask flags representing the four cardinal directions and walls.

    According to the A-Maze-ing specification:
    - Bit 0 (LSB, value 1): North
    - Bit 1 (value 2): East
    - Bit 2 (value 4): South
    - Bit 3 (value 8): West

    A closed wall has its bit set to 1; an open passage has its bit set to 0.
    """

    NONE = 0
    NORTH = 1 << 0  # 1 (0b0001)
    EAST = 1 << 1   # 2 (0b0010)
    SOUTH = 1 << 2  # 4 (0b0100)
    WEST = 1 << 3   # 8 (0b1000)
    ALL = NORTH | EAST | SOUTH | WEST  # 15 (0b1111 / 0xF)

    @property
    def opposite(self) -> "Direction":
        """Return the opposite cardinal direction.

        Returns:
            Direction: The opposite direction (e.g., NORTH -> SOUTH).

        Raises:
            ValueError: If called on a composite or NONE flag.
        """
        opposites: dict[Direction, Direction] = {
            Direction.NORTH: Direction.SOUTH,
            Direction.SOUTH: Direction.NORTH,
            Direction.EAST: Direction.WEST,
            Direction.WEST: Direction.EAST,
        }
        if self not in opposites:
            raise ValueError(f"Direction {self!r} has no single opposite.")
        return opposites[self]

    @property
    def delta(self) -> Coordinate:
        """Return the (dx, dy) coordinate offset for a single direction.

        Returns:
            Coordinate: A (dx, dy) tuple where x increases East and
                y increases South.

        Raises:
            ValueError: If called on a composite or NONE flag.
        """
        deltas: dict[Direction, Coordinate] = {
            Direction.NORTH: (0, -1),
            Direction.EAST: (1, 0),
            Direction.SOUTH: (0, 1),
            Direction.WEST: (-1, 0),
        }
        if self not in deltas:
            raise ValueError(f"Direction {self!r} has no single delta.")
        return deltas[self]

    @property
    def char(self) -> str:
        """Return the single-character representation ('N', 'E', 'S', 'W').

        Returns:
            str: Cardinal letter used in the output file solution path.

        Raises:
            ValueError: If called on a composite or NONE flag.
        """
        chars: dict[Direction, str] = {
            Direction.NORTH: "N",
            Direction.EAST: "E",
            Direction.SOUTH: "S",
            Direction.WEST: "W",
        }
        if self not in chars:
            raise ValueError(f"Direction {self!r} has no single character.")
        return chars[self]

    @classmethod
    def cardinals(cls) -> tuple["Direction", ...]:
        """Return all four primary cardinal directions in clockwise order.

        Returns:
            tuple[Direction, ...]: (NORTH, EAST, SOUTH, WEST).
        """
        return (cls.NORTH, cls.EAST, cls.SOUTH, cls.WEST)


@dataclass(frozen=True)
class MazeConfig:
    """Immutable configuration parameters for maze generation.

    Attributes:
        width: Maze width in number of cells (columns).
        height: Maze height in number of cells (rows).
        entry: Entry cell coordinates as (x, y).
        exit: Exit cell coordinates as (x, y).
        output_file: Path to the output file where the maze is serialized.
        perfect: True for a perfect maze (single path, no loops),
            False for a Pac-Man-like braided board with loops.
        seed: Optional integer seed for reproducible random generation.
        algorithm: Name of the primary generation algorithm ('dfs' or 'prim').
    """

    width: int
    height: int
    entry: Coordinate
    exit: Coordinate
    output_file: str
    perfect: bool = False
    seed: int | None = None
    algorithm: str = "dfs"


class MazeError(Exception):
    """Base exception for all domain errors in A-Maze-ing."""


class ConfigError(MazeError):
    """Raised when the configuration file or parameters are invalid."""


class GenerationError(MazeError):
    """Raised when maze generation fails or encounters invalid constraints."""


class SolverError(MazeError):
    """Raised when no valid path can be found between entry and exit."""
