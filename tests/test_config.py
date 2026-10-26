"""Unit tests for ConfigParser and MazeConfig validation."""

import tempfile
import unittest
from pathlib import Path

from mazegen.core.config_parser import ConfigParser
from mazegen.domain.types import ConfigError, MazeConfig


class TestConfigParser(unittest.TestCase):
    """Test suite verifying configuration parsing and error handling."""

    def test_valid_config_with_comments_and_optionals(self) -> None:
        """Parse a valid config string with comments and optional keys."""
        raw: str = (
            "# Comment line\n"
            "WIDTH=20\n"
            "HEIGHT=15\n"
            "ENTRY=0,0\n"
            "EXIT=19,14\n"
            "OUTPUT_FILE=maze.txt\n"
            "PERFECT=False\n"
            "SEED=12345\n"
            "ALGORITHM=prim\n"
        )
        cfg: MazeConfig = ConfigParser.parse_text(raw)
        self.assertEqual(cfg.width, 20)
        self.assertEqual(cfg.height, 15)
        self.assertEqual(cfg.entry, (0, 0))
        self.assertEqual(cfg.exit, (19, 14))
        self.assertEqual(cfg.output_file, "maze.txt")
        self.assertFalse(cfg.perfect)
        self.assertEqual(cfg.seed, 12345)
        self.assertEqual(cfg.algorithm, "prim")

    def test_missing_mandatory_key_raises(self) -> None:
        """Missing any mandatory key raises ConfigError."""
        raw: str = (
            "WIDTH=20\n"
            "HEIGHT=15\n"
            "ENTRY=0,0\n"
            "EXIT=19,14\n"
            "PERFECT=True\n"
        )
        with self.assertRaises(ConfigError):
            ConfigParser.parse_text(raw)

    def test_invalid_coordinates_or_equal_entry_exit_raises(self) -> None:
        """Out-of-bounds or identical ENTRY and EXIT raise ConfigError."""
        same_entry_exit: str = (
            "WIDTH=10\n"
            "HEIGHT=10\n"
            "ENTRY=1,1\n"
            "EXIT=1,1\n"
            "OUTPUT_FILE=out.txt\n"
            "PERFECT=True\n"
        )
        with self.assertRaises(ConfigError):
            ConfigParser.parse_text(same_entry_exit)

        out_of_bounds: str = (
            "WIDTH=10\n"
            "HEIGHT=10\n"
            "ENTRY=0,0\n"
            "EXIT=10,10\n"
            "OUTPUT_FILE=out.txt\n"
            "PERFECT=True\n"
        )
        with self.assertRaises(ConfigError):
            ConfigParser.parse_text(out_of_bounds)

    def test_unknown_or_duplicate_keys_raise(self) -> None:
        """Unknown or duplicate keys in configuration raise ConfigError."""
        unknown_key: str = (
            "WIDTH=10\n"
            "HEIGHT=10\n"
            "ENTRY=0,0\n"
            "EXIT=9,9\n"
            "OUTPUT_FILE=out.txt\n"
            "PERFECT=True\n"
            "FOO=bar\n"
        )
        with self.assertRaises(ConfigError):
            ConfigParser.parse_text(unknown_key)

    def test_parse_file_and_missing_file(self) -> None:
        """Verify reading from disk and handling non-existent file paths."""
        with self.assertRaises(ConfigError):
            ConfigParser.parse_file("/nonexistent/path/config.txt")

        with tempfile.TemporaryDirectory() as tmp_dir:
            cfg_path: Path = Path(tmp_dir) / "test_cfg.txt"
            cfg_path.write_text(
                "WIDTH=12\n"
                "HEIGHT=10\n"
                "ENTRY=0,0\n"
                "EXIT=11,9\n"
                "OUTPUT_FILE=maze.txt\n"
                "PERFECT=True\n",
                encoding="utf-8",
            )
            cfg: MazeConfig = ConfigParser.parse_file(cfg_path)
            self.assertEqual(cfg.width, 12)
            self.assertEqual(cfg.height, 10)


if __name__ == "__main__":
    unittest.main()
