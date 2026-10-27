"""Unit tests for maze generation, braiding, BFS solver, and serialization."""

import unittest

from mazegen import MazeGenerator
from mazegen.core.grid import MazeGrid
from mazegen.core.serializer import MazeSerializer
from mazegen.domain.types import Coordinate


class TestAlgorithmsAndGenerator(unittest.TestCase):
    """Test suite for DFS, Prim, Braided Pac-Man mode, and BFS solver."""

    def test_perfect_maze_is_spanning_tree(self) -> None:
        """PERFECT=True generates a tree with E = V - 1 and connectivity."""
        for algo in ("dfs", "prim"):
            gen: MazeGenerator = MazeGenerator(
                width=20,
                height=15,
                entry=(0, 0),
                exit_coord=(19, 14),
                perfect=True,
                seed=42,
                algorithm=algo,
            )
            grid: MazeGrid = gen.generate()
            vertices: int = (
                grid.width * grid.height - len(grid.masked_cells)
            )
            directed_edges: int = sum(
                len(grid.accessible_neighbors((x, y)))
                for y in range(grid.height)
                for x in range(grid.width)
                if not grid.is_masked((x, y))
            )
            self.assertEqual(directed_edges // 2, vertices - 1)
            self.assertEqual(len(grid.accessible_neighbors(grid.entry)), 1)
            self.assertEqual(len(grid.accessible_neighbors(grid.exit)), 1)
            self.assertGreater(len(gen.solution), 0)

    def test_seed_reproducibility(self) -> None:
        """Identical seeds produce identical maze matrices and solutions."""
        gen1: MazeGenerator = MazeGenerator(
            width=15, height=12, perfect=False, seed=999
        )
        gen2: MazeGenerator = MazeGenerator(
            width=15, height=12, perfect=False, seed=999
        )
        self.assertEqual(gen1.get_matrix(), gen2.get_matrix())
        self.assertEqual(gen1.solution_str, gen2.solution_str)

    def test_braided_pacman_mode_invariants(self) -> None:
        """PERFECT=False creates loops, opens corners, and avoids 3x3 rooms."""
        for seed in (1, 7, 42, 100):
            gen: MazeGenerator = MazeGenerator(
                width=20,
                height=15,
                entry=(0, 0),
                exit_coord=(19, 14),
                perfect=False,
                seed=seed,
            )
            grid: MazeGrid = gen.generate()

            # Check 4 corners have degree 2 (open corridors)
            corners: list[Coordinate] = [
                (0, 0),
                (grid.width - 1, 0),
                (0, grid.height - 1),
                (grid.width - 1, grid.height - 1),
            ]
            for corner in corners:
                self.assertEqual(len(grid.accessible_neighbors(corner)), 2)

            # Check no 3x3 open areas exist anywhere
            for bx in range(grid.width - 2):
                for by in range(grid.height - 2):
                    self.assertFalse(grid._is_block_open(bx, by, 3))

            # Check dead-ends only occur if surrounded on 3 sides by '42' mask
            for y in range(grid.height):
                for x in range(grid.width):
                    cell: Coordinate = (x, y)
                    if grid.is_masked(cell):
                        continue
                    if len(grid.neighbors(cell)) >= 2:
                        self.assertGreaterEqual(
                            len(grid.accessible_neighbors(cell)), 2
                        )

    def test_bfs_solution_is_valid_walk(self) -> None:
        """Walking the BFS solution from entry reaches exit cleanly."""
        gen: MazeGenerator = MazeGenerator(
            width=20,
            height=15,
            entry=(0, 0),
            exit_coord=(19, 14),
            perfect=True,
            seed=2026,
        )
        grid: MazeGrid = gen.generate()
        cursor: Coordinate = grid.entry
        for step in gen.solution:
            self.assertFalse(grid.has_wall(cursor, step))
            dx, dy = step.delta
            cursor = (cursor[0] + dx, cursor[1] + dy)
            self.assertTrue(grid.in_bounds(cursor))
            self.assertFalse(grid.is_masked(cursor))
        self.assertEqual(cursor, grid.exit)

    def test_serializer_output_format(self) -> None:
        """Verify serialized text structure matches Chapter IV.5."""
        gen: MazeGenerator = MazeGenerator(
            width=10,
            height=8,
            entry=(0, 0),
            exit_coord=(9, 7),
            perfect=True,
            seed=10,
        )
        payload: str = MazeSerializer.serialize(gen.grid, gen.solution)
        self.assertTrue(payload.endswith("\n"))
        lines: list[str] = payload.splitlines()
        self.assertEqual(len(lines), 8 + 1 + 3)
        for row_line in lines[:8]:
            self.assertEqual(len(row_line), 10)
            int(row_line, 16)
        self.assertEqual(lines[8], "")
        self.assertEqual(lines[9], "0,0")
        self.assertEqual(lines[10], "9,7")
        self.assertTrue(
            all(ch in {"N", "E", "S", "W"} for ch in lines[11])
        )
        self.assertEqual(len(lines[11]), len(gen.solution))

    def test_toggle_algorithm(self) -> None:
        """Verify toggle_algorithm alternates between dfs and prim cleanly."""
        gen: MazeGenerator = MazeGenerator(
            width=10, height=8, algorithm="dfs", seed=10
        )
        self.assertEqual(gen.config.algorithm, "dfs")
        new_algo: str = gen.toggle_algorithm()
        self.assertEqual(new_algo, "prim")
        self.assertEqual(gen.config.algorithm, "prim")
        self.assertGreater(len(gen.solution), 0)

        second_toggle: str = gen.toggle_algorithm()
        self.assertEqual(second_toggle, "dfs")
        self.assertEqual(gen.config.algorithm, "dfs")

    def test_animated_step_callback(self) -> None:
        """Verify step_callback is called during animated generation."""
        called_steps: list[Coordinate] = []

        def on_step(
            grid: object,
            coord: Coordinate,
            trail: list[Coordinate],
        ) -> None:
            """Collect visited coordinates during generation."""
            called_steps.append(coord)

        gen: MazeGenerator = MazeGenerator(width=8, height=8, seed=42)
        gen.generate(seed=42, step_callback=on_step)
        self.assertGreater(len(called_steps), 10)

    def test_bfs_wave_callback(self) -> None:
        """Verify step_callback is invoked during BFS solving wave."""
        visited_nodes: list[Coordinate] = []
        gen: MazeGenerator = MazeGenerator(width=8, height=8, seed=42)
        gen.solve(
            step_callback=lambda coord, wave: visited_nodes.append(coord)
        )
        self.assertGreater(len(visited_nodes), 5)

    def test_playable_game_movement(self) -> None:
        """Verify PlayableGame moves player and respects closed walls."""
        from mazegen.cli.game import PlayableGame
        from mazegen.cli.render import TerminalRenderer

        gen: MazeGenerator = MazeGenerator(width=8, height=8, seed=42)
        game: PlayableGame = PlayableGame(gen, TerminalRenderer())

        # Test movement attempt
        for key in ("w", "s", "a", "d"):
            game._handle_input(key)
        # Position should either be updated or stay valid in bounds
        self.assertTrue(gen.grid.in_bounds(game._player))
        self.assertFalse(gen.grid.is_masked(game._player))


if __name__ == "__main__":
    unittest.main()
