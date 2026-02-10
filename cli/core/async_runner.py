"""
Async Command Execution for B.DEV CLI.

Provides async command execution with parallel processing,
worker pools, and pipeline execution.
"""

import asyncio
import subprocess
import time
from pathlib import Path
from typing import Any, List, Dict, Optional, Callable, Tuple, Union
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from enum import Enum

from cli.utils.ui import console
from cli.utils.errors import handle_errors


class ExecutionStatus(Enum):
    """Status of async execution."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class AsyncCommand:
    """Async command definition."""

    command: List[str]
    shell: bool = False
    timeout: int = 300
    capture_output: bool = True
    env: Optional[Dict[str, str]] = None
    cwd: Optional[str] = None
    id: str = ""
    status: ExecutionStatus = ExecutionStatus.PENDING
    result: Optional[subprocess.CompletedProcess] = None
    start_time: float = 0
    end_time: float = 0
    output: str = ""
    error: str = ""


@dataclass
class ExecutionResult:
    """Result of async execution."""

    total: int
    successful: int
    failed: int
    cancelled: int
    commands: List[AsyncCommand]
    duration: float
    parallel: bool


class AsyncRunner:
    """Execute commands asynchronously with various strategies."""

    def __init__(self, max_workers: int = 4) -> None:
        self.max_workers = max_workers

    async def execute_single(
        self,
        cmd: AsyncCommand,
    ) -> AsyncCommand:
        """Execute a single command asynchronously."""
        cmd.status = ExecutionStatus.RUNNING
        cmd.start_time = time.time()

        try:
            result = await asyncio.to_thread(
                subprocess.run,
                cmd.command,
                shell=cmd.shell,
                capture_output=cmd.capture_output,
                text=True,
                timeout=cmd.timeout if cmd.timeout > 0 else None,
                env=cmd.env,
                cwd=cmd.cwd,
            )

            cmd.result = result
            cmd.output = result.stdout
            cmd.error = result.stderr

            if result.returncode == 0:
                cmd.status = ExecutionStatus.SUCCESS
            else:
                cmd.status = ExecutionStatus.FAILED

        except subprocess.TimeoutExpired:
            cmd.status = ExecutionStatus.FAILED
            cmd.error = f"Command timed out after {cmd.timeout}s"

        except asyncio.CancelledError:
            cmd.status = ExecutionStatus.CANCELLED
            cmd.error = "Command cancelled"

        except Exception as e:
            cmd.status = ExecutionStatus.FAILED
            cmd.error = str(e)

        cmd.end_time = time.time()
        return cmd

    async def execute_parallel(
        self,
        commands: List[AsyncCommand],
    ) -> ExecutionResult:
        """Execute commands in parallel."""
        console.info(
            f"Executing {len(commands)} commands in parallel (max {self.max_workers} workers)..."
        )

        start_time = time.time()

        # Create tasks
        tasks = [asyncio.create_task(self.execute_single(cmd)) for cmd in commands]

        # Execute with semaphore to limit concurrent tasks
        semaphore = asyncio.Semaphore(self.max_workers)

        async def execute_with_sem(task):
            async with semaphore:
                return await task

        results = await asyncio.gather(
            *[execute_with_sem(task) for task in tasks], return_exceptions=False
        )

        duration = time.time() - start_time

        # Count results
        successful = sum(1 for cmd in results if cmd.status == ExecutionStatus.SUCCESS)
        failed = sum(1 for cmd in results if cmd.status == ExecutionStatus.FAILED)
        cancelled = sum(1 for cmd in results if cmd.status == ExecutionStatus.CANCELLED)

        console.success(
            f"Parallel execution completed: {successful} success, {failed} failed, {cancelled} cancelled"
        )

        return ExecutionResult(
            total=len(commands),
            successful=successful,
            failed=failed,
            cancelled=cancelled,
            commands=results,
            duration=duration,
            parallel=True,
        )

    async def execute_sequence(
        self,
        commands: List[AsyncCommand],
        stop_on_error: bool = True,
    ) -> ExecutionResult:
        """Execute commands sequentially."""
        console.info(f"Executing {len(commands)} commands sequentially...")

        start_time = time.time()
        results = []

        for cmd in commands:
            result = await self.execute_single(cmd)
            results.append(result)

            # Stop if command failed and stop_on_error is True
            if result.status == ExecutionStatus.FAILED and stop_on_error:
                console.warning(
                    f"Stopping sequence due to failed command: {' '.join(cmd.command)}"
                )
                # Cancel remaining commands
                for remaining_cmd in commands[len(results) :]:
                    remaining_cmd.status = ExecutionStatus.CANCELLED
                    remaining_cmd.error = "Cancelled due to previous failure"
                    results.append(remaining_cmd)
                break

        duration = time.time() - start_time

        successful = sum(1 for cmd in results if cmd.status == ExecutionStatus.SUCCESS)
        failed = sum(1 for cmd in results if cmd.status == ExecutionStatus.FAILED)
        cancelled = sum(1 for cmd in results if cmd.status == ExecutionStatus.CANCELLED)

        console.success(
            f"Sequential execution completed: {successful} success, {failed} failed, {cancelled} cancelled"
        )

        return ExecutionResult(
            total=len(commands),
            successful=successful,
            failed=failed,
            cancelled=cancelled,
            commands=results,
            duration=duration,
            parallel=False,
        )

    async def execute_pipeline(
        self,
        commands: List[AsyncCommand],
        pipe_output: bool = True,
    ) -> ExecutionResult:
        """Execute commands as a pipeline (output of one feeds into next)."""
        console.info(f"Executing {len(commands)} commands as pipeline...")

        start_time = time.time()
        results = []

        previous_output = None

        for i, cmd in enumerate(commands):
            # For pipeline, each command (except first) receives input from previous
            if i > 0 and pipe_output:
                cmd.env = cmd.env or {}
                cmd.env["BDEV_PIPELINE_INPUT"] = previous_output or ""

            result = await self.execute_single(cmd)
            results.append(result)

            if result.status == ExecutionStatus.SUCCESS:
                previous_output = result.output
            else:
                console.warning(f"Pipeline failed at step {i + 1}")
                break

        duration = time.time() - start_time

        successful = sum(1 for cmd in results if cmd.status == ExecutionStatus.SUCCESS)
        failed = sum(1 for cmd in results if cmd.status == ExecutionStatus.FAILED)
        cancelled = sum(1 for cmd in results if cmd.status == ExecutionStatus.CANCELLED)

        return ExecutionResult(
            total=len(commands),
            successful=successful,
            failed=failed,
            cancelled=cancelled,
            commands=results,
            duration=duration,
            parallel=False,
        )

    async def execute_worker_pool(
        self,
        commands: List[AsyncCommand],
        batch_size: int = 10,
    ) -> ExecutionResult:
        """Execute commands using worker pool (process by process batches)."""
        console.info(
            f"Executing {len(commands)} commands with worker pool (batch size: {batch_size})..."
        )

        start_time = time.time()
        results = []

        # Process in batches
        for i in range(0, len(commands), batch_size):
            batch = commands[i : i + batch_size]
            console.info(f"Processing batch {i // batch_size + 1}...")

            batch_results = await self.execute_parallel(batch)
            results.extend(batch_results.commands)

        duration = time.time() - start_time

        successful = sum(1 for cmd in results if cmd.status == ExecutionStatus.SUCCESS)
        failed = sum(1 for cmd in results if cmd.status == ExecutionStatus.FAILED)
        cancelled = sum(1 for cmd in results if cmd.status == ExecutionStatus.CANCELLED)

        return ExecutionResult(
            total=len(commands),
            successful=successful,
            failed=failed,
            cancelled=cancelled,
            commands=results,
            duration=duration,
            parallel=True,
        )


@handle_errors()
def parse_command_args(
    *args: str,
    shell: bool = False,
    timeout: int = 300,
    env: Optional[Dict[str, str]] = None,
    cwd: Optional[str] = None,
) -> AsyncCommand:
    """Parse command arguments into AsyncCommand."""
    if shell:
        command = [" ".join(args)]
    else:
        command = list(args)

    return AsyncCommand(
        command=command,
        shell=shell,
        timeout=timeout,
        env=env,
        cwd=cwd,
        id=str(hash(" ".join(command))),
    )


async def run_async(*cmds: str) -> ExecutionResult:
    """Run commands asynchronously (parallel)."""
    commands = [parse_command_args(*cmd.split()) for cmd in cmds]
    runner = AsyncRunner()
    return await runner.execute_parallel(commands)


async def run_parallel(*cmds: str) -> ExecutionResult:
    """Run commands in parallel."""
    commands = [parse_command_args(*cmd.split()) for cmd in cmds]
    runner = AsyncRunner()
    return await runner.execute_parallel(commands)


async def run_sequence(*cmds: str, stop_on_error: bool = True) -> ExecutionResult:
    """Run commands sequentially."""
    commands = [parse_command_args(*cmd.split()) for cmd in cmds]
    runner = AsyncRunner()
    return await runner.execute_sequence(commands, stop_on_error)


async def run_pipeline(*cmds: str) -> ExecutionResult:
    """Run commands as a pipeline."""
    commands = [parse_command_args(*cmd.split()) for cmd in cmds]
    runner = AsyncRunner()
    return await runner.execute_pipeline(commands)


async def run_worker_pool(*cmds: str, batch_size: int = 10) -> ExecutionResult:
    """Run commands using worker pool."""
    commands = [parse_command_args(*cmd.split()) for cmd in cmds]
    runner = AsyncRunner()
    return await runner.execute_worker_pool(commands, batch_size)


# Helper function to run async commands and get result
def execute_async(*cmds: str, mode: str = "parallel", **kwargs) -> ExecutionResult:
    """Execute async commands synchronously (wrapper)."""
    mode_functions = {
        "async": run_async,
        "parallel": run_parallel,
        "sequence": run_sequence,
        "pipeline": run_pipeline,
        "worker_pool": lambda *c: run_worker_pool(*c, **kwargs),
    }

    func = mode_functions.get(mode, run_parallel)
    return asyncio.run(func(*cmds))
