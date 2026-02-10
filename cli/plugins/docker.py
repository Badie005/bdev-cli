"""
Docker Plugin for B.DEV CLI

Provides comprehensive Docker container management commands.
"""

import subprocess
import json
from typing import Any, List, Optional
from pathlib import Path

from cli.plugins import PluginBase
from cli.utils.ui import console


class DockerPlugin(PluginBase):
    """Plugin for Docker container and image management."""

    @property
    def name(self) -> str:
        return "docker"

    @property
    def description(self) -> str:
        return "Docker container and image management (status, ps, images, logs, exec, etc.)"

    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Execute Docker commands."""
        if not args:
            self._show_help()
            return

        command = args[0].lower()
        sub_args = args[1:]

        try:
            if command == "status":
                self._status()
            elif command == "ps":
                self._ps(all_containers=len(sub_args) > 0 and sub_args[0] == "all")
            elif command == "images":
                self._images()
            elif command == "build":
                self._build(*sub_args)
            elif command == "run":
                self._run(*sub_args)
            elif command == "stop":
                self._stop(*sub_args)
            elif command == "start":
                self._start(*sub_args)
            elif command == "restart":
                self._restart(*sub_args)
            elif command == "rm":
                self._rm(*sub_args, force=False)
            elif command == "rmi":
                self._rmi(*sub_args, force=False)
            elif command == "logs":
                self._logs(*sub_args)
            elif command == "exec":
                self._exec(*sub_args)
            elif command == "compose":
                self._compose(*sub_args)
            elif command == "prune":
                self._prune()
            elif command == "network":
                self._network(*sub_args)
            elif command == "volume":
                self._volume(*sub_args)
            elif command == "stats":
                self._stats(*sub_args)
            else:
                console.error(f"Unknown command: {command}")
                self._show_help()
        except subprocess.CalledProcessError as e:
            console.error(f"Docker command failed: {e}")
        except FileNotFoundError:
            console.error("Docker is not installed or not in PATH")

    def _run_command(self, cmd: List[str], capture: bool = True) -> str:
        """Run a Docker command."""
        if capture:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return result.stdout.strip()
        else:
            subprocess.run(cmd, check=True)
            return ""

    def _status(self) -> None:
        """Show Docker daemon status."""
        try:
            result = self._run_command(["docker", "info", "--format", "{{json .}}"])
            info = json.loads(result)

            rows = [
                ["Docker Version", info.get("ServerVersion", "Unknown")],
                ["Containers", info.get("Containers", "0")],
                ["Running", info.get("ContainersRunning", "0")],
                ["Paused", info.get("ContainersPaused", "0")],
                ["Stopped", info.get("ContainersStopped", "0")],
                ["Images", info.get("Images", "0")],
                ["Storage Driver", info.get("Driver", "Unknown")],
                ["OS", info.get("OperatingSystem", "Unknown")],
            ]
            console.table("Docker Status", ["Property", "Value"], rows)
            console.success("Docker daemon is running")
        except Exception as e:
            console.error(f"Docker daemon is not accessible: {e}")

    def _ps(self, all_containers: bool = False) -> None:
        """List containers."""
        cmd = [
            "docker",
            "ps",
            "--format",
            "table {{.ID}}\t{{.Names}}\t{{.Status}}\t{{.Ports}}",
        ]
        if all_containers:
            cmd.append("-a")

        result = self._run_command(cmd)
        console.rule(f"Containers ({'All' if all_containers else 'Running'})")
        console.print(result)

    def _images(self) -> None:
        """List Docker images."""
        cmd = [
            "docker",
            "images",
            "--format",
            "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}",
        ]
        result = self._run_command(cmd)
        console.rule("Docker Images")
        console.print(result)

    def _build(self, *args: str) -> None:
        """Build Docker image from Dockerfile."""
        if not args:
            console.error("Usage: docker build <path> [tag]")
            return

        path = args[0]
        tag = args[1] if len(args) > 1 else "latest"

        console.info(f"Building image from {path} (tag: {tag})...")
        cmd = ["docker", "build", "-t", tag, path]
        self._run_command(cmd, capture=False)
        console.success("Image built successfully")

    def _run(self, *args: str) -> None:
        """Run a new container."""
        if not args:
            console.error("Usage: docker run <image> [command]")
            return

        image = args[0]
        cmd = args[1:] if len(args) > 1 else None

        console.info(f"Running container from {image}...")
        docker_cmd = ["docker", "run", "-it", "--rm"]
        if cmd:
            docker_cmd.extend([image, *cmd])
        else:
            docker_cmd.append(image)

        self._run_command(docker_cmd, capture=False)

    def _stop(self, *args: str) -> None:
        """Stop running containers."""
        if not args:
            console.error("Usage: docker stop <container_id> [container_id...]")
            return

        console.info(f"Stopping containers: {', '.join(args)}")
        cmd = ["docker", "stop"] + list(args)
        self._run_command(cmd)
        console.success("Containers stopped")

    def _start(self, *args: str) -> None:
        """Start stopped containers."""
        if not args:
            console.error("Usage: docker start <container_id> [container_id...]")
            return

        console.info(f"Starting containers: {', '.join(args)}")
        cmd = ["docker", "start"] + list(args)
        self._run_command(cmd)
        console.success("Containers started")

    def _restart(self, *args: str) -> None:
        """Restart containers."""
        if not args:
            console.error("Usage: docker restart <container_id> [container_id...]")
            return

        console.info(f"Restarting containers: {', '.join(args)}")
        cmd = ["docker", "restart"] + list(args)
        self._run_command(cmd)
        console.success("Containers restarted")

    def _rm(self, *args: str, force: bool = False) -> None:
        """Remove containers."""
        if not args:
            console.error("Usage: docker rm <container_id> [container_id...]")
            return

        console.info(f"Removing containers: {', '.join(args)}")
        cmd = ["docker", "rm"]
        if force:
            cmd.append("-f")
        cmd.extend(args)
        self._run_command(cmd)
        console.success("Containers removed")

    def _rmi(self, *args: str, force: bool = False) -> None:
        """Remove images."""
        if not args:
            console.error("Usage: docker rmi <image_id> [image_id...]")
            return

        console.info(f"Removing images: {', '.join(args)}")
        cmd = ["docker", "rmi"]
        if force:
            cmd.append("-f")
        cmd.extend(args)
        self._run_command(cmd)
        console.success("Images removed")

    def _logs(self, *args: str) -> None:
        """Show container logs."""
        if not args:
            console.error("Usage: docker logs <container_id> [--follow]")
            return

        container = args[0]
        follow = "--follow" in args or "-f" in args

        console.info(f"Logs for {container} (Ctrl+C to exit)...")
        cmd = ["docker", "logs"]
        if follow:
            cmd.append("-f")
        cmd.append(container)
        self._run_command(cmd, capture=False)

    def _exec(self, *args: str) -> None:
        """Execute command in running container."""
        if len(args) < 2:
            console.error("Usage: docker exec <container_id> <command>")
            return

        container = args[0]
        cmd_args = list(args[1:])

        console.info(f"Executing in {container}: {' '.join(cmd_args)}")
        docker_cmd = ["docker", "exec", "-it", container] + cmd_args
        self._run_command(docker_cmd, capture=False)

    def _compose(self, *args: str) -> None:
        """Run docker-compose commands."""
        if not args:
            console.error("Usage: docker compose <up|down|ps|logs> [args]")
            return

        compose_cmd = args[0]
        compose_args = list(args[1:])

        console.info(f"Docker Compose: {compose_cmd}")
        cmd = ["docker", "compose", compose_cmd] + compose_args
        self._run_command(cmd, capture=False)

    def _prune(self) -> None:
        """Remove unused Docker data."""
        console.warning("This will remove all unused containers, networks, and images")
        console.muted("Docker prune removes:")
        console.muted("  - Stopped containers")
        console.muted("  - Unused networks")
        console.muted("  - Dangling images")
        console.muted("  - Unused build cache")

        result = self._run_command(["docker", "system", "prune", "--force"])
        console.success("Docker system pruned")
        console.print(result)

    def _network(self, *args: str) -> None:
        """Manage Docker networks."""
        if not args:
            self._run_command(["docker", "network", "ls"], capture=False)
            return

        action = args[0]
        if action == "ls":
            self._run_command(["docker", "network", "ls"], capture=False)
        elif action == "create" and len(args) > 1:
            self._run_command(["docker", "network", "create", args[1]], capture=False)
        elif action == "rm" and len(args) > 1:
            self._run_command(["docker", "network", "rm", args[1]], capture=False)

    def _volume(self, *args: str) -> None:
        """Manage Docker volumes."""
        if not args:
            self._run_command(["docker", "volume", "ls"], capture=False)
            return

        action = args[0]
        if action == "ls":
            self._run_command(["docker", "volume", "ls"], capture=False)
        elif action == "create" and len(args) > 1:
            self._run_command(["docker", "volume", "create", args[1]], capture=False)
        elif action == "rm" and len(args) > 1:
            self._run_command(["docker", "volume", "rm", args[1]], capture=False)

    def _stats(self, *args: str) -> None:
        """Show container resource usage statistics."""
        container = args[0] if args else None

        console.info("Container resource usage (Ctrl+C to exit)...")
        cmd = ["docker", "stats"]
        if container:
            cmd.append(container)

        self._run_command(cmd, capture=False)

    def _show_help(self) -> None:
        """Show Docker command help."""
        rows = [
            ["status", "Show Docker daemon status"],
            ["ps [all]", "List containers"],
            ["images", "List images"],
            ["build <path> [tag]", "Build image from Dockerfile"],
            ["run <image> [cmd]", "Run new container"],
            ["stop <id...>", "Stop containers"],
            ["start <id...>", "Start containers"],
            ["restart <id...>", "Restart containers"],
            ["rm <id...>", "Remove containers"],
            ["rmi <id...>", "Remove images"],
            ["logs <id> [--follow]", "Show container logs"],
            ["exec <id> <cmd>", "Execute in container"],
            ["compose <up|down|...>", "Docker compose commands"],
            ["prune", "Remove unused data"],
            ["network [ls|create|rm]", "Manage networks"],
            ["volume [ls|create|rm]", "Manage volumes"],
            ["stats [id]", "Show resource usage"],
        ]
        console.table("Docker Commands", ["Command", "Description"], rows)
