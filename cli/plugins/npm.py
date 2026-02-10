"""
NPM Plugin for B.DEV CLI

Provides comprehensive Node.js package management commands.
"""

import subprocess
import json
from typing import Any, List
from pathlib import Path

from cli.plugins import PluginBase
from cli.utils.ui import console


class NpmPlugin(PluginBase):
    """Plugin for Node.js package and script management."""

    @property
    def name(self) -> str:
        return "npm"

    @property
    def description(self) -> str:
        return "Node.js package management (install, scripts, outdated, audit, etc.)"

    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Execute NPM commands."""
        if not args:
            self._show_help()
            return

        command = args[0].lower()
        sub_args = args[1:]

        try:
            if command == "install":
                self._install(*sub_args)
            elif command == "i":
                self._install(*sub_args)
            elif command == "update":
                self._update(*sub_args)
            elif command == "uninstall":
                self._uninstall(*sub_args)
            elif command == "list":
                self._list(*sub_args)
            elif command == "ls":
                self._list(*sub_args)
            elif command == "outdated":
                self._outdated()
            elif command == "audit":
                self._audit(*sub_args)
            elif command == "run":
                self._run(*sub_args)
            elif command == "start":
                self._run_script("start")
            elif command == "dev":
                self._run_script("dev")
            elif command == "build":
                self._run_script("build")
            elif command == "test":
                self._run_script("test")
            elif command == "init":
                self._init(*sub_args)
            elif command == "clean":
                self._clean()
            elif command == "cache":
                self._cache(*sub_args)
            elif command == "version":
                self._version_info()
            elif command == "whoami":
                self._whoami()
            elif command == "search":
                self._search(*sub_args)
            elif command == "info":
                self._info(*sub_args)
            elif command == "dedupe":
                self._dedupe()
            elif command == "link":
                self._link(*sub_args)
            else:
                console.error(f"Unknown command: {command}")
                self._show_help()
        except subprocess.CalledProcessError as e:
            console.error(f"NPM command failed: {e}")
        except FileNotFoundError:
            console.error("NPM is not installed or not in PATH")

    def _run_command(self, cmd: List[str], capture: bool = True) -> str:
        """Run an NPM command."""
        if capture:
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)
            return result.stdout.strip()
        else:
            subprocess.run(cmd, check=False)
            return ""

    def _install(self, *args: str) -> None:
        """Install packages."""
        if args:
            packages = " ".join(args)
            console.info(f"Installing: {packages}")
            cmd = ["npm", "install"] + list(args)
        else:
            console.info("Installing dependencies from package.json")
            cmd = ["npm", "install"]

        self._run_command(cmd, capture=False)
        console.success("Installation completed")

    def _update(self, *args: str) -> None:
        """Update packages."""
        if args:
            packages = " ".join(args)
            console.info(f"Updating: {packages}")
            cmd = ["npm", "update"] + list(args)
        else:
            console.info("Updating all packages")
            cmd = ["npm", "update"]

        self._run_command(cmd, capture=False)
        console.success("Update completed")

    def _uninstall(self, *args: str) -> None:
        """Uninstall packages."""
        if not args:
            console.error("Usage: npm uninstall <package> [package...]")
            return

        packages = " ".join(args)
        console.info(f"Uninstalling: {packages}")
        cmd = ["npm", "uninstall"] + list(args)
        self._run_command(cmd, capture=False)
        console.success("Packages uninstalled")

    def _list(self, *args: str) -> None:
        """List installed packages."""
        depth = "--depth=0"
        if args:
            depth = args[0]

        cmd = ["npm", "list", depth, "--json"]
        result = self._run_command(cmd)

        try:
            data = json.loads(result)
            deps = data.get("dependencies", {})

            if not deps:
                console.info("No dependencies installed")
                return

            rows = []
            for name, info in deps.items():
                version = info.get("version", "unknown")
                rows.append([name, version])

            console.table("Installed Packages", ["Package", "Version"], rows)
        except json.JSONDecodeError:
            console.error("Failed to parse package list")

    def _outdated(self) -> None:
        """Show outdated packages."""
        cmd = ["npm", "outdated", "--json"]
        result = self._run_command(cmd)

        if not result:
            console.success("All packages are up to date!")
            return

        try:
            data = json.loads(result)
            if not data:
                console.success("All packages are up to date!")
                return

            rows = []
            for name, info in data.items():
                current = info.get("current", "-")
                latest = info.get("latest", "-")
                location = info.get("location", "-")
                rows.append([name, current, latest])

            console.warning("Outdated packages found!")
            console.table("Outdated Packages", ["Package", "Current", "Latest"], rows)
        except json.JSONDecodeError:
            console.warning("Failed to parse outdated packages")

    def _audit(self, *args: str) -> None:
        """Run security audit."""
        fix = "--fix" in args or "-f" in args
        console.info("Running security audit...")

        cmd = ["npm", "audit"]
        if fix:
            console.warning("Attempting to fix vulnerabilities...")
            cmd.append("--fix")

        result = self._run_command(cmd)
        console.print(result)

        if not result or "0 vulnerabilities" in result:
            console.success("No vulnerabilities found!")

    def _run(self, *args: str) -> None:
        """Run an npm script."""
        if not args:
            self._list_scripts()
            return

        script_name = args[0]
        script_args = list(args[1:]) if len(args) > 1 else []

        console.info(f"Running script: {script_name}")
        cmd = ["npm", "run", script_name] + script_args
        self._run_command(cmd, capture=False)

    def _run_script(self, script_name: str) -> None:
        """Run a common npm script."""
        console.info(f"Running: npm run {script_name}")
        cmd = ["npm", "run", script_name]
        self._run_command(cmd, capture=False)

    def _list_scripts(self) -> None:
        """List available npm scripts."""
        package_json = Path("package.json")
        if not package_json.exists():
            console.error("package.json not found in current directory")
            return

        try:
            with open(package_json, "r") as f:
                data = json.load(f)

            scripts = data.get("scripts", {})
            if not scripts:
                console.info("No scripts found in package.json")
                return

            rows = [[name, cmd] for name, cmd in scripts.items()]
            console.table("Available Scripts", ["Name", "Command"], rows)
        except Exception as e:
            console.error(f"Failed to read package.json: {e}")

    def _init(self, *args: str) -> None:
        """Initialize new package.json."""
        name = args[0] if args else None

        console.info("Initializing new package.json")
        cmd = ["npm", "init", "-y"]
        if name:
            console.info(f"Project name: {name}")

        self._run_command(cmd, capture=False)
        console.success("package.json created")

    def _clean(self) -> None:
        """Clean node_modules and reinstall."""
        console.warning("This will delete node_modules and reinstall dependencies")

        import shutil

        node_modules = Path("node_modules")
        if node_modules.exists():
            console.info("Removing node_modules...")
            shutil.rmtree(node_modules)
            console.success("node_modules removed")

        console.info("Installing dependencies...")
        self._run_command(["npm", "install"], capture=False)
        console.success("Dependencies reinstalled")

    def _cache(self, *args: str) -> None:
        """Manage npm cache."""
        if not args:
            self._run_command(["npm", "cache", "verify"], capture=False)
            return

        action = args[0]
        if action == "clean":
            console.info("Cleaning npm cache...")
            self._run_command(["npm", "cache", "clean", "--force"], capture=False)
            console.success("Cache cleaned")
        elif action == "verify":
            self._run_command(["npm", "cache", "verify"], capture=False)

    def _version_info(self) -> None:
        """Show npm and Node.js versions."""
        npm_version = self._run_command(["npm", "--version"])
        node_version = self._run_command(["node", "--version"])

        rows = [
            ["npm", npm_version],
            ["Node.js", node_version],
        ]
        console.table("Version Information", ["Tool", "Version"], rows)

    def _whoami(self) -> None:
        """Show npm username."""
        username = self._run_command(["npm", "whoami"])
        if username:
            console.success(f"Logged in as: {username}")
        else:
            console.warning("Not logged in to npm registry")

    def _search(self, *args: str) -> None:
        """Search for packages."""
        if not args:
            console.error("Usage: npm search <query>")
            return

        query = " ".join(args)
        console.info(f"Searching for: {query}")
        cmd = ["npm", "search", query]
        self._run_command(cmd, capture=False)

    def _info(self, *args: str) -> None:
        """Show package information."""
        if not args:
            console.error("Usage: npm info <package>")
            return

        package = args[0]
        console.info(f"Package information: {package}")
        cmd = ["npm", "info", package]
        self._run_command(cmd, capture=False)

    def _dedupe(self) -> None:
        """Deduplicate dependencies."""
        console.info("Deduplicating dependencies...")
        self._run_command(["npm", "dedupe"], capture=False)
        console.success("Dependencies deduplicated")

    def _link(self, *args: str) -> None:
        """Link a local package."""
        if args:
            package = args[0]
            console.info(f"Linking package: {package}")
            self._run_command(["npm", "link", package], capture=False)
        else:
            console.info("Linking current package globally")
            self._run_command(["npm", "link"], capture=False)

    def _show_help(self) -> None:
        """Show NPM command help."""
        rows = [
            ["install [pkg]", "Install packages"],
            ["update [pkg]", "Update packages"],
            ["uninstall <pkg>", "Uninstall packages"],
            ["list", "List installed packages"],
            ["outdated", "Show outdated packages"],
            ["audit [--fix]", "Run security audit"],
            ["run <script>", "Run npm script"],
            ["start", "Run start script"],
            ["dev", "Run dev script"],
            ["build", "Run build script"],
            ["test", "Run test script"],
            ["init [name]", "Initialize package.json"],
            ["clean", "Clean and reinstall"],
            ["cache [clean|verify]", "Manage cache"],
            ["version", "Show version info"],
            ["whoami", "Show npm username"],
            ["search <query>", "Search packages"],
            ["info <pkg>", "Show package info"],
            ["dedupe", "Deduplicate deps"],
            ["link [pkg]", "Link packages"],
        ]
        console.table("NPM Commands", ["Command", "Description"], rows)
