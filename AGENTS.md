# AGENTS.md

This file contains essential guidelines for agentic coding agents working on the bdev-cli repository.

## Build / Lint / Test Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run all tests
pytest

# Run a single test
pytest tests/test_plugins.py::TestPluginRegistry::test_register_plugin

# Run tests in a specific file
pytest tests/test_git_tools.py

# Run with verbose output
pytest -v

# Run with coverage (if pytest-cov is installed)
pytest --cov=cli

# Build the package
pip install -e .
```

## Code Style Guidelines

### Python Version
- Minimum: Python 3.10
- Use modern type hints: `str | None` instead of `Optional[str]`

### Imports
- Order: stdlib → third-party → local
- Group imports with blank lines between sections
- Avoid wildcard imports (`from module import *`)
- Use absolute imports for internal modules: `from cli.utils.ui import console`

### Formatting
- Use 4 spaces for indentation (no tabs)
- Maximum line length: 100-120 characters
- Add blank line after each function/method
- Use docstrings for all public classes, functions, and methods

### Type Hints
- Always include type hints for function signatures
- Use `list[str]`, `dict[str, Any]`, `tuple[str, ...]` instead of `List`, `Dict`, `Tuple`
- Return types: `-> str | None` not `-> Optional[str]`
- Self-referencing types: use `"ClassName"` with quotes

### Naming Conventions
- Classes: `PascalCase` (e.g., `PluginRegistry`, `ConfigManager`)
- Functions/Methods: `snake_case` (e.g., `register_command`, `_ensure_config_exists`)
- Constants: `UPPER_SNAKE_CASE` (e.g., `CONFIG_FILE`, `DEFAULT_CONFIG`)
- Private members: prefix with underscore (e.g., `_plugins`, `_load`)
- Plugins: name property should be `snake_case` (e.g., "cloud", "cicd", "mon")

### Error Handling
- NEVER use `print()` directly - always use `console` from `cli.utils.ui`
- Use `@handle_errors()` decorator for CLI commands
- Raise custom exceptions: `CLIError`, `CommandError`, `ValidationError`, `PluginError`
- Catch specific exceptions, not bare `except:`
- Gracefully handle subprocess failures

### Plugin Development
- Extend `PluginBase` from `cli.plugins`
- Implement required properties: `name`, `description`, `execute()`
- `execute()` signature: `def execute(self, *args: Any, **kwargs: Any) -> Any:`
- Import utilities from `cli.utils.ui` for output
- Use `console.success()`, `console.error()`, `console.info()`, `console.warning()`

### Testing
- Test files: `tests/test_*.py`
- Test classes: `Test*`
- Test functions: `test_*`
- Use fixtures from `conftest.py` for shared setup
- Mock external dependencies: `from unittest.mock import patch, MagicMock`

### Architecture Patterns
- Singletons: Use `__new__` pattern for managers (ConfigManager, ConsoleManager)
- Properties: Use `@property` decorators for computed attributes
- Enums: Use for fixed sets of values (CloudProvider, PipelineStatus)
- Dataclasses: For structured data (Pipeline, Alert, AIModel)

### CLI Output Rules
- **FORBIDDEN**: `print()`, `logging.info()`, `sys.stdout.write()`
- **REQUIRED**: Use `console.success()`, `console.error()`, `console.info()`, `console.warning()`, `console.muted()`
- **Advanced**: Access raw Rich console via `console.raw.print()`

### Security
- Never log or expose secrets/credentials
- Handle MFA, sandbox, and privilege block through security module
- Validate all user input before processing

### Windows Compatibility
- Handle both `\\` and `/` in paths using `pathlib.Path`
- Configure console for UTF-8 encoding (handled in ui.py)
- Use proper subprocess handling for Windows commands
