"""Iterative Randomized Prim's maze generation algorithm.

This module implements an iterative frontier-based Prim's algorithm to build
a minimum spanning tree (perfect maze) over all non-masked grid cells while
keeping entry and exit as clean degree-1 endpoints and supporting animation.
"""

from random import Random
from mazegen.domain.interfaces import GridProtocol, StepCallback
from mazegen.domain.types import Coordinate, Direction, GenerationError


class PrimGenerator:
    """Generate a perfect maze using Randomized Prim's algorithm."""

    def generate(
        self,
        grid: GridProtocol,
        rng: Random,
        step_callback: StepCallback | None = None,
    ) -> None:
        """Carve a spanning tree across all non-masked grid cells.

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
            self._expand_frontier(
                grid=grid,
                rng=rng,
                seed_cell=first_cell,
                visited=visited,
                avoid={goal},
                step_callback=step_callback,
            )

        # Fallback if start was an articulation point
        self._expand_frontier(
            grid=grid,
            rng=rng,
            seed_cell=start,
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

        # Fallback if goal was an articulation point
        self._expand_frontier(
            grid=grid,
            rng=rng,
            seed_cell=goal,
            visited=visited,
            avoid=set(),
            step_callback=step_callback,
        )

        expected_count: int = (
            grid.width * grid.height - len(grid.masked_cells)
        )
        if len(visited) != expected_count:
            raise GenerationError(
                f"Prim could only reach {len(visited)} of {expected_count} "
                f"non-masked cells; the maze is not fully connected."
            )

    @staticmethod
    def _expand_frontier(
        grid: GridProtocol,
        rng: Random,
        seed_cell: Coordinate,
        visited: set[Coordinate],
        avoid: set[Coordinate],
        step_callback: StepCallback | None = None,
    ) -> None:
        """Run Randomized Prim's expansion from seed_cell avoiding avoid.

        Args:
            grid: The maze grid to modify.
            rng: Seeded random number generator.
            seed_cell: Already-visited cell whose edges seed the frontier.
            visited: Mutable set of visited coordinates.
            avoid: Coordinates to defer visiting during this pass.
            step_callback: Optional animation step callback.
        """
        frontier: list[tuple[Coordinate, Direction, Coordinate]] = [
            (seed_cell, direction, neighbor)
            for direction, neighbor in grid.neighbors(seed_cell)
            if neighbor not in visited and neighbor not in avoid
        ]

        while frontier:
            idx: int = rng.randrange(len(frontier))
            frontier[idx], frontier[-1] = frontier[-1], frontier[idx]
            source, direction, target = frontier.pop()

            if target in visited or target in avoid:
                continue

            grid.remove_wall(source, direction)
            visited.add(target)
            if step_callback is not None:
                step_callback(grid, target, [source, target])

            for next_dir, next_neighbor in grid.neighbors(target):
                if next_neighbor not in visited and next_neighbor not in avoid:
                    frontier.append((target, next_dir, next_neighbor))
