"""
bdev-cli: Main Entry Point

Typer-based CLI application with commands for REPL mode
and other utilities.
"""

import typer
from typing import Optional

from cli import __version__
from cli.utils.ui import console
from cli.utils.errors import handle_errors
from cli.core.repl import REPLSession
from cli.core.security import security


# Initialize Typer app
app = typer.Typer(
    name="B.DEV",
    help="B.DEV CLI - Your Personal Development Assistant",
    add_completion=True,
    no_args_is_help=False,
)


@app.command()
@handle_errors()
def repl() -> None:
    """
    Start the interactive REPL (Read-Eval-Print Loop).

    Provides a command-line interface with history,
    auto-completion, and built-in utilities.
    """
    # MFA is optional for REPL - only enforce if explicitly configured
    # Users can enable MFA via 'security mfa setup' command in REPL
    session = REPLSession()
    session.run()


@app.command()
def version() -> None:
    """Display the current CLI version."""
    console.panel(
        f"[primary]bdev-cli[/primary] version [success]{__version__}[/success]",
        title="Version Info",
        border_style="primary",
    )


@app.command()
def security_status() -> None:
    """Show security status and features."""
    status = security.get_status()
    console.panel(
        f"MFA: {'Enabled' if status['mfa_enabled'] else 'Disabled'}\n"
        f"Sandbox: {'Enabled' if status['sandbox_enabled'] else 'Disabled'}\n"
        f"Privilege Block: {'Enabled' if status['privilege_block_enabled'] else 'Disabled'}",
        title="Security Status",
        border_style="success" if status["mfa_enabled"] else "warning",
    )


@app.command()
@handle_errors()
def hello(name: Optional[str] = typer.Argument(None, help="Name to greet")) -> None:
    """
    Simple greeting command for testing.

    Args:
        name: Optional name for personalized greeting.
    """
    if name:
        console.success(f"Hello, {name}!")
    else:
        console.success("Hello, World!")


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    show_version: bool = typer.Option(
        False, "--version", "-v", help="Show version and exit"
    ),
) -> None:
    """
    B.DEV CLI - Your Personal Development Assistant.

    Run without arguments to start interactive mode,
    or use individual commands directly.
    """
    if show_version:
        version()
        raise typer.Exit()

    # If no command provided, start REPL automatically
    if ctx.invoked_subcommand is None:
        repl()


def run() -> None:
    """Entry point function for package execution."""
    app()


if __name__ == "__main__":
    run()
