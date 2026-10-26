"""Terminal ASCII/ANSI visual renderer for A-Maze-ing.

This module renders a MazeGrid into a colored Unicode block string suitable
for terminal display, highlighting walls, the '42' pattern, entry/exit
points, and the optional shortest path.
"""

from dataclasses import dataclass
from mazegen.algorithms.bfs_solver import BFSSolver
from mazegen.domain.interfaces import GridProtocol
from mazegen.domain.types import Coordinate, Direction

ANSI_RESET: str = "\033[0m"
BLOCK_SOLID: str = "██"
BLOCK_PATTERN: str = "▓▓"
BLOCK_EMPTY: str = "  "


@dataclass(frozen=True)
class ColorTheme:
    """ANSI color palette for terminal maze rendering.

    Attributes:
        name: Human-readable theme name.
        wall: ANSI escape code for maze walls.
        pattern_42: ANSI escape code for the '42' closed cells.
        path: ANSI escape code for the shortest solution path.
        entry: ANSI escape code for the entry cell.
        exit: ANSI escape code for the exit cell.
    """

    name: str
    wall: str
    pattern_42: str
    path: str
    entry: str
    exit: str


THEMES: tuple[ColorTheme, ...] = (
    ColorTheme(
        name="Classic White & Cyan",
        wall="\033[97m",        # Bright White
        pattern_42="\033[90m",  # Cool Grey
        path="\033[96m",        # Bright Cyan
        entry="\033[92m",       # Bright Green
        exit="\033[91m",        # Bright Red
    ),
    ColorTheme(
        name="Amber Retro",
        wall="\033[33m",        # Amber / Yellow
        pattern_42="\033[97m",  # Bright White
        path="\033[93m",        # Bright Yellow
        entry="\033[95m",       # Magenta
        exit="\033[91m",        # Bright Red
    ),
    ColorTheme(
        name="Matrix Green",
        wall="\033[32m",        # Green
        pattern_42="\033[92m",  # Neon Green
        path="\033[94m",        # Bright Blue
        entry="\033[96m",       # Cyan
        exit="\033[91m",        # Bright Red
    ),
    ColorTheme(
        name="Cyberpunk Neon",
        wall="\033[35m",        # Purple
        pattern_42="\033[96m",  # Cyan
        path="\033[93m",        # Yellow
        entry="\033[92m",       # Green
        exit="\033[91m",        # Red
    ),
)


class TerminalRenderer:
    """Render a MazeGrid to the terminal using ANSI colors and blocks."""

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
        """Build the multi-line ANSI string representing the maze.

        Args:
            grid: The maze grid to render.
            solution: Optional list of Directions from entry to exit.
            show_path: Whether to overlay the shortest path on the maze.

        Returns:
            str: Multi-line string ready to print to stdout.
        """
        theme: ColorTheme = self.current_theme
        canvas_w: int = 2 * grid.width + 1
        canvas_h: int = 2 * grid.height + 1

        wall_tile: str = f"{theme.wall}{BLOCK_SOLID}{ANSI_RESET}"
        pattern_tile: str = f"{theme.pattern_42}{BLOCK_PATTERN}{ANSI_RESET}"
        path_tile: str = f"{theme.path}{BLOCK_SOLID}{ANSI_RESET}"
        entry_tile: str = f"{theme.entry}{BLOCK_SOLID}{ANSI_RESET}"
        exit_tile: str = f"{theme.exit}{BLOCK_SOLID}{ANSI_RESET}"

        canvas: list[list[str]] = [
            [BLOCK_EMPTY for _ in range(canvas_w)]
            for _ in range(canvas_h)
        ]
        is_wall_grid: list[list[bool]] = [
            [False for _ in range(canvas_w)]
            for _ in range(canvas_h)
        ]

        # Populate horizontal and vertical wall segments and cell interiors
        for y in range(grid.height):
            cy: int = 2 * y + 1
            for x in range(grid.width):
                cx: int = 2 * x + 1
                coord: Coordinate = (x, y)

                if grid.is_masked(coord):
                    canvas[cy][cx] = pattern_tile
                elif coord == grid.entry:
                    canvas[cy][cx] = entry_tile
                elif coord == grid.exit:
                    canvas[cy][cx] = exit_tile

                if grid.has_wall(coord, Direction.NORTH):
                    canvas[cy - 1][cx] = wall_tile
                    is_wall_grid[cy - 1][cx] = True
                if grid.has_wall(coord, Direction.SOUTH):
                    canvas[cy + 1][cx] = wall_tile
                    is_wall_grid[cy + 1][cx] = True
                if grid.has_wall(coord, Direction.WEST):
                    canvas[cy][cx - 1] = wall_tile
                    is_wall_grid[cy][cx - 1] = True
                if grid.has_wall(coord, Direction.EAST):
                    canvas[cy][cx + 1] = wall_tile
                    is_wall_grid[cy][cx + 1] = True

        # Populate corner/pillar tiles (even y, even x)
        for py in range(0, canvas_h, 2):
            for px in range(0, canvas_w, 2):
                if self._pillar_has_adjacent_wall(
                    is_wall_grid, px, py, canvas_w, canvas_h
                ):
                    canvas[py][px] = wall_tile
                    is_wall_grid[py][px] = True

        # Overlay shortest path if requested
        if show_path and solution is not None:
            self._overlay_path(
                canvas=canvas,
                entry=grid.entry,
                exit_coord=grid.exit,
                solution=solution,
                path_tile=path_tile,
            )

        return "\n".join("".join(row) for row in canvas)

    @staticmethod
    def _pillar_has_adjacent_wall(
        is_wall_grid: list[list[bool]],
        px: int,
        py: int,
        canvas_w: int,
        canvas_h: int,
    ) -> bool:
        """Check if a corner pillar connects to any closed wall segment.

        Args:
            is_wall_grid: Boolean matrix marking closed wall segments.
            px: Pillar x index in canvas coordinates.
            py: Pillar y index in canvas coordinates.
            canvas_w: Total canvas width.
            canvas_h: Total canvas height.

        Returns:
            bool: True if at least one adjacent wall segment is closed.
        """
        for dx, dy in ((0, -1), (1, 0), (0, 1), (-1, 0)):
            nx, ny = px + dx, py + dy
            if 0 <= nx < canvas_w and 0 <= ny < canvas_h:
                if is_wall_grid[ny][nx]:
                    return True
        return False

    @staticmethod
    def _overlay_path(
        canvas: list[list[str]],
        entry: Coordinate,
        exit_coord: Coordinate,
        solution: list[Direction],
        path_tile: str,
    ) -> None:
        """Draw the shortest path across cell interiors and open doorways.

        Args:
            canvas: 2D character tile buffer to mutate.
            entry: Entry coordinate.
            exit_coord: Exit coordinate.
            solution: Sequence of Directions forming the shortest path.
            path_tile: Colored tile string for path segments.
        """
        coords: list[Coordinate] = BFSSolver.trace_coordinates(entry, solution)
        for idx, current in enumerate(coords):
            cx: int = 2 * current[0] + 1
            cy: int = 2 * current[1] + 1
            if current != entry and current != exit_coord:
                canvas[cy][cx] = path_tile

            if idx < len(solution):
                dx, dy = solution[idx].delta
                canvas[cy + dy][cx + dx] = path_tile

