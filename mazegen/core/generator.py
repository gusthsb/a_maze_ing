"""Reusable MazeGenerator facade for A-Maze-ing.

This module provides the standalone MazeGenerator class required by Chapter VI
of the specification, orchestrating grid creation, algorithm execution,
shortest-path resolution, and serialization.
"""

from pathlib import Path
from random import Random

from mazegen.algorithms.bfs_solver import BFSSolver
from mazegen.algorithms.braided_pac import BraidedPacModifier
from mazegen.algorithms.dfs_backtracker import DFSBacktracker
from mazegen.algorithms.prim import PrimGenerator
from mazegen.core.config_parser import ConfigParser
from mazegen.core.grid import MazeGrid
from mazegen.core.serializer import MazeSerializer
from mazegen.domain.interfaces import GenerationStrategy, SolverStrategy
from mazegen.domain.types import (
    ConfigError,
    Coordinate,
    Direction,
    MazeConfig,
)


class MazeGenerator:
    """High-level reusable maze generator and solver.

    Example:
        >>> from mazegen import MazeGenerator
        >>> gen = MazeGenerator(width=20, height=15, perfect=False, seed=42)
        >>> gen.generate()
        >>> matrix = gen.get_matrix()
        >>> path_str = gen.solution_str
    """

    def __init__(
        self,
        width: int = 20,
        height: int = 15,
        entry: Coordinate = (0, 0),
        exit_coord: Coordinate | None = None,
        perfect: bool = False,
        seed: int | None = None,
        algorithm: str = "dfs",
        output_file: str = "maze.txt",
    ) -> None:
        """Initialize the MazeGenerator with custom parameters.

        Args:
            width: Number of columns (default 20, minimum 2).
            height: Number of rows (default 15, minimum 2).
            entry: Starting (x, y) coordinate (default (0, 0)).
            exit_coord: Target (x, y) coordinate (defaults to
                (width - 1, height - 1)).
            perfect: True for a single-path perfect maze, False for a
                Pac-Man braided maze with loops.
            seed: Optional integer seed for reproducible generation.
            algorithm: Primary spanning-tree algorithm ('dfs' or 'prim').
            output_file: Default file path for saving serialized output.

        Raises:
            ConfigError: If any parameter is invalid.
        """
        resolved_exit: Coordinate = (
            exit_coord if exit_coord is not None else (width - 1, height - 1)
        )
        algo_normalized: str = algorithm.lower()
        if algo_normalized not in {"dfs", "prim"}:
            raise ConfigError(
                f"Unsupported algorithm '{algorithm}'. Choose 'dfs' or 'prim'."
            )

        self._config: MazeConfig = MazeConfig(
            width=width,
            height=height,
            entry=entry,
            exit=resolved_exit,
            output_file=output_file,
            perfect=perfect,
            seed=seed,
            algorithm=algo_normalized,
        )
        self._seed: int | None = seed
        self._grid: MazeGrid | None = None
        self._solution: list[Direction] = []
        self._solver: SolverStrategy = BFSSolver()

    @classmethod
    def from_config(cls, config: MazeConfig) -> "MazeGenerator":
        """Create a MazeGenerator instance from a validated MazeConfig.

        Args:
            config: Immutable MazeConfig instance.

        Returns:
            MazeGenerator: Configured generator ready to run.
        """
        return cls(
            width=config.width,
            height=config.height,
            entry=config.entry,
            exit_coord=config.exit,
            perfect=config.perfect,
            seed=config.seed,
            algorithm=config.algorithm,
            output_file=config.output_file,
        )

    @classmethod
    def from_file(cls, config_path: str | Path) -> "MazeGenerator":
        """Create a MazeGenerator instance by parsing a configuration file.

        Args:
            config_path: Path to the configuration text file.

        Returns:
            MazeGenerator: Configured generator ready to run.
        """
        config: MazeConfig = ConfigParser.parse_file(config_path)
        return cls.from_config(config)

    @property
    def config(self) -> MazeConfig:
        """Return the active MazeConfig."""
        return self._config

    @property
    def grid(self) -> MazeGrid:
        """Return the generated MazeGrid, generating it first if needed."""
        if self._grid is None:
            self.generate()
        assert self._grid is not None
        return self._grid

    @property
    def solution(self) -> list[Direction]:
        """Return the shortest path as a list of Directions."""
        if self._grid is None:
            self.generate()
        return list(self._solution)

    @property
    def solution_str(self) -> str:
        """Return the shortest path as a string of 'N', 'E', 'S', 'W'."""
        return "".join(step.char for step in self.solution)

    @property
    def solution_coordinates(self) -> list[Coordinate]:
        """Return ordered (x, y) coordinates visited on the shortest path."""
        return BFSSolver.trace_coordinates(self.grid.entry, self.solution)

    def generate(self, seed: int | None = None) -> MazeGrid:
        """Generate a new maze and compute its shortest path solution.

        Args:
            seed: Optional override seed. If None, uses the configured seed
                (or system entropy if no seed was configured).

        Returns:
            MazeGrid: The newly generated maze grid.
        """
        active_seed: int | None = seed if seed is not None else self._seed
        rng: Random = Random(active_seed)

        grid: MazeGrid = MazeGrid(
            width=self._config.width,
            height=self._config.height,
            entry=self._config.entry,
            exit_coord=self._config.exit,
            apply_42_pattern=True,
        )

        primary_strategy: GenerationStrategy = self._select_strategy(
            self._config.algorithm
        )
        primary_strategy.generate(grid, rng)

        if not self._config.perfect:
            braider: GenerationStrategy = BraidedPacModifier()
            braider.generate(grid, rng)

        self._grid = grid
        self._solution = self._solver.solve(grid)
        return grid

    def get_matrix(self) -> list[list[int]]:
        """Return the generated 2D matrix of 4-bit wall integers (0..15).

        Returns:
            list[list[int]]: Copy of the 2D grid matrix.
        """
        return self.grid.to_matrix()

    def get_hex_rows(self) -> list[str]:
        """Return the hexadecimal row strings of the generated maze.

        Returns:
            list[str]: One lowercase hex string per row.
        """
        return MazeSerializer.to_hex_rows(self.grid)

    def save(self, output_path: str | Path | None = None) -> None:
        """Serialize and save the generated maze and solution to a file.

        Args:
            output_path: Optional override file path; defaults to
                config.output_file.
        """
        target: str | Path = (
            output_path
            if output_path is not None
            else self._config.output_file
        )
        MazeSerializer.save(self.grid, self.solution, target)

    @staticmethod
    def _select_strategy(algorithm: str) -> GenerationStrategy:
        """Instantiate the requested primary spanning-tree strategy.

        Args:
            algorithm: Algorithm identifier ('dfs' or 'prim').

        Returns:
            GenerationStrategy: Strategy instance.
        """
        if algorithm == "prim":
            return PrimGenerator()
        return DFSBacktracker()
