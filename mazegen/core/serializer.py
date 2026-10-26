"""Maze output serializer for A-Maze-ing.

This module serializes a generated MazeGrid and its shortest path solution
into the hexadecimal output format required by the specification.
"""

from pathlib import Path
from mazegen.domain.interfaces import GridProtocol
from mazegen.domain.types import Direction, MazeError


class MazeSerializer:
    """Serialize maze structure and solution path to text or file."""

    @staticmethod
    def to_hex_rows(grid: GridProtocol) -> list[str]:
        """Convert each grid row into a lowercase hexadecimal string.

        Args:
            grid: The generated maze grid.

        Returns:
            list[str]: List of hexadecimal strings, one per row.
        """
        rows: list[str] = []
        for y in range(grid.height):
            row_chars: list[str] = [
                f"{grid.get_walls((x, y)):x}" for x in range(grid.width)
            ]
            rows.append("".join(row_chars))
        return rows

    @classmethod
    def serialize(
        cls,
        grid: GridProtocol,
        solution: list[Direction],
    ) -> str:
        """Format the complete output file payload as a string.

        Format:
        - H lines of W hexadecimal digits (one row per line)
        - 1 empty line
        - Entry coordinates as 'x,y'
        - Exit coordinates as 'x,y'
        - Shortest path string using 'N', 'E', 'S', 'W'
        - Every line terminated by '\\n'

        Args:
            grid: The generated maze grid.
            solution: Ordered sequence of Directions from entry to exit.

        Returns:
            str: Formatted output file content ending with '\\n'.
        """
        lines: list[str] = cls.to_hex_rows(grid)
        lines.append("")
        lines.append(f"{grid.entry[0]},{grid.entry[1]}")
        lines.append(f"{grid.exit[0]},{grid.exit[1]}")
        lines.append("".join(step.char for step in solution))
        return "\n".join(lines) + "\n"

    @classmethod
    def save(
        cls,
        grid: GridProtocol,
        solution: list[Direction],
        output_path: str | Path,
    ) -> None:
        """Write the serialized maze and solution to disk.

        Args:
            grid: The generated maze grid.
            solution: Ordered sequence of Directions from entry to exit.
            output_path: Destination file path.

        Raises:
            MazeError: If writing the file fails due to an OS error.
        """
        path: Path = Path(output_path)
        payload: str = cls.serialize(grid, solution)
        try:
            if path.parent and not path.parent.exists():
                path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("w", encoding="utf-8") as handle:
                handle.write(payload)
        except OSError as exc:
            raise MazeError(
                f"Failed to write output file '{path}': {exc}"
            ) from exc

