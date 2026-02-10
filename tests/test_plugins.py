"""
Unit tests for Plugin System.
"""

import pytest
from unittest.mock import patch, MagicMock
from typing import Any

from cli.plugins import PluginBase, PluginRegistry


class MockPlugin(PluginBase):
    """Test plugin implementation."""
    
    @property
    def name(self) -> str:
        return "mock_plugin"
    
    @property
    def description(self) -> str:
        return "A mock plugin for testing"
    
    def execute(self, *args: Any, **kwargs: Any) -> str:
        return "executed"


class TestPluginRegistry:
    """Test PluginRegistry functionality."""

    def test_singleton_pattern(self) -> None:
        """Registry should be singleton."""
        # Reset for test
        PluginRegistry._instance = None
        PluginRegistry._instance = None
        
        reg1 = PluginRegistry()
        reg2 = PluginRegistry()
        
        assert reg1 is reg2

    def test_register_plugin(self) -> None:
        """Should register plugin class."""
        registry = PluginRegistry()
        initial_count = len(registry._plugins)
        
        # Unregister if exists
        registry.unregister("mock_plugin")
        
        registry.register(MockPlugin)
        assert "mock_plugin" in registry._plugins
        
        # Cleanup
        registry.unregister("mock_plugin")

    def test_get_plugin(self) -> None:
        """Should retrieve plugin instance by name."""
        registry = PluginRegistry()
        registry.unregister("mock_plugin")
        registry.register(MockPlugin)
        
        plugin = registry.get("mock_plugin")
        assert plugin is not None
        assert plugin.name == "mock_plugin"
        
        registry.unregister("mock_plugin")

    def test_get_nonexistent_plugin(self) -> None:
        """Should return None for unknown plugin."""
        registry = PluginRegistry()
        result = registry.get("nonexistent_plugin")
        assert result is None

    def test_unregister_plugin(self) -> None:
        """Should remove plugin from registry."""
        registry = PluginRegistry()
        registry.unregister("mock_plugin")
        registry.register(MockPlugin)
        
        result = registry.unregister("mock_plugin")
        assert result is True
        assert registry.get("mock_plugin") is None

    def test_duplicate_registration_raises(self) -> None:
        """Should raise error on duplicate registration."""
        registry = PluginRegistry()
        registry.unregister("mock_plugin")
        registry.register(MockPlugin)
        
        with pytest.raises(ValueError, match="already registered"):
            registry.register(MockPlugin)
        
        registry.unregister("mock_plugin")

    def test_plugin_execute(self) -> None:
        """Plugin execute should work."""
        plugin = MockPlugin()
        result = plugin.execute()
        assert result == "executed"
