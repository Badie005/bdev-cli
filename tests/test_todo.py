"""
Unit tests for TodoPlugin.
"""

import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock


class TestTodoPlugin:
    """Test TodoPlugin functionality."""

    def test_load_empty_todos(self, temp_todo_file: Path) -> None:
        """Should return empty list when no file exists."""
        with patch("cli.plugins.todo.TodoPlugin.TODO_FILE", temp_todo_file):
            from cli.plugins.todo import TodoPlugin
            plugin = TodoPlugin()
            todos = plugin._load_todos()
            assert todos == []

    def test_add_todo(self, temp_todo_file: Path, mock_console: MagicMock) -> None:
        """Should add todo and persist."""
        with patch("cli.plugins.todo.TodoPlugin.TODO_FILE", temp_todo_file):
            with patch("cli.plugins.todo.console", mock_console):
                from cli.plugins.todo import TodoPlugin
                plugin = TodoPlugin()
                
                result = plugin._add_todo("Test task")
                
                assert result["task"] == "Test task"
                assert result["done"] is False
                assert "created" in result
                
                # Verify persistence
                with open(temp_todo_file) as f:
                    data = json.load(f)
                assert len(data) == 1
                assert data[0]["task"] == "Test task"

    def test_complete_todo(self, temp_todo_file: Path, mock_console: MagicMock) -> None:
        """Should mark todo as complete."""
        # Pre-populate
        temp_todo_file.write_text(json.dumps([
            {"task": "Task 1", "done": False},
            {"task": "Task 2", "done": False}
        ]))
        
        with patch("cli.plugins.todo.TodoPlugin.TODO_FILE", temp_todo_file):
            with patch("cli.plugins.todo.console", mock_console):
                from cli.plugins.todo import TodoPlugin
                plugin = TodoPlugin()
                
                result = plugin._complete_todo(1)
                
                assert result["done"] is True
                
                # Verify persistence
                with open(temp_todo_file) as f:
                    data = json.load(f)
                assert data[0]["done"] is True
                assert data[1]["done"] is False

    def test_complete_invalid_index(self, temp_todo_file: Path, mock_console: MagicMock) -> None:
        """Should handle invalid index gracefully."""
        temp_todo_file.write_text(json.dumps([{"task": "Task", "done": False}]))
        
        with patch("cli.plugins.todo.TodoPlugin.TODO_FILE", temp_todo_file):
            with patch("cli.plugins.todo.console", mock_console):
                from cli.plugins.todo import TodoPlugin
                plugin = TodoPlugin()
                
                result = plugin._complete_todo(99)
                assert result is None

    def test_clear_completed(self, temp_todo_file: Path, mock_console: MagicMock) -> None:
        """Should remove completed todos."""
        temp_todo_file.write_text(json.dumps([
            {"task": "Done", "done": True},
            {"task": "Pending", "done": False}
        ]))
        
        with patch("cli.plugins.todo.TodoPlugin.TODO_FILE", temp_todo_file):
            with patch("cli.plugins.todo.console", mock_console):
                from cli.plugins.todo import TodoPlugin
                plugin = TodoPlugin()
                
                removed = plugin._clear_completed()
                
                assert removed == 1
                
                with open(temp_todo_file) as f:
                    data = json.load(f)
                assert len(data) == 1
                assert data[0]["task"] == "Pending"
