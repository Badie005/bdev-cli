"""
Shell Plugin for B.DEV CLI

Provides integrated shell commands and system operations.
"""

import subprocess
import os
import platform
import shutil
from typing import Any, Optional
from pathlib import Path

from cli.plugins import PluginBase
from cli.utils.ui import console


class ShellPlugin(PluginBase):
    """Plugin for shell commands and system operations."""

    @property
    def name(self) -> str:
        return "shell"

    @property
    def description(self) -> str:
        return "Integrated shell commands (exec, ls, cd, cat, grep, find, etc.)"

    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Execute shell commands."""
        if not args:
            self._show_help()
            return

        command = args[0].lower()
        sub_args = args[1:]

        try:
            if command == "exec":
                self._exec(*sub_args)
            elif command == "run":
                self._exec(*sub_args)
            elif command == "ls":
                self._ls(*sub_args)
            elif command == "dir":
                self._ls(*sub_args)
            elif command == "cd":
                self._cd(*sub_args)
            elif command == "pwd":
                self._pwd()
            elif command == "cat":
                self._cat(*sub_args)
            elif command == "echo":
                self._echo(*sub_args)
            elif command == "grep":
                self._grep(*sub_args)
            elif command == "find":
                self._find(*sub_args)
            elif command == "cp":
                self._cp(*sub_args)
            elif command == "copy":
                self._cp(*sub_args)
            elif command == "mv":
                self._mv(*sub_args)
            elif command == "move":
                self._mv(*sub_args)
            elif command == "rm":
                self._rm(*sub_args)
            elif command == "del":
                self._rm(*sub_args)
            elif command == "mkdir":
                self._mkdir(*sub_args)
            elif command == "md":
                self._mkdir(*sub_args)
            elif command == "touch":
                self._touch(*sub_args)
            elif command == "chmod":
                self._chmod(*sub_args)
            elif command == "history":
                self._history()
            elif command == "env":
                self._env(*sub_args)
            elif command == "export":
                self._export(*sub_args)
            elif command == "which":
                self._which(*sub_args)
            elif command == "where":
                self._which(*sub_args)
            elif command == "alias":
                self._alias(*sub_args)
            elif command == "source":
                self._source(*sub_args)
            elif command == "sleep":
                self._sleep(*sub_args)
            elif command == "date":
                self._date()
            elif command == "time":
                self._time()
            elif command == "uptime":
                self._uptime()
            elif command == "jobs":
                self._jobs()
            elif command == "kill":
                self._kill(*sub_args)
            elif command == "ps":
                self._ps(*sub_args)
            elif command == "netstat":
                self._netstat(*sub_args)
            elif command == "ping":
                self._ping(*sub_args)
            elif command == "curl":
                self._curl(*sub_args)
            elif command == "wget":
                self._wget(*sub_args)
            elif command == "download":
                self._wget(*sub_args)
            else:
                console.error(f"Unknown command: {command}")
                self._show_help()
        except Exception as e:
            console.error(f"Shell command failed: {e}")

    def _exec(self, *args: str) -> None:
        """Execute a shell command."""
        if not args:
            console.error("Usage: shell exec <command>")
            return

        cmd_str = " ".join(args)
        console.info(f"Executing: {cmd_str}")

        if platform.system() == "Windows":
            subprocess.run(cmd_str, shell=True)
        else:
            subprocess.run(cmd_str, shell=True)

    def _ls(self, *args: str) -> None:
        """List files and directories."""
        path = args[0] if args else "."
        show_hidden = "-a" in args or "--all" in args
        long_format = "-l" in args or "--long" in args

        try:
            files = os.listdir(path)

            if not show_hidden:
                files = [f for f in files if not f.startswith(".")]

            if long_format:
                rows = []
                for f in files:
                    full_path = os.path.join(path, f)
                    is_dir = os.path.isdir(full_path)
                    size = (
                        os.path.getsize(full_path) if os.path.isfile(full_path) else 0
                    )
                    rows.append([f, "DIR" if is_dir else "FILE", f"{size:,} bytes"])
                console.table(f"Contents of {path}", ["Name", "Type", "Size"], rows)
            else:
                items = []
                for f in files:
                    full_path = os.path.join(path, f)
                    prefix = "[DIR] " if os.path.isdir(full_path) else "[FILE] "
                    items.append(prefix + f)
                console.print("\n".join(items))
        except FileNotFoundError:
            console.error(f"Path not found: {path}")
        except PermissionError:
            console.error(f"Permission denied: {path}")

    def _cd(self, *args: str) -> None:
        """Change directory."""
        if not args:
            os.chdir(os.path.expanduser("~"))
            console.info(f"Changed to home directory")
            return

        path = args[0]
        if path == "~":
            path = os.path.expanduser("~")

        try:
            os.chdir(path)
            console.info(f"Changed to: {os.getcwd()}")
        except FileNotFoundError:
            console.error(f"Directory not found: {path}")

    def _pwd(self) -> None:
        """Print working directory."""
        console.info(os.getcwd())

    def _cat(self, *args: str) -> None:
        """Print file contents."""
        if not args:
            console.error("Usage: shell cat <file>")
            return

        for file_path in args:
            try:
                with open(file_path, "r") as f:
                    console.print(f.read())
            except FileNotFoundError:
                console.error(f"File not found: {file_path}")
            except IsADirectoryError:
                console.error(f"{file_path} is a directory")

    def _echo(self, *args: str) -> None:
        """Print text to stdout."""
        text = " ".join(args)
        console.print(text)

    def _grep(self, *args: str) -> None:
        """Search for patterns in files."""
        if len(args) < 2:
            console.error("Usage: shell grep <pattern> <file> [file...]")
            return

        pattern = args[0]
        files = args[1:]

        for file_path in files:
            try:
                with open(file_path, "r") as f:
                    for line_num, line in enumerate(f, 1):
                        if pattern.lower() in line.lower():
                            console.print(f"{file_path}:{line_num}: {line.strip()}")
            except FileNotFoundError:
                console.error(f"File not found: {file_path}")

    def _find(self, *args: str) -> None:
        """Find files by name."""
        if not args:
            console.error("Usage: shell find <name> [directory]")
            return

        name = args[0]
        directory = args[1] if len(args) > 1 else "."

        console.info(f"Searching for: {name}")

        for root, dirs, files in os.walk(directory):
            for file in files:
                if name.lower() in file.lower():
                    console.print(os.path.join(root, file))

    def _cp(self, *args: str) -> None:
        """Copy files."""
        if len(args) < 2:
            console.error("Usage: shell cp <source> <destination>")
            return

        source = args[0]
        dest = args[1]

        try:
            if os.path.isdir(source):
                shutil.copytree(source, dest)
            else:
                shutil.copy2(source, dest)
            console.success(f"Copied {source} to {dest}")
        except FileNotFoundError:
            console.error(f"Source not found: {source}")

    def _mv(self, *args: str) -> None:
        """Move/rename files."""
        if len(args) < 2:
            console.error("Usage: shell mv <source> <destination>")
            return

        source = args[0]
        dest = args[1]

        try:
            shutil.move(source, dest)
            console.success(f"Moved {source} to {dest}")
        except FileNotFoundError:
            console.error(f"Source not found: {source}")

    def _rm(self, *args: str) -> None:
        """Remove files/directories."""
        if not args:
            console.error("Usage: shell rm <path> [path...]")
            return

        recursive = "-r" in args or "--recursive" in args
        force = "-f" in args or "--force" in args
        paths = [p for p in args if not p.startswith("-")]

        for path in paths:
            try:
                if os.path.isdir(path):
                    if recursive:
                        shutil.rmtree(path)
                        console.success(f"Removed directory: {path}")
                    else:
                        console.error(f"{path} is a directory. Use -r to remove")
                else:
                    os.remove(path)
                    console.success(f"Removed file: {path}")
            except FileNotFoundError:
                if not force:
                    console.error(f"Not found: {path}")

    def _mkdir(self, *args: str) -> None:
        """Create directories."""
        if not args:
            console.error("Usage: shell mkdir <directory> [directory...]")
            return

        parents = "-p" in args or "--parents" in args
        dirs = [d for d in args if not d.startswith("-")]

        for dir_path in dirs:
            try:
                if parents:
                    os.makedirs(dir_path, exist_ok=True)
                else:
                    os.makedirs(dir_path)
                console.success(f"Created directory: {dir_path}")
            except FileExistsError:
                console.warning(f"Directory already exists: {dir_path}")

    def _touch(self, *args: str) -> None:
        """Create empty files."""
        if not args:
            console.error("Usage: shell touch <file> [file...]")
            return

        for file_path in args:
            try:
                with open(file_path, "a"):
                    os.utime(file_path, None)
                console.success(f"Created file: {file_path}")
            except Exception as e:
                console.error(f"Failed to create {file_path}: {e}")

    def _chmod(self, *args: str) -> None:
        """Change file permissions (Unix only)."""
        if platform.system() == "Windows":
            console.warning("chmod is not available on Windows")
            return

        if len(args) < 2:
            console.error("Usage: shell chmod <mode> <file>")
            return

        mode = args[0]
        file_path = args[1]

        try:
            os.chmod(file_path, int(mode, 8))
            console.success(f"Changed permissions: {file_path}")
        except FileNotFoundError:
            console.error(f"File not found: {file_path}")

    def _history(self) -> None:
        """Show command history."""
        history_file = Path.home() / ".bdev" / "repl_history"
        if history_file.exists():
            with open(history_file, "r") as f:
                lines = f.readlines()
                for i, line in enumerate(lines[-20:], 1):
                    console.print(f"{i}: {line.strip()}")
        else:
            console.warning("No history found")

    def _env(self, *args: str) -> None:
        """Show environment variables."""
        if args:
            var_name = args[0]
            value = os.environ.get(var_name)
            if value:
                console.print(f"{var_name}={value}")
            else:
                console.warning(f"Variable not found: {var_name}")
        else:
            rows = [[k, v] for k, v in sorted(os.environ.items())[:20]]
            console.table("Environment Variables", ["Name", "Value"], rows)

    def _export(self, *args: str) -> None:
        """Set environment variable."""
        if not args:
            console.error("Usage: shell export <VAR=value>")
            return

        for arg in args:
            if "=" in arg:
                key, value = arg.split("=", 1)
                os.environ[key] = value
                console.success(f"Set {key}={value}")

    def _which(self, *args: str) -> None:
        """Find executable in PATH."""
        if not args:
            console.error("Usage: shell which <command>")
            return

        for cmd in args:
            result = shutil.which(cmd)
            if result:
                console.print(result)
            else:
                console.warning(f"{cmd} not found in PATH")

    def _alias(self, *args: str) -> None:
        """Create shell alias (display only)."""
        console.warning(
            "Aliases are not supported in this shell. Use custom scripts instead."
        )

    def _source(self, *args: str) -> None:
        """Source a script file."""
        if not args:
            console.error("Usage: shell source <script>")
            return

        script = args[0]
        console.info(f"Sourcing: {script}")
        subprocess.run(
            ["source", script]
            if platform.system() != "Windows"
            else ["cmd", "/c", script],
            shell=True,
        )

    def _sleep(self, *args: str) -> None:
        """Sleep for specified seconds."""
        if not args:
            console.error("Usage: shell sleep <seconds>")
            return

        try:
            import time

            time.sleep(int(args[0]))
            console.success(f"Slept for {args[0]} seconds")
        except ValueError:
            console.error("Invalid seconds value")

    def _date(self) -> None:
        """Show current date and time."""
        from datetime import datetime

        console.print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    def _time(self) -> None:
        """Show execution time (use as prefix)."""
        console.info("Use 'exec' with time command for timing")

    def _uptime(self) -> None:
        """Show system uptime."""
        console.info("System uptime not available in this shell")

    def _jobs(self) -> None:
        """Show background jobs."""
        console.info("No background jobs in this shell")

    def _kill(self, *args: str) -> None:
        """Kill process by PID."""
        if not args:
            console.error("Usage: shell kill <pid>")
            return

        try:
            import signal

            pid = int(args[0])
            os.kill(pid, signal.SIGTERM)
            console.success(f"Killed process {pid}")
        except ProcessLookupError:
            console.error(f"Process not found: {args[0]}")
        except PermissionError:
            console.error(f"Permission denied to kill process {args[0]}")

    def _ps(self, *args: str) -> None:
        """Show running processes."""
        console.info("Running processes (top 10 by name):")
        result = subprocess.run(
            ["tasklist" if platform.system() == "Windows" else "ps", "aux"],
            capture_output=True,
            text=True,
        )
        lines = result.stdout.split("\n")[:11]
        for line in lines:
            console.print(line)

    def _netstat(self, *args: str) -> None:
        """Show network connections."""
        console.info("Network connections:")
        result = subprocess.run(["netstat", "-an"], capture_output=True, text=True)
        console.print(result.stdout)

    def _ping(self, *args: str) -> None:
        """Ping a host."""
        if not args:
            console.error("Usage: shell ping <host>")
            return

        host = args[0]
        count = args[1] if len(args) > 1 else "4"
        subprocess.run(
            ["ping", "-n", count, host]
            if platform.system() == "Windows"
            else ["ping", "-c", count, host]
        )

    def _curl(self, *args: str) -> None:
        """Make HTTP request (if curl available)."""
        if not args:
            console.error("Usage: shell curl <url>")
            return

        url = args[0]
        subprocess.run(["curl", url] + list(args[1:]), shell=True)

    def _wget(self, *args: str) -> None:
        """Download file (if wget available)."""
        if not args:
            console.error("Usage: shell wget <url>")
            return

        url = args[0]
        subprocess.run(["wget", url] + list(args[1:]), shell=True)

    def _show_help(self) -> None:
        """Show shell command help."""
        rows = [
            ["exec <cmd>", "Execute shell command"],
            ["ls [path]", "List files"],
            ["cd <path>", "Change directory"],
            ["pwd", "Print working directory"],
            ["cat <file>", "Show file contents"],
            ["grep <pat> <file>", "Search in files"],
            ["find <name>", "Find files"],
            ["cp <src> <dst>", "Copy files"],
            ["mv <src> <dst>", "Move files"],
            ["rm <path>", "Remove files"],
            ["mkdir <dir>", "Create directory"],
            ["touch <file>", "Create empty file"],
            ["env [var]", "Show env variables"],
            ["which <cmd>", "Find command"],
            ["ps", "Show processes"],
            ["ping <host>", "Ping host"],
        ]
        console.table("Shell Commands", ["Command", "Description"], rows)
