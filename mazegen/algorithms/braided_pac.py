"""Pac-Man braided maze modifier for non-perfect mazes (PERFECT=False).

This module transforms a perfect spanning-tree maze into a braided,
Pac-Man-compatible board by opening corner and center corridors, removing
dead-ends to create loops, and preventing forbidden 3x3 open areas.
"""

from random import Random
from mazegen.domain.interfaces import GridProtocol
from mazegen.domain.types import Coordinate, Direction


class BraidedPacModifier:
    """Transform a spanning-tree maze into a braided Pac-Man board."""

    def generate(self, grid: GridProtocol, rng: Random) -> None:
        """Eliminate dead-ends and ensure multiple loops without 3x3 rooms.

        Args:
            grid: A connected maze grid to braid in-place.
            rng: Seeded random number generator for reproducibility.
        """
        self._open_corners_and_center(grid, rng)
        self._eliminate_dead_ends(grid, rng)
        self._ensure_minimum_loops(grid, rng, min_loops=2)

    def _open_corners_and_center(
        self,
        grid: GridProtocol,
        rng: Random,
    ) -> None:
        """Ensure the four corners and center cell are open corridors.

        Args:
            grid: The maze grid to modify.
            rng: Seeded random number generator.
        """
        w: int = grid.width
        h: int = grid.height
        key_cells: list[Coordinate] = [
            (0, 0),
            (w - 1, 0),
            (0, h - 1),
            (w - 1, h - 1),
            (w // 2, h // 2),
        ]

        for cell in key_cells:
            if not grid.in_bounds(cell) or grid.is_masked(cell):
                continue
            if len(grid.accessible_neighbors(cell)) < 2:
                self._open_best_wall(grid, cell, rng)

    def _eliminate_dead_ends(
        self,
        grid: GridProtocol,
        rng: Random,
    ) -> None:
        """Iteratively open closed walls on dead-end cells.

        Args:
            grid: The maze grid to modify.
            rng: Seeded random number generator.
        """
        for _ in range(2):
            dead_ends: list[Coordinate] = self._find_dead_ends(grid)
            if not dead_ends:
                break
            rng.shuffle(dead_ends)
            for cell in dead_ends:
                if len(grid.accessible_neighbors(cell)) <= 1:
                    self._open_best_wall(grid, cell, rng)

    def _find_dead_ends(self, grid: GridProtocol) -> list[Coordinate]:
        """Return all non-masked cells with at most one open passage.

        Args:
            grid: The maze grid to inspect.

        Returns:
            list[Coordinate]: Coordinates of current dead-end cells.
        """
        dead_ends: list[Coordinate] = []
        for y in range(grid.height):
            for x in range(grid.width):
                cell: Coordinate = (x, y)
                if grid.is_masked(cell):
                    continue
                if len(grid.accessible_neighbors(cell)) <= 1:
                    dead_ends.append(cell)
        return dead_ends

    def _open_best_wall(
        self,
        grid: GridProtocol,
        cell: Coordinate,
        rng: Random,
    ) -> bool:
        """Open one closed wall from cell without creating a 3x3 open area.

        Prioritizes candidates that connect to another dead-end and avoid
        creating 2x2 open blocks, falling back to any candidate that avoids
        creating a forbidden 3x3 open area.

        Args:
            grid: The maze grid to modify.
            cell: The cell whose closed walls are evaluated.
            rng: Seeded random number generator.

        Returns:
            bool: True if a wall was opened, False if no valid wall exists.
        """
        closed: list[tuple[Direction, Coordinate]] = [
            (direction, neighbor)
            for direction, neighbor in grid.neighbors(cell)
            if grid.has_wall(cell, direction)
            and not grid.creates_open_3x3(cell, direction)
        ]
        if not closed:
            return False

        tier1: list[Direction] = []
        tier2: list[Direction] = []
        tier3: list[Direction] = []
        tier4: list[Direction] = []

        for direction, neighbor in closed:
            neighbor_is_dead_end: bool = (
                len(grid.accessible_neighbors(neighbor)) <= 1
            )
            forms_2x2: bool = grid.creates_open_2x2(cell, direction)

            if neighbor_is_dead_end and not forms_2x2:
                tier1.append(direction)
            elif not forms_2x2:
                tier2.append(direction)
            elif neighbor_is_dead_end:
                tier3.append(direction)
            else:
                tier4.append(direction)

        for tier in (tier1, tier2, tier3, tier4):
            if tier:
                chosen_dir: Direction = rng.choice(tier)
                grid.remove_wall(cell, chosen_dir)
                return True
        return False

    def _ensure_minimum_loops(
        self,
        grid: GridProtocol,
        rng: Random,
        min_loops: int,
    ) -> None:
        """Ensure the braided maze has at least min_loops independent cycles.

        Args:
            grid: The maze grid to inspect and modify.
            rng: Seeded random number generator.
            min_loops: Minimum required cyclomatic number (E - V + 1).
        """
        current_loops: int = self._count_loops(grid)
        if current_loops >= min_loops:
            return

        candidates: list[tuple[Coordinate, Direction]] = []
        for y in range(grid.height):
            for x in range(grid.width):
                cell: Coordinate = (x, y)
                if grid.is_masked(cell):
                    continue
                for direction in (Direction.EAST, Direction.SOUTH):
                    dx, dy = direction.delta
                    neighbor: Coordinate = (x + dx, y + dy)
                    if (
                        grid.in_bounds(neighbor)
                        and not grid.is_masked(neighbor)
                        and grid.has_wall(cell, direction)
                    ):
                        candidates.append((cell, direction))

        rng.shuffle(candidates)
        for cell, direction in candidates:
            if current_loops >= min_loops:
                break
            if (
                grid.has_wall(cell, direction)
                and not grid.creates_open_3x3(cell, direction)
            ):
                grid.remove_wall(cell, direction)
                current_loops += 1

    @staticmethod
    def _count_loops(grid: GridProtocol) -> int:
        """Calculate the cyclomatic number (independent loops) of the grid.

        Args:
            grid: The connected maze grid.

        Returns:
            int: Number of independent cycles (edges - vertices + 1).
        """
        vertices: int = grid.width * grid.height - len(grid.masked_cells)
        directed_edges: int = 0
        for y in range(grid.height):
            for x in range(grid.width):
                cell: Coordinate = (x, y)
                if not grid.is_masked(cell):
                    directed_edges += len(grid.accessible_neighbors(cell))
        undirected_edges: int = directed_edges // 2
        return max(0, undirected_edges - vertices + 1)
