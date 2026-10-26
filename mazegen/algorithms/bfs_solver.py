"""Breadth-First Search (BFS) shortest-path solver for A-Maze-ing.

This module implements an unweighted shortest-path search using a FIFO queue
(collections.deque) and parent-pointer mapping to reconstruct the optimal
route from entry to exit.
"""

from collections import deque
from mazegen.domain.interfaces import GridProtocol
from mazegen.domain.types import Coordinate, Direction, SolverError


class BFSSolver:
    """Find the shortest valid path in a maze using Breadth-First Search."""

    def solve(self, grid: GridProtocol) -> list[Direction]:
        """Compute the shortest path from grid.entry to grid.exit.

        Args:
            grid: The generated maze grid to solve.

        Returns:
            list[Direction]: Ordered sequence of cardinal steps from entry
                to exit.

        Raises:
            SolverError: If no valid path exists between entry and exit.
        """
        start: Coordinate = grid.entry
        goal: Coordinate = grid.exit

        if start == goal:
            return []

        queue: deque[Coordinate] = deque([start])
        visited: set[Coordinate] = {start}
        parent_map: dict[Coordinate, tuple[Coordinate, Direction]] = {}

        while queue:
            current: Coordinate = queue.popleft()
            if current == goal:
                return self._reconstruct_path(parent_map, start, goal)

            for direction, neighbor in grid.accessible_neighbors(current):
                if neighbor not in visited:
                    visited.add(neighbor)
                    parent_map[neighbor] = (current, direction)
                    queue.append(neighbor)

        raise SolverError(
            f"No valid path found from entry {start} to exit {goal}."
        )

    @staticmethod
    def _reconstruct_path(
        parent_map: dict[Coordinate, tuple[Coordinate, Direction]],
        start: Coordinate,
        goal: Coordinate,
    ) -> list[Direction]:
        """Reconstruct the directional route from parent pointers.

        Args:
            parent_map: Mapping of child -> (parent, direction_taken).
            start: Starting coordinate.
            goal: Target coordinate.

        Returns:
            list[Direction]: Directions ordered from start to goal.
        """
        steps: list[Direction] = []
        cursor: Coordinate = goal
        while cursor != start:
            parent, direction = parent_map[cursor]
            steps.append(direction)
            cursor = parent
        steps.reverse()
        return steps

    @staticmethod
    def trace_coordinates(
        start: Coordinate,
        steps: list[Direction],
    ) -> list[Coordinate]:
        """Convert a directional path into the sequence of visited coordinates.

        Args:
            start: Starting (x, y) coordinate.
            steps: Ordered list of Directions taken from start.

        Returns:
            list[Coordinate]: Coordinates visited from start to end inclusive.
        """
        coords: list[Coordinate] = [start]
        x, y = start
        for step in steps:
            dx, dy = step.delta
            x += dx
            y += dy
            coords.append((x, y))
        return coords

