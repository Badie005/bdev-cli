"""
Scripts Plugin for B.DEV CLI

Manage and execute custom scripts and snippets.
"""

import json
import os
import subprocess
from typing import Any, Optional
from pathlib import Path
from datetime import datetime

from cli.plugins import PluginBase
from cli.utils.ui import console


class ScriptsPlugin(PluginBase):
    """Plugin for managing custom scripts and snippets."""

    @property
    def name(self) -> str:
        return "scripts"

    @property
    def description(self) -> str:
        return "Custom scripts management (list, add, run, edit, delete)"

    SCRIPTS_DIR = Path.home() / ".bdev" / "scripts"
    INDEX_FILE = SCRIPTS_DIR / "index.json"

    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Execute script commands."""
        if not args:
            self._show_help()
            return

        command = args[0].lower()
        sub_args = args[1:]

        try:
            if command == "list":
                self._list(*sub_args)
            elif command == "ls":
                self._list(*sub_args)
            elif command == "add":
                self._add(*sub_args)
            elif command == "create":
                self._add(*sub_args)
            elif command == "run":
                self._run(*sub_args)
            elif command == "edit":
                self._edit(*sub_args)
            elif command == "delete":
                self._delete(*sub_args)
            elif command == "rm":
                self._delete(*sub_args)
            elif command == "info":
                self._info(*sub_args)
            elif command == "search":
                self._search(*sub_args)
            elif command == "export":
                self._export(*sub_args)
            elif command == "import":
                self._import(*sub_args)
            else:
                console.error(f"Unknown command: {command}")
                self._show_help()
        except Exception as e:
            console.error(f"Script command failed: {e}")

    def _ensure_scripts_dir(self) -> None:
        """Create scripts directory if it doesn't exist."""
        self.SCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
        if not self.INDEX_FILE.exists():
            self.INDEX_FILE.write_text("{}")

    def _load_index(self) -> dict:
        """Load scripts index."""
        self._ensure_scripts_dir()
        try:
            with open(self.INDEX_FILE, "r") as f:
                return json.load(f)
        except:
            return {}

    def _save_index(self, index: dict) -> None:
        """Save scripts index."""
        with open(self.INDEX_FILE, "w") as f:
            json.dump(index, f, indent=2)

    def _list(self, *args: str) -> None:
        """List all scripts."""
        index = self._load_index()

        if not index:
            console.info("No scripts found")
            console.muted("Use 'scripts add <name>' to create a script")
            return

        category = args[0] if args else None

        console.rule("Available Scripts")

        rows = []
        for script_id, meta in index.items():
            if category and meta.get("category") != category:
                continue

            name = meta.get("name", script_id)
            desc = meta.get("description", "No description")
            cat = meta.get("category", "general")
            runs = meta.get("runs", 0)
            rows.append([name, desc, cat, runs])

        if rows:
            console.table("Scripts", ["Name", "Description", "Category", "Runs"], rows)
        else:
            console.info(f"No scripts found in category: {category}")

    def _add(self, *args: str) -> None:
        """Add a new script."""
        if not args:
            console.error(
                "Usage: scripts add <name> [description] [--category <cat>] [--type <py|sh|ps1>]"
            )
            return

        name = args[0]
        description = (
            args[1]
            if len(args) > 1 and not args[1].startswith("--")
            else "Custom script"
        )

        script_type = "py"
        category = "general"

        i = 1
        while i < len(args):
            if args[i] == "--category" and i + 1 < len(args):
                category = args[i + 1]
                i += 2
            elif args[i] == "--type" and i + 1 < len(args):
                script_type = args[i + 1]
                i += 2
            else:
                i += 1

        index = self._load_index()

        if name in index:
            console.error(f"Script '{name}' already exists")
            return

        script_dir = self.SCRIPTS_DIR / name
        script_dir.mkdir(exist_ok=True)

        ext = script_type
        script_file = script_dir / f"script.{ext}"

        if script_type == "py":
            content = '''"""
Auto-generated script
"""

def main():
    print("Hello from script!")

if __name__ == "__main__":
    main()
'''
        elif script_type == "sh":
            content = """#!/bin/bash
# Auto-generated script

echo "Hello from script!"
"""
        elif script_type == "ps1":
            content = """# Auto-generated script

Write-Host "Hello from script!"
"""
        else:
            content = f"# Auto-generated {script_type} script\n"

        script_file.write_text(content)

        index[name] = {
            "name": name,
            "description": description,
            "category": category,
            "type": script_type,
            "created": datetime.now().isoformat(),
            "runs": 0,
        }

        self._save_index(index)

        console.success(f"Script '{name}' created")
        console.muted(f"File: {script_file}")
        console.muted("Edit the script with: scripts edit <name>")

    def _run(self, *args: str) -> None:
        """Run a script."""
        if not args:
            console.error("Usage: scripts run <name> [script_args...]")
            return

        name = args[0]
        script_args = list(args[1:])

        index = self._load_index()

        if name not in index:
            console.error(f"Script '{name}' not found")
            return

        meta = index[name]
        script_type = meta.get("type", "py")
        script_file = self.SCRIPTS_DIR / name / f"script.{script_type}"

        if not script_file.exists():
            console.error(f"Script file not found: {script_file}")
            return

        console.info(f"Running script: {name}")

        import subprocess

        try:
            if script_type == "py":
                cmd = ["python", str(script_file)] + script_args
                subprocess.run(cmd, check=True)
            elif script_type == "sh":
                cmd = ["bash", str(script_file)] + script_args
                subprocess.run(cmd, check=True)
            elif script_type == "ps1":
                cmd = ["powershell", "-File", str(script_file)] + script_args
                subprocess.run(cmd, check=True)
            else:
                console.error(f"Unsupported script type: {script_type}")
                return

            meta["runs"] = meta.get("runs", 0) + 1
            meta["last_run"] = datetime.now().isoformat()
            self._save_index(index)

            console.success(f"Script '{name}' completed")

        except subprocess.CalledProcessError as e:
            console.error(f"Script failed with exit code {e.returncode}")
        except Exception as e:
            console.error(f"Script execution error: {e}")

    def _edit(self, *args: str) -> None:
        """Edit a script."""
        if not args:
            console.error("Usage: scripts edit <name>")
            return

        name = args[0]
        index = self._load_index()

        if name not in index:
            console.error(f"Script '{name}' not found")
            return

        meta = index[name]
        script_type = meta.get("type", "py")
        script_file = self.SCRIPTS_DIR / name / f"script.{script_type}"

        editor = os.environ.get("EDITOR", "code")

        console.info(f"Opening {script_file} with {editor}...")
        subprocess.run([editor, str(script_file)])

        console.success(f"Script '{name}' updated")

    def _delete(self, *args: str) -> None:
        """Delete a script."""
        if not args:
            console.error("Usage: scripts delete <name>")
            return

        name = args[0]
        index = self._load_index()

        if name not in index:
            console.error(f"Script '{name}' not found")
            return

        script_dir = self.SCRIPTS_DIR / name

        console.warning(f"Deleting script '{name}'...")
        import shutil

        shutil.rmtree(script_dir)

        del index[name]
        self._save_index(index)

        console.success(f"Script '{name}' deleted")

    def _info(self, *args: str) -> None:
        """Show script information."""
        if not args:
            console.error("Usage: scripts info <name>")
            return

        name = args[0]
        index = self._load_index()

        if name not in index:
            console.error(f"Script '{name}' not found")
            return

        meta = index[name]
        script_type = meta.get("type", "py")
        script_file = self.SCRIPTS_DIR / name / f"script.{script_type}"

        rows = [
            ["Name", meta.get("name", name)],
            ["Description", meta.get("description", "N/A")],
            ["Category", meta.get("category", "general")],
            ["Type", script_type],
            ["Created", meta.get("created", "N/A")],
            ["Last Run", meta.get("last_run", "Never")],
            ["Total Runs", str(meta.get("runs", 0))],
            ["File", str(script_file)],
        ]

        console.table(f"Script: {name}", ["Property", "Value"], rows)

    def _search(self, *args: str) -> None:
        """Search for scripts."""
        if not args:
            console.error("Usage: scripts search <query>")
            return

        query = args[0].lower()
        index = self._load_index()

        results = []
        for script_id, meta in index.items():
            if (
                query in meta.get("name", "").lower()
                or query in meta.get("description", "").lower()
            ):
                results.append((script_id, meta))

        if not results:
            console.info(f"No scripts found matching: {query}")
            return

        console.rule(f"Search Results: {query}")

        rows = []
        for script_id, meta in results:
            rows.append([meta.get("name", script_id), meta.get("description", "N/A")])

        console.table("Matching Scripts", ["Name", "Description"], rows)

    def _export(self, *args: str) -> None:
        """Export scripts to JSON."""
        index = self._load_index()
        output = args[0] if args else "scripts-export.json"

        export_data = {"exported_at": datetime.now().isoformat(), "scripts": index}

        with open(output, "w") as f:
            json.dump(export_data, f, indent=2)

        console.success(f"Exported {len(index)} scripts to {output}")

    def _import(self, *args: str) -> None:
        """Import scripts from JSON."""
        if not args:
            console.error("Usage: scripts import <file>")
            return

        import_file = args[0]

        if not Path(import_file).exists():
            console.error(f"File not found: {import_file}")
            return

        with open(import_file, "r") as f:
            data = json.load(f)

        scripts = data.get("scripts", {})
        index = self._load_index()

        added = 0
        for script_id, meta in scripts.items():
            if script_id not in index:
                index[script_id] = meta
                added += 1

        self._save_index(index)
        console.success(f"Imported {added} scripts from {import_file}")

    def _show_help(self) -> None:
        """Show script command help."""
        rows = [
            ["list [category]", "List all scripts"],
            ["add <name> [desc]", "Add new script"],
            ["run <name> [args]", "Run a script"],
            ["edit <name>", "Edit script code"],
            ["delete <name>", "Delete script"],
            ["info <name>", "Show script details"],
            ["search <query>", "Search scripts"],
            ["export [file]", "Export scripts to JSON"],
            ["import <file>", "Import scripts from JSON"],
        ]
        console.table("Script Commands", ["Command", "Description"], rows)
