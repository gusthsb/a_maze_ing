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
            seed: typing.Optional[int] = None
    ) -> None:
        self.grid: list[list[int]] = [
            [15 for _ in range(width) for _ in range(height)]
        ]
        self.directions = [
            (0, -1, 1, 4),
            (1, 0, 2, 8),
            (0, 1, 4, 1),
            (-1, 0, 8, 2)
        ]
        

    def generate(self) -> None:
        """
        Function to execute de maze generation algorithm.
        """
        pass

    def get_structure(self) -> None:
        """
        Access the maze structure
        """
        pass
