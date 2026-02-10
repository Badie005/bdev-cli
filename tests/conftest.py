"""
Pytest configuration and shared fixtures.
"""

import pytest
import json
from pathlib import Path
from unittest.mock import MagicMock, patch
from typing import Generator, Any


@pytest.fixture
def temp_config_file(tmp_path: Path) -> Generator[Path, None, None]:
    """Create a temporary config file."""
    config_file = tmp_path / ".bdev" / "config.json"
    config_file.parent.mkdir(parents=True, exist_ok=True)
    yield config_file


@pytest.fixture
def mock_config_manager(temp_config_file: Path) -> Generator[Any, None, None]:
    """Mock ConfigManager to use temp directory."""
    with patch("cli.core.config.ConfigManager.CONFIG_FILE", temp_config_file):
        with patch("cli.core.config.ConfigManager.CONFIG_DIR", temp_config_file.parent):
            # Reset singleton
            from cli.core.config import ConfigManager
            ConfigManager._instance = None
            yield ConfigManager()
            ConfigManager._instance = None


@pytest.fixture
def temp_todo_file(tmp_path: Path) -> Generator[Path, None, None]:
    """Create a temporary todo file."""
    todo_file = tmp_path / ".bdev" / "todos.json"
    todo_file.parent.mkdir(parents=True, exist_ok=True)
    yield todo_file


@pytest.fixture
def mock_console() -> Generator[MagicMock, None, None]:
    """Mock console output."""
    with patch("cli.utils.ui.console") as mock:
        yield mock
