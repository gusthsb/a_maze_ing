"""Terminal TrueColor Half-Block pixel renderer for A-Maze-ing.

This module renders a MazeGrid into a high-resolution 2D RGB pixel buffer
displayed via Unicode upper-half-block characters ('▀'). Each cell has a
3x3 pixel interior and 1-pixel drawn walls, ensuring zero gaps between
entry/exit blocks and walls, beveled '42' tiles, and a continuous center
line for the solution path.
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
        name="Classic Crisp White & Cyan",
        floor=(14, 17, 24),
        wall=(225, 232, 240),
        pattern_outer=(150, 162, 180),
        pattern_inner=(80, 90, 110),
        path=(0, 215, 255),
        entry=(45, 225, 115),
        exit=(255, 65, 85),
    ),
    ColorTheme(
        name="Ocean Cobalt & Gold",
        floor=(10, 15, 28),
        wall=(65, 140, 245),
        pattern_outer=(135, 195, 250),
        pattern_inner=(35, 85, 165),
        path=(255, 220, 40),
        entry=(50, 235, 120),
        exit=(255, 70, 90),
    ),
    ColorTheme(
        name="Cyberpunk Violet & Mint",
        floor=(16, 12, 28),
        wall=(175, 85, 255),
        pattern_outer=(215, 165, 255),
        pattern_inner=(100, 45, 160),
        path=(0, 245, 200),
        entry=(55, 245, 115),
        exit=(255, 55, 115),
    ),
    ColorTheme(
        name="Matrix Emerald & Sunset",
        floor=(10, 20, 14),
        wall=(45, 200, 105),
        pattern_outer=(145, 235, 175),
        pattern_inner=(30, 115, 60),
        path=(255, 165, 40),
        entry=(0, 215, 255),
        exit=(255, 65, 80),
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
        player: Coordinate | None = None,
        active_cell: Coordinate | None = None,
        trail: list[Coordinate] | None = None,
        wave: set[Coordinate] | None = None,
    ) -> str:
        """Build the multi-line TrueColor half-block string for the maze.

        Args:
            grid: The maze grid to render.
            solution: Optional list of Directions from entry to exit.
            show_path: Whether to overlay the path line on the maze.
            player: Optional (x, y) coordinates of the player avatar.
            active_cell: Optional coordinate highlighted during animation.
            trail: Optional list of recent stack coordinates forming a trail.
            wave: Optional set of coordinates in active BFS search wave.

        Returns:
            str: Multi-line ANSI TrueColor string ready for stdout.
        """
        theme: ColorTheme = self.current_theme
        pw: int = grid.width * STRIDE + 1
        ph: int = grid.height * STRIDE + 1

        canvas: list[list[RGB]] = [
            [theme.floor for _ in range(pw)] for _ in range(ph)
        ]

        self._draw_cells_and_walls(
            canvas=canvas,
            grid=grid,
            theme=theme,
            player=player,
            active_cell=active_cell,
            trail=trail,
            wave=wave,
        )

        if show_path and solution is not None:
            self._draw_solution_line(canvas, grid, solution, theme)
            self._fill_cell_block(canvas, grid.entry, theme.entry)
            self._fill_cell_block(canvas, grid.exit, theme.exit)
            if player is not None:
                self._fill_cell_block(canvas, player, (255, 230, 40))

        return self._encode_half_blocks(canvas, pw, ph)

    def _draw_cells_and_walls(
        self,
        canvas: list[list[RGB]],
        grid: GridProtocol,
        theme: ColorTheme,
        player: Coordinate | None = None,
        active_cell: Coordinate | None = None,
        trail: list[Coordinate] | None = None,
        wave: set[Coordinate] | None = None,
    ) -> None:
        """Paint cell interiors, '42' beveled tiles, and 1px walls.

        Args:
            canvas: 2D RGB pixel buffer to mutate.
            grid: The maze grid to inspect.
            theme: Active color theme.
            player: Optional player coordinate.
            active_cell: Optional animated carver cell coordinate.
            trail: Optional trailing snake coordinates.
            wave: Optional BFS search wave coordinates.
        """
        trail_indices: dict[Coordinate, int] = (
            {coord: idx for idx, coord in enumerate(trail)}
            if trail
            else {}
        )
        trail_len: int = len(trail) if trail else 1

        for y in range(grid.height):
            py0: int = y * STRIDE + 1
            for x in range(grid.width):
                px0: int = x * STRIDE + 1
                coord: Coordinate = (x, y)

                if coord == player:
                    self._fill_cell_block(canvas, coord, (255, 230, 40))
                elif coord == active_cell:
                    self._fill_cell_block(canvas, coord, (255, 255, 220))
                elif coord in trail_indices:
                    ratio: float = (trail_indices[coord] + 1) / trail_len
                    r: int = int(245 * ratio)
                    g: int = int(195 * ratio)
                    b: int = int(45 * ratio)
                    self._fill_cell_block(canvas, coord, (r, g, b))
                elif coord == grid.entry:
                    self._fill_cell_block(canvas, coord, theme.entry)
                elif coord == grid.exit:
                    self._fill_cell_block(canvas, coord, theme.exit)
                elif grid.is_masked(coord):
                    self._fill_42_tile(canvas, px0, py0, theme)
                elif wave is not None and coord in wave:
                    self._fill_cell_block(canvas, coord, (30, 65, 120))

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
        """Draw a continuous 1px line along the center of the solution path.

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
