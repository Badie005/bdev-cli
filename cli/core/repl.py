"""
REPL (Read-Eval-Print Loop) for bdev-cli.

Provides an interactive command interface with history,
auto-completion, and custom styling using PromptToolkit.
"""

from typing import Callable, Dict, Optional, Any
from pathlib import Path
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.styles import Style

from cli.utils.ui import console
from cli.utils.theme import theme
from cli.utils.errors import handle_errors, CommandError
from cli.core.config import config
from cli.plugins import registry


class REPLSession:
    """
    Interactive REPL session with history and auto-completion.

    Features:
        - Persistent command history
        - Auto-suggestions from history
        - Tab completion for commands
        - Custom Claude-styled prompt
        - Graceful exit handling
        - Dynamic Plugin System

    Usage:
        repl = REPLSession()
        repl.register_command("hello", lambda: console.success("Hello!"))
        repl.run()
    """

    HISTORY_FILE = Path.home() / ".bdev" / "repl_history"

    def __init__(self) -> None:
        self._ensure_history_dir()
        self._commands: Dict[str, Dict[str, Any]] = {}
        self._running: bool = False
        self._last_args: list[str] = []

        # Load plugins if enabled
        if config.get("plugins_enabled", True):
            count = registry.load_plugins()
            if count > 0:
                console.muted(f"Loaded {count} plugins.")

        # PromptToolkit styles
        self._style = Style.from_dict(
            {
                "prompt": theme.palette.PRIMARY,
                "prompt.symbol": theme.palette.PRIMARY_LIGHT,
            }
        )

        # Configure for Windows compatibility
        self._session: PromptSession[str] = PromptSession(
            history=FileHistory(str(self.HISTORY_FILE)),
            auto_suggest=AutoSuggestFromHistory(),
            style=self._style,
            enable_history_search=True,
            erase_when_done=True,
        )

        # Register built-in commands
        self._register_builtin_commands()

        # Register plugin commands
        self._register_plugin_commands()

    def _ensure_history_dir(self) -> None:
        """Create history directory if it doesn't exist."""
        self.HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)

    def _register_builtin_commands(self) -> None:
        """Register default REPL commands."""
        self.register_command("help", self._cmd_help, "Show available commands")
        self.register_command("exit", self._cmd_exit, "Exit the REPL")
        self.register_command("quit", self._cmd_exit, "Exit the REPL")
        self.register_command("clear", self._cmd_clear, "Clear the screen")
        self.register_command("version", self._cmd_version, "Show CLI version")
        self.register_command(
            "config", self._cmd_config, "View or update configuration"
        )
        self.register_command(
            "security", self._cmd_security, "Security management (MFA, Sandbox)"
        )

    def _register_plugin_commands(self) -> None:
        """Register commands from loaded plugins."""
        for name, plugin in registry.get_all().items():
            self.register_command(plugin.name, plugin.execute, plugin.description)

    def register_command(
        self, name: str, handler: Callable[..., Any], description: str = ""
    ) -> None:
        """
        Register a command with the REPL.

        Args:
            name: Command name (what user types).
            handler: Function to execute when command is called.
            description: Help text for the command.
        """
        self._commands[name] = {"handler": handler, "description": description}

    def _get_completer(self) -> WordCompleter:
        """Get word completer with current commands."""
        return WordCompleter(list(self._commands.keys()), ignore_case=True)

    def _get_prompt(self) -> HTML:
        """Generate the styled prompt."""
        return HTML(
            "<prompt.symbol>B.DEV</prompt.symbol><prompt.symbol>></prompt.symbol> "
        )

    # Built-in command handlers
    def _cmd_help(self) -> None:
        """Display available commands."""
        console.rule("Available Commands")
        rows = [
            [name, cmd.get("description", "")]
            for name, cmd in sorted(self._commands.items())
        ]
        console.table("Commands", ["Command", "Description"], rows)

    def _cmd_exit(self) -> None:
        """Exit the REPL loop."""
        self._running = False
        console.info("Goodbye!")

    def _cmd_clear(self) -> None:
        """Clear terminal screen."""
        console.raw.clear()

    def _cmd_version(self) -> None:
        """Show CLI version."""
        from cli import __version__

        console.info(f"bdev-cli v{__version__}")

    def _cmd_config(
        self, key: Optional[str] = None, value: Optional[str] = None
    ) -> None:
        """
        View or modify configuration.

        Usage:
            config              -> Show all config
            config key value    -> Set key to value
        """
        if key and value:
            # Simple type inference for booleans
            final_value: Any = value
            if value.lower() == "true":
                final_value = True
            elif value.lower() == "false":
                final_value = False

            config.set(key, final_value)
            console.success(f"Set '{key}' to '{final_value}'")
            return

        # Show all config
        data = config.get_all()
        rows = [[k, str(v)] for k, v in sorted(data.items())]
        console.table("Configuration", ["Key", "Value"], rows)

    def _cmd_security(self, action: str = "status") -> None:
        """
        Security management commands.

        Usage:
            security status      - Show security status
            security mfa setup   - Setup MFA
            security mfa verify  - Verify MFA code
            security mfa disable - Disable MFA
            security sandbox enable  - Enable sandbox
            security sandbox disable - Disable sandbox
        """
        from cli.core.security import security

        action = action.lower()

        if action == "status":
            status = security.get_status()
            rows = [
                ["MFA Enabled", str(status["mfa_enabled"])],
                ["MFA Verified", str(status["mfa_verified"])],
                ["Sandbox", "Enabled" if status["sandbox_enabled"] else "Disabled"],
                [
                    "Privilege Block",
                    "Enabled" if status["privilege_block_enabled"] else "Disabled",
                ],
                ["Session Timeout", f"{status['session_timeout']}s"],
            ]
            console.table("Security Status", ["Feature", "Status"], rows)

        elif action == "mfa":
            if len(self._last_args) < 2:
                console.error("Usage: security mfa [setup|verify|disable]")
                return

            mfa_action = self._last_args[1].lower()

            if mfa_action == "setup":
                security.setup_mfa()
            elif mfa_action == "verify":
                from prompt_toolkit import prompt

                code = prompt("Enter 6-digit code: ")
                security.mfa.verify(code)
            elif mfa_action == "disable":
                try:
                    security.mfa.disable()
                except Exception as e:
                    console.error(str(e))
            else:
                console.error("Unknown MFA action. Use: setup, verify, disable")

        elif action == "sandbox":
            if len(self._last_args) < 2:
                console.error("Usage: security sandbox [enable|disable]")
                return

            sandbox_action = self._last_args[1].lower()

            if sandbox_action == "enable":
                security.enable_sandbox()
            elif sandbox_action == "disable":
                try:
                    security.disable_sandbox()
                except Exception as e:
                    console.error(str(e))
            else:
                console.error("Unknown action. Use: enable, disable")

        else:
            console.error(f"Unknown action: {action}")
            console.muted("Available actions: status, mfa, sandbox")

    @handle_errors(show_traceback=False)
    def _execute_command(self, user_input: str) -> None:
        """
        Parse and execute a command.

        Supports both regular commands and /slash commands.

        Args:
            user_input: Raw user input string.

        Raises:
            CommandError: If command is not found.
        """
        parts = user_input.strip().split()
        if not parts:
            return

        command_name = parts[0].lower()
        args = parts[1:]
        self._last_args = parts

        # Support slash commands (Claude Code style)
        if command_name.startswith("/"):
            command_name = command_name[1:]  # Strip leading /

        if command_name not in self._commands:
            raise CommandError(
                f"Unknown command: '{command_name}'. Type 'help' for available commands.",
                command=command_name,
            )

        handler = self._commands[command_name].get("handler")

        if handler is None:
            raise CommandError(
                f"Invalid command handler: '{command_name}'", command=command_name
            )

        # Call handler with args if it accepts them
        try:
            handler(*args)
        except TypeError:
            handler()

    def run(self) -> None:
        """
        Start the interactive REPL loop.

        Loop continues until 'exit' command or Ctrl+D.
        Ctrl+C cancels current input but doesn't exit.
        """
        console.banner("B.DEV CLI")
        console.muted("Type 'help' for commands, 'exit' to quit.\n")

        self._running = True

        while self._running:
            try:
                user_input = self._session.prompt(
                    self._get_prompt(), completer=self._get_completer()
                )
                self._execute_command(user_input)

            except KeyboardInterrupt:
                console.print()  # New line after ^C
                console.warning("Use 'exit' or Ctrl+D to quit.")
                continue

            except EOFError:
                # Ctrl+D pressed
                console.print()
                self._cmd_exit()
                break
