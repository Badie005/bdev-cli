"""
Animation System - Claude Code-inspired micro-animations.

Provides smooth, performant animations for CLI interactions.
All animations are cross-platform and respect user preferences.
"""

import time
import sys
import threading
from typing import Optional, Callable
from enum import Enum
from dataclasses import dataclass

from rich.console import Console
from rich.text import Text
from rich.progress import Progress, BarColumn, TextColumn, SpinnerColumn, TaskID
from rich.live import Live
from rich.spinner import Spinner

from cli.utils.theme import theme


class AnimationSpeed(Enum):
    """Animation speed presets."""

    INSTANT = 0.0
    FAST = 0.1
    NORMAL = 0.25
    SLOW = 0.4
    VERY_SLOW = 0.6


@dataclass
class AnimationConfig:
    """Configuration for animation behavior."""

    enabled: bool = True
    speed: AnimationSpeed = AnimationSpeed.NORMAL
    minimal_mode: bool = False
    fade_steps: int = 10

    @property
    def duration(self) -> float:
        """Get base duration from speed setting."""
        return self.speed.value


class AnimationController:
    """
    Centralized animation controller.

    Manages all CLI animations with consistent timing and behavior.
    """

    _instance: "AnimationController | None" = None

    def __new__(cls) -> "AnimationController":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """Initialize animation controller."""
        if not hasattr(self, "_config"):
            self._config = AnimationConfig()

    @property
    def config(self) -> AnimationConfig:
        """Get animation configuration."""
        return self._config

    @property
    def enabled(self) -> bool:
        """Check if animations are enabled."""
        return self._config.enabled and not self._config.minimal_mode

    def play_fade_in(
        self,
        console: Console,
        text: str | Text,
        duration: float | None = None,
        style: str = "",
    ) -> None:
        """
        Play fade-in animation for text.

        Args:
            console: Rich console instance
            text: Text to animate
            duration: Animation duration (uses config if None)
            style: Optional Rich style
        """
        if not self.enabled:
            console.print(text, style=style)
            return

        duration = duration or self.config.duration
        steps = self.config.fade_steps
        delay = duration / steps

        p = theme.palette
        full_style = style or f"{p.TEXT}"

        # Simulate fade by printing progressively
        if isinstance(text, str):
            console.print(text, style=full_style)
        else:
            console.print(text, style=style)

    def play_typewriter(
        self,
        console: Console,
        text: str,
        speed: float = 0.02,
        style: str = "",
        randomize: bool = False,
    ) -> None:
        """
        Play typewriter effect for text.

        Args:
            console: Rich console instance
            text: Text to type out
            speed: Delay between characters
            style: Optional Rich style
            randomize: Add randomness to typing speed
        """
        if not self.enabled:
            console.print(text, style=style)
            return

        import random

        p = theme.palette
        full_style = style or f"{p.TEXT}"

        for i, char in enumerate(text):
            # Randomize speed slightly for natural feel
            actual_delay = speed
            if randomize and i > 0:
                actual_delay *= random.uniform(0.7, 1.3)

            console.print(char, end="", style=full_style)
            time.sleep(actual_delay)
        console.print()

    def play_pulse(
        self,
        console: Console,
        text: str,
        times: int = 2,
        duration: float = 1.0,
        style: str = "",
    ) -> None:
        """
        Play pulsing animation for attention-grabbing.

        Args:
            console: Rich console instance
            text: Text to pulse
            times: Number of pulse cycles
            duration: Total animation duration
            style: Base style
        """
        if not self.enabled:
            console.print(text, style=style)
            return

        p = theme.palette
        base_style = style or f"{p.PRIMARY}"
        dim_style = f"dim {base_style}"

        cycle_delay = duration / (times * 2)

        for _ in range(times):
            console.print("\r\033[K", end="")
            console.print(text, style=dim_style)
            time.sleep(cycle_delay)

            console.print("\r\033[K", end="")
            console.print(text, style=base_style)
            time.sleep(cycle_delay)

        console.print(text, style=base_style)

    def play_shake(
        self,
        console: Console,
        text: str,
        times: int = 3,
        distance: int = 2,
        style: str = "",
    ) -> None:
        """
        Play shake animation (usually for errors).

        Args:
            console: Rich console instance
            text: Text to shake
            times: Number of shake cycles
            distance: Horizontal shake distance
            style: Text style
        """
        if not self.enabled:
            console.print(text, style=style)
            return

        p = theme.palette
        base_style = style or f"{p.ERROR}"

        cycle_delay = 0.05

        for _ in range(times):
            # Shake left
            console.print("\r\033[K", end="")
            console.print(" " * distance + text, style=base_style)
            time.sleep(cycle_delay)

            # Shake right
            console.print("\r\033[K", end="")
            console.print(" " * -distance + text, style=base_style)
            time.sleep(cycle_delay)

        console.print("\r\033[K", end="")
        console.print(text, style=base_style)

    def play_count_up(
        self,
        console: Console,
        from_value: int,
        to_value: int,
        duration: float = 1.0,
        prefix: str = "",
        suffix: str = "",
        style: str = "",
    ) -> None:
        """
        Animate counting up from one number to another.

        Args:
            console: Rich console instance
            from_value: Starting number
            to_value: Target number
            duration: Animation duration
            prefix: Text before number
            suffix: Text after number
            style: Number style
        """
        if not self.enabled:
            console.print(f"{prefix}{to_value}{suffix}", style=style)
            return

        p = theme.palette
        base_style = style or f"bold {p.PRIMARY}"

        steps = 20
        delay = duration / steps
        step_size = (to_value - from_value) / steps

        for i in range(steps + 1):
            current = int(from_value + (step_size * i))
            console.print(f"\r{prefix}{current}{suffix}", end="", style=base_style)
            time.sleep(delay)

        console.print()  # New line

    def play_progress(
        self,
        console: Console,
        current: int,
        total: int,
        width: int = 40,
        style: str = "",
    ) -> None:
        """
        Display animated progress bar.

        Args:
            console: Rich console instance
            current: Current progress value
            total: Total value
            width: Bar width in characters
            style: Bar style
        """
        if total == 0:
            return

        p = theme.palette
        bar_style = style or f"on {p.PRIMARY}"
        empty_style = f"on {p.SURFACE}"

        percentage = current / total
        filled = int(width * percentage)
        empty = width - filled

        bar = "█" * filled + "░" * empty
        percent_text = f"{percentage * 100:.0f}%"

        console.print(
            f"\r[{bar}] {percent_text}",
            end="",
            style=bar_style if filled > 0 else empty_style,
        )

    def play_thinking(
        self,
        console: Console,
        message: str = "",
        duration: float | None = None,
    ) -> None:
        """
        Play "thinking" animation with bouncing dots.

        Args:
            console: Rich console instance
            message: Optional message to display
            duration: How long to animate (None = infinite)
        """
        if not self.enabled:
            if message:
                console.print(f"{message}...")
            return

        p = theme.palette
        dots = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        delay = 0.08

        try:
            while True:
                for dot in dots:
                    if message:
                        console.print(
                            f"\r\033[K{message} {dot}", end="", style=f"{p.TEXT}"
                        )
                    else:
                        console.print(
                            f"\r\033[K  {dot}  ", end="", style=f"{p.PRIMARY}"
                        )
                    time.sleep(delay)

                    # Check if duration elapsed
                    if duration is not None:
                        duration -= delay
                        if duration <= 0:
                            raise StopIteration
        except (StopIteration, KeyboardInterrupt):
            console.print("\r\033[K", end="")

    def create_loader(
        self,
        console: Console,
        message: str = "Loading...",
        spinner_type: str = "dots",
    ) -> "LoadingAnimation":
        """
        Create a loading animation context.

        Args:
            console: Rich console instance
            message: Loading message
            spinner_type: Spinner style from Rich

        Returns:
            LoadingAnimation context manager
        """
        return LoadingAnimation(console, message, spinner_type, self.enabled)

    def create_progress(
        self,
        console: Console,
        message: str = "Processing",
        total: int = 100,
    ) -> "ProgressBar":
        """
        Create a progress bar context.

        Args:
            console: Rich console instance
            message: Progress description
            total: Total value for progress

        Returns:
            ProgressBar context manager
        """
        return ProgressBar(console, message, total, self.enabled)


class LoadingAnimation:
    """Context manager for loading animation."""

    def __init__(
        self,
        console: Console,
        message: str,
        spinner_type: str,
        enabled: bool = True,
    ):
        self.console = console
        self.message = message
        self.spinner_type = spinner_type
        self.enabled = enabled
        self.spinner: Optional[Spinner] = None
        self.live: Optional[Live] = None

    def __enter__(self):
        if self.enabled:
            self.spinner = Spinner(
                self.spinner_type, text=self.message, style="primary"
            )
            self.live = Live(self.spinner, console=self.console, refresh_per_second=10)
            self.live.start()
        else:
            self.console.print(self.message, style="text.muted")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.live:
            self.live.stop()


class ProgressBar:
    """Context manager for progress tracking."""

    def __init__(
        self,
        console: Console,
        message: str,
        total: int,
        enabled: bool = True,
    ):
        self.console = console
        self.message = message
        self.total = total
        self.enabled = enabled
        self.progress: Optional[Progress] = None
        self.task_id: Optional[TaskID] = None

    def __enter__(self):
        if self.enabled:
            self.progress = Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(bar_width=40),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                console=self.console,
                refresh_per_second=30,
            )
            self.progress.start()
            self.task_id = self.progress.add_task(self.message, total=self.total)
        return self

    def update(self, advance: int = 1, description: str | None = None):
        """Update progress."""
        if self.progress and self.task_id is not None:
            self.progress.update(self.task_id, advance=advance, description=description)

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.progress:
            self.progress.stop()


# Global animation controller instance
animations = AnimationController()
