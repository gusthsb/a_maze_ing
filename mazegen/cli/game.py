"""Playable interactive maze navigation controller for A-Maze-ing.

This module provides the interactive gameplay mode allowing the user to
navigate the generated maze from entry to exit using WASD or arrow keys,
and traces the completed route line upon reaching the exit.
"""

import sys
from typing import TextIO

from mazegen.cli.render import TerminalRenderer
from mazegen.core.generator import MazeGenerator
from mazegen.core.grid import MazeGrid
from mazegen.domain.types import Coordinate, Direction

KEY_DIRECTIONS: dict[str, Direction] = {
    "w": Direction.NORTH,
    "W": Direction.NORTH,
    "s": Direction.SOUTH,
    "S": Direction.SOUTH,
    "a": Direction.WEST,
    "A": Direction.WEST,
    "d": Direction.EAST,
    "D": Direction.EAST,
}


class PlayableGame:
    """Run interactive keyboard-driven maze navigation in the terminal."""

    def __init__(
        self,
        generator: MazeGenerator,
        renderer: TerminalRenderer,
    ) -> None:
        """Initialize the game with the generator's grid and a renderer.

        Args:
            generator: Active MazeGenerator instance.
            renderer: TerminalRenderer instance.
        """
        self._generator: MazeGenerator = generator
        self._renderer: TerminalRenderer = renderer
        self._grid: MazeGrid = generator.grid
        self._player: Coordinate = self._grid.entry
        self._steps: int = 0
        self._route: list[Direction] = []

    def play(self) -> bool:
        """Enter the interactive game loop until exit or quit.

        Returns:
            bool: True if the player reached the exit, False if quit early.
        """
        if sys.stdin.isatty():
            return self._play_interactive()
        return self._play_stream()

    def _play_interactive(self) -> bool:
        """Run game using unbuffered raw cbreak terminal input.

        Returns:
            bool: True if the player reached the exit.
        """
        import termios
        import tty

        fd: int = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setcbreak(fd)
            while True:
                if self._player == self._grid.exit:
                    self._draw_victory()
                    return True

                self._draw_screen()
                key: str = self._read_key(sys.stdin)
                if key in {"q", "Q", "\x03"}:
                    print("\nQuit game. Returning to menu.")
                    return False

                self._handle_input(key)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

    def _play_stream(self) -> bool:
        """Fallback game loop for non-interactive piped input.

        Returns:
            bool: True if the player reached the exit.
        """
        while True:
            if self._player == self._grid.exit:
                self._draw_victory()
                return True

            self._draw_screen()
            line: str = sys.stdin.readline()
            if not line:
                return False
            for char in line.strip():
                if char in {"q", "Q"}:
                    return False
                self._handle_input(char)
                if self._player == self._grid.exit:
                    self._draw_victory()
                    return True

    def _handle_input(self, key: str) -> None:
        """Process a single directional key and update position and route.

        Args:
            key: Single character mapped to a cardinal Direction.
        """
        if key not in KEY_DIRECTIONS:
            return

        direction: Direction = KEY_DIRECTIONS[key]
        if self._grid.has_wall(self._player, direction):
            return

        dx, dy = direction.delta
        self._player = (self._player[0] + dx, self._player[1] + dy)
        self._steps += 1

        if self._route and self._route[-1] == direction.opposite:
            self._route.pop()
        else:
            self._route.append(direction)

    def _draw_screen(self) -> None:
        """Clear and redraw the maze with the player's current position."""
        frame: str = self._renderer.render(
            grid=self._grid,
            solution=None,
            show_path=False,
            player=self._player,
        )
        sys.stdout.write("\033[H\033[2J\033[3J")
        sys.stdout.write(frame + "\n")
        sys.stdout.write(
            f"🧭 STEPS: {self._steps:03d} | "
            f"POSITION: {self._player} -> EXIT: {self._grid.exit}\n"
            "Controls: [W/A/S/D] or Arrows to move | [Q] Quit to menu\n"
        )
        sys.stdout.flush()

    def _draw_victory(self) -> None:
        """Render the completed maze with the traced route line to the exit."""
        traced_frame: str = self._renderer.render(
            grid=self._grid,
            solution=self._route,
            show_path=True,
            player=None,
        )
        optimal_len: int = len(self._generator.solution)
        sys.stdout.write("\033[H\033[2J\033[3J")
        sys.stdout.write(traced_frame + "\n")
        sys.stdout.write(
            f"\n\033[92m🎉 VICTORY! Escaped in {self._steps} steps "
            f"(optimal route: {optimal_len} steps)! 🎉\033[0m\n"
            "Press any key to return to menu...\n"
        )
        sys.stdout.flush()
        try:
            sys.stdin.read(1)
        except (EOFError, OSError):
            pass

    @staticmethod
    def _read_key(stream: TextIO) -> str:
        """Read a single character or ANSI escape sequence for arrow keys.

        Args:
            stream: Text stream (sys.stdin).

        Returns:
            str: Normalized single character ('w', 'a', 's', 'd', 'q', etc.).
        """
        char: str = stream.read(1)
        if char == "\x1b":
            seq: str = stream.read(2)
            arrow_map: dict[str, str] = {
                "[A": "w",
                "[B": "s",
                "[C": "d",
                "[D": "a",
            }
            return arrow_map.get(seq, "")
        return char
