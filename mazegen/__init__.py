"""A-Maze-ing reusable maze generation and pathfinding package.

This package exposes MazeGenerator as its primary entry point for external
projects, alongside configuration, grid, and domain types.
"""

from mazegen.core.config_parser import ConfigParser
from mazegen.core.generator import MazeGenerator
from mazegen.core.grid import MazeGrid
from mazegen.core.serializer import MazeSerializer
from mazegen.domain.types import (
    ConfigError,
    Coordinate,
    Direction,
    GenerationError,
    MazeConfig,
    MazeError,
    SolverError,
)

__version__: str = "1.0.0"

__all__ = [
    "ConfigError",
    "ConfigParser",
    "Coordinate",
    "Direction",
    "GenerationError",
    "MazeConfig",
    "MazeError",
    "MazeGenerator",
    "MazeGrid",
    "MazeSerializer",
    "SolverError",
    "__version__",
]

