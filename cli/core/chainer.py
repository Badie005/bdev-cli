"""
Command Chaining Engine for B.DEV CLI.

Provides powerful command chaining with AND, OR, pipes,
and redirection operators.
"""

import subprocess
import os
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any
from dataclasses import dataclass
from enum import Enum
import tempfile

from cli.utils.ui import console
from cli.utils.errors import handle_errors


class ChainOperator(Enum):
    """Chain operators."""

    AND = "&&"  # Execute second if first succeeds
    OR = "||"  # Execute second if first fails
    SEQUENCE = ";"  # Execute both regardless
    PIPE = "|"  # Pipe output of first to input of second
    REDIRECT_OUT = ">"  # Redirect stdout to file
    REDIRECT_APPEND = ">>"  # Append stdout to file
    REDIRECT_IN = "<"  # Read input from file
    REDIRECT_ERR = "2>"  # Redirect stderr to file


@dataclass
class Chain:
    """Command chain definition."""

    name: str
    chain_string: str
    commands: List[List[str]]
    operators: List[ChainOperator]
    description: str = ""


class ChainExecutor:
    """Execute command chains with proper operator handling."""

    @staticmethod
    @handle_errors()
    def parse_chain(chain_str: str) -> Tuple[List[List[str]], List[ChainOperator]]:
        """Parse a chain string into commands and operators."""
        operators = [
            ChainOperator.AND.value,
            ChainOperator.OR.value,
            ChainOperator.SEQUENCE.value,
            ChainOperator.PIPE.value,
            ChainOperator.REDIRECT_OUT.value,
            ChainOperator.REDIRECT_APPEND.value,
            ChainOperator.REDIRECT_IN.value,
            ChainOperator.REDIRECT_ERR.value,
        ]

        # Find all operators in the chain
        op_positions = []
        for i, char in enumerate(chain_str):
            for op in operators:
                if chain_str.startswith(op, i):
                    op_positions.append((i, op))
                    break

        # Sort by position
        op_positions.sort(key=lambda x: x[0])

        # Extract commands and operators
        commands = []
        parsed_operators = []

        prev_pos = 0
        for pos, op in op_positions:
            cmd_str = chain_str[prev_pos:pos].strip()
            if cmd_str:
                # Parse command string into list of args
                # Simple parsing (quoted strings not fully handled)
                commands.append(cmd_str.split())
            parsed_operators.append(ChainOperator(op))
            prev_pos = pos + len(op)

        # Add last command
        if prev_pos < len(chain_str):
            cmd_str = chain_str[prev_pos:].strip()
            if cmd_str:
                commands.append(cmd_str.split())

        return commands, parsed_operators

    @staticmethod
    @handle_errors()
    def execute_chain(
        commands: List[List[str]],
        operators: List[ChainOperator],
        capture_output: bool = False,
    ) -> Tuple[int, str, str]:
        """
        Execute a command chain.

        Returns:
            (exit_code, stdout, stderr)
        """
        if not commands:
            return 0, "", ""

        stdout_accum = ""
        stderr_accum = ""

        cmd_index = 0
        prev_result = subprocess.CompletedProcess(args=[], returncode=0)

        while cmd_index < len(commands):
            current_cmd = commands[cmd_index]
            current_op = operators[cmd_index - 1] if cmd_index > 0 else None

            # Handle input redirection
            stdin_source = None
            if current_op == ChainOperator.REDIRECT_IN:
                if cmd_index + 1 < len(commands):
                    file_path = " ".join(commands[cmd_index + 1])
                    try:
                        stdin_source = open(file_path, "r")
                        cmd_index += 1  # Skip the file
                    except FileNotFoundError:
                        console.error(f"File not found: {file_path}")
                        return 1, stdout_accum, stderr_accum

            # Handle output redirection
            redirect_file = None
            redirect_mode = "w"
            if current_op == ChainOperator.REDIRECT_OUT:
                if cmd_index + 1 < len(commands):
                    redirect_file = " ".join(commands[cmd_index + 1])
                    cmd_index += 1
            elif current_op == ChainOperator.REDIRECT_APPEND:
                if cmd_index + 1 < len(commands):
                    redirect_file = " ".join(commands[cmd_index + 1])
                    redirect_mode = "a"
                    cmd_index += 1
            elif current_op == ChainOperator.REDIRECT_ERR:
                if cmd_index + 1 < len(commands):
                    redirect_file = " ".join(commands[cmd_index + 1])
                    cmd_index += 1

            # Handle pipe
            stdin_pipe = None
            if current_op == ChainOperator.PIPE:
                stdin_pipe = subprocess.PIPE

            # Execute command
            try:
                result = subprocess.run(
                    current_cmd,
                    stdin=stdin_source if stdin_source else prev_result.stdout,
                    stdout=subprocess.PIPE if stdin_pipe else None,
                    stderr=subprocess.PIPE if redirect_file else None,
                    text=True,
                )

                stdout_accum += result.stdout
                stderr_accum += result.stderr

                # Handle output redirection
                if redirect_file:
                    try:
                        with open(redirect_file, redirect_mode) as f:
                            f.write(result.stdout)
                    except IOError as e:
                        console.error(f"Failed to write to file: {e}")
                        return 1, stdout_accum, stderr_accum

                # Handle error redirection
                if current_op == ChainOperator.REDIRECT_ERR and redirect_file:
                    try:
                        with open(redirect_file, redirect_mode) as f:
                            f.write(result.stderr)
                    except IOError as e:
                        console.error(f"Failed to write error to file: {e}")

                if stdin_source:
                    stdin_source.close()

                # Check next operator to decide if we should continue
                if cmd_index < len(operators):
                    next_op = operators[cmd_index]
                    if next_op == ChainOperator.AND and result.returncode != 0:
                        break  # Don't continue on AND failure
                    elif next_op == ChainOperator.OR and result.returncode == 0:
                        break  # Don't continue on OR success

                prev_result = result

            except Exception as e:
                console.error(f"Command execution failed: {e}")
                return 1, stdout_accum, stderr_accum

            cmd_index += 1

        if prev_result.args:
            return prev_result.returncode, stdout_accum, stderr_accum
        return 0, stdout_accum, stderr_accum


class ChainManager:
    """Manager for saved command chains."""

    CHAINS_DIR = Path.home() / ".bdev" / "chains"
    INDEX_FILE = CHAINS_DIR / "index.json"

    def __init__(self) -> None:
        self._chains: Dict[str, Chain] = {}
        self._ensure_chains_dir()
        self._load()

    def _ensure_chains_dir(self) -> None:
        """Create chains directory if it doesn't exist."""
        self.CHAINS_DIR.mkdir(parents=True, exist_ok=True)
        if not self.INDEX_FILE.exists():
            self.INDEX_FILE.write_text("{}")

    def _load(self) -> None:
        """Load chains from file."""
        import json

        try:
            with open(self.INDEX_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                self._chains = {
                    name: Chain(
                        name=name,
                        commands=[cmd.split() for cmd in chain_data["commands"]],
                        operators=[ChainOperator(op) for op in chain_data["operators"]],
                        chain_string=chain_data["chain_string"],
                        description=chain_data.get("description", ""),
                    )
                    for name, chain_data in data.items()
                }
        except Exception:
            self._chains = {}

    def _save(self) -> None:
        """Save chains to file."""
        import json

        data = {
            name: {
                "chain_string": chain.chain_string,
                "commands": [" ".join(cmd) for cmd in chain.commands],
                "operators": [op.value for op in chain.operators],
                "description": chain.description,
            }
            for name, chain in self._chains.items()
        }

        with open(self.INDEX_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    @handle_errors()
    def save(self, name: str, chain_str: str, description: str = "") -> bool:
        """Save a command chain."""
        commands, operators = ChainExecutor.parse_chain(chain_str)

        chain = Chain(
            name=name,
            chain_string=chain_str,
            commands=commands,
            operators=operators,
            description=description,
        )

        self._chains[name] = chain
        self._save()
        console.success(f"Chain '{name}' saved")
        return True

    @handle_errors()
    def load(self, name: str) -> Optional[Chain]:
        """Load a saved chain."""
        return self._chains.get(name)

    @handle_errors()
    def list(self) -> List[Chain]:
        """List all saved chains."""
        if not self._chains:
            console.info("No saved chains")
            return []

        console.rule("Saved Chains")

        rows = []
        for chain in sorted(self._chains.values(), key=lambda c: c.name):
            rows.append(
                [
                    chain.name,
                    chain.chain_string[:50] + "..."
                    if len(chain.chain_string) > 50
                    else chain.chain_string,
                    chain.description or "-",
                    str(len(chain.commands)),
                ]
            )

        console.table("Chains", ["Name", "Chain", "Description", "Commands"], rows)

        return list(self._chains.values())

    @handle_errors()
    def delete(self, name: str) -> bool:
        """Delete a saved chain."""
        if name not in self._chains:
            console.error(f"Chain '{name}' not found")
            return False

        del self._chains[name]
        self._save()
        console.success(f"Chain '{name}' deleted")
        return True

    @handle_errors()
    def execute(
        self,
        chain_str: Optional[str] = None,
        chain_name: Optional[str] = None,
        capture_output: bool = True,
    ) -> Tuple[int, str, str]:
        """Execute a chain."""
        if chain_name:
            chain = self.load(chain_name)
            if not chain:
                console.error(f"Chain '{chain_name}' not found")
                return 1, "", ""

            commands = chain.commands
            operators = chain.operators
            console.info(f"Executing chain: {chain.name}")
        elif chain_str:
            commands, operators = ChainExecutor.parse_chain(chain_str)
            console.info(f"Executing: {chain_str}")
        else:
            console.error("Either chain_str or chain_name must be provided")
            return 1, "", ""

        returncode, stdout, stderr = ChainExecutor.execute_chain(
            commands, operators, capture_output
        )

        if returncode == 0:
            console.success("Chain executed successfully")
        else:
            console.error(f"Chain failed with exit code {returncode}")

        if stdout and capture_output:
            console.muted(stdout)

        return returncode, stdout, stderr


# Global chain manager instance
chains = ChainManager()


def chain(chain_str: str) -> Tuple[int, str, str]:
    """Execute a command chain."""
    return chains.execute(chain_str=chain_str)
