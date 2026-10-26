"""Configuration file parser and validator for A-Maze-ing.

This module parses KEY=VALUE configuration files, ignoring blank lines and
lines starting with '#', and validates all mandatory and optional keys into
an immutable MazeConfig instance.
"""

from pathlib import Path
from mazegen.domain.types import ConfigError, Coordinate, MazeConfig

MANDATORY_KEYS: frozenset[str] = frozenset(
    {"WIDTH", "HEIGHT", "ENTRY", "EXIT", "OUTPUT_FILE", "PERFECT"}
)
OPTIONAL_KEYS: frozenset[str] = frozenset({"SEED", "ALGORITHM"})
ALL_VALID_KEYS: frozenset[str] = MANDATORY_KEYS | OPTIONAL_KEYS
SUPPORTED_ALGORITHMS: frozenset[str] = frozenset({"dfs", "prim"})


class ConfigParser:
    """Parse and validate A-Maze-ing configuration files."""

    @classmethod
    def parse_file(cls, file_path: str | Path) -> MazeConfig:
        """Read and validate a configuration file from disk.

        Args:
            file_path: Path to the configuration text file.

        Returns:
            MazeConfig: Validated and immutable configuration object.

        Raises:
            ConfigError: If the file cannot be read or contains invalid data.
        """
        path: Path = Path(file_path)
        if not path.exists():
            raise ConfigError(f"Configuration file not found: '{path}'.")
        if not path.is_file():
            raise ConfigError(
                f"Configuration path is not a regular file: '{path}'."
            )

        try:
            with path.open("r", encoding="utf-8") as handle:
                content: str = handle.read()
        except (OSError, UnicodeDecodeError) as exc:
            raise ConfigError(
                f"Failed to read configuration file '{path}': {exc}"
            ) from exc

        return cls.parse_text(content)

    @classmethod
    def parse_text(cls, content: str) -> MazeConfig:
        """Parse configuration content from a string.

        Args:
            content: Raw text content in KEY=VALUE format.

        Returns:
            MazeConfig: Validated configuration object.

        Raises:
            ConfigError: On syntax errors, missing keys, or invalid values.
        """
        raw_pairs: dict[str, str] = {}

        for line_num, raw_line in enumerate(content.splitlines(), start=1):
            stripped: str = raw_line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if "=" not in stripped:
                raise ConfigError(
                    f"Line {line_num}: Missing '=' in '{stripped}'."
                )

            key_part, value_part = stripped.split("=", maxsplit=1)
            key: str = key_part.strip()
            value: str = value_part.strip()

            if not key:
                raise ConfigError(f"Line {line_num}: Empty configuration key.")
            if key not in ALL_VALID_KEYS:
                raise ConfigError(
                    f"Line {line_num}: Unknown configuration key '{key}'."
                )
            if key in raw_pairs:
                raise ConfigError(
                    f"Line {line_num}: Duplicate configuration key '{key}'."
                )
            if not value:
                raise ConfigError(
                    f"Line {line_num}: Empty value for key '{key}'."
                )

            raw_pairs[key] = value

        missing: set[str] = set(MANDATORY_KEYS) - set(raw_pairs.keys())
        if missing:
            missing_list: str = ", ".join(sorted(missing))
            raise ConfigError(
                f"Missing mandatory configuration keys: {missing_list}."
            )

        width: int = cls._parse_positive_int("WIDTH", raw_pairs["WIDTH"], 2)
        height: int = cls._parse_positive_int("HEIGHT", raw_pairs["HEIGHT"], 2)
        entry: Coordinate = cls._parse_coord(
            "ENTRY", raw_pairs["ENTRY"], width, height
        )
        exit_coord: Coordinate = cls._parse_coord(
            "EXIT", raw_pairs["EXIT"], width, height
        )

        if entry == exit_coord:
            raise ConfigError(
                f"ENTRY and EXIT cannot be identical ({entry})."
            )

        output_file: str = raw_pairs["OUTPUT_FILE"]
        if not output_file or output_file in {".", ".."}:
            raise ConfigError(f"Invalid OUTPUT_FILE value: '{output_file}'.")

        perfect: bool = cls._parse_bool("PERFECT", raw_pairs["PERFECT"])

        seed: int | None = None
        if "SEED" in raw_pairs:
            seed = cls._parse_int("SEED", raw_pairs["SEED"])

        algorithm: str = "dfs"
        if "ALGORITHM" in raw_pairs:
            algorithm = raw_pairs["ALGORITHM"].lower()
            if algorithm not in SUPPORTED_ALGORITHMS:
                allowed: str = ", ".join(sorted(SUPPORTED_ALGORITHMS))
                raise ConfigError(
                    f"Invalid ALGORITHM '{raw_pairs['ALGORITHM']}'. "
                    f"Supported: {allowed}."
                )

        return MazeConfig(
            width=width,
            height=height,
            entry=entry,
            exit=exit_coord,
            output_file=output_file,
            perfect=perfect,
            seed=seed,
            algorithm=algorithm,
        )

    @staticmethod
    def _parse_int(key: str, raw: str) -> int:
        """Parse an integer value for a given key.

        Args:
            key: Configuration key name.
            raw: Raw string value.

        Returns:
            int: Parsed integer.

        Raises:
            ConfigError: If raw is not a valid integer.
        """
        try:
            return int(raw)
        except ValueError as exc:
            raise ConfigError(
                f"Invalid integer for {key}: '{raw}'."
            ) from exc

    @classmethod
    def _parse_positive_int(cls, key: str, raw: str, minimum: int) -> int:
        """Parse an integer value and enforce a minimum bound.

        Args:
            key: Configuration key name.
            raw: Raw string value.
            minimum: Minimum allowed integer value (inclusive).

        Returns:
            int: Validated integer.

        Raises:
            ConfigError: If value is not an integer or < minimum.
        """
        val: int = cls._parse_int(key, raw)
        if val < minimum:
            raise ConfigError(
                f"{key} must be at least {minimum}, got {val}."
            )
        return val

    @classmethod
    def _parse_coord(
        cls,
        key: str,
        raw: str,
        width: int,
        height: int,
    ) -> Coordinate:
        """Parse a comma-separated 'x,y' coordinate within grid bounds.

        Args:
            key: Configuration key name ('ENTRY' or 'EXIT').
            raw: Raw string in 'x,y' format.
            width: Grid width upper bound (exclusive).
            height: Grid height upper bound (exclusive).

        Returns:
            Coordinate: Validated (x, y) tuple.

        Raises:
            ConfigError: If format is malformed or out of bounds.
        """
        parts: list[str] = raw.split(",")
        if len(parts) != 2:
            raise ConfigError(
                f"Invalid coordinate format for {key}: '{raw}'. "
                f"Expected 'x,y'."
            )
        x: int = cls._parse_int(f"{key}.x", parts[0].strip())
        y: int = cls._parse_int(f"{key}.y", parts[1].strip())
        if not (0 <= x < width and 0 <= y < height):
            raise ConfigError(
                f"{key} ({x},{y}) is out of bounds for grid {width}x{height}."
            )
        return (x, y)

    @staticmethod
    def _parse_bool(key: str, raw: str) -> bool:
        """Parse a boolean configuration value ('True' or 'False').

        Args:
            key: Configuration key name.
            raw: Raw string value.

        Returns:
            bool: Parsed boolean value.

        Raises:
            ConfigError: If raw does not represent a boolean.
        """
        normalized: str = raw.lower()
        if normalized in {"true", "1", "yes"}:
            return True
        if normalized in {"false", "0", "no"}:
            return False
        raise ConfigError(
            f"Invalid boolean for {key}: '{raw}'. Expected True or False."
        )
