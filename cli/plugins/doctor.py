"""
Doctor Plugin - System Health Check.

Provides /doctor command for diagnosing development environment.
"""

import subprocess
import shutil
import sys
from typing import Any, List, Tuple

from cli.plugins import PluginBase
from cli.utils.ui import console


class DoctorPlugin(PluginBase):
    """Check system health and development environment."""

    @property
    def name(self) -> str:
        return "doctor"

    @property
    def description(self) -> str:
        return "Check system health (/doctor)"

    def execute(self, *args: Any, **kwargs: Any) -> List[dict]:
        """Run health checks and display results."""
        console.rule("🩺 System Health Check")
        
        checks = [
            self._check_python(),
            self._check_git(),
            self._check_node(),
            self._check_docker(),
            self._check_venv(),
        ]
        
        # Display results
        rows = []
        for check in checks:
            status = "✓" if check["ok"] else "✗"
            style = "success" if check["ok"] else "error"
            rows.append([check["name"], status, check["version"]])
        
        console.table("Health Status", ["Tool", "Status", "Version/Info"], rows)
        
        # Summary
        passed = sum(1 for c in checks if c["ok"])
        total = len(checks)
        
        if passed == total:
            console.success(f"All checks passed ({passed}/{total})")
        else:
            console.warning(f"{passed}/{total} checks passed")
        
        return checks

    def _check_python(self) -> dict:
        """Check Python installation."""
        version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        return {
            "name": "Python",
            "ok": sys.version_info >= (3, 10),
            "version": version
        }

    def _check_git(self) -> dict:
        """Check Git installation."""
        try:
            result = subprocess.run(
                ["git", "--version"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                version = result.stdout.strip().replace("git version ", "")
                return {"name": "Git", "ok": True, "version": version}
        except FileNotFoundError:
            pass
        return {"name": "Git", "ok": False, "version": "Not installed"}

    def _check_node(self) -> dict:
        """Check Node.js installation."""
        try:
            result = subprocess.run(
                ["node", "--version"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                return {"name": "Node.js", "ok": True, "version": result.stdout.strip()}
        except FileNotFoundError:
            pass
        return {"name": "Node.js", "ok": False, "version": "Not installed"}

    def _check_docker(self) -> dict:
        """Check Docker installation."""
        try:
            result = subprocess.run(
                ["docker", "--version"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                version = result.stdout.strip().split(",")[0].replace("Docker version ", "")
                return {"name": "Docker", "ok": True, "version": version}
        except FileNotFoundError:
            pass
        return {"name": "Docker", "ok": False, "version": "Not installed"}

    def _check_venv(self) -> dict:
        """Check if running in virtual environment."""
        in_venv = sys.prefix != sys.base_prefix
        return {
            "name": "Virtual Env",
            "ok": in_venv,
            "version": "Active" if in_venv else "Not active"
        }
