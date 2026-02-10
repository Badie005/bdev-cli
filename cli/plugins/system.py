"""
System Information Plugin.

Demonstrates plugin system capabilities by displaying system stats.
"""

import platform
import sys
from typing import Any

from cli.plugins import PluginBase
from cli.utils.ui import console


class SysInfoPlugin(PluginBase):
    """Plugin to display system information."""

    @property
    def name(self) -> str:
        return "sysinfo"

    @property
    def description(self) -> str:
        return "Display detailed system information (OS, CPU, Python)"

    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Collect and display system stats."""
        
        info = [
            ["OS System", platform.system()],
            ["OS Release", platform.release()],
            ["OS Version", platform.version()],
            ["Machine", platform.machine()],
            ["Processor", platform.processor() or "Unknown"],
            ["Python Version", sys.version.split()[0]],
            ["Implementation", platform.python_implementation()],
        ]

        console.table(
            title="System Information",
            columns=["Property", "Value"],
            rows=info
        )
        
        return info
