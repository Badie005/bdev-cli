"""
Global Error Handling for bdev-cli.

Provides decorators and custom exceptions for graceful error handling
without crashing the CLI.
"""

from typing import Callable, TypeVar, Any, ParamSpec
from functools import wraps
import traceback

from cli.utils.ui import console


# Type variables for decorator typing
P = ParamSpec("P")
R = TypeVar("R")


class CLIError(Exception):
    """
    Base exception for all CLI errors.
    
    Attributes:
        message: Human-readable error message.
        code: Optional error code for programmatic handling.
    """

    def __init__(self, message: str, code: str = "CLI_ERROR") -> None:
        self.message = message
        self.code = code
        super().__init__(self.message)


class CommandError(CLIError):
    """Exception raised when a command execution fails."""

    def __init__(self, message: str, command: str = "") -> None:
        self.command = command
        super().__init__(message, code="COMMAND_ERROR")


class ValidationError(CLIError):
    """Exception raised for input validation failures."""

    def __init__(self, message: str, field: str = "") -> None:
        self.field = field
        super().__init__(message, code="VALIDATION_ERROR")


class PluginError(CLIError):
    """Exception raised for plugin-related failures."""

    def __init__(self, message: str, plugin_name: str = "") -> None:
        self.plugin_name = plugin_name
        super().__init__(message, code="PLUGIN_ERROR")


def handle_errors(
    show_traceback: bool = False,
    default_return: Any = None
) -> Callable[[Callable[P, R]], Callable[P, R | None]]:
    """
    Decorator for graceful error handling.
    
    Catches all exceptions, displays formatted error messages,
    and prevents the CLI from crashing.
    
    Args:
        show_traceback: If True, shows full traceback in debug mode.
        default_return: Value to return on error (default: None).
    
    Usage:
        @handle_errors()
        def risky_operation():
            ...
        
        @handle_errors(show_traceback=True)
        def debug_operation():
            ...
    """
    def decorator(func: Callable[P, R]) -> Callable[P, R | None]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R | None:
            try:
                return func(*args, **kwargs)
            except CLIError as e:
                console.error(f"[{e.code}] {e.message}")
                if show_traceback:
                    console.muted(traceback.format_exc())
                return default_return
            except KeyboardInterrupt:
                console.warning("Operation cancelled by user.")
                return default_return
            except Exception as e:
                console.error(f"Unexpected error: {e}")
                if show_traceback:
                    console.muted(traceback.format_exc())
                return default_return
        return wrapper
    return decorator


def safe_execution(func: Callable[P, R]) -> Callable[P, R | None]:
    """
    Simple decorator for safe execution without options.
    
    Equivalent to @handle_errors() but shorter.
    
    Usage:
        @safe_execution
        def my_function():
            ...
    """
    return handle_errors()(func)
