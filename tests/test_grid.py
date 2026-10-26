"""Unit tests for MazeGrid, Direction bitmasks, and '42' pattern masking."""

import io
import unittest
from contextlib import redirect_stderr

from mazegen.core.grid import MazeGrid
from mazegen.domain.types import ConfigError, Direction, GenerationError


class TestMazeGrid(unittest.TestCase):
    """Test suite verifying MazeGrid invariance, bitmasks, and '42' mask."""

    def test_direction_bitmask_values(self) -> None:
        """Verify cardinal bitmask values match the specification."""
        self.assertEqual(int(Direction.NORTH), 1)
        self.assertEqual(int(Direction.EAST), 2)
        self.assertEqual(int(Direction.SOUTH), 4)
        self.assertEqual(int(Direction.WEST), 8)
        self.assertEqual(int(Direction.ALL), 15)

    def test_direction_opposites_and_chars(self) -> None:
        """Verify opposite directions, deltas, and char representations."""
        self.assertEqual(Direction.NORTH.opposite, Direction.SOUTH)
        self.assertEqual(Direction.EAST.opposite, Direction.WEST)
        self.assertEqual(Direction.NORTH.delta, (0, -1))
        self.assertEqual(Direction.EAST.delta, (1, 0))
        self.assertEqual(Direction.SOUTH.delta, (0, 1))
        self.assertEqual(Direction.WEST.delta, (-1, 0))
        self.assertEqual(Direction.NORTH.char, "N")
        self.assertEqual(Direction.WEST.char, "W")

    def test_wall_coherence_on_remove_and_add(self) -> None:
        """Removing or adding a wall updates both adjacent cells coherently."""
        grid: MazeGrid = MazeGrid(
            width=10,
            height=10,
            entry=(0, 0),
            exit_coord=(9, 9),
        )
        self.assertTrue(grid.has_wall((0, 0), Direction.EAST))
        self.assertTrue(grid.has_wall((1, 0), Direction.WEST))

        grid.remove_wall((0, 0), Direction.EAST)
        self.assertFalse(grid.has_wall((0, 0), Direction.EAST))
        self.assertFalse(grid.has_wall((1, 0), Direction.WEST))

        grid.add_wall((0, 0), Direction.EAST)
        self.assertTrue(grid.has_wall((0, 0), Direction.EAST))
        self.assertTrue(grid.has_wall((1, 0), Direction.WEST))

    def test_border_walls_cannot_be_removed(self) -> None:
        """Attempting to remove an external boundary wall raises an error."""
        grid: MazeGrid = MazeGrid(
            width=10,
            height=10,
            entry=(0, 0),
            exit_coord=(9, 9),
        )
        with self.assertRaises(GenerationError):
            grid.remove_wall((0, 0), Direction.NORTH)
        with self.assertRaises(GenerationError):
            grid.remove_wall((0, 0), Direction.WEST)

    def test_42_pattern_applied_and_omitted_when_small(self) -> None:
        """Verify '42' pattern on standard grids and omission when small."""
        large_grid: MazeGrid = MazeGrid(
            width=20,
            height=15,
            entry=(0, 0),
            exit_coord=(19, 14),
        )
        self.assertEqual(len(large_grid.masked_cells), 18)

        stderr_buf: io.StringIO = io.StringIO()
        with redirect_stderr(stderr_buf):
            small_grid: MazeGrid = MazeGrid(
                width=5,
                height=5,
                entry=(0, 0),
                exit_coord=(4, 4),
            )
        self.assertEqual(len(small_grid.masked_cells), 0)
        self.assertIn("Warning", stderr_buf.getvalue())

    def test_entry_overlapping_42_raises_config_error(self) -> None:
        """Verify entry placed inside '42' mask raises ConfigError."""
        with self.assertRaises(ConfigError):
            MazeGrid(
                width=20,
                height=15,
                entry=(6, 5),
                exit_coord=(19, 14),
            )

    def test_creates_open_3x3_detection(self) -> None:
        """Verify creates_open_3x3 detects when a 3x3 open room would form."""
        grid: MazeGrid = MazeGrid(
            width=5,
            height=5,
            entry=(0, 0),
            exit_coord=(4, 4),
            apply_42_pattern=False,
        )
        for y in range(3):
            for x in range(3):
                if x < 2:
                    grid.remove_wall((x, y), Direction.EAST)
                if y < 2 and not (x == 2 and y == 1):
                    grid.remove_wall((x, y), Direction.SOUTH)

        self.assertTrue(grid.creates_open_3x3((2, 1), Direction.SOUTH))


if __name__ == "__main__":
    unittest.main()
