import sys
import typing


def parse(file: str) -> dict[str, typing.Any]:
    """
    Read, validate and extract the content of the file configuration
    Ignore comments and verify the mandatory's keys
    (WIDTH, HEIGHT, ENTRY, EXIT, OUTPUT_FILE, PERFECT) have to be in the txt
    """
    config: dict[str, typing.Any] = dict()
    keys: list[str] = ["WIDTH", "HEIGHT", "ENTRY", "EXIT", "OUTPUT_FILE", "PERFECT"]

    try:
        with open(file, 'r') as f:
            for line in f:
                line = line.strip()

                if not line or line.startswith('#'):
                    continue
                if '=' in line:
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip()
                else:
                    print(f"Error: invalid syntax in the config_file '{line}'")
                    sys.exit(1)

    except FileNotFoundError:
        print(f"Error: '{file}' config_file not found")
        sys.exit(1)

    for key in keys:
        if key not in config:
            print(f"Error: mandatory key '{key}' is missing in the '{file}'")
            sys.exit(1)

    try:
        config['WIDTH'] = int(config['WIDTH'])
        config['HEIGHT'] = int(config['HEIGHT'])
        config['PERFECT'] = config['PERFECT'].lower() == 'true'
    except ValueError:
        print("Error: WIDTH and HEIGHT has too be int")
        sys.exit(1)

    return config


def main() -> None:
    if len(sys.argv) != 2:
        print("correct using: python3 a_maze_ing.py <config.txt>")
        sys.exit(1)

    config_file = sys.argv[1]
    config_data = parse(config_file)

    # Teste para leitura/parsing do txt
    print("=== Configurações Carregadas ===")
    for key, value in config_data.items():
        print(f"{key}: {value} (Tipo: {type(value).__name__})")


if __name__ == "__main__":
    main()
