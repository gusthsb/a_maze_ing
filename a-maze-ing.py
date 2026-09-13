import mlx
import sys


def main() -> None:
    if len(sys.argv) != 2:
        print("correct using: python3 a_maze_ing.py <config.txt>")
        sys.exit(1)

    config_file = sys.argv[1]

    try:
        with open(config_file, "r") as file:
            print("Sucess to open the file")
            content = file.read()
            print(content)
    except FileNotFoundError:
        print(f"Error: '{config_file}' not found")
        sys.exit(1)


if __name__ == "__main__":
    main()
