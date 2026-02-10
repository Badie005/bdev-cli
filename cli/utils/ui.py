"""
ConsoleManager: Claude Code-inspired output manager with advanced animations.

All output goes through this module with Claude's warm, minimal aesthetic
and sophisticated micro-animations.
"""

import sys
import time
from typing import Any, Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.rule import Rule
from rich.align import Align
from rich.columns import Columns
from rich.live import Live

from cli.utils.theme import theme
from cli.utils.animation import animations, AnimationSpeed

# UTF-8 encoding for Windows
if sys.platform == "win32":
    try:
        if sys.stdout and hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
        if sys.stderr and hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except Exception:
        pass


class ConsoleManager:
    """
    Claude Code-style console manager with advanced animations.

    Warm, friendly, minimal output design with smooth micro-interactions.
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
                width=110,
                highlight=False,
                emoji=True,
                force_interactive=True,
            )
        return cls._instance

    @property
    def raw(self) -> Console:
        """Access underlying Rich Console."""
        return self._console

    def print(self, *args: Any, style: Optional[str] = None, **kwargs: Any) -> None:
        """Print with optional style."""
        self._console.print(*args, style=style, **kwargs)

    def success(self, message: str, icon: str = "", animate: bool = True) -> None:
        """
        Success with green checkmark and optional fade animation.

        Args:
            message: Success message text
            icon: Icon to use (default: checkmark)
            animate: Whether to animate the output
        """
        icon = icon or "✓"
        p = theme.palette

        if animate:
            animations.play_fade_in(
                self._console,
                f"[text.muted]{icon}[/text.muted] [success]{message}[/success]",
                duration=0.2,
            )
        else:
            self._console.print(
                f"[text.muted]{icon}[/text.muted] [success]{message}[/success]"
            )

    def error(self, message: str, icon: str = "", animate: bool = True) -> None:
        """
        Error with soft X and optional shake animation.

        Args:
            message: Error message text
            icon: Icon to use (default: X)
            animate: Whether to animate with shake effect
        """
        icon = icon or "×"
        p = theme.palette

        if animate:
            animations.play_shake(
                self._console,
                f"[text.muted]{icon}[/text.muted] [error]{message}[/error]",
                times=2,
                distance=1,
                style=f"error",
            )
        else:
            self._console.print(
                f"[text.muted]{icon}[/text.muted] [error]{message}[/error]"
            )

    def warning(self, message: str, icon: str = "", animate: bool = True) -> None:
        """
        Warning with exclamation and optional pulse animation.

        Args:
            message: Warning message text
            icon: Icon to use (default: warning sign)
            animate: Whether to animate with pulse effect
        """
        icon = icon or "⚠"
        p = theme.palette

        if animate:
            animations.play_fade_in(
                self._console,
                f"[text.muted]{icon}[/text.muted] [warning]{message}[/warning]",
                duration=0.2,
            )
        else:
            self._console.print(
                f"[text.muted]{icon}[/text.muted] [warning]{message}[/warning]"
            )

    def info(self, message: str, icon: str = "", animate: bool = True) -> None:
        """
        Info with dot and optional fade animation.

        Args:
            message: Info message text
            icon: Icon to use (default: bullet)
            animate: Whether to animate with fade effect
        """
        icon = icon or "●"
        p = theme.palette

        if animate:
            animations.play_fade_in(
                self._console,
                f"[text.muted]{icon}[/text.muted] [info]{message}[/info]",
                duration=0.15,
            )
        else:
            self._console.print(
                f"[text.muted]{icon}[/text.muted] [info]{message}[/info]"
            )

    def type(self, text: str, style: str = "text", speed: float = 0.015) -> None:
        """
        Typewriter animation for text.

        Args:
            text: Text to type out
            style: Optional Rich style
            speed: Delay between characters
        """
        p = theme.palette
        full_style = f"{p.TEXT}" if style == "text" else style
        animations.play_typewriter(self._console, text, speed=speed, style=full_style)

    def muted(self, message: str) -> None:
        """Secondary/muted text."""
        self._console.print(message, style="text.muted")

    def dim(self, message: str) -> None:
        """Very dim text."""
        self._console.print(message, style="text.dim")

    def rule(self, title: str = "", style: str = "divider") -> None:
        """Horizontal divider with optional title."""
        if title:
            self._console.print(Rule(title, characters="─", style=style))
        else:
            self._console.print(Rule(characters="─", style=style))

    def panel(
        self,
        content: str,
        title: Optional[str] = None,
        border_style: str = "panel.border",
        padding: tuple[int, int] = (1, 2),
    ) -> None:
        """Content in bordered panel."""
        self._console.print(
            Panel(content, title=title, border_style=border_style, padding=padding)
        )

    def table(
        self,
        title: str = "",
        columns: list[str] | None = None,
        rows: list[list[Any]] | None = None,
    ) -> None:
        """Formatted table."""
        table = Table(
            title=title if title else None,
            header_style="table.header",
            border_style="table.border",
            show_header=bool(columns),
            show_lines=False,
            padding=(0, 1),
        )

        if columns:
            for col in columns:
                table.add_column(col)

        if rows:
            for row in rows:
                table.add_row(*[str(cell) for cell in row])

        self._console.print(table)

    def banner(
        self,
        title: str = "B.DEV",
        subtitle: str = "Your Development Assistant",
        animate: bool = True,
    ) -> None:
        """
        Claude Code-style welcome banner with animation.

        Args:
            title: Main banner title
            subtitle: Banner subtitle
            animate: Whether to animate the banner
        """
        p = theme.palette

        self._console.print()

        if animate:
            # Animated title appearance
            time.sleep(0.1)
        else:
            time.sleep(0)

        # Main title with gradient effect
        title_text = Text.assemble(
            ("  B", f"bold {p.TEXT}"),
            (".", f"bold {p.PRIMARY}"),
            ("DEV", f"bold {p.TEXT}"),
            ("  ", ""),
        )

        self._console.print(Align.center(title_text))

        if animate:
            time.sleep(0.15)

        # Subtitle
        self._console.print(
            Align.center(
                Text(f"  {subtitle}  ", style=f"on {p.SURFACE} {p.TEXT_SECONDARY}")
            )
        )

        # Decorative line
        self._console.print()

        if animate:
            time.sleep(0.1)

        self._console.print(
            Align.center(Text(f"─ {p.PRIMARY_FADE} ─" * 8, style=f"{p.DIVIDER}"))
        )
        self._console.print()

    def command_list(
        self, commands: list[tuple[str, str]], animate: bool = True
    ) -> None:
        """
        Styled command list like Claude Code help.

        Args:
            commands: List of (command, description) tuples
            animate: Whether to animate the list appearance
        """
        p = theme.palette
        self._console.print()

        for i, (cmd, desc) in enumerate(commands):
            if animate and i == 0:
                time.sleep(0.05)
            self._console.print(
                Text.assemble(
                    ("  ", ""),
                    (cmd, f"bold {p.PRIMARY}"),
                    ("  ", ""),
                    (desc, f"{p.TEXT_MUTED}"),
                )
            )

        self._console.print()

    def spinner(self, message: str, icon: str = "◇") -> None:
        """Show a spinner-style indicator."""
        p = theme.palette
        self._console.print(
            f"[text.muted]{icon}[/text.muted] [text.secondary]{message}[/text.secondary]"
        )

    def badge(self, text: str, style: str = "primary") -> None:
        """Small badge/pill indicator."""
        p = theme.palette
        bg_color = getattr(p, style.upper(), p.PRIMARY)
        badge = Text(f" {text} ", style=f"on {bg_color} {p.BACKGROUND}")
        self._console.print(badge)

    def code_block(self, code: str, language: str = "") -> None:
        """Display code in a styled block."""
        self.panel(code, title=f" {language} " if language else None)

    def section(self, title: str, animate: bool = True) -> None:
        """
        Section header with underlining.

        Args:
            title: Section title
            animate: Whether to animate the section header
        """
        p = theme.palette

        self._console.print()

        if animate:
            animations.play_fade_in(
                self._console,
                Text(f" {title} ", style=f"bold {p.PRIMARY}"),
                duration=0.1,
            )
        else:
            self._console.print(Text(f" {title} ", style=f"bold {p.PRIMARY}"))

        self.rule(style=f"{p.DIVIDER}")

    def empty_line(self, count: int = 1) -> None:
        """Print empty lines for spacing."""
        for _ in range(count):
            self._console.print()

    def header(self, text: str, level: int = 1, animate: bool = True) -> None:
        """
        Header at different levels.

        Args:
            text: Header text
            level: Header level (1=h1, 2=h2, 3=h3)
            animate: Whether to animate the header
        """
        p = theme.palette

        if level == 1:
            self._console.print()
            if animate:
                animations.play_fade_in(
                    self._console,
                    Text(f"  {text}  ", style=f"bold {p.PRIMARY}"),
                    duration=0.15,
                )
            else:
                self._console.print(Text(f"  {text}  ", style=f"bold {p.PRIMARY}"))
            self.rule()
        elif level == 2:
            self._console.print()
            self._console.print(Text(f"▸ {text}", style=f"bold {p.TEXT}"))
        else:
            self._console.print(Text(f"  • {text}", style=f"{p.TEXT_SECONDARY}"))

    def thinking(self, message: str = "") -> None:
        """
        Show animated thinking indicator.

        Args:
            message: Optional message to display
        """
        animations.play_thinking(self._console, message, duration=0.5)

    def pulse(self, text: str, times: int = 2, duration: float = 0.8) -> None:
        """
        Pulse animation for attention-grabbing.

        Args:
            text: Text to pulse
            times: Number of pulse cycles
            duration: Total duration
        """
        animations.play_pulse(self._console, text, times, duration)

    def loading(self, message: str = "Loading...", spinner_type: str = "dots") -> Any:
        """Create a loading spinner context manager."""
        return animations.create_loader(self._console, message, spinner_type)

    def progress(self, message: str = "Processing", total: int = 100) -> Any:
        """Create a progress bar context manager."""
        return animations.create_progress(self._console, message, total)

    # NEW: Rich UI Components

    def card(
        self, title: str, content: str, icon: str = "", action_text: str = ""
    ) -> None:
        """
        Display a rich card with optional action button.

        Args:
            title: Card title
            content: Card body content
            icon: Optional icon for title
            action_text: Optional action button text
        """
        p = theme.palette

        if icon:
            title = f"{icon} {title}"

        if action_text:
            content = f"{content}\n\n[on {p.PRIMARY}] {action_text} [/]"

        self.panel(content, title=title, border_style="panel.border")

    def status_card(
        self, status: str, title: str, details: Optional[list[str]] = None
    ) -> None:
        """
        Display a status indicator card.

        Args:
            status: Status level (success, warning, error, info)
            title: Card title
            details: Optional list of detail items
        """
        p = theme.palette

        status_colors = {
            "success": p.SUCCESS,
            "warning": p.WARNING,
            "error": p.ERROR,
            "info": p.INFO,
        }

        color = status_colors.get(status.lower(), p.INFO)
        border_style = f"on {color}"

        content = title
        if details:
            content += "\n" + "\n".join(f"  • {detail}" for detail in details)

        self.panel(content, border_style=border_style)

    def toast(self, message: str, duration: float = 3.0, type: str = "info") -> None:
        """
        Display temporary notification toast.

        Args:
            message: Toast message
            duration: How long to display (seconds)
            type: Toast type (success, warning, error, info)
        """
        p = theme.palette

        type_colors = {
            "success": f"[on {p.SUCCESS}]",
            "warning": f"[on {p.WARNING}]",
            "error": f"[on {p.ERROR}]",
            "info": f"[on {p.INFO}]",
        }

        prefix = type_colors.get(type.lower(), "")
        self.print(f"{prefix} {message}")
        time.sleep(duration)
        # In a real implementation, we'd use Live to remove it

    def notification(
        self, title: str, message: str, type: str = "info", persistent: bool = True
    ) -> None:
        """
        Display rich notification panel.

        Args:
            title: Notification title
            message: Notification message
            type: Notification type
            persistent: Whether notification stays until dismissed
        """
        p = theme.palette

        type_colors = {
            "success": p.SUCCESS,
            "warning": p.WARNING,
            "error": p.ERROR,
            "info": p.INFO,
        }

        color = type_colors.get(type.lower(), p.INFO)
        icon_map = {"success": "✓", "warning": "⚠", "error": "✗", "info": "●"}

        icon = icon_map.get(type.lower(), "●")

        content = f"{icon} {message}"
        self.panel(content, title=title, border_style=f"on {color}")

    def count_up(self, from_value: int, to_value: int, duration: float = 1.0) -> None:
        """
        Animate counting up from one number to another.

        Args:
            from_value: Starting number
            to_value: Target number
            duration: Animation duration
        """
        animations.play_count_up(self._console, from_value, to_value, duration)

    def progress_bar(self, current: int, total: int, width: int = 40) -> None:
        """
        Display animated progress bar.

        Args:
            current: Current progress
            total: Total value
            width: Bar width
        """
        animations.play_progress(self._console, current, total, width)


# Global instance
console = ConsoleManager()
