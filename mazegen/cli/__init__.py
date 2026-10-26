"""CLI package providing terminal rendering and interactive menu."""

from mazegen.cli.menu import InteractiveMenu
from mazegen.cli.render import ColorTheme, THEMES, TerminalRenderer

__all__ = [
    "ColorTheme",
    "InteractiveMenu",
    "THEMES",
    "TerminalRenderer",
]

