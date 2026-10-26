"""Domain package exposing types, exceptions, and protocols."""

from mazegen.domain.interfaces import (
    GenerationStrategy,
    GridProtocol,
    SolverStrategy,
)
from mazegen.domain.types import (
    ConfigError,
    Coordinate,
    Direction,
    GenerationError,
    MazeConfig,
    MazeError,
    SolverError,
)

__all__ = [
    "ConfigError",
    "Coordinate",
    "Direction",
    "GenerationError",
    "GenerationStrategy",
    "GridProtocol",
    "MazeConfig",
    "MazeError",
    "SolverError",
    "SolverStrategy",
]
