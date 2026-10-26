"""Interactive terminal menu controller for A-Maze-ing.

This module manages the user interaction loop required by Chapter V of the
specification: regenerating mazes, toggling the shortest path display,
rotating color themes, and exiting cleanly.
"""

from random import SystemRandom
import sys

from mazegen.cli.render import TerminalRenderer
from mazegen.core.generator import MazeGenerator


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
                choice: str = input("Choice? (1-4): ").strip()
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
                break
            else:
                print(
                    f"Invalid choice '{choice}'. Please enter 1, 2, 3, or 4.",
                    file=sys.stderr,
                )

    def _display_screen(self) -> None:
        """Render the current maze state and print the interactive options."""
        visual: str = self._renderer.render(
            grid=self._generator.grid,
            solution=self._generator.solution,
            show_path=self._show_path,
        )
        print(visual)
        print("=== A-Maze-ing ===")
        print("1. Re-generate a new maze")
        print("2. Show / Hide the shortest path")
        print("3. Rotate the wall colours")
        print("4. Quit")
