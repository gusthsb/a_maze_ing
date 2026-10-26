"""Main CLI entry point for the A-Maze-ing maze generator and solver.

Usage:
    python3 a_maze_ing.py config.txt
"""

import sys
from mazegen.cli.menu import InteractiveMenu
from mazegen.core.generator import MazeGenerator
from mazegen.domain.types import MazeError


def main(argv: list[str] | None = None) -> int:
    """Execute the A-Maze-ing application from command-line arguments.

    Args:
        argv: Optional list of CLI arguments (defaults to sys.argv[1:]).

    Returns:
        int: Process exit code (0 on success, non-zero on error).
    """
    args: list[str] = argv if argv is not None else sys.argv[1:]
    if len(args) != 1:
        print(
            "Error: Invalid number of arguments.\n"
            "Usage: python3 a_maze_ing.py <config_file>",
            file=sys.stderr,
        )
        return 1

    config_path: str = args[0]

    try:
        generator: MazeGenerator = MazeGenerator.from_file(config_path)
        menu: InteractiveMenu = InteractiveMenu(generator=generator)
        menu.run()
    except MazeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nInterrupted by user.", file=sys.stderr)
        return 130
    except Exception as exc:
        print(f"Unexpected error: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())

