"""
Workflows Automation System for B.DEV CLI.

Provides powerful workflow automation with YAML definitions,
step execution, error handling, retries, and scheduling.
"""

import json
import yaml
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, asdict, field
from datetime import datetime
from enum import Enum
import asyncio

from cli.utils.ui import console
from cli.utils.errors import handle_errors, ValidationError


class StepStatus(Enum):
    """Status of a workflow step."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    RETRYING = "retrying"


class WorkflowStatus(Enum):
    """Status of a workflow."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


@dataclass
class Step:
    """Workflow step definition."""

    name: str
    command: str
    description: str = ""
    on_fail: str = "stop"  # stop, continue, retry
    retry: int = 0
    retry_delay: int = 5
    timeout: int = 300
    conditions: List[str] = field(default_factory=list)
    output_capture: bool = True
    status: StepStatus = StepStatus.PENDING
    output: str = ""
    error: str = ""
    start_time: Optional[str] = None
    end_time: Optional[str] = None


@dataclass
class Workflow:
    """Workflow definition."""

    name: str
    description: str = ""
    steps: List[Step] = field(default_factory=list)
    status: WorkflowStatus = WorkflowStatus.PENDING
    created_at: str = ""
    last_run: Optional[str] = None
    total_runs: int = 0
    successful_runs: int = 0
    failed_runs: int = 0
    variables: Dict[str, Any] = field(default_factory=dict)
    environment: Dict[str, str] = field(default_factory=dict)


class WorkflowRunner:
    """Execute workflow steps with error handling and retries."""

    def __init__(self, workflow: Workflow) -> None:
        self.workflow = workflow
        self.current_step: int = 0
        self._stop_flag = False

    def stop(self) -> None:
        """Stop workflow execution."""
        self._stop_flag = True

    async def run_step(self, step: Step) -> Step:
        """Run a single workflow step."""
        step.status = StepStatus.RUNNING
        step.start_time = datetime.now().isoformat()

        console.info(f"Running step: {step.name}")
        console.muted(f"  Command: {step.command}")

        # Check conditions
        if not self._check_conditions(step):
            step.status = StepStatus.SKIPPED
            console.warning(f"  Skipped: Conditions not met")
            return step

        # Run command with retries
        retry_count = 0
        while retry_count <= step.retry and not self._stop_flag:
            try:
                # Execute command
                result = await asyncio.to_thread(
                    subprocess.run,
                    step.command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=step.timeout,
                    env={
                        **dict(self.workflow.environment),
                        **dict(self.workflow.variables),
                    },
                )

                if result.returncode == 0:
                    step.status = StepStatus.SUCCESS
                    step.output = result.stdout
                    console.success(f"  [OK] {step.name}")
                    break
                else:
                    raise subprocess.CalledProcessError(
                        result.returncode, step.command, result.stderr
                    )

            except subprocess.TimeoutExpired:
                step.error = f"Command timed out after {step.timeout}s"
                retry_count += 1

            except subprocess.CalledProcessError as e:
                step.error = str(e.stderr)
                retry_count += 1

            except Exception as e:
                step.error = str(e)
                retry_count += 1

            if retry_count <= step.retry and not self._stop_flag:
                step.status = StepStatus.RETRYING
                console.warning(f"  [RETRY {retry_count}/{step.retry}] {step.name}")
                await asyncio.sleep(step.retry_delay)
            elif self._stop_flag:
                step.status = StepStatus.FAILED
                break
            else:
                step.status = StepStatus.FAILED
                console.error(f"  [FAILED] {step.name}: {step.error}")

        step.end_time = datetime.now().isoformat()
        return step

    def _check_conditions(self, step: Step) -> bool:
        """Check step conditions."""
        if not step.conditions:
            return True

        for condition in step.conditions:
            # Simple variable substitution and evaluation
            try:
                condition = condition.format(**self.workflow.variables)
                if not eval(condition):
                    return False
            except Exception:
                return False

        return True

    async def run(self) -> Workflow:
        """Run the entire workflow."""
        self.workflow.status = WorkflowStatus.RUNNING
        console.rule(f"Running Workflow: {self.workflow.name}")

        failed_steps = []

        for i, step in enumerate(self.workflow.steps):
            if self._stop_flag:
                self.workflow.status = WorkflowStatus.CANCELLED
                break

            self.current_step = i
            step = await self.run_step(step)

            if step.status == StepStatus.FAILED:
                failed_steps.append(step)

                if step.on_fail == "stop":
                    console.error(f"Workflow stopped due to failed step: {step.name}")
                    break
                elif step.on_fail == "continue":
                    console.warning(f"Continuing despite failed step: {step.name}")
                elif step.on_fail == "retry":
                    console.warning(f"Retrying step (max {step.retry} times)")

        # Determine final status
        if self._stop_flag:
            self.workflow.status = WorkflowStatus.CANCELLED
        elif failed_steps:
            self.workflow.status = WorkflowStatus.FAILED
            self.workflow.failed_runs += 1
            console.error(f"Workflow failed: {len(failed_steps)} step(s) failed")
        else:
            self.workflow.status = WorkflowStatus.SUCCESS
            self.workflow.successful_runs += 1
            console.success("Workflow completed successfully")

        self.workflow.last_run = datetime.now().isoformat()
        self.workflow.total_runs += 1

        return self.workflow


class WorkflowManager:
    """Manager for workflow definitions and execution."""

    WORKFLOWS_DIR = Path.home() / ".bdev" / "workflows"
    INDEX_FILE = WORKFLOWS_DIR / "index.json"

    def __init__(self) -> None:
        self._workflows: Dict[str, Workflow] = {}
        self._ensure_workflows_dir()
        self._load_index()

    def _ensure_workflows_dir(self) -> None:
        """Create workflows directory if it doesn't exist."""
        self.WORKFLOWS_DIR.mkdir(parents=True, exist_ok=True)

    def _load_index(self) -> None:
        """Load workflow index."""
        if self.INDEX_FILE.exists():
            try:
                with open(self.INDEX_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for name, workflow_data in data.items():
                        steps_data = workflow_data.get("steps", [])
                        steps = [
                            Step(
                                **{
                                    k: v
                                    for k, v in step_data.items()
                                    if k != "status" and k != "output" and k != "error"
                                }
                            )
                            for step_data in steps_data
                        ]
                        workflow_data["steps"] = steps
                        self._workflows[name] = Workflow(**workflow_data)
            except Exception as e:
                console.error(f"Failed to load workflow index: {e}")

    def _save_index(self) -> None:
        """Save workflow index."""
        try:
            data = {
                name: {
                    **asdict(workflow),
                    "steps": [
                        {k: v for k, v in asdict(step).items() if k != "status"}
                        for step in workflow.steps
                    ],
                }
                for name, workflow in self._workflows.items()
            }
            with open(self.INDEX_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            console.error(f"Failed to save workflow index: {e}")

    @handle_errors()
    def create(
        self,
        name: str,
        steps: List[Dict[str, Any]],
        description: str = "",
        variables: Optional[Dict[str, Any]] = None,
        environment: Optional[Dict[str, str]] = None,
    ) -> Workflow:
        """Create a new workflow."""
        if name in self._workflows:
            console.warning(f"Workflow '{name}' already exists. Overwriting.")

        workflow = Workflow(
            name=name,
            description=description,
            steps=[
                Step(**{k: v for k, v in step.items() if k != "status"})
                for step in steps
            ],
            created_at=datetime.now().isoformat(),
            variables=variables or {},
            environment=environment or {},
        )

        self._workflows[name] = workflow
        self._save_index()
        console.success(f"Workflow '{name}' created with {len(steps)} steps")
        return workflow

    @handle_errors()
    def create_from_yaml(self, file_path: str) -> Optional[Workflow]:
        """Create workflow from YAML file."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            name = data.get("name", Path(file_path).stem)
            description = data.get("description", "")
            steps_data = data.get("steps", [])
            variables = data.get("variables", {})
            environment = data.get("environment", {})

            return self.create(name, steps_data, description, variables, environment)

        except FileNotFoundError:
            console.error(f"File not found: {file_path}")
            return None
        except yaml.YAMLError as e:
            console.error(f"Invalid YAML: {e}")
            return None

    @handle_errors()
    def list(self) -> List[Workflow]:
        """List all workflows."""
        if not self._workflows:
            console.info("No workflows found")
            return []

        console.rule("Workflows")

        rows = []
        for workflow in sorted(self._workflows.values(), key=lambda w: w.name):
            success_rate = (
                (workflow.successful_runs / workflow.total_runs * 100)
                if workflow.total_runs > 0
                else 0
            )
            rows.append(
                [
                    workflow.name,
                    workflow.description or "-",
                    str(len(workflow.steps)),
                    str(workflow.total_runs),
                    f"{success_rate:.1f}%",
                ]
            )

        console.table(
            "Workflows", ["Name", "Description", "Steps", "Runs", "Success Rate"], rows
        )

        return list(self._workflows.values())

    @handle_errors()
    def get(self, name: str) -> Optional[Workflow]:
        """Get a workflow by name."""
        return self._workflows.get(name)

    @handle_errors()
    async def run(
        self, name: str, variables: Optional[Dict[str, Any]] = None
    ) -> Optional[Workflow]:
        """Run a workflow."""
        workflow = self.get(name)
        if not workflow:
            console.error(f"Workflow '{name}' not found")
            return None

        # Merge runtime variables
        if variables:
            workflow.variables.update(variables)

        runner = WorkflowRunner(workflow)
        result = await runner.run()

        self._save_index()
        return result

    @handle_errors()
    def run_sync(
        self, name: str, variables: Optional[Dict[str, Any]] = None
    ) -> Optional[Workflow]:
        """Run a workflow synchronously."""
        return asyncio.run(self.run(name, variables))

    @handle_errors()
    def logs(self, name: str) -> Optional[Dict[str, Any]]:
        """Show workflow logs from last run."""
        workflow = self.get(name)
        if not workflow:
            console.error(f"Workflow '{name}' not found")
            return None

        console.rule(f"Workflow Logs: {name}")
        console.info(f"Status: {workflow.status.value}")
        console.info(f"Last run: {workflow.last_run or 'Never'}")

        if workflow.steps:
            console.table(
                "Steps",
                ["Name", "Status", "Command", "Duration"],
                [
                    [
                        step.name,
                        step.status.value,
                        step.command[:50],
                        self._calculate_duration(step),
                    ]
                    for step in workflow.steps
                ],
            )

        return {
            "workflow": workflow.name,
            "status": workflow.status.value,
            "steps": len(workflow.steps),
        }

    def _calculate_duration(self, step: Step) -> str:
        """Calculate step duration."""
        if step.start_time and step.end_time:
            try:
                start = datetime.fromisoformat(step.start_time)
                end = datetime.fromisoformat(step.end_time)
                duration = (end - start).total_seconds()
                return f"{duration:.2f}s"
            except Exception:
                pass
        return "-"

    @handle_errors()
    def validate(self, name: str) -> bool:
        """Validate a workflow."""
        workflow = self.get(name)
        if not workflow:
            console.error(f"Workflow '{name}' not found")
            return False

        console.info(f"Validating workflow '{name}'...")

        errors = []

        if not workflow.steps:
            errors.append("Workflow has no steps")

        for i, step in enumerate(workflow.steps):
            if not step.name:
                errors.append(f"Step {i + 1} has no name")
            if not step.command:
                errors.append(f"Step '{step.name}' has no command")

        if errors:
            console.error("Validation failed:")
            for error in errors:
                console.error(f"  - {error}")
            return False

        console.success("Workflow validation passed")
        return True

    @handle_errors()
    def delete(self, name: str) -> bool:
        """Delete a workflow."""
        if name not in self._workflows:
            console.error(f"Workflow '{name}' not found")
            return False

        del self._workflows[name]
        self._save_index()
        console.success(f"Workflow '{name}' deleted")
        return True

    @handle_errors()
    def export(self, name: str, file_path: str, format: str = "yaml") -> bool:
        """Export workflow to file."""
        workflow = self.get(name)
        if not workflow:
            console.error(f"Workflow '{name}' not found")
            return False

        try:
            data = {
                "name": workflow.name,
                "description": workflow.description,
                "steps": [
                    {
                        "name": step.name,
                        "command": step.command,
                        "description": step.description,
                        "on_fail": step.on_fail,
                        "retry": step.retry,
                        "timeout": step.timeout,
                    }
                    for step in workflow.steps
                ],
                "variables": workflow.variables,
                "environment": workflow.environment,
            }

            with open(file_path, "w", encoding="utf-8") as f:
                if format == "yaml":
                    yaml.dump(data, f, default_flow_style=False)
                else:
                    json.dump(data, f, indent=2)

            console.success(f"Workflow '{name}' exported to {file_path}")
            return True
        except Exception as e:
            console.error(f"Failed to export workflow: {e}")
            return False

    @handle_errors()
    def import_from(self, file_path: str) -> Optional[Workflow]:
        """Import workflow from file."""
        path = Path(file_path)
        if path.suffix in [".yaml", ".yml"]:
            return self.create_from_yaml(file_path)
        else:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                name = data.get("name", path.stem)
                return self.create(
                    name,
                    data.get("steps", []),
                    data.get("description", ""),
                    data.get("variables", {}),
                    data.get("environment", {}),
                )
            except Exception as e:
                console.error(f"Failed to import workflow: {e}")
                return None


# Global workflow manager instance
workflows = WorkflowManager()
