"""
Todo List Plugin.

Manages tasks with JSON persistence.
"""

import json
from pathlib import Path
from typing import Any, List, Dict
from datetime import datetime

from cli.plugins import PluginBase
from cli.utils.ui import console
from cli.utils.errors import handle_errors, ValidationError


class TodoPlugin(PluginBase):
    """Manage personal task list."""

    TODO_FILE = Path.home() / ".bdev" / "todos.json"

    @property
    def name(self) -> str:
        return "todo"

    @property
    def description(self) -> str:
        return "Task manager: todo [add <task> | done <index>]"

    def _load_todos(self) -> List[Dict[str, Any]]:
        """Load todos from JSON file."""
        if not self.TODO_FILE.exists():
            return []
        try:
            with open(self.TODO_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []

    def _save_todos(self, todos: List[Dict[str, Any]]) -> None:
        """Save todos to JSON file."""
        self.TODO_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(self.TODO_FILE, "w", encoding="utf-8") as f:
            json.dump(todos, f, indent=2)

    @handle_errors()
    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Handle todo commands."""
        if not args:
            return self._list_todos()

        action = args[0].lower()
        
        if action == "add" and len(args) > 1:
            task_text = " ".join(args[1:])
            return self._add_todo(task_text)
        elif action == "done" and len(args) > 1:
            try:
                index = int(args[1])
                return self._complete_todo(index)
            except ValueError:
                raise ValidationError("Index must be a number.", field="index")
        elif action == "clear":
            return self._clear_completed()
        else:
            console.warning("Usage:")
            console.muted("  todo            → List tasks")
            console.muted("  todo add <task> → Add task")
            console.muted("  todo done <n>   → Complete task #n")
            console.muted("  todo clear      → Remove completed")
            return None

    def _list_todos(self) -> List[Dict[str, Any]]:
        """Display all todos."""
        todos = self._load_todos()
        
        if not todos:
            console.info("No tasks. Use 'todo add <task>' to create one.")
            return []

        console.rule("Todo List")
        rows = []
        for i, todo in enumerate(todos, 1):
            status = "✓" if todo.get("done") else "○"
            style = "muted" if todo.get("done") else ""
            rows.append([str(i), status, todo["task"]])

        console.table("Tasks", ["#", "Status", "Task"], rows)
        
        pending = sum(1 for t in todos if not t.get("done"))
        console.muted(f"{pending} pending, {len(todos) - pending} completed")
        
        return todos

    def _add_todo(self, task: str) -> Dict[str, Any]:
        """Add a new todo."""
        todos = self._load_todos()
        
        new_todo = {
            "task": task,
            "done": False,
            "created": datetime.now().isoformat()
        }
        
        todos.append(new_todo)
        self._save_todos(todos)
        
        console.success(f"Added: {task}")
        return new_todo

    def _complete_todo(self, index: int) -> Dict[str, Any] | None:
        """Mark a todo as complete."""
        todos = self._load_todos()
        
        if index < 1 or index > len(todos):
            console.error(f"Invalid index. Use 1-{len(todos)}.")
            return None

        todos[index - 1]["done"] = True
        todos[index - 1]["completed"] = datetime.now().isoformat()
        self._save_todos(todos)
        
        console.success(f"Completed: {todos[index - 1]['task']}")
        return todos[index - 1]

    def _clear_completed(self) -> int:
        """Remove all completed todos."""
        todos = self._load_todos()
        original_count = len(todos)
        
        todos = [t for t in todos if not t.get("done")]
        self._save_todos(todos)
        
        removed = original_count - len(todos)
        console.success(f"Cleared {removed} completed tasks.")
        return removed
