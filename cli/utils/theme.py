"""
Claude Code Design System - Color Palette and Theme.

Inspired by Anthropic's Claude Code interface with its clean,
minimal aesthetic and warm orange accents.
"""

from dataclasses import dataclass
from rich.theme import Theme as RichTheme


@dataclass(frozen=True)
class Palette:
    """
    Claude Code-inspired color palette.

    Warm, approachable colors with a modern, minimal feel.
    """

    # Primary Brand - Claude's signature warm orange
    PRIMARY: str = "#E88638"  # Claude orange
    PRIMARY_FADE: str = "#F4A261"  # Soft orange gradient
    PRIMARY_DARK: str = "#CD5B08"  # Darker orange for emphasis

    # Backgrounds - Dark, clean surfaces
    BACKGROUND: str = "#1a1a1a"  # Deep background
    SURFACE: str = "#2d2d2d"  # Elevated elements
    SURFACE_HOVER: str = "#3a3a3a"  # Hover states
    OVERLAY: str = "#242424"  # Modal/overlay backgrounds

    # Semantic Colors - Muted, professional
    SUCCESS: str = "#6B9080"  # Soft sage green
    ERROR: str = "#E57373"  # Muted coral red
    WARNING: str = "#F4A261"  # Warm amber
    INFO: str = "#8AB4F8"  # Soft blue

    # Text Colors - Warm, readable
    TEXT: str = "#E8E8E8"  # Primary text
    TEXT_SECONDARY: str = "#B0B0B0"  # Secondary text
    TEXT_MUTED: str = "#707070"  # Muted text
    TEXT_DIM: str = "#505050"  # Very dim text

    # Accents & Highlights
    ACCENT_BLUE: str = "#7AA2F7"  # Blue accent
    ACCENT_PURPLE: str = "#BB9AF7"  # Purple accent
    ACCENT_CYAN: str = "#7DCFFF"  # Cyan accent
    ACCENT_GREEN: str = "#9CECEC"  # Green accent

    # UI Elements
    BORDER: str = "#404040"  # Borders
    DIVIDER: str = "#333333"  # Dividers
    SHADOW: str = "rgba(0,0,0,0.3)"  # Shadows


class Theme:
    """
    Claude Code theme manager.

    Provides the warm, minimal aesthetic of Claude Code.
    """

    def __init__(self) -> None:
        self._palette = Palette()

    @property
    def palette(self) -> Palette:
        """Access the color palette."""
        return self._palette

    @property
    def rich_theme(self) -> RichTheme:
        """Get Rich Theme for Console."""
        return RichTheme(
            {
                # Brand styles
                "primary": f"bold {self._palette.PRIMARY}",
                "primary.fade": self._palette.PRIMARY_FADE,
                "primary.dark": f"bold {self._palette.PRIMARY_DARK}",
                # Text styles
                "text": self._palette.TEXT,
                "text.secondary": self._palette.TEXT_SECONDARY,
                "text.muted": self._palette.TEXT_MUTED,
                "text.dim": self._palette.TEXT_DIM,
                # Semantic styles - soft, approachable
                "success": f"bold {self._palette.SUCCESS}",
                "error": f"bold {self._palette.ERROR}",
                "warning": f"bold {self._palette.WARNING}",
                "info": self._palette.INFO,
                # Prompt styles - friendly Claude-style
                "prompt": f"bold {self._palette.PRIMARY}",
                "prompt.bracket": f"bold {self._palette.PRIMARY_FADE}",
                "prompt.text": self._palette.TEXT,
                # UI Elements
                "border": self._palette.BORDER,
                "divider": self._palette.DIVIDER,
                "surface": self._palette.SURFACE,
                # Table styles
                "table.header": f"bold {self._palette.PRIMARY_FADE}",
                "table.border": self._palette.BORDER,
                "table.row": self._palette.TEXT,
                "table.row.alt": f"{self._palette.TEXT} on {self._palette.SURFACE_HOVER}",
                # Panel styles
                "panel.border": self._palette.PRIMARY_FADE,
                "panel.title": f"bold {self._palette.PRIMARY}",
                # Accent colors
                "accent.blue": self._palette.ACCENT_BLUE,
                "accent.purple": self._palette.ACCENT_PURPLE,
                "accent.cyan": self._palette.ACCENT_CYAN,
                "accent.green": self._palette.ACCENT_GREEN,
            }
        )

    def get_prompt_style(self) -> str:
        """Get PromptToolkit prompt style."""
        return f"fg:{self._palette.PRIMARY} bold"


# Global theme instance
theme = Theme()
