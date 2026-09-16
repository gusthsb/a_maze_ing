import random
import typing


class MazeGenerator:
    """
    Class to manage the maze generation.
    """

    def __init__(
        self,
        width: int,
        height: int,
        entry: tuple[int, int],
        exit_pos: tuple[int, int],
        perfect: bool,
        seed: typing.Optional[int] = None,
    ) -> None:
        self.grid: list[list[int]] = [[15 for _ in range(width)] for _ in range(height)]
        self.directions = [(0, -1, 1, 4), (1, 0, 2, 8), (0, 1, 4, 1), (-1, 0, 8, 2)]
        self.width = width
        self.height = height
        self.entry = entry
        self.exit_pos = exit_pos
        self.perfect = perfect
        self.seed = seed

    def _braid_maze(self) -> None:
        """
        Removes dead-ends to create a braided maze with multiple paths.
        """
        for y in range(self.height):
            for x in range(self.width):
                if bin(self.grid[y][x]).count("1") == 3:
                    closed = list()

                    for dirx, diry, current, neighbor in self.directions:
                        next_x = x + dirx
                        next_y = y + diry

                        if 0 <= next_x < self.width and 0 <= next_y < self.height:

                            if self.grid[y][x] & current:
                                closed.append((next_x, next_y, current, neighbor))
                    if closed:
                        next_x, next_y, current, neighbor = random.choice(closed)
                        self.grid[y][x] &= ~current
                        self.grid[next_y][next_x] &= ~neighbor

    def generate(self) -> None:
        """
        Function to execute the recursive backtracker algorithm.
        """
        print("Generating maze architecture...")
        start_x, start_y = 0, 0
        stack: list[tuple[int, int]] = [(start_x, start_y)]

        while stack:
            current_x, current_y = stack[-1]
            unvisited = list()

            for dirx, diry, current_wall, neighbor in self.directions:
                next_x = current_x + dirx
                next_y = current_y + diry

                if (
                    0 <= next_x < self.width
                    and 0 <= next_y < self.height
                    and self.grid[next_y][next_x] == 15
                ):

                    unvisited.append((next_x, next_y, current_wall, neighbor))

            if unvisited:
                next_x, next_y, current_wall, neighbor = random.choice(unvisited)

                self.grid[current_y][current_x] &= ~current_wall
                self.grid[next_y][next_x] &= ~neighbor

                stack.append((next_x, next_y))

            else:
                stack.pop()

        if not self.perfect:
            self._braid_maze()

    def get_structure(self) -> list[list[int]]:
        """
        Return the maze structure
        """
        return self.grid
