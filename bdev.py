"""
B.DEV CLI Standalone Launcher
This file can be run directly as: python bdev.py
"""

import sys
from pathlib import Path

# Add cli directory to path
cli_dir = Path(__file__).parent / "cli"
sys.path.insert(0, str(cli_dir))

# Import and run
if __name__ == "__main__":
    from cli.main import run

    run()
