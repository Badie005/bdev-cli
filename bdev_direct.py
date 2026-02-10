"""
B.DEV CLI - Direct Command Mode
For running commands without REPL (works on all terminals)
"""

import sys
from pathlib import Path

# Add cli directory to path
cli_dir = Path(__file__).parent / "cli"
sys.path.insert(0, str(cli_dir))


def main():
    """Run B.DEV in direct command mode."""
    from cli.utils.ui import console
    from cli.plugins import registry

    # Load plugins
    count = registry.load_plugins()
    console.muted(f"Loaded {count} plugins.")

    # Show welcome
    console.banner("B.DEV CLI - Direct Mode")
    console.muted("Type 'help' for available commands, 'exit' to quit.\n")

    while True:
        try:
            # Simple prompt
            user_input = input("B.DEV> ")

            if not user_input.strip():
                continue

            parts = user_input.strip().split()
            command_name = parts[0].lower()
            args = parts[1:]

            if command_name in ["exit", "quit"]:
                console.info("Goodbye!")
                break

            if command_name == "help":
                _show_help(registry)
                continue

            # Try to find and execute command
            plugin = registry.get(command_name)
            if plugin:
                try:
                    plugin.execute(*args)
                except Exception as e:
                    console.error(f"Command error: {e}")
            else:
                console.error(f"Unknown command: {command_name}")
                console.muted("Type 'help' for available commands")

        except KeyboardInterrupt:
            console.print("\n")
            console.warning("Use 'exit' to quit.")
            continue
        except EOFError:
            console.info("\nGoodbye!")
            break


def _show_help(registry):
    """Show available commands."""
    from cli.utils.ui import console

    console.rule("Available Commands")

    # Built-in commands
    built_in = [
        ("help", "Show this help"),
        ("exit", "Exit B.DEV"),
        ("clear", "Clear screen (use Ctrl+L)"),
    ]

    rows = []
    for cmd, desc in built_in:
        rows.append([cmd, desc, "builtin"])

    # Plugin commands
    for name, plugin in registry.get_all().items():
        rows.append([name, plugin.description, "plugin"])

    if rows:
        console.table("Commands", ["Command", "Description", "Type"], rows)


if __name__ == "__main__":
    main()
