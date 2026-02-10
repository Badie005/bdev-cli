"""
Configuration Manager for bdev-cli.

Handles persistent configuration storage using a JSON file in the user's
home directory. Implements Singleton pattern.
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional
from cli.utils.ui import console


class ConfigManager:
    """
    Singleton Configuration Manager.

    Persists settings to ~/.bdev/config.json.

    Usage:
        config = ConfigManager()
        val = config.get("theme", "default")
        config.set("editor", "vim")
    """

    _instance: "ConfigManager | None" = None
    CONFIG_DIR = Path.home() / ".bdev"
    CONFIG_FILE = CONFIG_DIR / "config.json"

    DEFAULT_CONFIG: Dict[str, Any] = {
        "editor": "code",
        "theme": "default",
        "plugins_enabled": True,
        "security": {
            "mfa_enabled": False,
            "sandbox_enabled": True,
            "privilege_block_enabled": True,
            "session_timeout": 300,
        },
    }

    def __new__(cls) -> "ConfigManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._ensure_config_exists()
            cls._instance._load()
        return cls._instance

    def _ensure_config_exists(self) -> None:
        """Create config directory and file if they don't exist."""
        if not self.CONFIG_DIR.exists():
            self.CONFIG_DIR.mkdir(parents=True)

        if not self.CONFIG_FILE.exists():
            self._data = self.DEFAULT_CONFIG.copy()
            self._save()
        else:
            self._data = {}

    def _load(self) -> None:
        """Load configuration from JSON file."""
        try:
            if self.CONFIG_FILE.exists():
                with open(self.CONFIG_FILE, "r", encoding="utf-8") as f:
                    file_data = json.load(f)
                    # Merge with defaults to ensure all keys exist
                    self._data = {**self.DEFAULT_CONFIG, **file_data}
            else:
                self._data = self.DEFAULT_CONFIG.copy()
        except json.JSONDecodeError:
            console.error("Failed to parse config file. Using defaults.")
            self._data = self.DEFAULT_CONFIG.copy()
        except Exception as e:
            console.error(f"Error loading config: {e}")
            self._data = self.DEFAULT_CONFIG.copy()

    def _save(self) -> None:
        """Save configuration to JSON file."""
        try:
            with open(self.CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=2)
        except Exception as e:
            console.error(f"Error saving config: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.

        Args:
            key: Config key.
            default: Value to return if key not found (defaults to None).

        Returns:
            The config value.
        """
        return self._data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value and save.

        Args:
            key: Config key.
            value: Value to set.
        """
        self._data[key] = value
        self._save()

    def reset(self) -> None:
        """Reset configuration to defaults."""
        self._data = self.DEFAULT_CONFIG.copy()
        self._save()
        console.success("Configuration reset to defaults.")

    def get_all(self) -> Dict[str, Any]:
        """Return all configuration data."""
        return self._data.copy()


# Global config instance
config = ConfigManager()
