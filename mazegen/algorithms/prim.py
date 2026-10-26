"""Iterative Randomized Prim's maze generation algorithm.

This module implements an iterative frontier-based Prim's algorithm to build
a minimum spanning tree (perfect maze) over all non-masked grid cells.
"""

from random import Random
from mazegen.domain.interfaces import GridProtocol
from mazegen.domain.types import Coordinate, Direction, GenerationError


class PrimGenerator:
    """Generate a perfect maze using Randomized Prim's algorithm."""

    def generate(self, grid: GridProtocol, rng: Random) -> None:
        """Carve a spanning tree across all non-masked grid cells.

        Args:
            grid: The maze grid to carve passages into.
            rng: Seeded random number generator for reproducibility.

        Raises:
            GenerationError: If the grid is disconnected by masked cells.
        """
        start: Coordinate = grid.entry
        if grid.is_masked(start):
            raise GenerationError(
                f"Start coordinate {start} is masked by the '42' pattern."
            )

        visited: set[Coordinate] = {start}
        frontier: list[tuple[Coordinate, Direction, Coordinate]] = [
            (start, direction, neighbor)
            for direction, neighbor in grid.neighbors(start)
        ]

        while frontier:
            idx: int = rng.randrange(len(frontier))
            frontier[idx], frontier[-1] = frontier[-1], frontier[idx]
            source, direction, target = frontier.pop()

            if target in visited:
                continue

            grid.remove_wall(source, direction)
            visited.add(target)

            for next_dir, next_neighbor in grid.neighbors(target):
                if next_neighbor not in visited:
                    frontier.append((target, next_dir, next_neighbor))

        expected_count: int = (
            grid.width * grid.height - len(grid.masked_cells)
        )
        if len(visited) != expected_count:
            raise GenerationError(
                f"Prim could only reach {len(visited)} of {expected_count} "
                f"non-masked cells; the maze is not fully connected."
            )

