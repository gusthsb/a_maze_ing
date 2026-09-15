import sys
import mlx


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
    print("Window created! Press CTRL+C in the terminal to close it.")
    engine.mlx_loop(mlx_ptr)


if __name__ == "__main__":
    main()
