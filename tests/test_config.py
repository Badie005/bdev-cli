"""
Unit tests for ConfigManager.
"""

import json
import pytest
from pathlib import Path
from unittest.mock import patch


class TestConfigManager:
    """Test ConfigManager singleton and persistence."""

    def test_singleton_pattern(self, temp_config_file: Path) -> None:
        """ConfigManager should return same instance."""
        with patch("cli.core.config.ConfigManager.CONFIG_FILE", temp_config_file):
            with patch("cli.core.config.ConfigManager.CONFIG_DIR", temp_config_file.parent):
                from cli.core.config import ConfigManager
                ConfigManager._instance = None
                
                config1 = ConfigManager()
                config2 = ConfigManager()
                
                assert config1 is config2
                ConfigManager._instance = None

    def test_default_values(self, mock_config_manager) -> None:
        """Config should have default values."""
        assert mock_config_manager.get("editor") == "code"
        assert mock_config_manager.get("theme") == "default"
        assert mock_config_manager.get("plugins_enabled") is True

    def test_set_and_get(self, mock_config_manager) -> None:
        """Should set and retrieve values."""
        mock_config_manager.set("editor", "vim")
        assert mock_config_manager.get("editor") == "vim"

    def test_persistence(self, temp_config_file: Path) -> None:
        """Config should persist to file."""
        with patch("cli.core.config.ConfigManager.CONFIG_FILE", temp_config_file):
            with patch("cli.core.config.ConfigManager.CONFIG_DIR", temp_config_file.parent):
                from cli.core.config import ConfigManager
                ConfigManager._instance = None
                
                config = ConfigManager()
                config.set("custom_key", "custom_value")
                
                # Read file directly
                with open(temp_config_file) as f:
                    data = json.load(f)
                
                assert data["custom_key"] == "custom_value"
                ConfigManager._instance = None

    def test_get_all(self, mock_config_manager) -> None:
        """get_all should return copy of all config."""
        all_config = mock_config_manager.get_all()
        assert "editor" in all_config
        assert "theme" in all_config
