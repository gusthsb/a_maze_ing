import sys
import mlx
import typing
from maze_generator import MazeGenerator


def draw_horizontal_line(
    engine: typing.Any,
    mlx_ptr: typing.Any,
    win_ptr: typing.Any,
    x: int,
    y: int,
    length: int,
    color: int,
) -> None:
    """Draws a horizontal line using pixels."""
    for i in range(length + 1):
        engine.mlx_pixel_put(mlx_ptr, win_ptr, x + i, y, color)


def draw_vertical_line(
    engine: typing.Any,
    mlx_ptr: typing.Any,
    win_ptr: typing.Any,
    x: int,
    y: int,
    length: int,
    color: int,
) -> None:
    """Draws a vertical line using pixels."""
    for i in range(length + 1):
        engine.mlx_pixel_put(mlx_ptr, win_ptr, x, y + i, color)


def fill_square(
    engine: typing.Any,
    mlx_ptr: typing.Any,
    win_ptr: typing.Any,
    x: int,
    y: int,
    size: int,
    color: int,
) -> None:
    """Fills the inside of a cell with a specific color."""
    for i in range(2, size - 1):
        for j in range(2, size - 1):
            engine.mlx_pixel_put(mlx_ptr, win_ptr, x + i, y + j, color)


def render_maze(
    engine: typing.Any,
    mlx_ptr: typing.Any,
    win_ptr: typing.Any,
    maze: MazeGenerator,
    size: int = 20,
    offset_x: int = 50,
    offset_y: int = 50,
) -> None:
    """
    Renders the maze grid.
    Bits (1 == North, 2 == East, 4 == South, 8 == West) to draw walls.
    """
    grid = maze.get_structure()

    wall_color = 0xFF00FF00  # Verde Opaco
    entry_color = 0xFFFF00FF  # Rosa Opaco
    exit_color = 0xFFFF0000  # Vermelho Opaco

    for y in range(maze.height):
        for x in range(maze.width):
            cell_value = grid[y][x]

            px = offset_x + (x * size)
            py = offset_y + (y * size)

            if cell_value & 1:
                draw_horizontal_line(engine, mlx_ptr, win_ptr, px, py, size, wall_color)
            if cell_value & 2:
                draw_vertical_line(
                    engine, mlx_ptr, win_ptr, px + size, py, size, wall_color
                )
            if cell_value & 4:
                draw_horizontal_line(
                    engine, mlx_ptr, win_ptr, px, py + size, size, wall_color
                )
            if cell_value & 8:
                draw_vertical_line(engine, mlx_ptr, win_ptr, px, py, size, wall_color)

    entry_x, entry_y = maze.entry
    fill_square(
        engine,
        mlx_ptr,
        win_ptr,
        offset_x + (entry_x * size),
        offset_y + (entry_y * size),
        size,
        entry_color,
    )

    exit_x, exit_y = maze.exit_pos
    fill_square(
        engine,
        mlx_ptr,
        win_ptr,
        offset_x + (exit_x * size),
        offset_y + (exit_y * size),
        size,
        exit_color,
    )

    engine.mlx_do_sync(mlx_ptr)


def loop_render(parameter: typing.Any = None) -> int:
    """
    Loop Hook: Runs continuously in the background 60 times per second.
    This defeats any WSL window manager black screens!
    """
    if parameter:
        engine, mlx_ptr, win_ptr, maze = parameter
        render_maze(engine, mlx_ptr, win_ptr, maze)
    return 0


def close_window(*args: typing.Any) -> int:
    """Closes the application window safely."""
    print("(X button) Closing...")
    for arg in args:
        if isinstance(arg, list) and len(arg) == 2:
            engine, mlx_ptr = arg
            engine.mlx_loop_exit(mlx_ptr)
            return 0
    sys.exit(0)


def key_press(keycode: int, parameter: typing.Any = None) -> int:
    """Handles keyboard events."""
    if parameter:
        engine, mlx_ptr = parameter
        if keycode == 65307:
            print("(ESC) Closing...")
            engine.mlx_loop_exit(mlx_ptr)
    return 0


def main() -> None:
    print("Generating Maze...")
    maze = MazeGenerator(
        width=30, height=20, entry=(0, 0), exit_pos=(29, 19), perfect=False
    )

    maze.generate()

    print("Starting MLX Engine...")
    engine = mlx.Mlx()
    mlx_ptr = engine.mlx_init()
    if not mlx_ptr:
        print("Error: Failed to initialize mlx")
        sys.exit(1)

    width = 800
    height = 600
    title = "A-maze-ing -- Live Preview"
    win_ptr = engine.mlx_new_window(mlx_ptr, width, height, title)

    mlx_data = [engine, mlx_ptr]
    expose_data = [engine, mlx_ptr, win_ptr, maze]

    engine.mlx_hook(win_ptr, 2, 1, key_press, mlx_data)
    engine.mlx_hook(win_ptr, 17, 0, close_window, mlx_data)
    engine.mlx_hook(win_ptr, 33, 0, close_window, mlx_data)

    engine.mlx_loop_hook(mlx_ptr, loop_render, expose_data)

    engine.mlx_loop(mlx_ptr)
    print("Engine stopped safely.")


if __name__ == "__main__":
    main()
