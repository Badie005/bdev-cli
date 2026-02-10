"""
Snippets Plugin for B.DEV CLI

Code snippets library for quick code insertion.
"""

import json
import os
from typing import Any, Optional
from pathlib import Path

from cli.plugins import PluginBase
from cli.utils.ui import console


class SnippetsPlugin(PluginBase):
    """Plugin for managing code snippets."""

    @property
    def name(self) -> str:
        return "snippets"

    @property
    def description(self) -> str:
        return "Code snippets library (list, add, copy, search, export)"

    SNIPPETS_DIR = Path.home() / ".bdev" / "snippets"
    INDEX_FILE = SNIPPETS_DIR / "index.json"

    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Execute snippet commands."""
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
            elif command == "get":
                self._get(*sub_args)
            elif command == "copy":
                self._get(*sub_args)
            elif command == "edit":
                self._edit(*sub_args)
            elif command == "delete":
                self._delete(*sub_args)
            elif command == "search":
                self._search(*sub_args)
            elif command == "export":
                self._export(*sub_args)
            elif command == "import":
                self._import(*sub_args)
            elif command == "languages":
                self._languages()
            elif command == "categories":
                self._categories()
            else:
                console.error(f"Unknown command: {command}")
                self._show_help()
        except Exception as e:
            console.error(f"Snippet command failed: {e}")

    def _ensure_snippets_dir(self) -> None:
        """Create snippets directory if it doesn't exist."""
        self.SNIPPETS_DIR.mkdir(parents=True, exist_ok=True)
        if not self.INDEX_FILE.exists():
            self.INDEX_FILE.write_text("{}")

    def _load_index(self) -> dict:
        """Load snippets index."""
        self._ensure_snippets_dir()
        try:
            with open(self.INDEX_FILE, "r") as f:
                return json.load(f)
        except:
            return {}

    def _save_index(self, index: dict) -> None:
        """Save snippets index."""
        with open(self.INDEX_FILE, "w") as f:
            json.dump(index, f, indent=2)

    def _list(self, *args: str) -> None:
        """List all snippets."""
        index = self._load_index()

        if not index:
            console.info("No snippets found")
            console.muted("Use 'snippets add <name>' to create a snippet")
            return

        language = args[0] if args else None

        console.rule("Available Snippets")

        rows = []
        for snippet_id, meta in index.items():
            if language and meta.get("language") != language:
                continue

            name = meta.get("name", snippet_id)
            desc = meta.get("description", "No description")
            lang = meta.get("language", "text")
            category = meta.get("category", "general")
            rows.append([name, desc, lang, category])

        if rows:
            console.table(
                "Snippets", ["Name", "Description", "Language", "Category"], rows
            )
        else:
            console.info(f"No snippets found for language: {language}")

    def _add(self, *args: str) -> None:
        """Add a new snippet."""
        if not args:
            console.error(
                "Usage: snippets add <name> [description] [--language <lang>] [--category <cat>]"
            )
            return

        name = args[0]
        description = (
            args[1]
            if len(args) > 1 and not args[1].startswith("--")
            else "No description"
        )

        language = "text"
        category = "general"

        i = 1
        while i < len(args):
            if args[i] == "--language" and i + 1 < len(args):
                language = args[i + 1]
                i += 2
            elif args[i] == "--category" and i + 1 < len(args):
                category = args[i + 1]
                i += 2
            else:
                i += 1

        index = self._load_index()

        if name in index:
            console.error(f"Snippet '{name}' already exists")
            return

        snippet_file = self.SNIPPETS_DIR / f"{name}.txt"

        console.info(f"Enter snippet content (Ctrl+D or Ctrl+Z to finish):")
        lines = []
        try:
            while True:
                line = input("> ")
                lines.append(line)
        except EOFError:
            pass

        content = "\n".join(lines)

        snippet_file.write_text(content)

        index[name] = {
            "name": name,
            "description": description,
            "language": language,
            "category": category,
            "file": str(snippet_file),
        }

        self._save_index(index)

        console.success(f"Snippet '{name}' added")

    def _get(self, *args: str) -> None:
        """Get and display a snippet."""
        if not args:
            console.error("Usage: snippets get <name>")
            return

        name = args[0]
        index = self._load_index()

        if name not in index:
            console.error(f"Snippet '{name}' not found")
            return

        meta = index[name]
        snippet_file = Path(meta.get("file", ""))

        if not snippet_file.exists():
            console.error(f"Snippet file not found: {snippet_file}")
            return

        content = snippet_file.read_text()

        console.rule(f"Snippet: {name}")
        console.print(content)
        console.muted(f"Language: {meta.get('language', 'text')}")

        console.muted("Use clipboard command to copy (if available)")

    def _edit(self, *args: str) -> None:
        """Edit a snippet."""
        if not args:
            console.error("Usage: snippets edit <name>")
            return

        name = args[0]
        index = self._load_index()

        if name not in index:
            console.error(f"Snippet '{name}' not found")
            return

        meta = index[name]
        snippet_file = Path(meta.get("file", ""))

        if not snippet_file.exists():
            console.error(f"Snippet file not found: {snippet_file}")
            return

        editor = os.environ.get("EDITOR", "code")

        console.info(f"Opening {snippet_file} with {editor}...")
        import subprocess

        subprocess.run([editor, str(snippet_file)])

        console.success(f"Snippet '{name}' updated")

    def _delete(self, *args: str) -> None:
        """Delete a snippet."""
        if not args:
            console.error("Usage: snippets delete <name>")
            return

        name = args[0]
        index = self._load_index()

        if name not in index:
            console.error(f"Snippet '{name}' not found")
            return

        meta = index[name]
        snippet_file = Path(meta.get("file", ""))

        console.warning(f"Deleting snippet '{name}'...")
        if snippet_file.exists():
            snippet_file.unlink()

        del index[name]
        self._save_index(index)

        console.success(f"Snippet '{name}' deleted")

    def _search(self, *args: str) -> None:
        """Search for snippets."""
        if not args:
            console.error("Usage: snippets search <query>")
            return

        query = args[0].lower()
        index = self._load_index()

        results = []
        for snippet_id, meta in index.items():
            if (
                query in meta.get("name", "").lower()
                or query in meta.get("description", "").lower()
            ):
                results.append((snippet_id, meta))
            else:
                snippet_file = Path(meta.get("file", ""))
                if snippet_file.exists():
                    content = snippet_file.read_text().lower()
                    if query in content:
                        results.append((snippet_id, meta))

        if not results:
            console.info(f"No snippets found matching: {query}")
            return

        console.rule(f"Search Results: {query}")

        rows = []
        for snippet_id, meta in results:
            rows.append([meta.get("name", snippet_id), meta.get("description", "N/A")])

        console.table("Matching Snippets", ["Name", "Description"], rows)

    def _export(self, *args: str) -> None:
        """Export snippets to JSON."""
        index = self._load_index()
        output = args[0] if args else "snippets-export.json"

        export_data = {
            "snippets": {},
        }

        for snippet_id, meta in index.items():
            snippet_file = Path(meta.get("file", ""))
            if snippet_file.exists():
                export_data["snippets"][snippet_id] = {
                    "meta": meta,
                    "content": snippet_file.read_text(),
                }

        with open(output, "w") as f:
            json.dump(export_data, f, indent=2)

        console.success(f"Exported {len(export_data['snippets'])} snippets to {output}")

    def _import(self, *args: str) -> None:
        """Import snippets from JSON."""
        if not args:
            console.error("Usage: snippets import <file>")
            return

        import_file = args[0]

        if not Path(import_file).exists():
            console.error(f"File not found: {import_file}")
            return

        with open(import_file, "r") as f:
            data = json.load(f)

        snippets = data.get("snippets", {})
        index = self._load_index()

        added = 0
        for snippet_id, snippet_data in snippets.items():
            if snippet_id not in index:
                meta = snippet_data.get("meta", {})
                content = snippet_data.get("content", "")

                snippet_file = self.SNIPPETS_DIR / f"{snippet_id}.txt"
                snippet_file.write_text(content)

                meta["file"] = str(snippet_file)
                index[snippet_id] = meta
                added += 1

        self._save_index(index)
        console.success(f"Imported {added} snippets from {import_file}")

    def _languages(self) -> None:
        """List all programming languages."""
        index = self._load_index()

        languages = {}
        for meta in index.values():
            lang = meta.get("language", "text")
            languages[lang] = languages.get(lang, 0) + 1

        if not languages:
            console.info("No snippets found")
            return

        rows = [[lang, count] for lang, count in sorted(languages.items())]
        console.table("Programming Languages", ["Language", "Count"], rows)

    def _categories(self) -> None:
        """List all categories."""
        index = self._load_index()

        categories = {}
        for meta in index.values():
            cat = meta.get("category", "general")
            categories[cat] = categories.get(cat, 0) + 1

        if not categories:
            console.info("No snippets found")
            return

        rows = [[cat, count] for cat, count in sorted(categories.items())]
        console.table("Categories", ["Category", "Count"], rows)

    def _show_help(self) -> None:
        """Show snippet command help."""
        rows = [
            ["list [language]", "List all snippets"],
            ["add <name> [desc]", "Add new snippet"],
            ["get <name>", "Display snippet content"],
            ["edit <name>", "Edit snippet"],
            ["delete <name>", "Delete snippet"],
            ["search <query>", "Search snippets"],
            ["export [file]", "Export snippets to JSON"],
            ["import <file>", "Import snippets from JSON"],
            ["languages", "List all languages"],
            ["categories", "List all categories"],
        ]
        console.table("Snippet Commands", ["Command", "Description"], rows)
