"""Terminal Unicode box-drawing visual renderer for A-Maze-ing.

This module renders a MazeGrid using Unicode Heavy Box-Drawing characters
(┏, ━, ┳, ┓, ┃, ┣, ╋, ┫, ┗, ┻, ┛) so walls are explicitly drawn as thin
connected lines and corridors remain wide and visually unmistakable.
"""

from dataclasses import dataclass
from mazegen.algorithms.bfs_solver import BFSSolver
from mazegen.domain.interfaces import GridProtocol
from mazegen.domain.types import Coordinate, Direction

ANSI_RESET: str = "\033[0m"

# 4-bit junction lookup: bit 0=UP, bit 1=RIGHT, bit 2=DOWN, bit 3=LEFT
BOX_JUNCTIONS: dict[int, str] = {
    0: " ",
    1: "╹",
    2: "╺",
    3: "┗",
    4: "╻",
    5: "┃",
    6: "┏",
    7: "┣",
    8: "╸",
    9: "┛",
    10: "━",
    11: "┻",
    12: "┓",
    13: "┫",
    14: "┳",
    15: "╋",
}


@dataclass(frozen=True)
class ColorTheme:
    """ANSI color palette for terminal maze rendering.

    Attributes:
        name: Human-readable theme name.
        wall: ANSI escape code for drawn maze walls.
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
        name="Amber Gold & Cyan",
        wall="\033[33m",        # Amber / Gold walls (like PDF screenshot)
        pattern_42="\033[97m",  # Bright White '42' blocks
        path="\033[96m",        # Bright Cyan path dots
        entry="\033[92m",       # Bright Green entry
        exit="\033[91m",        # Bright Red exit
    ),
    ColorTheme(
        name="Classic White & Yellow",
        wall="\033[97m",        # Bright White walls
        pattern_42="\033[90m",  # Cool Grey '42' blocks
        path="\033[93m",        # Bright Yellow path dots
        entry="\033[92m",       # Bright Green entry
        exit="\033[91m",        # Bright Red exit
    ),
    ColorTheme(
        name="Matrix Neon Green",
        wall="\033[32m",        # Green walls
        pattern_42="\033[92m",  # Neon Green '42' blocks
        path="\033[96m",        # Cyan path dots
        entry="\033[93m",       # Yellow entry
        exit="\033[91m",        # Bright Red exit
    ),
    ColorTheme(
        name="Cyberpunk Magenta",
        wall="\033[95m",        # Magenta walls
        pattern_42="\033[96m",  # Cyan '42' blocks
        path="\033[93m",        # Yellow path dots
        entry="\033[92m",       # Green entry
        exit="\033[91m",        # Red exit
    ),
)


class TerminalRenderer:
    """Render a MazeGrid using connected Unicode box-drawing walls."""

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
        """Build the multi-line Unicode box-drawing string for the maze.

        Args:
            grid: The maze grid to render.
            solution: Optional list of Directions from entry to exit.
            show_path: Whether to overlay the shortest path on the maze.

        Returns:
            str: Multi-line string ready to print to stdout.
        """
        theme: ColorTheme = self.current_theme
        path_cells, h_doors, v_doors = self._compute_path_sets(
            grid, solution, show_path
        )

        lines: list[str] = []
        for gy in range(grid.height + 1):
            lines.append(
                self._render_wall_row(grid, gy, h_doors, theme)
            )
            if gy < grid.height:
                lines.append(
                    self._render_cell_row(
                        grid, gy, path_cells, v_doors, theme
                    )
                )
        return "\n".join(lines)

    def _render_wall_row(
        self,
        grid: GridProtocol,
        gy: int,
        h_doors: set[Coordinate],
        theme: ColorTheme,
    ) -> str:
        """Render a horizontal wall and junction row at grid y-boundary gy.

        Args:
            grid: The maze grid.
            gy: Horizontal grid line index (0..height).
            h_doors: Set of open horizontal doorways traversed by the path.
            theme: Active color theme.

        Returns:
            str: Rendered horizontal line string.
        """
        parts: list[str] = []
        w: int = grid.width
        for gx in range(w + 1):
            mask: int = self._junction_mask(grid, gx, gy)
            junction_ch: str = BOX_JUNCTIONS[mask]
            parts.append(f"{theme.wall}{junction_ch}{ANSI_RESET}")

            if gx < w:
                if self._has_h_wall(grid, gx, gy):
                    parts.append(f"{theme.wall}━━━{ANSI_RESET}")
                elif (gx, gy) in h_doors:
                    parts.append(f"{theme.path} • {ANSI_RESET}")
                else:
                    parts.append("   ")
        return "".join(parts)

    def _render_cell_row(
        self,
        grid: GridProtocol,
        gy: int,
        path_cells: set[Coordinate],
        v_doors: set[Coordinate],
        theme: ColorTheme,
    ) -> str:
        """Render a row of cell interiors and vertical walls at row gy.

        Args:
            grid: The maze grid.
            gy: Cell row index (0..height - 1).
            path_cells: Coordinates visited along the shortest path.
            v_doors: Set of open vertical doorways traversed by the path.
            theme: Active color theme.

        Returns:
            str: Rendered cell row string.
        """
        parts: list[str] = []
        w: int = grid.width
        for gx in range(w):
            if self._has_v_wall(grid, gx, gy):
                parts.append(f"{theme.wall}┃{ANSI_RESET}")
            elif (gx, gy) in v_doors:
                parts.append(f"{theme.path}•{ANSI_RESET}")
            else:
                parts.append(" ")

            coord: Coordinate = (gx, gy)
            if coord == grid.entry:
                parts.append(f"{theme.entry}███{ANSI_RESET}")
            elif coord == grid.exit:
                parts.append(f"{theme.exit}███{ANSI_RESET}")
            elif grid.is_masked(coord):
                parts.append(f"{theme.pattern_42}▓▓▓{ANSI_RESET}")
            elif coord in path_cells:
                parts.append(f"{theme.path} • {ANSI_RESET}")
            else:
                parts.append("   ")

        if self._has_v_wall(grid, w, gy):
            parts.append(f"{theme.wall}┃{ANSI_RESET}")
        else:
            parts.append(" ")
        return "".join(parts)

    @classmethod
    def _junction_mask(
        cls,
        grid: GridProtocol,
        gx: int,
        gy: int,
    ) -> int:
        """Compute the 4-bit box-drawing mask at grid vertex (gx, gy).

        Args:
            grid: The maze grid.
            gx: Vertex column index (0..width).
            gy: Vertex row index (0..height).

        Returns:
            int: Bitmask (1=UP, 2=RIGHT, 4=DOWN, 8=LEFT).
        """
        mask: int = 0
        if cls._has_v_wall(grid, gx, gy - 1):
            mask |= 1
        if cls._has_h_wall(grid, gx, gy):
            mask |= 2
        if cls._has_v_wall(grid, gx, gy):
            mask |= 4
        if cls._has_h_wall(grid, gx - 1, gy):
            mask |= 8
        return mask

    @staticmethod
    def _has_h_wall(grid: GridProtocol, x: int, y: int) -> bool:
        """Check if the horizontal wall above cell (x, y) is closed.

        Args:
            grid: The maze grid.
            x: Column index.
            y: Boundary row index (0..height).

        Returns:
            bool: True if the horizontal wall segment is closed.
        """
        if not (0 <= x < grid.width):
            return False
        if y == 0:
            return grid.has_wall((x, 0), Direction.NORTH)
        if y == grid.height:
            return grid.has_wall((x, grid.height - 1), Direction.SOUTH)
        return grid.has_wall((x, y), Direction.NORTH)

    @staticmethod
    def _has_v_wall(grid: GridProtocol, x: int, y: int) -> bool:
        """Check if the vertical wall to the left of cell (x, y) is closed.

        Args:
            grid: The maze grid.
            x: Boundary column index (0..width).
            y: Row index.

        Returns:
            bool: True if the vertical wall segment is closed.
        """
        if not (0 <= y < grid.height):
            return False
        if x == 0:
            return grid.has_wall((0, y), Direction.WEST)
        if x == grid.width:
            return grid.has_wall((grid.width - 1, y), Direction.EAST)
        return grid.has_wall((x, y), Direction.WEST)

    @staticmethod
    def _compute_path_sets(
        grid: GridProtocol,
        solution: list[Direction] | None,
        show_path: bool,
    ) -> tuple[set[Coordinate], set[Coordinate], set[Coordinate]]:
        """Compute visited cells and open doorways along the solution path.

        Args:
            grid: The maze grid.
            solution: Optional list of Directions from entry to exit.
            show_path: Whether path rendering is enabled.

        Returns:
            tuple[set[Coordinate], set[Coordinate], set[Coordinate]]:
                (path_cells, horizontal_doors, vertical_doors).
        """
        if not show_path or solution is None:
            return set(), set(), set()

        coords: list[Coordinate] = BFSSolver.trace_coordinates(
            grid.entry, solution
        )
        path_cells: set[Coordinate] = set(coords)
        h_doors: set[Coordinate] = set()
        v_doors: set[Coordinate] = set()

        for idx, step in enumerate(solution):
            cx, cy = coords[idx]
            nx, ny = coords[idx + 1]
            if step in (Direction.EAST, Direction.WEST):
                v_doors.add((max(cx, nx), cy))
            else:
                h_doors.add((cx, max(cy, ny)))

        return path_cells, h_doors, v_doors
