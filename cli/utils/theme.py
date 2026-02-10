"""
Claude Code Design System - Color Palette and Theme.

Centralizes all colors to prevent hardcoded values and ensure
consistent styling across the CLI.
"""

from dataclasses import dataclass
from rich.theme import Theme as RichTheme


@dataclass(frozen=True)
class Palette:
    """
    Immutable color palette based on Claude Code design system.
    
    All colors are hex strings compatible with Rich.
    """

    # Primary Brand
    PRIMARY: str = "#D95628"       # Brick orange - main accent
    PRIMARY_LIGHT: str = "#FF6B35" # Lighter orange for highlights

    # Backgrounds
    BACKGROUND: str = "#282828"    # Dark background
    SURFACE: str = "#3C3836"       # Elevated surfaces
    OVERLAY: str = "#504945"       # Overlays and modals

    # Semantic Colors
    SUCCESS: str = "#98971A"       # Green - positive actions
    ERROR: str = "#CC241D"         # Red - errors and destructive
    WARNING: str = "#D79921"       # Yellow/amber - warnings
    INFO: str = "#458588"          # Teal - informational

    # Text Colors
    TEXT: str = "#EBDBB2"          # Primary text
    TEXT_MUTED: str = "#928374"    # Secondary/muted text
    TEXT_DISABLED: str = "#665C54" # Disabled state

    # Syntax Highlighting
    KEYWORD: str = "#FB4934"       # Keywords
    STRING: str = "#B8BB26"        # Strings
    NUMBER: str = "#D3869B"        # Numbers
    COMMENT: str = "#928374"       # Comments
    FUNCTION: str = "#FABD2F"      # Functions


class Theme:
    """
    Theme manager providing Rich-compatible theme configuration.
    
    This is the single source of truth for all styling in the CLI.
    
    Usage:
        theme = Theme()
        console = Console(theme=theme.rich_theme)
    """

    def __init__(self) -> None:
        self._palette = Palette()

    @property
    def palette(self) -> Palette:
        """Access the color palette directly."""
        return self._palette

    @property
    def rich_theme(self) -> RichTheme:
        """
        Get Rich Theme object for Console initialization.
        
        Returns:
            RichTheme configured with Claude Code colors.
        """
        return RichTheme({
            # Base styles
            "primary": f"bold {self._palette.PRIMARY}",
            "secondary": self._palette.TEXT_MUTED,
            "muted": self._palette.TEXT_MUTED,
            
            # Semantic styles
            "success": f"bold {self._palette.SUCCESS}",
            "error": f"bold {self._palette.ERROR}",
            "warning": f"bold {self._palette.WARNING}",
            "info": self._palette.INFO,
            
            # UI Elements
            "prompt": f"bold {self._palette.PRIMARY}",
            "prompt.symbol": self._palette.PRIMARY_LIGHT,
            "title": f"bold {self._palette.TEXT}",
            "subtitle": self._palette.TEXT_MUTED,
            "rule": self._palette.SURFACE,
            
            # Table styles
            "table.header": f"bold {self._palette.PRIMARY}",
            "table.border": self._palette.SURFACE,
            
            # Syntax (for code display)
            "code.keyword": self._palette.KEYWORD,
            "code.string": self._palette.STRING,
            "code.number": self._palette.NUMBER,
            "code.comment": self._palette.COMMENT,
            "code.function": self._palette.FUNCTION,
        })

    def get_prompt_style(self) -> str:
        """
        Get ANSI style string for PromptToolkit prompts.
        
        Returns:
            Style string compatible with prompt_toolkit.
        """
        return f"fg:{self._palette.PRIMARY} bold"


# Global theme instance
theme = Theme()
