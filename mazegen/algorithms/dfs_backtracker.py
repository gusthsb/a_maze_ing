"""Iterative Depth-First Search (Recursive Backtracker) maze generator.

This module implements an explicit stack-based DFS algorithm to generate a
spanning-tree (perfect) maze over all non-masked cells without risking
Python's RecursionError on large grids, while keeping entry and exit as
clean degree-1 endpoints and supporting step-by-step animation callbacks.
"""

from random import Random
from mazegen.domain.interfaces import GridProtocol, StepCallback
from mazegen.domain.types import Coordinate, Direction, GenerationError


class DFSBacktracker:
    """Generate a perfect maze using an iterative DFS backtracker."""

    def generate(
        self,
        grid: GridProtocol,
        rng: Random,
        step_callback: StepCallback | None = None,
    ) -> None:
        """Carve a spanning tree across all non-masked grid cells.

        Holds the exit cell out of the main traversal so the exit is
        connected as a clean degree-1 leaf (preventing confusing dead-end
        branches behind the exit marker), falling back to traversing
        through the exit only if it is an articulation point.

        Args:
            grid: The maze grid to carve passages into.
            rng: Seeded random number generator for reproducibility.
            step_callback: Optional callback invoked after each carving step.

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
        if step_callback is not None:
            step_callback(grid, first_cell, [start, first_cell])

        if first_cell != goal:
            self._carve_from(
                grid=grid,
                rng=rng,
                roots=[first_cell],
                visited=visited,
                avoid={goal},
                step_callback=step_callback,
            )

        # Fallback if start was an articulation point
        self._carve_from(
            grid=grid,
            rng=rng,
            roots=[start],
            visited=visited,
            avoid={goal},
            step_callback=step_callback,
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
            if step_callback is not None:
                step_callback(grid, goal, [goal])

        # Fallback if goal was an articulation point isolating a pocket
        self._carve_from(
            grid=grid,
            rng=rng,
            roots=[goal],
            visited=visited,
            avoid=set(),
            step_callback=step_callback,
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
        step_callback: StepCallback | None = None,
    ) -> None:
        """Run iterative stack-based DFS from roots avoiding specified cells.

        Args:
            grid: The maze grid to modify.
            rng: Seeded random number generator.
            roots: Initial stack of visited coordinates.
            visited: Mutable set of already visited coordinates.
            avoid: Coordinates to defer visiting during this pass.
            step_callback: Optional animation step callback.
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
                if step_callback is not None:
                    step_callback(grid, chosen, list(stack))
            else:
                stack.pop()
                if step_callback is not None and stack:
                    step_callback(grid, stack[-1], list(stack))
