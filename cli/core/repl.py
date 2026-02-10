"""
REPL (Read-Eval-Print Loop) for bdev-cli.

Provides an interactive command interface with history,
auto-completion, Claude Code styling, and smooth micro-animations.
"""

from typing import Callable, Dict, Optional, Any
from pathlib import Path
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.styles import Style
import time

from cli.utils.ui import console
from cli.utils.theme import theme
from cli.utils.animation import animations
from cli.utils.errors import handle_errors, CommandError
from cli.core.config import config
from cli.plugins import registry


class REPLSession:
    """
    Interactive REPL session with history, auto-completion, and Claude Code styling.

    Features:
        - Persistent command history
        - Auto-suggestions from history
        - Tab completion for commands
        - Animated prompt with status indicator
        - Command execution feedback
        - Smooth micro-animations
        - Graceful exit handling
        - Dynamic Plugin System

    Usage:
        repl = REPLSession()
        repl.register_command("hello", lambda: console.success("Hello!"))
        repl.run()
    """

    HISTORY_FILE = Path.home() / ".bdev" / "repl_history"

    # Prompt states
    STATE_IDLE = "idle"
    STATE_WORKING = "working"
    STATE_SUCCESS = "success"
    STATE_ERROR = "error"

    def __init__(self) -> None:
        self._ensure_history_dir()
        self._commands: Dict[str, Dict[str, Any]] = {}
        self._running: bool = False
        self._last_args: list[str] = []
        self._current_state: str = self.STATE_IDLE

        # Load plugins if enabled
        if config.get("plugins_enabled", True):
            count = registry.load_plugins()
            if count > 0:
                console.spinner(f"Loaded {count} plugins")

        # PromptToolkit styles - Claude Code inspired
        self._style = Style.from_dict(
            {
                "prompt": theme.palette.PRIMARY,
                "prompt.bracket": theme.palette.PRIMARY_FADE,
                "prompt.text": theme.palette.TEXT,
                "prompt.status": theme.palette.PRIMARY_FADE,
                "prompt.status.success": theme.palette.SUCCESS,
                "prompt.status.error": theme.palette.ERROR,
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
        """
        Generate Claude Code-style prompt with status indicator.

        Status indicators:
            ● - Idle (waiting for input)
            ◉ - Working (executing command)
            ✓ - Success (last command succeeded)
            ✗ - Error (last command failed)
        """
        p = theme.palette

        status_icons = {
            self.STATE_IDLE: "●",
            self.STATE_WORKING: "◉",
            self.STATE_SUCCESS: "✓",
            self.STATE_ERROR: "✗",
        }

        status_style = {
            self.STATE_IDLE: "prompt.status",
            self.STATE_WORKING: "prompt.status",
            self.STATE_SUCCESS: "prompt.status.success",
            self.STATE_ERROR: "prompt.status.error",
        }

        icon = status_icons.get(self._current_state, "●")
        icon_style = status_style.get(self._current_state, "prompt.status")

        return HTML(
            f"<{icon_style}>{icon}</{icon_style}> "
            "<prompt.bracket>[</prompt.bracket>"
            "<prompt>B.DEV</prompt>"
            "<prompt.bracket>]</prompt.bracket>"
            "<prompt.text> </prompt.text>"
        )

    def _set_state(self, state: str) -> None:
        """Set current prompt state."""
        self._current_state = state

    # Built-in command handlers
    def _cmd_help(self) -> None:
        """Display available commands in Claude Code style."""
        console.header("Available Commands", animate=True)

        # Group commands by type
        builtin_cmds = [
            (name, cmd.get("description", "No description"))
            for name, cmd in self._commands.items()
            if not self._is_plugin_command(name)
        ]
        plugin_cmds = [
            (name, cmd.get("description", "No description"))
            for name, cmd in self._commands.items()
            if self._is_plugin_command(name)
        ]

        if builtin_cmds:
            console.section("Built-in Commands")
            console.command_list(builtin_cmds, animate=True)

        if plugin_cmds:
            console.section("Plugin Commands")
            console.command_list(plugin_cmds, animate=True)

    def _is_plugin_command(self, name: str) -> bool:
        """Check if command is from a plugin."""
        builtin = {"help", "exit", "quit", "clear", "version", "config", "security"}
        return name not in builtin

    def _cmd_exit(self) -> None:
        """Exit the REPL loop."""
        self._running = False
        self._set_state(self.STATE_SUCCESS)
        console.info("Goodbye!", animate=True)

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
        console.header("Configuration")
        data = config.get_all()
        rows = [[k, str(v)] for k, v in sorted(data.items())]
        console.table(rows=rows)

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
            console.header("Security Status")
            status = security.get_status()
            rows = [
                ["MFA", "Enabled" if status["mfa_enabled"] else "Disabled"],
                ["Sandbox", "Enabled" if status["sandbox_enabled"] else "Disabled"],
                [
                    "Privilege Block",
                    "Enabled" if status["privilege_block_enabled"] else "Disabled",
                ],
            ]
            console.table(rows=rows)

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
        Parse and execute a command with Claude Code animations.

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
            self._set_state(self.STATE_ERROR)
            raise CommandError(
                f"Unknown command: '{command_name}'. Type 'help' for available commands.",
                command=command_name,
            )

        handler = self._commands[command_name].get("handler")

        if handler is None:
            self._set_state(self.STATE_ERROR)
            raise CommandError(
                f"Invalid command handler: '{command_name}'", command=command_name
            )

        # Set working state
        self._set_state(self.STATE_WORKING)

        try:
            # Execute handler with subtle feedback
            handler(*args)

            # Set success state
            self._set_state(self.STATE_SUCCESS)

            # Auto-reset to idle after a moment
            def _reset_to_idle():
                time.sleep(0.3)
                if self._current_state in (self.STATE_SUCCESS, self.STATE_ERROR):
                    self._set_state(self.STATE_IDLE)

            import threading

            threading.Thread(target=_reset_to_idle, daemon=True).start()

        except Exception as e:
            self._set_state(self.STATE_ERROR)
            raise

    def run(self) -> None:
        """
        Start the interactive REPL loop with Claude Code styling.

        Loop continues until 'exit' command or Ctrl+D.
        Ctrl+C cancels current input but doesn't exit.
        """
        # Animated welcome
        console.banner(animate=True)

        if animations.enabled:
            time.sleep(0.15)

        console.muted("Type 'help' for available commands.")

        if animations.enabled:
            time.sleep(0.1)

        console.muted("Use 'exit' or Ctrl+D to quit.\n")

        self._running = True

        while self._running:
            try:
                user_input = self._session.prompt(
                    self._get_prompt(), completer=self._get_completer()
                )
                self._execute_command(user_input)

            except KeyboardInterrupt:
                console.print()
                console.dim("Use 'exit' or Ctrl+D to quit.")
                self._set_state(self.STATE_IDLE)
                continue

            except EOFError:
                console.print()
                console.muted("Goodbye!")
                if animations.enabled:
                    time.sleep(0.15)
                self._running = False
                break
