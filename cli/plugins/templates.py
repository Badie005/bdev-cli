"""
Templates Plugin for B.DEV CLI

Provides project scaffolding with customizable templates.
"""

import os
import shutil
from typing import Any, Optional
from pathlib import Path

from cli.plugins import PluginBase
from cli.utils.ui import console


class TemplatesPlugin(PluginBase):
    """Plugin for project template management and scaffolding."""

    @property
    def name(self) -> str:
        return "templates"

    @property
    def description(self) -> str:
        return "Project templates and scaffolding (list, create, use, custom)"

    TEMPLATES_DIR = Path.home() / ".bdev" / "templates"

    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Execute template commands."""
        if not args:
            self._show_help()
            return

        command = args[0].lower()
        sub_args = args[1:]

        try:
            if command == "list":
                self._list()
            elif command == "create":
                self._create(*sub_args)
            elif command == "use":
                self._use(*sub_args)
            elif command == "delete":
                self._delete(*sub_args)
            elif command == "export":
                self._export(*sub_args)
            elif command == "import":
                self._import(*sub_args)
            elif command == "info":
                self._info(*sub_args)
            elif command == "builtin":
                self._builtin(*sub_args)
            else:
                console.error(f"Unknown command: {command}")
                self._show_help()
        except Exception as e:
            console.error(f"Template command failed: {e}")

    def _ensure_templates_dir(self) -> None:
        """Create templates directory if it doesn't exist."""
        self.TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)

    def _list(self) -> None:
        """List all available templates."""
        self._ensure_templates_dir()

        console.rule("Available Templates")

        if not any(self.TEMPLATES_DIR.iterdir()):
            console.info("No custom templates found")
            console.muted("Use 'templates builtin' to see built-in templates")
            return

        rows = []
        for template_dir in sorted(self.TEMPLATES_DIR.iterdir()):
            if template_dir.is_dir():
                meta_file = template_dir / "template.json"
                if meta_file.exists():
                    import json

                    try:
                        with open(meta_file, "r") as f:
                            meta = json.load(f)
                            name = meta.get("name", template_dir.name)
                            description = meta.get("description", "No description")
                            rows.append([name, description])
                    except:
                        rows.append([template_dir.name, "Custom template"])
                else:
                    rows.append([template_dir.name, "Custom template"])

        if rows:
            console.table("Custom Templates", ["Name", "Description"], rows)

        console.muted("\nBuilt-in templates: use 'templates builtin' to list")

    def _create(self, *args: str) -> None:
        """Create a new template from current directory."""
        if not args:
            console.error("Usage: templates create <name> [description]")
            return

        name = args[0]
        description = args[1] if len(args) > 1 else "Custom template"

        self._ensure_templates_dir()
        template_dir = self.TEMPLATES_DIR / name

        if template_dir.exists():
            console.error(f"Template '{name}' already exists")
            return

        console.info(f"Creating template '{name}' from current directory...")

        shutil.copytree(
            ".",
            template_dir,
            ignore=shutil.ignore_patterns(
                "__pycache__",
                "*.pyc",
                ".git",
                "node_modules",
                ".venv",
                "venv",
                "*.egg-info",
                ".pytest_cache",
                "dist",
                "build",
            ),
        )

        meta = {
            "name": name,
            "description": description,
            "version": "1.0.0",
            "created": str(Path.cwd()),
        }

        import json

        with open(template_dir / "template.json", "w") as f:
            json.dump(meta, f, indent=2)

        console.success(f"Template '{name}' created")

    def _use(self, *args: str) -> None:
        """Use a template to create a new project."""
        if len(args) < 2:
            console.error(
                "Usage: templates use <template> <project_name> [variable=value...]"
            )
            return

        template_name = args[0]
        project_name = args[1]
        variables = dict(v.split("=") for v in args[2:]) if len(args) > 2 else {}

        self._ensure_templates_dir()
        template_dir = self.TEMPLATES_DIR / template_name

        if not template_dir.exists():
            console.error(f"Template '{template_name}' not found")
            console.muted("Use 'templates list' to see available templates")
            return

        if Path(project_name).exists():
            console.error(f"Directory '{project_name}' already exists")
            return

        console.info(
            f"Creating project '{project_name}' from template '{template_name}'..."
        )

        shutil.copytree(
            template_dir, project_name, ignore=shutil.ignore_patterns("template.json")
        )

        self._process_template(Path(project_name), variables)

        console.success(f"Project '{project_name}' created")

    def _process_template(self, project_dir: Path, variables: dict) -> None:
        """Process template files with variable replacement."""
        for file_path in project_dir.rglob("*"):
            if file_path.is_file():
                try:
                    content = file_path.read_text()
                    for key, value in variables.items():
                        content = content.replace(f"{{{{{key}}}}}", str(value))
                    file_path.write_text(content)
                except:
                    pass

    def _delete(self, *args: str) -> None:
        """Delete a custom template."""
        if not args:
            console.error("Usage: templates delete <template>")
            return

        template_name = args[0]
        template_dir = self.TEMPLATES_DIR / template_name

        if not template_dir.exists():
            console.error(f"Template '{template_name}' not found")
            return

        console.warning(f"Deleting template '{template_name}'...")
        shutil.rmtree(template_dir)
        console.success(f"Template '{template_name}' deleted")

    def _export(self, *args: str) -> None:
        """Export a template to a zip file."""
        if not args:
            console.error("Usage: templates export <template> [output.zip]")
            return

        template_name = args[0]
        output = args[1] if len(args) > 1 else f"{template_name}.zip"

        template_dir = self.TEMPLATES_DIR / template_name

        if not template_dir.exists():
            console.error(f"Template '{template_name}' not found")
            return

        shutil.make_archive(output.replace(".zip", ""), "zip", template_dir)
        console.success(f"Template exported to {output}")

    def _import(self, *args: str) -> None:
        """Import a template from a zip file."""
        if not args:
            console.error("Usage: templates import <zip_file> [template_name]")
            return

        zip_file = args[0]
        template_name = args[1] if len(args) > 1 else Path(zip_file).stem

        self._ensure_templates_dir()
        template_dir = self.TEMPLATES_DIR / template_name

        if template_dir.exists():
            console.error(f"Template '{template_name}' already exists")
            return

        console.info(f"Importing template from {zip_file}...")

        shutil.unpack_archive(zip_file, template_dir)
        console.success(f"Template '{template_name}' imported")

    def _info(self, *args: str) -> None:
        """Show template information."""
        if not args:
            console.error("Usage: templates info <template>")
            return

        template_name = args[0]
        template_dir = self.TEMPLATES_DIR / template_name

        if not template_dir.exists():
            console.error(f"Template '{template_name}' not found")
            return

        meta_file = template_dir / "template.json"
        if meta_file.exists():
            import json

            with open(meta_file, "r") as f:
                meta = json.load(f)

            rows = [
                ["Name", meta.get("name", template_name)],
                ["Description", meta.get("description", "N/A")],
                ["Version", meta.get("version", "N/A")],
                ["Created From", meta.get("created", "N/A")],
            ]
            console.table(f"Template: {template_name}", ["Property", "Value"], rows)
        else:
            console.warning(f"No metadata found for template '{template_name}'")

    def _builtin(self, *args: str) -> None:
        """List or use built-in templates."""
        builtin_templates = {
            "python-fastapi": {
                "description": "FastAPI Python web application",
                "files": [
                    (
                        "main.py",
                        """
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="{{PROJECT_NAME}}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
""",
                    ),
                    ("requirements.txt", "fastapi\nuvicorn[standard]\npydantic\n"),
                    (".gitignore", "*.pyc\n__pycache__/\n.venv/\n"),
                    (
                        "README.md",
                        """# {{PROJECT_NAME}}

FastAPI application.

## Installation

```bash
pip install -r requirements.txt
```

## Running

```bash
python main.py
```

API available at http://localhost:8000
""",
                    ),
                ],
            },
            "python-flask": {
                "description": "Flask Python web application",
                "files": [
                    (
                        "app.py",
                        """
from flask import Flask, jsonify

app = Flask(__name__)

@app.route("/")
def hello():
    return jsonify({"message": "Hello World"})

@app.route("/health")
def health():
    return jsonify({"status": "healthy"})

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
""",
                    ),
                    ("requirements.txt", "flask\n"),
                    (".gitignore", "*.pyc\n__pycache__/\n.venv/\n"),
                ],
            },
            "nextjs": {
                "description": "Next.js React application",
                "files": [
                    (
                        "package.json",
                        """{
  "name": "{{PROJECT_NAME}}",
  "version": "0.1.0",
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start"
  },
  "dependencies": {
    "next": "latest",
    "react": "latest",
    "react-dom": "latest"
  }
}""",
                    ),
                    (
                        "README.md",
                        """# {{PROJECT_NAME}}

Next.js application.

## Installation

```bash
npm install
```

## Running

```bash
npm run dev
```

App available at http://localhost:3000
""",
                    ),
                ],
            },
            "node-express": {
                "description": "Node.js Express server",
                "files": [
                    (
                        "package.json",
                        """{
  "name": "{{PROJECT_NAME}}",
  "version": "1.0.0",
  "scripts": {
    "start": "node server.js"
  },
  "dependencies": {
    "express": "latest"
  }
}""",
                    ),
                    (
                        "server.js",
                        """
const express = require('express');
const app = express();

app.get('/', (req, res) => {
  res.json({ message: 'Hello World' });
});

app.get('/health', (req, res) => {
  res.json({ status: 'healthy' });
});

app.listen(3000, () => {
  console.log('Server running on port 3000');
});
""",
                    ),
                    (
                        "README.md",
                        """# {{PROJECT_NAME}}

Express.js server.

## Installation

```bash
npm install
```

## Running

```bash
npm start
```

Server available at http://localhost:3000
""",
                    ),
                ],
            },
            "python-selenium": {
                "description": "Python Selenium web automation",
                "files": [
                    (
                        "main.py",
                        """
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service

driver = webdriver.Chrome()

try:
    driver.get("https://example.com")
    title = driver.title
    print(f"Page title: {title}")
finally:
    driver.quit()
""",
                    ),
                    ("requirements.txt", "selenium\nwebdriver-manager\n"),
                ],
            },
        }

        if not args:
            console.rule("Built-in Templates")
            rows = [
                [name, info["description"]] for name, info in builtin_templates.items()
            ]
            console.table("Built-in Templates", ["Template", "Description"], rows)
            console.muted(
                "\nUse 'templates builtin <template> <project_name>' to create project"
            )
            return

        template_name = args[0]
        project_name = args[1] if len(args) > 1 else "my-project"

        if template_name not in builtin_templates:
            console.error(f"Built-in template '{template_name}' not found")
            return

        template = builtin_templates[template_name]
        project_dir = Path(project_name)

        if project_dir.exists():
            console.error(f"Directory '{project_name}' already exists")
            return

        console.info(
            f"Creating project '{project_name}' from built-in template '{template_name}'..."
        )

        project_dir.mkdir(parents=True, exist_ok=True)

        for file_name, content in template["files"]:
            file_path = project_dir / file_name
            content_processed = content.replace("{{PROJECT_NAME}}", project_name)
            file_path.write_text(content_processed.strip() + "\n")

        console.success(f"Project '{project_name}' created from built-in template")
        console.muted(f"Template: {template['description']}")

    def _show_help(self) -> None:
        """Show template command help."""
        rows = [
            ["list", "List all templates"],
            ["create <name> [desc]", "Create template from current dir"],
            ["use <template> <name>", "Use template to create project"],
            ["delete <template>", "Delete custom template"],
            ["export <template> [file]", "Export template to zip"],
            ["import <zip> [name]", "Import template from zip"],
            ["info <template>", "Show template information"],
            ["builtin [template] [name]", "List/use built-in templates"],
        ]
        console.table("Template Commands", ["Command", "Description"], rows)
