"""
Project Initialization Plugin.

Creates project scaffolding for different project types.
"""

import os
from pathlib import Path
from typing import Any

from cli.plugins import PluginBase
from cli.utils.ui import console
from cli.utils.errors import handle_errors, ValidationError


class ProjectInitPlugin(PluginBase):
    """Initialize new project structures."""

    TEMPLATES = {
        "python": {
            "dirs": ["src", "tests", "docs"],
            "files": {
                "requirements.txt": "# Project dependencies\n",
                "README.md": "# {name}\n\nProject description.\n",
                "src/__init__.py": '"""Main package."""\n',
                "tests/__init__.py": '"""Test package."""\n',
                ".gitignore": "venv/\n__pycache__/\n*.pyc\n.env\n"
            }
        },
        "web": {
            "dirs": ["css", "js", "images"],
            "files": {
                "index.html": """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{name}</title>
    <link rel="stylesheet" href="css/style.css">
</head>
<body>
    <h1>{name}</h1>
    <script src="js/main.js"></script>
</body>
</html>
""",
                "css/style.css": """/* Main styles */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: system-ui, sans-serif;
    line-height: 1.6;
}
""",
                "js/main.js": '// Main JavaScript\nconsole.log("{name} loaded");\n',
                "README.md": "# {name}\n\nWeb project.\n"
            }
        }
    }

    @property
    def name(self) -> str:
        return "init"

    @property
    def description(self) -> str:
        return "Initialize project: init <name> <python|web>"

    @handle_errors()
    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Create project structure."""
        if len(args) < 2:
            console.warning("Usage: init <project_name> <python|web>")
            console.muted("Example: init my-app python")
            return None

        project_name = args[0]
        project_type = args[1].lower()

        if project_type not in self.TEMPLATES:
            raise ValidationError(
                f"Unknown type '{project_type}'. Use: python, web",
                field="type"
            )

        # Create in current directory
        project_path = Path.cwd() / project_name
        
        if project_path.exists():
            console.error(f"Directory '{project_name}' already exists.")
            return None

        template = self.TEMPLATES[project_type]
        
        # Create directories
        project_path.mkdir(parents=True)
        for dir_name in template["dirs"]:
            (project_path / dir_name).mkdir(parents=True, exist_ok=True)

        # Create files
        for file_path, content in template["files"].items():
            full_path = project_path / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content.format(name=project_name))

        # Create venv for Python projects
        if project_type == "python":
            console.muted("Creating virtual environment...")
            os.system(f'cd "{project_path}" && python -m venv venv')

        console.success(f"Created {project_type} project: {project_name}")
        
        # Show structure
        created_items = template["dirs"] + list(template["files"].keys())
        rows = [[item] for item in sorted(created_items)]
        console.table("Created", ["Path"], rows)
        
        return {"name": project_name, "type": project_type, "path": str(project_path)}
