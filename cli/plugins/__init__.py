"""
Plugin System for bdev-cli.

Provides a registry for dynamically loading and managing plugins.
"""

from typing import Dict, Type, Any, Callable
from abc import ABC, abstractmethod


class PluginBase(ABC):
    """Abstract base class for all plugins."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique plugin identifier."""
        raise NotImplementedError

    @property
    @abstractmethod
    def description(self) -> str:
        """Short description of the plugin."""
        raise NotImplementedError

    @abstractmethod
    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Execute the plugin's main functionality."""
        raise NotImplementedError


class PluginRegistry:
    """
    Singleton registry for managing plugins.

    Usage:
        registry = PluginRegistry()
        registry.register(MyPlugin)
        plugin = registry.get("my_plugin")
    """

    _instance: "PluginRegistry | None" = None
    _plugins: Dict[str, Type[PluginBase]]

    def __new__(cls) -> "PluginRegistry":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._plugins = {}
        return cls._instance

    def register(self, plugin_class: Type[PluginBase]) -> None:
        """
        Register a plugin class.

        Args:
            plugin_class: A class that extends PluginBase.

        Raises:
            ValueError: If plugin with same name already exists.
        """
        instance = plugin_class()
        plugin_name = instance.name

        if plugin_name in self._plugins:
            raise ValueError(f"Plugin '{plugin_name}' is already registered.")

        self._plugins[plugin_name] = plugin_class

    def get(self, name: str) -> PluginBase | None:
        """
        Get a plugin instance by name.

        Args:
            name: The unique plugin identifier.

        Returns:
            An instance of the plugin, or None if not found.
        """
        plugin_class = self._plugins.get(name)
        if plugin_class:
            return plugin_class()
        return None

    def get_all(self) -> Dict[str, PluginBase]:
        """
        Get all registered plugins as instances.

        Returns:
            Dictionary mapping plugin names to instances.
        """
        return {name: cls() for name, cls in self._plugins.items()}

    def unregister(self, name: str) -> bool:
        """
        Remove a plugin from the registry.

        Args:
            name: The unique plugin identifier.

        Returns:
            True if plugin was removed, False if not found.
        """
        if name in self._plugins:
            del self._plugins[name]
            return True
        return False

    def load_plugins(self, package_path: str = "cli.plugins") -> int:
        """
        Dynamically load plugins from a package path.

        Scans values in the package directory and imports modules.
        Classes inheriting from PluginBase are automatically registered
        via the registration logic (which must be called explicitly or
        during instantiation if preferred, but here we assume plugins
        register themselves or we inspect the module).

        Actually, a better pattern for auto-discovery without modules
        self-registering is to inspect the module content.

        Args:
            package_path: Dot-notation path to plugins package.

        Returns:
            Number of plugins loaded.
        """
        import importlib
        import pkgutil
        import sys

        count = 0
        try:
            # Import the package to get its path
            package = importlib.import_module(package_path)

            if not hasattr(package, "__path__"):
                return 0

            # Iterate over all modules in the package
            for _, name, _ in pkgutil.iter_modules(package.__path__):
                full_name = f"{package_path}.{name}"
                try:
                    module = importlib.import_module(full_name)

                    # Inspect module for PluginBase subclasses
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        if (
                            isinstance(attr, type)
                            and issubclass(attr, PluginBase)
                            and attr is not PluginBase
                            and not getattr(attr, "_is_base", False)
                        ):
                            try:
                                self.register(attr)
                                count += 1
                            except ValueError:
                                # Already registered or name conflict
                                pass

                except Exception as e:
                    # We print to console here but avoid circular imports if possible
                    # or just ignore broken plugins
                    print(f"Failed to load plugin {full_name}: {e}")

        except ImportError:
            return 0

        return count


# Global registry instance
registry = PluginRegistry()
