"""
Event Bus System for B.DEV CLI.

Provides a publish-subscribe event system for plugins and core functionality.
"""

import asyncio
from typing import Any, Callable, Dict, List, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import threading
from collections import defaultdict

from cli.utils.ui import console
from cli.utils.errors import handle_errors


class EventPriority(Enum):
    """Event priority levels."""

    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class Event:
    """Event object."""

    name: str
    data: Dict[str, Any] = field(default_factory=dict)
    source: str = ""
    timestamp: str = ""
    priority: EventPriority = EventPriority.NORMAL

    def __post_init__(self) -> None:
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


@dataclass
class EventHandler:
    """Event handler with metadata."""

    name: str
    callback: Callable[[Event], Any]
    priority: EventPriority = EventPriority.NORMAL
    once: bool = False
    async_callback: bool = False
    source: str = ""
    enabled: bool = True


class EventBus:
    """
    Event bus for pub-sub pattern.

    Supports:
    - Event publishing with priorities
    - Synchronous and async handlers
    - One-time handlers
    - Handler filtering
    - Event history
    """

    _instance: Optional["EventBus"] = None

    def __new__(cls) -> "EventBus":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return

        self._handlers: Dict[str, List[EventHandler]] = defaultdict(list)
        self._event_history: List[Event] = []
        self._max_history = 1000
        self._event_counter = 0
        self._lock = threading.RLock()
        self._initialized = True

    @handle_errors()
    def subscribe(
        self,
        event_name: str,
        callback: Callable[[Event], Any],
        priority: EventPriority = EventPriority.NORMAL,
        once: bool = False,
        async_callback: bool = False,
        source: str = "",
    ) -> str:
        """
        Subscribe to an event.

        Returns:
            Handler ID.
        """
        handler = EventHandler(
            name=f"{event_name}_{self._event_counter}",
            callback=callback,
            priority=priority,
            once=once,
            async_callback=async_callback,
            source=source,
        )

        with self._lock:
            self._handlers[event_name].append(handler)
            # Sort by priority (higher first)
            self._handlers[event_name].sort(
                key=lambda h: h.priority.value, reverse=True
            )
            self._event_counter += 1

        return handler.name

    @handle_errors()
    def unsubscribe(self, event_name: str, handler_id: Optional[str] = None) -> bool:
        """
        Unsubscribe from an event.

        If handler_id is provided, remove specific handler.
        Otherwise, remove all handlers for the event.
        """
        with self._lock:
            if event_name not in self._handlers:
                return False

            if handler_id:
                self._handlers[event_name] = [
                    h for h in self._handlers[event_name] if h.name != handler_id
                ]
            else:
                self._handlers[event_name].clear()

            return True

    @handle_errors()
    async def publish_async(self, event: Event) -> int:
        """
        Publish an event asynchronously.

        Returns:
            Number of handlers called.
        """
        # Add to history
        self._add_to_history(event)

        handlers = self._handlers.get(event.name, [])
        if not handlers:
            return 0

        called = 0
        to_remove = []

        for handler in handlers:
            if not handler.enabled:
                continue

            try:
                if handler.async_callback:
                    await handler.callback(event)
                else:
                    handler.callback(event)

                called += 1

                if handler.once:
                    to_remove.append(handler.name)

            except Exception as e:
                console.error(f"Event handler error ({handler.name}): {e}")

        # Remove one-time handlers
        if to_remove:
            with self._lock:
                self._handlers[event.name] = [
                    h for h in self._handlers[event.name] if h.name not in to_remove
                ]

        return called

    @handle_errors()
    def publish(self, event: Event) -> int:
        """
        Publish an event synchronously.

        Returns:
            Number of handlers called.
        """
        # Add to history
        self._add_to_history(event)

        handlers = self._handlers.get(event.name, [])
        if not handlers:
            return 0

        called = 0
        to_remove = []

        for handler in handlers:
            if not handler.enabled:
                continue

            try:
                if handler.async_callback:
                    asyncio.create_task(handler.callback(event))
                else:
                    handler.callback(event)

                called += 1

                if handler.once:
                    to_remove.append(handler.name)

            except Exception as e:
                console.error(f"Event handler error ({handler.name}): {e}")

        # Remove one-time handlers
        if to_remove:
            with self._lock:
                self._handlers[event.name] = [
                    h for h in self._handlers[event.name] if h.name not in to_remove
                ]

        return called

    def _add_to_history(self, event: Event) -> None:
        """Add event to history."""
        with self._lock:
            self._event_history.append(event)
            if len(self._event_history) > self._max_history:
                self._event_history.pop(0)

    @handle_errors()
    def get_history(
        self, event_name: Optional[str] = None, limit: int = 50
    ) -> List[Event]:
        """Get event history."""
        with self._lock:
            if event_name:
                history = [e for e in self._event_history if e.name == event_name]
            else:
                history = self._event_history.copy()

            return history[-limit:]

    @handle_errors()
    def clear_history(self) -> None:
        """Clear event history."""
        with self._lock:
            self._event_history.clear()

    @handle_errors()
    def list_handlers(
        self, event_name: Optional[str] = None
    ) -> Dict[str, List[EventHandler]]:
        """List all handlers."""
        with self._lock:
            if event_name:
                return {event_name: self._handlers.get(event_name, []).copy()}
            else:
                return {
                    name: handlers.copy()
                    for name, handlers in self._handlers.items()
                    if handlers
                }

    @handle_errors()
    def enable_handler(self, handler_id: str) -> bool:
        """Enable a handler."""
        with self._lock:
            for handlers in self._handlers.values():
                for handler in handlers:
                    if handler.name == handler_id:
                        handler.enabled = True
                        return True
        return False

    @handle_errors()
    def disable_handler(self, handler_id: str) -> bool:
        """Disable a handler."""
        with self._lock:
            for handlers in self._handlers.values():
                for handler in handlers:
                    if handler.name == handler_id:
                        handler.enabled = False
                        return True
        return False

    @handle_errors()
    def stats(self) -> Dict[str, Any]:
        """Get event bus statistics."""
        with self._lock:
            handler_counts = {
                name: len(handlers) for name, handlers in self._handlers.items()
            }

            return {
                "total_events": len(self._event_history),
                "total_handlers": sum(len(h) for h in self._handlers.values()),
                "handler_counts": handler_counts,
                "event_types": list(self._handlers.keys()),
            }


# Built-in event names
class Events:
    """Predefined event names."""

    # Command events
    PRE_COMMAND = "pre_command"
    POST_COMMAND = "post_command"
    COMMAND_ERROR = "command_error"
    COMMAND_SUCCESS = "command_success"

    # Plugin events
    PLUGIN_LOAD = "plugin_load"
    PLUGIN_UNLOAD = "plugin_unload"
    PLUGIN_ERROR = "plugin_error"

    # Deployment events
    PRE_DEPLOY = "pre_deploy"
    POST_DEPLOY = "post_deploy"
    DEPLOY_SUCCESS = "deploy_success"
    DEPLOY_FAILED = "deploy_failed"

    # Test events
    PRE_TEST = "pre_test"
    POST_TEST = "post_test"
    TEST_SUCCESS = "test_success"
    TEST_FAILED = "test_failed"

    # System events
    STARTUP = "startup"
    SHUTDOWN = "shutdown"
    CONFIG_CHANGE = "config_change"


# Global event bus instance
event_bus = EventBus()


# Convenience decorator for event handlers
def on(
    event_name: str, priority: EventPriority = EventPriority.NORMAL, once: bool = False
):
    """Decorator to register a function as an event handler."""

    def decorator(func):
        event_bus.subscribe(event_name, func, priority=priority, once=once)
        return func

    return decorator


# Async version
def on_async(
    event_name: str, priority: EventPriority = EventPriority.NORMAL, once: bool = False
):
    """Decorator to register an async function as an event handler."""

    def decorator(func):
        event_bus.subscribe(
            event_name, func, priority=priority, once=once, async_callback=True
        )
        return func

    return decorator
