import sys
import mlx
import typing


def close_window(*args: typing.Any) -> int:
    """
    Work with key_press to close the application window
    """
    print("(X button) Closing...")

    for arg in args:
        if isinstance(arg, list) and len(arg) == 2:
            engine, mlx_ptr = arg
            engine.mlx_loop_exit(mlx_ptr)
            return 0

    sys.exit(0)


def key_press(keycode: int, parameter: typing.Any = None) -> int:
    """
    Function to handle keyboard events
    """
    if parameter:
        engine, mlx_ptr = parameter
        if keycode == 65307:
            print("(ESC) Closing...")
            engine.mlx_loop_exit(mlx_ptr)
        else:
            print(f"{keycode} pressed...")

    return 0


def main() -> None:
    print("Starting Mlx")
    engine = mlx.Mlx()
    mlx_ptr = engine.mlx_init()
    if not mlx_ptr:
        print("Error: Failed to initialize mlx")
        sys.exit(1)
    width = 800
    height = 600
    title = "A-maze-ing -- Test"
    win_ptr = engine.mlx_new_window(mlx_ptr, width, height, title)
    print("Window created!")
    print("Press ESC or click the 'x' button to close it")
    mlx_data = [engine, mlx_ptr]
    engine.mlx_hook(win_ptr, 2, 1, key_press, mlx_data)
    engine.mlx_hook(win_ptr, 17, 0, close_window, mlx_data)
    engine.mlx_hook(win_ptr, 33, 0, close_window, mlx_data)
    engine.mlx_loop(mlx_ptr)
    print("Engine stopped safely. Goodbye!")


if __name__ == "__main__":
    main()
