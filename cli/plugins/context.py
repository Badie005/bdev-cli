"""
Context Plugin - Project Context Generator.

Provides /context command to generate BDEV.md project summary.
"""

import os
from pathlib import Path
from typing import Any, List
from datetime import datetime

from cli.plugins import PluginBase
from cli.utils.ui import console


class ContextPlugin(PluginBase):
    """Generate project context file (BDEV.md)."""

    @property
    def name(self) -> str:
        return "context"

    @property
    def description(self) -> str:
        return "Generate BDEV.md context file (/context)"

    def execute(self, *args: Any, **kwargs: Any) -> str:
        """Generate BDEV.md in current directory."""
        cwd = Path.cwd()
        output_file = cwd / "BDEV.md"
        
        console.muted(f"Scanning {cwd}...")
        
        content = self._generate_context(cwd)
        
        output_file.write_text(content, encoding="utf-8")
        
        console.success(f"Generated: {output_file}")
        console.muted(f"Size: {len(content)} bytes")
        
        return str(output_file)

    def _generate_context(self, root: Path) -> str:
        """Generate markdown context content."""
        lines = [
            f"# Project Context: {root.name}",
            "",
            f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*",
            "",
            "## Structure",
            "",
            "```",
        ]
        
        # Generate tree (limited depth)
        lines.extend(self._generate_tree(root, max_depth=3))
        lines.append("```")
        
        # Detect project type
        project_info = self._detect_project_type(root)
        if project_info:
            lines.extend([
                "",
                "## Project Info",
                "",
            ])
            for key, value in project_info.items():
                lines.append(f"- **{key}**: {value}")
        
        # Key files
        key_files = self._find_key_files(root)
        if key_files:
            lines.extend([
                "",
                "## Key Files",
                "",
            ])
            for f in key_files:
                lines.append(f"- `{f}`")
        
        lines.append("")
        return "\n".join(lines)

    def _generate_tree(self, root: Path, max_depth: int = 3, prefix: str = "") -> List[str]:
        """Generate directory tree."""
        lines = []
        
        # Ignored patterns
        ignore = {".git", "__pycache__", "node_modules", "venv", ".venv", "dist", "build", ".pytest_cache"}
        
        try:
            items = sorted(root.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
        except PermissionError:
            return lines
        
        # Filter
        items = [i for i in items if i.name not in ignore and not i.name.startswith(".")]
        
        for i, item in enumerate(items[:20]):  # Limit items
            is_last = i == len(items[:20]) - 1
            connector = "└── " if is_last else "├── "
            
            if item.is_dir():
                lines.append(f"{prefix}{connector}{item.name}/")
                if max_depth > 1:
                    extension = "    " if is_last else "│   "
                    lines.extend(self._generate_tree(item, max_depth - 1, prefix + extension))
            else:
                lines.append(f"{prefix}{connector}{item.name}")
        
        if len(items) > 20:
            lines.append(f"{prefix}... and {len(items) - 20} more")
        
        return lines

    def _detect_project_type(self, root: Path) -> dict:
        """Detect project type from files."""
        info = {}
        
        if (root / "package.json").exists():
            info["Type"] = "Node.js"
            try:
                import json
                pkg = json.loads((root / "package.json").read_text())
                info["Name"] = pkg.get("name", "Unknown")
                info["Version"] = pkg.get("version", "0.0.0")
            except Exception:
                pass
        elif (root / "setup.py").exists() or (root / "pyproject.toml").exists():
            info["Type"] = "Python"
            if (root / "requirements.txt").exists():
                info["Dependencies"] = "requirements.txt"
        elif (root / "Cargo.toml").exists():
            info["Type"] = "Rust"
        elif (root / "go.mod").exists():
            info["Type"] = "Go"
        elif (root / "index.html").exists():
            info["Type"] = "Web (Static)"
        
        # Git info
        if (root / ".git").exists():
            info["Git"] = "Yes"
        
        return info

    def _find_key_files(self, root: Path) -> List[str]:
        """Find important files."""
        key_patterns = [
            "README.md", "CONTRIBUTING.md", "LICENSE",
            "package.json", "setup.py", "pyproject.toml",
            "Dockerfile", "docker-compose.yml",
            ".env.example", "Makefile"
        ]
        
        found = []
        for pattern in key_patterns:
            if (root / pattern).exists():
                found.append(pattern)
        
        return found
