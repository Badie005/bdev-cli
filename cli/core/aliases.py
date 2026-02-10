"""
Command Aliases System for B.DEV CLI.

Provides powerful alias management with presets, import/export,
and intelligent alias expansion.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict

from cli.utils.ui import console
from cli.utils.errors import handle_errors, ValidationError


@dataclass
class Alias:
    """Alias data structure."""

    name: str
    command: str
    description: str = ""
    category: str = "custom"
    created_at: str = ""


class AliasesManager:
    """
    Manager for command aliases.

    Provides:
    - Alias creation, listing, deletion
    - Import/export functionality
    - Built-in presets (Git, Docker, K8s, Cloud)
    - Command expansion
    """

    ALIASES_DIR = Path.home() / ".bdev"
    ALIASES_FILE = ALIASES_DIR / "aliases.json"

    # Built-in presets
    GIT_PRESETS = {
        "gst": "git status",
        "gco": "git checkout",
        "gcb": "git checkout -b",
        "gcm": "git commit -m",
        "gca": "git commit -am",
        "gam": "git commit --amend",
        "gp": "git push",
        "gpl": "git pull",
        "gfo": "git fetch origin",
        "gb": "git branch",
        "gba": "git branch -a",
        "gbd": "git branch -d",
        "gbD": "git branch -D",
        "gl": "git log --oneline --graph",
        "glg": "git log --graph --decorate --oneline --abbrev-commit --all",
        "gd": "git diff",
        "gds": "git diff --staged",
        "ga": "git add",
        "gaa": "git add -A",
        "grh": "git reset HEAD",
        "gcl": "git clean -fd",
        "gsh": "git stash",
        "gshp": "git stash pop",
        "gshl": "git stash list",
        "grb": "git rebase",
        "grbi": "git rebase -i",
        "grbc": "git rebase --continue",
        "grba": "git rebase --abort",
        "gm": "git merge",
        "gmf": "git merge --no-ff",
        "grt": "git reset --hard",
        "grst": "git reset --soft",
        "grm": "git reset --mixed",
        "grv": "git revert",
        "gt": "git tag",
        "gtl": "git tag -l",
        "gbl": "git blame",
        "gshw": "git show",
        "gft": "git fetch",
        "gcln": "git clean",
        "gcfg": "git config",
    }

    DOCKER_PRESETS = {
        "dps": "docker ps",
        "dpsa": "docker ps -a",
        "di": "docker images",
        "db": "docker build",
        "dr": "docker run",
        "drm": "docker rm",
        "drmi": "docker rmi",
        "dstop": "docker stop",
        "dstart": "docker start",
        "dre": "docker restart",
        "dl": "docker logs",
        "dex": "docker exec",
        "dcp": "docker compose",
        "dcpu": "docker compose up",
        "dcpd": "docker compose down",
        "dcpl": "docker compose logs",
        "dcpb": "docker compose build",
        "dnet": "docker network",
        "dvol": "docker volume",
        "dprn": "docker prune",
    }

    K8S_PRESETS = {
        "k8s_pods": "k8s_pods list",
        "k8s_deployments": "k8s_deployments list",
        "k8s_services": "k8s_services list",
        "k8s_ingress": "k8s_ingress list",
        "k8s_configmaps": "k8s_configmaps list",
        "k8s_secrets": "k8s_secrets list",
        "k8s_pvc": "k8s_pvc list",
        "k8s_namespaces": "k8s_namespaces list",
        "k8s_nodes": "k8s_nodes list",
        "k8s_apply": "k8s apply",
        "k8s_delete": "k8s delete",
        "k8s_logs": "k8s_pods logs",
        "k8s_exec": "k8s_pods exec",
        "k8s_describe": "k8s describe",
        "k8s_port_forward": "k8s_pods port-forward",
        "k8s_scale": "k8s_deployments scale",
        "k8s_rollout": "k8s_deployments rollout",
    }

    CLOUD_PRESETS = {
        "cloud_s3_ls": "cloud aws s3 ls",
        "cloud_s3_up": "cloud aws s3 upload",
        "cloud_ec2_ls": "cloud aws ec2 list",
        "cloud_lambda_dep": "cloud aws lambda deploy",
        "cloud_gcp_ls": "cloud gcp compute list",
        "cloud_gcp_up": "cloud gcp storage upload",
        "cloud_azure_ls": "cloud azure vm list",
        "cloud_cost": "cloud cost analyze",
        "cloud_deploy": "cloud deploy",
        "cloud_inventory": "cloud inventory list",
    }

    PRESETS = {
        "git": GIT_PRESETS,
        "docker": DOCKER_PRESETS,
        "k8s": K8S_PRESETS,
        "cloud": CLOUD_PRESETS,
    }

    def __init__(self) -> None:
        self._aliases: Dict[str, Alias] = {}
        self._ensure_aliases_file()
        self._load()

    def _ensure_aliases_file(self) -> None:
        """Create aliases file if it doesn't exist."""
        self.ALIASES_DIR.mkdir(parents=True, exist_ok=True)
        if not self.ALIASES_FILE.exists():
            self._aliases = {}
            self._save()

    def _load(self) -> None:
        """Load aliases from file."""
        try:
            with open(self.ALIASES_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                self._aliases = {
                    name: Alias(**alias_data) for name, alias_data in data.items()
                }
        except (json.JSONDecodeError, FileNotFoundError):
            self._aliases = {}

    def _save(self) -> None:
        """Save aliases to file."""
        try:
            with open(self.ALIASES_FILE, "w", encoding="utf-8") as f:
                json.dump(
                    {name: asdict(alias) for name, alias in self._aliases.items()},
                    f,
                    indent=2,
                )
        except Exception as e:
            console.error(f"Failed to save aliases: {e}")

    @handle_errors()
    def add(
        self,
        name: str,
        command: str,
        description: str = "",
        category: str = "custom",
    ) -> bool:
        """Add a new alias."""
        from datetime import datetime

        if not name or not command:
            raise ValidationError("Alias name and command are required")

        if name in self._aliases:
            console.warning(f"Alias '{name}' already exists. Overwriting.")

        alias = Alias(
            name=name,
            command=command,
            description=description,
            category=category,
            created_at=datetime.now().isoformat(),
        )
        self._aliases[name] = alias
        self._save()
        console.success(f"Alias '{name}' added")
        return True

    @handle_errors()
    def remove(self, name: str) -> bool:
        """Remove an alias."""
        if name not in self._aliases:
            console.error(f"Alias '{name}' not found")
            return False

        del self._aliases[name]
        self._save()
        console.success(f"Alias '{name}' removed")
        return True

    @handle_errors()
    def list(self, category: Optional[str] = None) -> List[Alias]:
        """List all aliases, optionally filtered by category."""
        if category:
            aliases = [
                alias for alias in self._aliases.values() if alias.category == category
            ]
        else:
            aliases = list(self._aliases.values())

        if not aliases:
            console.info("No aliases found")
            return []

        console.rule("Aliases")

        if category:
            console.info(f"Category: {category}")

        rows = []
        for alias in sorted(aliases, key=lambda a: a.name):
            rows.append(
                [
                    alias.name,
                    alias.command,
                    alias.description or "-",
                    alias.category,
                ]
            )

        console.table("Aliases", ["Name", "Command", "Description", "Category"], rows)

        return aliases

    @handle_errors()
    def get(self, name: str) -> Optional[Alias]:
        """Get an alias by name."""
        return self._aliases.get(name)

    @handle_errors()
    def expand(self, command: str) -> str:
        """Expand an alias in a command."""
        words = command.split()
        if not words:
            return command

        alias = self.get(words[0])
        if alias:
            expanded = alias.command + " " + " ".join(words[1:])
            return expanded.strip()

        return command

    @handle_errors()
    def preset_list(self) -> Dict[str, Dict[str, str]]:
        """List all available presets."""
        console.rule("Available Presets")

        rows = []
        for preset_name, aliases in self.PRESETS.items():
            rows.append(
                [
                    preset_name.capitalize(),
                    str(len(aliases)),
                    ", ".join(list(aliases.keys())[:5])
                    + (", ..." if len(aliases) > 5 else ""),
                ]
            )

        console.table("Presets", ["Name", "Aliases", "Preview"], rows)

        return self.PRESETS

    @handle_errors()
    def preset_apply(self, preset: str, overwrite: bool = False) -> bool:
        """Apply a preset (add all aliases from preset)."""
        from datetime import datetime

        preset = preset.lower()
        if preset not in self.PRESETS:
            console.error(
                f"Preset '{preset}' not found. Available: {list(self.PRESETS.keys())}"
            )
            return False

        aliases_dict = self.PRESETS[preset]
        count = 0

        for name, command in aliases_dict.items():
            if name in self._aliases and not overwrite:
                continue

            alias = Alias(
                name=name,
                command=command,
                description=f"Preset: {preset}",
                category=preset,
                created_at=datetime.now().isoformat(),
            )
            self._aliases[name] = alias
            count += 1

        self._save()
        console.success(f"Applied '{preset}' preset ({count} aliases)")
        return True

    @handle_errors()
    def preset_remove(self, preset: str) -> bool:
        """Remove all aliases from a preset."""
        preset = preset.lower()
        if preset not in self.PRESETS:
            console.error(f"Preset '{preset}' not found")
            return False

        aliases_dict = self.PRESETS[preset]
        count = 0

        for name in aliases_dict.keys():
            if name in self._aliases and self._aliases[name].category == preset:
                del self._aliases[name]
                count += 1

        self._save()
        console.success(f"Removed '{preset}' preset ({count} aliases)")
        return True

    @handle_errors()
    def export(self, file_path: str, category: Optional[str] = None) -> bool:
        """Export aliases to a JSON file."""
        export_data = {}

        if category:
            for name, alias in self._aliases.items():
                if alias.category == category:
                    export_data[name] = asdict(alias)
        else:
            export_data = {name: asdict(alias) for name, alias in self._aliases.items()}

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(export_data, f, indent=2)
            console.success(f"Exported {len(export_data)} aliases to {file_path}")
            return True
        except Exception as e:
            console.error(f"Failed to export aliases: {e}")
            return False

    @handle_errors()
    def import_from(self, file_path: str, overwrite: bool = False) -> bool:
        """Import aliases from a JSON file."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            count = 0
            for name, alias_data in data.items():
                if name in self._aliases and not overwrite:
                    continue

                self._aliases[name] = Alias(**alias_data)
                count += 1

            self._save()
            console.success(f"Imported {count} aliases from {file_path}")
            return True
        except FileNotFoundError:
            console.error(f"File not found: {file_path}")
            return False
        except json.JSONDecodeError:
            console.error(f"Invalid JSON file: {file_path}")
            return False
        except Exception as e:
            console.error(f"Failed to import aliases: {e}")
            return False

    @handle_errors()
    def search(self, pattern: str) -> List[Alias]:
        """Search aliases by name or command."""
        pattern = pattern.lower()
        results = [
            alias
            for alias in self._aliases.values()
            if pattern in alias.name.lower() or pattern in alias.command.lower()
        ]

        if not results:
            console.info(f"No aliases found matching '{pattern}'")
            return []

        console.rule(f"Search Results: '{pattern}'")

        rows = []
        for alias in sorted(results, key=lambda a: a.name):
            rows.append(
                [
                    alias.name,
                    alias.command,
                    alias.description or "-",
                ]
            )

        console.table("Matching Aliases", ["Name", "Command", "Description"], rows)

        return results

    @handle_errors()
    def clear(self) -> bool:
        """Clear all aliases."""
        self._aliases.clear()
        self._save()
        console.success("All aliases cleared")
        return True

    @handle_errors()
    def stats(self) -> Dict[str, Any]:
        """Show alias statistics."""
        categories = {}
        for alias in self._aliases.values():
            cat = alias.category
            categories[cat] = categories.get(cat, 0) + 1

        stats = {
            "total": len(self._aliases),
            "categories": categories,
            "presets_available": list(self.PRESETS.keys()),
        }

        console.rule("Alias Statistics")
        console.info(f"Total aliases: {stats['total']}")

        console.table(
            "By Category",
            ["Category", "Count"],
            [[cat, str(count)] for cat, count in categories.items()],
        )

        return stats


# Global aliases manager instance
aliases = AliasesManager()
