"""Iterative Depth-First Search (Recursive Backtracker) maze generator.

This module implements an explicit stack-based DFS algorithm to generate a
spanning-tree (perfect) maze over all non-masked cells without risking
Python's RecursionError on large grids, while keeping entry and exit as
clean degree-1 endpoints whenever topology permits.
"""

from random import Random
from mazegen.domain.interfaces import GridProtocol
from mazegen.domain.types import Coordinate, Direction, GenerationError


class DFSBacktracker:
    """Generate a perfect maze using an iterative DFS backtracker."""

    def generate(self, grid: GridProtocol, rng: Random) -> None:
        """Carve a spanning tree across all non-masked grid cells.

        Holds the exit cell out of the main traversal so the exit is
        connected as a clean degree-1 leaf (preventing confusing dead-end
        branches behind the exit marker), falling back to traversing
        through the exit only if it is an articulation point.

        Args:
            grid: The maze grid to carve passages into.
            rng: Seeded random number generator for reproducibility.

        Raises:
            GenerationError: If the grid is disconnected by masked cells.
        """
        start: Coordinate = grid.entry
        goal: Coordinate = grid.exit
        if grid.is_masked(start):
            raise GenerationError(
                f"Start coordinate {start} is masked by the '42' pattern."
            )

        visited: set[Coordinate] = {start}
        start_neighbors: list[tuple[Direction, Coordinate]] = [
            (d, n) for d, n in grid.neighbors(start) if n != goal
        ]
        if not start_neighbors:
            start_neighbors = grid.neighbors(start)
        if not start_neighbors:
            raise GenerationError(
                f"Start cell {start} has no valid neighbors."
            )

        first_dir, first_cell = rng.choice(start_neighbors)
        grid.remove_wall(start, first_dir)
        visited.add(first_cell)

        if first_cell != goal:
            self._carve_from(
                grid=grid,
                rng=rng,
                roots=[first_cell],
                visited=visited,
                avoid={goal},
            )

        # Fallback if start was an articulation point
        self._carve_from(
            grid=grid,
            rng=rng,
            roots=[start],
            visited=visited,
            avoid={goal},
        )

        # Connect goal (exit) via a single passage to the visited tree
        if goal not in visited:
            visited_exit_neighbors: list[tuple[Direction, Coordinate]] = [
                (d, n) for d, n in grid.neighbors(goal) if n in visited
            ]
            if not visited_exit_neighbors:
                raise GenerationError(
                    f"Exit cell {goal} could not be reached from {start}."
                )
            exit_dir, _ = rng.choice(visited_exit_neighbors)
            grid.remove_wall(goal, exit_dir)
            visited.add(goal)

        # Fallback if goal was an articulation point isolating a pocket
        self._carve_from(
            grid=grid,
            rng=rng,
            roots=[goal],
            visited=visited,
            avoid=set(),
        )

        expected_count: int = (
            grid.width * grid.height - len(grid.masked_cells)
        )
        if len(visited) != expected_count:
            raise GenerationError(
                f"DFS could only reach {len(visited)} of {expected_count} "
                f"non-masked cells; the maze is not fully connected."
            )

    @staticmethod
    def _carve_from(
        grid: GridProtocol,
        rng: Random,
        roots: list[Coordinate],
        visited: set[Coordinate],
        avoid: set[Coordinate],
    ) -> None:
        """Run iterative stack-based DFS from roots avoiding specified cells.

        Args:
            grid: The maze grid to modify.
            rng: Seeded random number generator.
            roots: Initial stack of visited coordinates.
            visited: Mutable set of already visited coordinates.
            avoid: Coordinates to defer visiting during this pass.
        """
        stack: list[Coordinate] = list(roots)
        while stack:
            current: Coordinate = stack[-1]
            unvisited: list[tuple[Direction, Coordinate]] = [
                (direction, neighbor)
                for direction, neighbor in grid.neighbors(current)
                if neighbor not in visited and neighbor not in avoid
            ]
            if unvisited:
                direction, chosen = rng.choice(unvisited)
                grid.remove_wall(current, direction)
                visited.add(chosen)
                stack.append(chosen)
            else:
                stack.pop()
