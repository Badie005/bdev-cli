"""
ConsoleManager: Singleton wrapper for Rich Console.

All output in the CLI MUST go through this module.
Using print() directly is forbidden.
"""

import sys
import locale
from typing import Any, Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.rule import Rule

from cli.utils.theme import theme

# Set UTF-8 encoding for Windows console
if sys.platform == "win32":
    import io

    try:
        if sys.stdout and hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
        if sys.stderr and hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except Exception:
        pass


class ConsoleManager:
    """
    Singleton Console wrapper for consistent output styling.

    Provides semantic methods (success, error, warning, info)
    that automatically apply the correct theme styles.

    Usage:
        from cli.utils.ui import console
        console.success("Operation completed!")
        console.error("Something went wrong")
    """

    _instance: "ConsoleManager | None" = None
    _console: Console

    def __new__(cls) -> "ConsoleManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._console = Console(
                theme=theme.rich_theme,
                force_terminal=True,
                color_system="truecolor",
                legacy_windows=True,
                width=120,
            )
        return cls._instance

    @property
    def raw(self) -> Console:
        """Access the underlying Rich Console for advanced usage."""
        return self._console

    def print(self, *args: Any, style: Optional[str] = None, **kwargs: Any) -> None:
        """
        Print with optional style.

        Args:
            *args: Content to print.
            style: Optional Rich style name from theme.
            **kwargs: Additional Console.print arguments.
        """
        self._console.print(*args, style=style, **kwargs)

    def success(self, message: str, prefix: str = "[OK]") -> None:
        """
        Display success message.

        Args:
            message: Success message text.
            prefix: Icon prefix (default: checkmark).
        """
        self._console.print(f"{prefix} {message}", style="success")

    def error(self, message: str, prefix: str = "[X]") -> None:
        """
        Display error message.

        Args:
            message: Error message text.
            prefix: Icon prefix (default: X mark).
        """
        self._console.print(f"{prefix} {message}", style="error")

    def warning(self, message: str, prefix: str = "[!]") -> None:
        """
        Display warning message.

        Args:
            message: Warning message text.
            prefix: Icon prefix (default: warning sign).
        """
        self._console.print(f"{prefix} {message}", style="warning")

    def info(self, message: str, prefix: str = "[i]") -> None:
        """
        Display informational message.

        Args:
            message: Info message text.
            prefix: Icon prefix (default: info symbol).
        """
        self._console.print(f"{prefix} {message}", style="info")

    def muted(self, message: str) -> None:
        """
        Display muted/secondary text.

        Args:
            message: Text to display in muted style.
        """
        self._console.print(message, style="muted")

    def rule(self, title: str = "", style: str = "primary") -> None:
        """
        Display a horizontal rule with optional title.

        Args:
            title: Optional centered title.
            style: Rule style (default: primary).
        """
        self._console.print(Rule(title=title, style=style))

    def panel(
        self, content: str, title: Optional[str] = None, border_style: str = "primary"
    ) -> None:
        """
        Display content in a bordered panel.

        Args:
            content: Panel body text.
            title: Optional panel title.
            border_style: Border color style.
        """
        self._console.print(
            Panel(content, title=title, border_style=border_style, padding=(1, 2))
        )

    def table(self, title: str, columns: list[str], rows: list[list[Any]]) -> None:
        """
        Display a formatted table.

        Args:
            title: Table title.
            columns: Column header names.
            rows: List of row data (each row is a list of values).
        """
        table = Table(
            title=title,
            header_style="table.header",
            border_style="table.border",
            show_lines=True,
        )

        for col in columns:
            table.add_column(col)

        for row in rows:
            table.add_row(*[str(cell) for cell in row])

        self._console.print(table)

    def banner(self, text: str) -> None:
        """
        Display a prominent banner/header.

        Args:
            text: Banner text.
        """
        styled_text = Text(text, style="primary")
        self._console.print()
        self._console.print(styled_text, justify="center")
        self.rule()


# Global console instance - import this in other modules
console = ConsoleManager()
