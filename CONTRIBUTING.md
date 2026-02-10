# Contributing to B.DEV CLI

Thank you for your interest in contributing to B.DEV CLI!

## How to Contribute

### Reporting Bugs

Before creating bug reports, please check the existing issues as you might find that the problem has already been reported.

When creating a bug report, please include:
- **Description**: A clear and concise description of what the bug is
- **Reproduction Steps**: Steps to reproduce the behavior
- **Expected Behavior**: What you expected to happen
- **Actual Behavior**: What actually happened
- **Screenshots**: If applicable, add screenshots
- **Environment**: OS, Python version, B.DEV CLI version
- **Additional Context**: Any other relevant information

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement request:
- Use a clear and descriptive title
- Provide a detailed description of the proposed enhancement
- Explain why this enhancement would be useful
- Provide examples of how the enhancement would be used

### Pull Requests

1. **Fork the repository**
2. **Create your feature branch** (`git checkout -b feature/AmazingFeature`)
3. **Commit your changes** (`git commit -m 'Add some AmazingFeature'`)
4. **Push to the branch** (`git push origin feature/AmazingFeature`)
5. **Open a Pull Request**

### Development Setup

```bash
# Clone the repository
git clone https://github.com/Badie005/bdev-cli.git
cd bdev-cli

# Create virtual environment
python -m venv venv
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Install in development mode
pip install -e .[dev]

# Run tests
pytest -v
```

### Adding New Plugins

1. Create a new file in `cli/plugins/` (e.g., `myplugin.py`)
2. Inherit from `PluginBase`:
```python
from cli.plugins import PluginBase
from cli.utils.ui import console

class MyPlugin(PluginBase):
    @property
    def name(self) -> str:
        return "myplugin"

    @property
    def description(self) -> str:
        return "My custom plugin"

    def execute(self, *args, **kwargs):
        console.info("My plugin executed!")
```

3. The plugin will be auto-loaded on next startup

### Code Style

- Follow PEP 8 guidelines
- Use type hints where appropriate
- Write docstrings for all functions and classes
- Keep functions focused and small
- Use meaningful variable names
- **No `print()`**: Use `console` from `cli.utils.ui`
- **Error Handling**: Use `@handle_errors` decorator or `CLIError` exceptions
- **Type Hints**: All functions must have type annotations
- **Docstrings**: Use triple-quoted docstrings for all public functions/classes

### Testing

Write tests for new features in the `tests/` directory:
```python
import pytest
from cli.plugins.myplugin import MyPlugin

def test_myplugin():
    plugin = MyPlugin()
    assert plugin.name == "myplugin"
```

Run tests:
```bash
pytest -v
```

### Documentation

Update the following when adding features:
- `README.md` - Main documentation
- `DOCUMENTATION.md` - Complete command reference
- `RELEASE-NOTES.md` - Release notes

## Development Guidelines

### Architecture Principles

- **SOLID Principles**: Single Responsibility, Open/Closed, Liskov Substitution, Interface Segregation, Dependency Inversion
- **DRY**: Don't Repeat Yourself
- **KISS**: Keep It Simple, Stupid
- **YAGNI**: You Aren't Gonna Need It

### Plugin Design

- Each plugin should be self-contained
- Avoid dependencies between plugins
- Use configuration for customization
- Handle errors gracefully
- Provide helpful error messages

### Performance

- Lazy load resources
- Cache results when appropriate
- Avoid unnecessary computations
- Profile before optimizing

### Security

- Validate all user input
- Sanitize file paths
- Use environment variables for secrets
- Never log sensitive information

## Code Review Process

1. All PRs must pass CI tests
2. At least one approval required
3. Address all review comments
4. Keep PRs focused and small
5. Update documentation if needed

## Release Process

1. Update version in `cli/__init__.py`
2. Update `RELEASE-NOTES.md`
3. Tag the release: `git tag v1.0.0`
4. Push tags: `git push --tags`
5. Create GitHub release

## Getting Help

- GitHub Issues: For bugs and feature requests
- Discussions: For questions and general discussion
- Documentation: Check `DOCUMENTATION.md` first

## Recognition

Contributors will be acknowledged in the project documentation and release notes.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
