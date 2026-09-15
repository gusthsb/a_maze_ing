import sys
import mlx
import typing


def close_window(parameter: typing.Any = None) -> int:
    """
    Work with key_press to close the application window
    """
    print("Window closed gracefully")
    sys.exit(0)


def key_press(keycode: int, parameter: typing.Any = None) -> int:
    """
    Function to handle keyboard events
    """
    if keycode == 65307:
        print("Closing...")
        sys.exit(0)
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
    engine.mlx_key_hook(win_ptr, key_press, None)
    engine.mlx_hook(win_ptr, 17, 0, close_window, None)
    engine.mlx_loop(mlx_ptr)


if __name__ == "__main__":
    main()
