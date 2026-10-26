"""Terminal TrueColor Half-Block pixel renderer for A-Maze-ing.

This module renders a MazeGrid into a high-resolution 2D RGB pixel buffer
displayed via Unicode upper-half-block characters ('▀'). Each cell has a
3x3 pixel interior and 1-pixel drawn walls, ensuring zero gaps between
entry/exit blocks and walls, beveled '42' tiles, and a continuous center
line for the shortest path.
"""

from dataclasses import dataclass
from typing import TypeAlias

from mazegen.algorithms.bfs_solver import BFSSolver
from mazegen.domain.interfaces import GridProtocol
from mazegen.domain.types import Coordinate, Direction

RGB: TypeAlias = tuple[int, int, int]

ANSI_RESET: str = "\033[0m"
HALF_BLOCK_TOP: str = "▀"
CELL_PIXELS: int = 3
STRIDE: int = CELL_PIXELS + 1  # 4 pixels per cell (1px wall + 3px interior)


@dataclass(frozen=True)
class ColorTheme:
    """24-bit RGB color palette for high-resolution terminal rendering.

    Attributes:
        name: Human-readable theme name.
        floor: RGB color for open corridor background.
        wall: RGB color for 1px drawn maze walls.
        pattern_outer: RGB color for outer bevel of '42' pattern cells.
        pattern_inner: RGB color for center dot of '42' pattern cells.
        path: RGB color for the continuous shortest-path line.
        entry: RGB color for the entry cell block (flush with walls).
        exit: RGB color for the exit cell block (flush with walls).
    """

    name: str
    floor: RGB
    wall: RGB
    pattern_outer: RGB
    pattern_inner: RGB
    path: RGB
    entry: RGB
    exit: RGB


THEMES: tuple[ColorTheme, ...] = (
    ColorTheme(
        name="Golden Amber (PDF Style)",
        floor=(18, 16, 22),
        wall=(235, 170, 60),
        pattern_outer=(245, 225, 185),
        pattern_inner=(180, 140, 80),
        path=(255, 215, 90),
        entry=(185, 85, 235),
        exit=(235, 75, 115),
    ),
    ColorTheme(
        name="Classic Crisp White & Cyan",
        floor=(14, 17, 24),
        wall=(225, 232, 240),
        pattern_outer=(165, 175, 190),
        pattern_inner=(95, 105, 120),
        path=(0, 225, 255),
        entry=(45, 225, 115),
        exit=(255, 65, 85),
    ),
    ColorTheme(
        name="Cyberpunk Neon",
        floor=(16, 12, 28),
        wall=(175, 85, 255),
        pattern_outer=(0, 230, 250),
        pattern_inner=(15, 120, 160),
        path=(255, 230, 45),
        entry=(50, 245, 140),
        exit=(255, 55, 115),
    ),
    ColorTheme(
        name="Matrix Emerald",
        floor=(10, 20, 14),
        wall=(45, 205, 95),
        pattern_outer=(140, 245, 165),
        pattern_inner=(30, 125, 60),
        path=(80, 220, 255),
        entry=(245, 230, 60),
        exit=(255, 70, 70),
    ),
)


class TerminalRenderer:
    """Render a MazeGrid using a 2x-vertical-resolution RGB pixel canvas."""

    def __init__(self, theme_index: int = 0) -> None:
        """Initialize the renderer with a starting color theme index.

        Args:
            theme_index: Index into the predefined THEMES tuple.
        """
        self._theme_index: int = theme_index % len(THEMES)

    @property
    def current_theme(self) -> ColorTheme:
        """Return the currently active ColorTheme."""
        return THEMES[self._theme_index]

    def rotate_theme(self) -> ColorTheme:
        """Advance to the next color theme and return it.

        Returns:
            ColorTheme: The newly activated color theme.
        """
        self._theme_index = (self._theme_index + 1) % len(THEMES)
        return self.current_theme

    def render(
        self,
        grid: GridProtocol,
        solution: list[Direction] | None = None,
        show_path: bool = False,
    ) -> str:
        """Build the multi-line TrueColor half-block string for the maze.

        Args:
            grid: The maze grid to render.
            solution: Optional list of Directions from entry to exit.
            show_path: Whether to overlay the shortest path on the maze.

        Returns:
            str: Multi-line ANSI TrueColor string ready for stdout.
        """
        theme: ColorTheme = self.current_theme
        pw: int = grid.width * STRIDE + 1
        ph: int = grid.height * STRIDE + 1

        canvas: list[list[RGB]] = [
            [theme.floor for _ in range(pw)] for _ in range(ph)
        ]

        self._draw_cells_and_walls(canvas, grid, theme)

        if show_path and solution is not None:
            self._draw_solution_line(canvas, grid, solution, theme)
            # Re-paint entry and exit on top so they stay solid flush blocks
            self._fill_cell_block(canvas, grid.entry, theme.entry)
            self._fill_cell_block(canvas, grid.exit, theme.exit)

        return self._encode_half_blocks(canvas, pw, ph)

    def _draw_cells_and_walls(
        self,
        canvas: list[list[RGB]],
        grid: GridProtocol,
        theme: ColorTheme,
    ) -> None:
        """Paint cell interiors, '42' beveled tiles, and 1px walls.

        Args:
            canvas: 2D RGB pixel buffer to mutate.
            grid: The maze grid to inspect.
            theme: Active color theme.
        """
        for y in range(grid.height):
            py0: int = y * STRIDE + 1
            for x in range(grid.width):
                px0: int = x * STRIDE + 1
                coord: Coordinate = (x, y)

                if coord == grid.entry:
                    self._fill_cell_block(canvas, coord, theme.entry)
                elif coord == grid.exit:
                    self._fill_cell_block(canvas, coord, theme.exit)
                elif grid.is_masked(coord):
                    self._fill_42_tile(canvas, px0, py0, theme)

                if grid.has_wall(coord, Direction.NORTH):
                    for dx in range(STRIDE + 1):
                        canvas[py0 - 1][px0 - 1 + dx] = theme.wall
                if grid.has_wall(coord, Direction.SOUTH):
                    for dx in range(STRIDE + 1):
                        canvas[py0 + CELL_PIXELS][px0 - 1 + dx] = theme.wall
                if grid.has_wall(coord, Direction.WEST):
                    for dy in range(STRIDE + 1):
                        canvas[py0 - 1 + dy][px0 - 1] = theme.wall
                if grid.has_wall(coord, Direction.EAST):
                    for dy in range(STRIDE + 1):
                        canvas[py0 - 1 + dy][px0 + CELL_PIXELS] = theme.wall

    @staticmethod
    def _fill_cell_block(
        canvas: list[list[RGB]],
        coord: Coordinate,
        color: RGB,
    ) -> None:
        """Fill the 3x3 interior of coord flush against surrounding walls.

        Args:
            canvas: 2D RGB pixel buffer.
            coord: Cell (x, y) coordinate.
            color: RGB color to fill.
        """
        px0: int = coord[0] * STRIDE + 1
        py0: int = coord[1] * STRIDE + 1
        for dy in range(CELL_PIXELS):
            for dx in range(CELL_PIXELS):
                canvas[py0 + dy][px0 + dx] = color

    @staticmethod
    def _fill_42_tile(
        canvas: list[list[RGB]],
        px0: int,
        py0: int,
        theme: ColorTheme,
    ) -> None:
        """Paint a beveled 3x3 '42' pattern cell (outer ring + center dot).

        Args:
            canvas: 2D RGB pixel buffer.
            px0: Top-left interior pixel x.
            py0: Top-left interior pixel y.
            theme: Active color theme.
        """
        for dy in range(CELL_PIXELS):
            for dx in range(CELL_PIXELS):
                if dx == 1 and dy == 1:
                    canvas[py0 + dy][px0 + dx] = theme.pattern_inner
                else:
                    canvas[py0 + dy][px0 + dx] = theme.pattern_outer

    @staticmethod
    def _draw_solution_line(
        canvas: list[list[RGB]],
        grid: GridProtocol,
        solution: list[Direction],
        theme: ColorTheme,
    ) -> None:
        """Draw a continuous 1px line along the center of the shortest path.

        Args:
            canvas: 2D RGB pixel buffer.
            grid: The maze grid.
            solution: Sequence of Directions from entry to exit.
            theme: Active color theme.
        """
        coords: list[Coordinate] = BFSSolver.trace_coordinates(
            grid.entry, solution
        )
        for idx, step in enumerate(solution):
            cx: int = coords[idx][0] * STRIDE + 2
            cy: int = coords[idx][1] * STRIDE + 2
            dx, dy = step.delta
            for offset in range(STRIDE + 1):
                canvas[cy + dy * offset][cx + dx * offset] = theme.path

    @staticmethod
    def _encode_half_blocks(
        canvas: list[list[RGB]],
        pw: int,
        ph: int,
    ) -> str:
        """Encode pairs of pixel rows into ANSI TrueColor '▀' strings.

        Since terminal character cells have a ~1:2 width-to-height ratio,
        splitting each character cell vertically into top (foreground '▀')
        and bottom (background) produces square 1:1 pixels with zero gaps.

        Args:
            canvas: 2D RGB pixel buffer of height ph and width pw.
            pw: Pixel buffer width.
            ph: Pixel buffer height.

        Returns:
            str: Multi-line ANSI string.
        """
        lines: list[str] = []

        for py in range(0, ph, 2):
            row_parts: list[str] = []
            for px in range(pw):
                tr, tg, tb = canvas[py][px]
                if py + 1 < ph:
                    br, bg_c, bb = canvas[py + 1][px]
                    row_parts.append(
                        f"\033[38;2;{tr};{tg};{tb}m"
                        f"\033[48;2;{br};{bg_c};{bb}m"
                        f"{HALF_BLOCK_TOP}"
                    )
                else:
                    row_parts.append(
                        f"\033[38;2;{tr};{tg};{tb}m"
                        f"{HALF_BLOCK_TOP}"
                    )
            row_parts.append(ANSI_RESET)
            lines.append("".join(row_parts))

        return "\n".join(lines)
