"""Interactive terminal menu controller for A-Maze-ing.

This module manages the user interaction loop: regenerating mazes, toggling
the shortest path, rotating colors, switching algorithms, animating maze
carving and BFS wavefront solving, and launching the playable mode.
"""

from random import SystemRandom
import sys
import time

from mazegen.cli.game import PlayableGame
from mazegen.cli.render import TerminalRenderer
from mazegen.core.generator import MazeGenerator
from mazegen.domain.interfaces import GridProtocol
from mazegen.domain.types import Coordinate, Direction


class InteractiveMenu:
    """Run the interactive CLI loop for visualizing the maze."""

    def __init__(
        self,
        generator: MazeGenerator,
        renderer: TerminalRenderer | None = None,
    ) -> None:
        """Initialize the interactive menu with a generator and renderer.

        Args:
            generator: Configured MazeGenerator instance.
            renderer: Optional custom TerminalRenderer instance.
        """
        self._generator: MazeGenerator = generator
        self._renderer: TerminalRenderer = (
            renderer if renderer is not None else TerminalRenderer()
        )
        self._show_path: bool = False
        self._sys_rng: SystemRandom = SystemRandom()

    def run(self) -> None:
        """Generate initial maze, save output, and enter interactive loop."""
        self._generator.generate()
        self._generator.save()

        while True:
            self._display_screen()
            try:
                choice: str = input("Choice? (1-8): ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nExiting A-Maze-ing.")
                break

            if choice == "1":
                next_seed: int = self._sys_rng.randint(0, 2**31 - 1)
                self._generator.generate(seed=next_seed)
                self._generator.save()
            elif choice == "2":
                self._show_path = not self._show_path
            elif choice == "3":
                self._renderer.rotate_theme()
            elif choice == "4":
                self._generator.toggle_algorithm()
                self._generator.save()
            elif choice == "5":
                self._run_animated_generation()
            elif choice == "6":
                self._run_animated_solution()
            elif choice == "7":
                game: PlayableGame = PlayableGame(
                    generator=self._generator,
                    renderer=self._renderer,
                )
                if game.play():
                    self._show_path = True
            elif choice == "8":
                break
            else:
                print(
                    f"Invalid choice '{choice}'. Please enter 1-8.",
                    file=sys.stderr,
                )

    def _run_animated_generation(self) -> None:
        """Animate carving of a maze in-place with clear algorithmic pacing."""
        next_seed: int = self._sys_rng.randint(0, 2**31 - 1)
        step_counter: list[int] = [0]
        algo: str = self._generator.config.algorithm.lower()

        # Calibrated delay: DFS has ~500 steps (with backtrack), Prim has ~280
        delay: float = 0.025 if algo == "dfs" else 0.040

        def step_animator(
            grid: GridProtocol,
            active: Coordinate,
            trail: list[Coordinate],
        ) -> None:
            """Render in-place frames displaying the carving progression."""
            step_counter[0] += 1
            frame: str = self._renderer.render(
                grid=grid,
                solution=None,
                show_path=False,
                active_cell=active,
                trail=trail[-8:],
            )
            sys.stdout.write("\033[H\033[2J\033[3J")
            sys.stdout.write(frame + "\n")
            if algo == "dfs":
                info: str = (
                    f"\033[93m⚡ DFS Backtracker (Snake & Backtrack) | "
                    f"Step: {step_counter[0]:03d} | "
                    f"Stack Depth: {len(trail):02d}\033[0m"
                )
            else:
                info = (
                    f"\033[95m⚡ Prim (Radial Frontier Expansion) | "
                    f"Step: {step_counter[0]:03d} | "
                    f"Carving at: {active}\033[0m"
                )
            sys.stdout.write(info + "\n")
            sys.stdout.flush()
            time.sleep(delay)

        self._generator.generate(seed=next_seed, step_callback=step_animator)
        self._generator.save()
        time.sleep(0.5)

    def _run_animated_solution(self) -> None:
        """Animate BFS search wave expanding and trace the shortest path."""
        wave_counter: list[int] = [0]
        latest_wave: list[set[Coordinate]] = [set()]
        wave_delay: float = 0.025

        def wave_animator(
            active: Coordinate,
            visited: set[Coordinate],
        ) -> None:
            """Render in-place frames for the expanding BFS wavefront."""
            wave_counter[0] += 1
            latest_wave[0] = visited
            frame: str = self._renderer.render(
                grid=self._generator.grid,
                solution=None,
                show_path=False,
                active_cell=active,
                wave=visited,
            )
            sys.stdout.write("\033[H\033[2J\033[3J")
            sys.stdout.write(frame + "\n")
            sys.stdout.write(
                f"\033[96m🌊 BFS Wavefront Search (FIFO Queue) | "
                f"Visited: {len(visited):03d} cells | "
                f"Active: {active}\033[0m\n"
            )
            sys.stdout.flush()
            time.sleep(wave_delay)

        solution: list[Direction] = self._generator.solve(
            step_callback=wave_animator
        )
        time.sleep(0.4)

        # Trace the solution line step-by-step from entry to exit
        path_delay: float = 0.035
        for length in range(1, len(solution) + 1):
            frame = self._renderer.render(
                grid=self._generator.grid,
                solution=solution[:length],
                show_path=True,
                wave=latest_wave[0],
            )
            sys.stdout.write("\033[H\033[2J\033[3J")
            sys.stdout.write(frame + "\n")
            step_dir: str = solution[length - 1].name
            sys.stdout.write(
                f"\033[92m✨ Tracing Shortest Path | "
                f"Step {length:03d}/{len(solution):03d} "
                f"({step_dir})\033[0m\n"
            )
            sys.stdout.flush()
            time.sleep(path_delay)

        self._show_path = True
        time.sleep(0.8)

    def _display_screen(self) -> None:
        """Render the current maze state and print the interactive options."""
        visual: str = self._renderer.render(
            grid=self._generator.grid,
            solution=self._generator.solution,
            show_path=self._show_path,
        )
        if sys.stdout.isatty():
            sys.stdout.write("\033[H\033[2J\033[3J")
            sys.stdout.flush()
        print(visual)
        algo_name: str = self._generator.config.algorithm.upper()
        theme_name: str = self._renderer.current_theme.name
        path_len: int = len(self._generator.solution)
        print(
            f"=== A-Maze-ing === [{algo_name} | Theme: {theme_name} | "
            f"Shortest path: {path_len} steps]"
        )
        print("1. Re-generate a new maze")
        print("2. Show / Hide the shortest path")
        print("3. Rotate the wall colours")
        print(f"4. Toggle algorithm (current: {algo_name})")
        print("5. Animate maze generation (Snake trail)")
        print("6. Animate solution path (BFS search wave)")
        print("7. Play maze (WASD controls)")
        print("8. Quit")
