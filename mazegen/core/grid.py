"""Core 2D maze grid representation with bitmask walls and '42' mask.

This module implements the MazeGrid class, enforcing wall coherence between
adjacent cells, external boundary walls, the central '42' closed-cell
pattern, and detection of forbidden 3x3 open areas.
"""

import sys
from mazegen.domain.types import (
    ConfigError,
    Coordinate,
    Direction,
    GenerationError,
)

PATTERN_42_WIDTH: int = 7
PATTERN_42_HEIGHT: int = 5
MIN_WIDTH_FOR_42: int = 9
MIN_HEIGHT_FOR_42: int = 7

# Relative (dx, dy) offsets forming the 7x5 "42" pattern of closed cells.
PATTERN_42_OFFSETS: tuple[Coordinate, ...] = (
    # Digit '4' (columns 0..2, rows 0..4)
    (0, 0),
    (0, 1),
    (0, 2),
    (1, 2),
    (2, 2),
    (2, 3),
    (2, 4),
    # Digit '2' (columns 4..6, rows 0..4)
    (4, 0),
    (5, 0),
    (6, 0),
    (6, 1),
    (4, 2),
    (5, 2),
    (6, 2),
    (4, 3),
    (4, 4),
    (5, 4),
    (6, 4),
)


class MazeGrid:
    """Represent a 2D grid of maze cells encoded as 4-bit wall bitmasks.

    Each cell stores an integer in 0..15 where set bits (1) indicate closed
    walls (NORTH=1, EAST=2, SOUTH=4, WEST=8) and cleared bits (0) indicate
    open passages.
    """

    def __init__(
        self,
        width: int,
        height: int,
        entry: Coordinate,
        exit_coord: Coordinate,
        apply_42_pattern: bool = True,
    ) -> None:
        """Initialize a fully closed grid and apply the '42' pattern if able.

        Args:
            width: Number of columns (must be >= 2).
            height: Number of rows (must be >= 2).
            entry: Starting cell (x, y) coordinate.
            exit_coord: Target cell (x, y) coordinate.
            apply_42_pattern: Whether to embed the central '42' pattern.

        Raises:
            ConfigError: If dimensions or entry/exit coordinates are invalid.
        """
        if width < 2 or height < 2:
            raise ConfigError(
                f"Grid dimensions must be at least 2x2, got {width}x{height}."
            )
        self._width: int = width
        self._height: int = height
        self._entry: Coordinate = entry
        self._exit: Coordinate = exit_coord

        if not self.in_bounds(entry):
            raise ConfigError(
                f"ENTRY {entry} is outside grid bounds ({width}x{height})."
            )
        if not self.in_bounds(exit_coord):
            raise ConfigError(
                f"EXIT {exit_coord} is outside grid bounds ({width}x{height})."
            )
        if entry == exit_coord:
            raise ConfigError(
                f"ENTRY and EXIT must be distinct, both are {entry}."
            )

        self._cells: list[list[int]] = [
            [int(Direction.ALL) for _ in range(width)]
            for _ in range(height)
        ]
        self._masked_cells: frozenset[Coordinate] = frozenset()

        if apply_42_pattern:
            self._init_42_pattern()

    def _init_42_pattern(self) -> None:
        """Compute and lock the central '42' pattern cells if size permits.

        Raises:
            ConfigError: If entry or exit overlaps with the '42' pattern.
        """
        if (
            self._width < MIN_WIDTH_FOR_42
            or self._height < MIN_HEIGHT_FOR_42
        ):
            print(
                f"Warning: Maze size ({self._width}x{self._height}) is too "
                f"small for the '42' pattern (minimum "
                f"{MIN_WIDTH_FOR_42}x{MIN_HEIGHT_FOR_42}). Omitting pattern.",
                file=sys.stderr,
            )
            return

        x0: int = (self._width - PATTERN_42_WIDTH) // 2
        y0: int = (self._height - PATTERN_42_HEIGHT) // 2
        masked: set[Coordinate] = {
            (x0 + dx, y0 + dy) for dx, dy in PATTERN_42_OFFSETS
        }

        if self._entry in masked:
            raise ConfigError(
                f"ENTRY {self._entry} overlaps with the '42' pattern."
            )
        if self._exit in masked:
            raise ConfigError(
                f"EXIT {self._exit} overlaps with the '42' pattern."
            )

        self._masked_cells = frozenset(masked)

    @property
    def width(self) -> int:
        """Return the number of columns in the grid."""
        return self._width

    @property
    def height(self) -> int:
        """Return the number of rows in the grid."""
        return self._height

    @property
    def entry(self) -> Coordinate:
        """Return the (x, y) entry coordinate."""
        return self._entry

    @property
    def exit(self) -> Coordinate:
        """Return the (x, y) exit coordinate."""
        return self._exit

    @property
    def masked_cells(self) -> frozenset[Coordinate]:
        """Return the set of coordinates belonging to the '42' pattern."""
        return self._masked_cells

    def in_bounds(self, coord: Coordinate) -> bool:
        """Check whether a coordinate lies within the grid boundaries.

        Args:
            coord: The (x, y) coordinate to check.

        Returns:
            bool: True if 0 <= x < width and 0 <= y < height.
        """
        x, y = coord
        return 0 <= x < self._width and 0 <= y < self._height

    def is_masked(self, coord: Coordinate) -> bool:
        """Check whether a coordinate belongs to the closed '42' pattern.

        Args:
            coord: The (x, y) coordinate to check.

        Returns:
            bool: True if the cell is part of the '42' pattern.
        """
        return coord in self._masked_cells

    def get_walls(self, coord: Coordinate) -> int:
        """Return the 4-bit wall bitmask (0..15) for the given coordinate.

        Args:
            coord: Cell (x, y) coordinate.

        Returns:
            int: Integer bitmask of closed walls.

        Raises:
            GenerationError: If coord is out of bounds.
        """
        if not self.in_bounds(coord):
            raise GenerationError(f"Coordinate {coord} is out of bounds.")
        x, y = coord
        return self._cells[y][x]

    def has_wall(self, coord: Coordinate, direction: Direction) -> bool:
        """Return True if the wall in the given direction is closed.

        Args:
            coord: Cell (x, y) coordinate.
            direction: Cardinal direction to inspect.

        Returns:
            bool: True if the wall bit is set (closed).
        """
        return bool(self.get_walls(coord) & int(direction))

    def neighbor_coord(
        self,
        coord: Coordinate,
        direction: Direction,
    ) -> Coordinate:
        """Compute the adjacent coordinate in the specified direction.

        Args:
            coord: Starting (x, y) coordinate.
            direction: Cardinal direction to step toward.

        Returns:
            Coordinate: The resulting (x + dx, y + dy) coordinate.
        """
        dx, dy = direction.delta
        return (coord[0] + dx, coord[1] + dy)

    def remove_wall(self, coord: Coordinate, direction: Direction) -> None:
        """Open the passage between coord and its neighbor in direction.

        Updates both cells symmetrically to preserve wall coherence.
        Refuses to remove external border walls or walls of masked '42' cells.

        Args:
            coord: Source cell (x, y) coordinate.
            direction: Cardinal direction of the wall to open.

        Raises:
            GenerationError: If the wall cannot be legally removed.
        """
        neighbor: Coordinate = self.neighbor_coord(coord, direction)
        if not self.in_bounds(coord) or not self.in_bounds(neighbor):
            raise GenerationError(
                f"Cannot remove border wall from {coord} toward {direction}."
            )
        if self.is_masked(coord) or self.is_masked(neighbor):
            raise GenerationError(
                f"Cannot remove wall involving '42' pattern cell {coord}."
            )
        x, y = coord
        nx, ny = neighbor
        self._cells[y][x] &= ~int(direction)
        self._cells[ny][nx] &= ~int(direction.opposite)

    def add_wall(self, coord: Coordinate, direction: Direction) -> None:
        """Close the wall between coord and its neighbor in direction.

        Args:
            coord: Source cell (x, y) coordinate.
            direction: Cardinal direction of the wall to close.

        Raises:
            GenerationError: If coord is out of bounds.
        """
        if not self.in_bounds(coord):
            raise GenerationError(f"Coordinate {coord} is out of bounds.")
        x, y = coord
        self._cells[y][x] |= int(direction)
        neighbor: Coordinate = self.neighbor_coord(coord, direction)
        if self.in_bounds(neighbor):
            nx, ny = neighbor
            self._cells[ny][nx] |= int(direction.opposite)

    def neighbors(
        self,
        coord: Coordinate,
    ) -> list[tuple[Direction, Coordinate]]:
        """Return all in-bounds, non-masked (direction, neighbor) pairs.

        Args:
            coord: Cell (x, y) coordinate.

        Returns:
            list[tuple[Direction, Coordinate]]: Valid adjacent cells.
        """
        result: list[tuple[Direction, Coordinate]] = []
        for direction in Direction.cardinals():
            target: Coordinate = self.neighbor_coord(coord, direction)
            if self.in_bounds(target) and not self.is_masked(target):
                result.append((direction, target))
        return result

    def accessible_neighbors(
        self,
        coord: Coordinate,
    ) -> list[tuple[Direction, Coordinate]]:
        """Return neighbors reachable from coord through open passages.

        Args:
            coord: Cell (x, y) coordinate.

        Returns:
            list[tuple[Direction, Coordinate]]: Connected adjacent cells.
        """
        result: list[tuple[Direction, Coordinate]] = []
        for direction, target in self.neighbors(coord):
            if not self.has_wall(coord, direction):
                result.append((direction, target))
        return result

    def creates_open_2x2(
        self,
        coord: Coordinate,
        direction: Direction,
    ) -> bool:
        """Check if removing a wall would create a 2x2 fully open block.

        Args:
            coord: Source cell (x, y) coordinate.
            direction: Wall direction candidate for removal.

        Returns:
            bool: True if removing the wall creates a 2x2 open room.
        """
        neighbor: Coordinate = self.neighbor_coord(coord, direction)
        if not self.in_bounds(neighbor) or self.is_masked(neighbor):
            return False

        self.remove_wall(coord, direction)
        try:
            x, y = coord
            for bx in range(max(0, x - 1), min(self._width - 1, x + 1)):
                for by in range(max(0, y - 1), min(self._height - 1, y + 1)):
                    if self._is_block_open(bx, by, 2):
                        return True
            return False
        finally:
            self.add_wall(coord, direction)

    def creates_open_3x3(
        self,
        coord: Coordinate,
        direction: Direction,
    ) -> bool:
        """Check if removing a wall would create a forbidden 3x3 open area.

        Args:
            coord: Source cell (x, y) coordinate.
            direction: Wall direction candidate for removal.

        Returns:
            bool: True if removing the wall creates an open 3x3 area.
        """
        neighbor: Coordinate = self.neighbor_coord(coord, direction)
        if not self.in_bounds(neighbor) or self.is_masked(neighbor):
            return False

        self.remove_wall(coord, direction)
        try:
            x, y = coord
            for bx in range(max(0, x - 2), min(self._width - 2, x + 1)):
                for by in range(max(0, y - 2), min(self._height - 2, y + 1)):
                    if self._is_block_open(bx, by, 3):
                        return True
            return False
        finally:
            self.add_wall(coord, direction)

    def _is_block_open(self, bx: int, by: int, size: int) -> bool:
        """Check whether a square subgrid of given size has no internal walls.

        Args:
            bx: Top-left x coordinate of the square block.
            by: Top-left y coordinate of the square block.
            size: Side length of the square block (e.g., 2 or 3).

        Returns:
            bool: True if all internal walls inside the block are open.
        """
        for dy in range(size):
            for dx in range(size):
                cell: Coordinate = (bx + dx, by + dy)
                if self.is_masked(cell):
                    return False
                if dx < size - 1 and self.has_wall(cell, Direction.EAST):
                    return False
                if dy < size - 1 and self.has_wall(cell, Direction.SOUTH):
                    return False
        return True

    def to_matrix(self) -> list[list[int]]:
        """Return a deep copy of the 2D wall bitmask matrix.

        Returns:
            list[list[int]]: Copy of rows and columns of 4-bit wall integers.
        """
        return [row[:] for row in self._cells]
