"""Iterative Depth-First Search (Recursive Backtracker) maze generator.

This module implements an explicit stack-based DFS algorithm to generate a
spanning-tree (perfect) maze over all non-masked cells without risking
Python's RecursionError on large grids.
"""

from random import Random
from mazegen.domain.interfaces import GridProtocol
from mazegen.domain.types import Coordinate, Direction, GenerationError


class DFSBacktracker:
    """Generate a perfect maze using an iterative DFS backtracker."""

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
        stack: list[Coordinate] = [start]

        while stack:
            current: Coordinate = stack[-1]
            unvisited: list[tuple[Direction, Coordinate]] = [
                (direction, neighbor)
                for direction, neighbor in grid.neighbors(current)
                if neighbor not in visited
            ]

            if unvisited:
                direction, chosen = rng.choice(unvisited)
                grid.remove_wall(current, direction)
                visited.add(chosen)
                stack.append(chosen)
            else:
                stack.pop()

        expected_count: int = (
            grid.width * grid.height - len(grid.masked_cells)
        )
        if len(visited) != expected_count:
            raise GenerationError(
                f"DFS could only reach {len(visited)} of {expected_count} "
                f"non-masked cells; the maze is not fully connected."
            )

