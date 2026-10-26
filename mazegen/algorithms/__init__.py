"""Algorithms package for maze generation and pathfinding."""

from mazegen.algorithms.bfs_solver import BFSSolver
from mazegen.algorithms.braided_pac import BraidedPacModifier
from mazegen.algorithms.dfs_backtracker import DFSBacktracker
from mazegen.algorithms.prim import PrimGenerator

__all__ = [
    "BFSSolver",
    "BraidedPacModifier",
    "DFSBacktracker",
    "PrimGenerator",
]

