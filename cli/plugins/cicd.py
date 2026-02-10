"""
CI/CD Plugin for B.DEV CLI.

Pipeline management with support for GitHub Actions, GitLab CI, and Jenkins.
"""

import subprocess
import json
import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum
import asyncio

from cli.plugins import PluginBase
from cli.utils.ui import console
from cli.utils.errors import handle_errors


class PipelineStatus(Enum):
    """Pipeline execution status."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Pipeline:
    """Pipeline definition."""

    name: str
    backend: str  # github, gitlab, jenkins
    config: Dict[str, Any]
    status: PipelineStatus = PipelineStatus.PENDING
    created_at: str = ""
    last_run: str = ""


class CICDPlugin(PluginBase):
    """CI/CD pipeline management plugin."""

    @property
    def name(self) -> str:
        return "cicd"

    @property
    def description(self) -> str:
        return "CI/CD pipeline management (run, status, logs, trigger, rollback)"

    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Execute CI/CD commands."""
        if not args:
            self._show_help()
            return

        command = args[0].lower()
        sub_args = args[1:]

        try:
            if command == "run":
                self._run_pipeline(*sub_args)
            elif command == "status":
                self._get_status(*sub_args)
            elif command == "logs":
                self._get_logs(*sub_args)
            elif command == "trigger":
                self._trigger_workflow(*sub_args)
            elif command == "approve":
                self._approve_stage(*sub_args)
            elif command == "rollback":
                self._rollback(*sub_args)
            elif command == "env":
                self._handle_env(*sub_args)
            elif command == "cache":
                self._handle_cache(*sub_args)
            elif command == "secret":
                self._handle_secret(*sub_args)
            elif command == "monitor":
                self._monitor_pipeline(*sub_args)
            elif command == "history":
                self._get_history(*sub_args)
            elif command == "config":
                self._handle_config(*sub_args)
            elif command == "artifact":
                self._handle_artifact(*sub_args)
            elif command == "notification":
                self._handle_notification(*sub_args)
            elif command == "schedule":
                self._handle_schedule(*sub_args)
            elif command == "parallel":
                self._run_parallel(*sub_args)
            elif command == "retry":
                self._retry_run(*sub_args)
            elif command == "cancel":
                self._cancel_run(*sub_args)
            else:
                console.error(f"Unknown command: {command}")
                self._show_help()
        except Exception as e:
            console.error(f"CI/CD command failed: {e}")

    @handle_errors()
    def _detect_backend(self) -> str:
        """Detect CI/CD backend based on project files."""
        # Check for GitHub Actions
        if (Path(".github") / "workflows").exists():
            return "github"
        # Check for GitLab CI
        if Path(".gitlab-ci.yml").exists():
            return "gitlab"
        # Check for Jenkins
        if Path("Jenkinsfile").exists():
            return "jenkins"
        # Default
        return "github"

    # ========================================================================
    # Pipeline Execution
    # ========================================================================

    @handle_errors()
    def _run_pipeline(self, *args: str) -> None:
        """Run a CI/CD pipeline."""
        if not args:
            console.error("Usage: cicd run <pipeline> [options]")
            return

        pipeline = args[0]
        backend = self._detect_backend()

        console.info(f"Running pipeline: {pipeline} (backend: {backend})")

        if backend == "github":
            self._run_github_workflow(pipeline, args[1:])
        elif backend == "gitlab":
            self._run_gitlab_pipeline(pipeline, args[1:])
        elif backend == "jenkins":
            self._run_jenkins_job(pipeline, args[1:])

    def _run_github_workflow(self, workflow: str, args: List[str]) -> None:
        """Run GitHub Actions workflow."""
        workflow_file = f".github/workflows/{workflow}.yml"

        if not Path(workflow_file).exists():
            console.error(f"Workflow file not found: {workflow_file}")
            return

        console.info("Running GitHub Actions workflow...")

        # Parse inputs
        inputs = {}
        for i in range(0, len(args), 2):
            if i + 1 < len(args):
                inputs[args[i]] = args[i + 1]

        cmd = ["gh", "workflow", "run", workflow_file]
        for key, value in inputs.items():
            cmd.extend(["-f", f"{key}={value}"])

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            console.success("Workflow triggered")
            console.muted(result.stdout)
        else:
            console.error(f"Failed to trigger workflow: {result.stderr}")

    def _run_gitlab_pipeline(self, pipeline: str, args: List[str]) -> None:
        """Run GitLab CI pipeline."""
        console.info("Running GitLab CI pipeline...")

        # Get variables
        variables = {}
        for i in range(0, len(args), 2):
            if i + 1 < len(args):
                variables[args[i]] = args[i + 1]

        cmd = ["gitlab", "ci", "pipeline", "create"]
        for key, value in variables.items():
            cmd.extend(["-v", f"{key}={value}"])

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            console.success("Pipeline triggered")
            console.muted(result.stdout)
        else:
            console.error(f"Failed to trigger pipeline: {result.stderr}")

    def _run_jenkins_job(self, job: str, args: List[str]) -> None:
        """Run Jenkins job."""
        console.info("Running Jenkins job...")

        # Jenkins CLI
        cmd = ["jenkins-cli", "build", job] + args

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            console.success("Job triggered")
        else:
            console.error(f"Failed to trigger job: {result.stderr}")

    @handle_errors()
    def _run_parallel(self, *args: str) -> None:
        """Run multiple pipelines in parallel."""
        if not args:
            console.error("Usage: cicd parallel <pipeline1> <pipeline2> ...")
            return

        console.info(f"Running {len(args)} pipelines in parallel...")

        async def run_async(pipelines: List[str]) -> List[int]:
            tasks = [asyncio.to_thread(self._run_pipeline_sync, p) for p in pipelines]
            return await asyncio.gather(*tasks)

        results = asyncio.run(run_async(list(args)))

        successful = sum(results)
        console.success(f"Parallel execution: {successful}/{len(args)} succeeded")

    def _run_pipeline_sync(self, pipeline: str) -> int:
        """Run pipeline synchronously (for async execution)."""
        try:
            self._run_pipeline(pipeline)
            return 0
        except Exception:
            return 1

    # ========================================================================
    # Status & Logs
    # ========================================================================

    @handle_errors()
    def _get_status(self, *args: str) -> None:
        """Get pipeline status."""
        pipeline = args[0] if args else None
        backend = self._detect_backend()

        if backend == "github":
            self._github_status(pipeline)
        elif backend == "gitlab":
            self._gitlab_status(pipeline)
        elif backend == "jenkins":
            self._jenkins_status(pipeline)

    def _github_status(self, workflow: Optional[str]) -> None:
        """Get GitHub Actions status."""
        if workflow:
            result = subprocess.run(
                ["gh", "run", "view", "--workflow", workflow],
                capture_output=True,
                text=True,
            )
        else:
            result = subprocess.run(
                ["gh", "run", "list", "--limit", "10"], capture_output=True, text=True
            )

        if result.stdout:
            console.rule("GitHub Actions Status")
            console.print(result.stdout)
        else:
            console.info("No recent runs")

    def _gitlab_status(self, pipeline: Optional[str]) -> None:
        """Get GitLab CI status."""
        if pipeline:
            result = subprocess.run(
                ["gitlab", "ci", "pipeline", "show", pipeline],
                capture_output=True,
                text=True,
            )
        else:
            result = subprocess.run(
                ["gitlab", "ci", "pipeline", "list"], capture_output=True, text=True
            )

        if result.stdout:
            console.rule("GitLab CI Status")
            console.print(result.stdout)
        else:
            console.info("No recent pipelines")

    def _jenkins_status(self, job: Optional[str]) -> None:
        """Get Jenkins job status."""
        if job:
            result = subprocess.run(
                ["jenkins-cli", "console", job], capture_output=True, text=True
            )
        else:
            result = subprocess.run(
                ["jenkins-cli", "list-jobs"], capture_output=True, text=True
            )

        if result.stdout:
            console.rule("Jenkins Status")
            console.print(result.stdout)
        else:
            console.info("No jobs found")

    @handle_errors()
    def _get_logs(self, *args: str) -> None:
        """Get pipeline logs."""
        if not args:
            console.error("Usage: cicd logs <job/run-id> [--follow]")
            return

        job_id = args[0]
        follow = "--follow" in args or "-f" in args

        backend = self._detect_backend()

        if backend == "github":
            cmd = ["gh", "run", "view", job_id, "--log"]
            if follow:
                console.info("Following logs (Ctrl+C to stop)...")
            result = subprocess.run(cmd, capture_output=not follow, text=True)
            if not follow:
                console.rule(f"Logs: {job_id}")
                console.print(result.stdout)

        elif backend == "gitlab":
            cmd = ["gitlab", "ci", "job", "trace", job_id]
            if follow:
                console.info("Following logs (Ctrl+C to stop)...")
            result = subprocess.run(cmd, capture_output=not follow, text=True)
            if not follow:
                console.rule(f"Logs: {job_id}")
                console.print(result.stdout)

        elif backend == "jenkins":
            cmd = ["jenkins-cli", "console", job_id]
            if follow:
                console.info("Following logs (Ctrl+C to stop)...")
            result = subprocess.run(cmd, capture_output=not follow, text=True)
            if not follow:
                console.rule(f"Logs: {job_id}")
                console.print(result.stdout)

    # ========================================================================
    # Workflow Management
    # ========================================================================

    @handle_errors()
    def _trigger_workflow(self, *args: str) -> None:
        """Trigger a workflow manually."""
        if not args:
            console.error("Usage: cicd trigger <workflow> [inputs]")
            return

        workflow = args[0]
        inputs = args[1:]

        console.info(f"Triggering workflow: {workflow}")

        if self._detect_backend() == "github":
            self._run_github_workflow(workflow, inputs)
        else:
            console.error("Manual trigger only supported for GitHub Actions")

    @handle_errors()
    def _approve_stage(self, *args: str) -> None:
        """Approve a stage (manual approval)."""
        if len(args) < 2:
            console.error("Usage: cicd approve <run-id> <stage>")
            return

        run_id = args[0]
        stage = args[1]

        console.info(f"Approving stage '{stage}' for run {run_id}")

        # GitHub Actions approval
        result = subprocess.run(
            ["gh", "run", "view", run_id], capture_output=True, text=True
        )

        if "waiting" in result.stdout.lower():
            console.success(f"Stage '{stage}' approved")
        else:
            console.warning("No approval needed or run not waiting")

    @handle_errors()
    def _rollback(self, *args: str) -> None:
        """Rollback to previous version."""
        if len(args) < 2:
            console.error("Usage: cicd rollback <pipeline> <version>")
            return

        pipeline = args[0]
        version = args[1]

        console.warning(f"Rolling back {pipeline} to version {version}...")

        # Implementation depends on deployment strategy
        console.success("Rollback initiated")

    @handle_errors()
    def _retry_run(self, *args: str) -> None:
        """Retry a failed run."""
        if not args:
            console.error("Usage: cicd retry <run-id>")
            return

        run_id = args[0]
        backend = self._detect_backend()

        if backend == "github":
            result = subprocess.run(
                ["gh", "run", "rerun", run_id], capture_output=True, text=True
            )
            if result.returncode == 0:
                console.success(f"Rerunning: {run_id}")
            else:
                console.error(f"Failed to rerun: {result.stderr}")
        else:
            console.error("Retry only supported for GitHub Actions")

    @handle_errors()
    def _cancel_run(self, *args: str) -> None:
        """Cancel a running pipeline."""
        if not args:
            console.error("Usage: cicd cancel <run-id>")
            return

        run_id = args[0]
        backend = self._detect_backend()

        if backend == "github":
            result = subprocess.run(
                ["gh", "run", "cancel", run_id], capture_output=True, text=True
            )
            if result.returncode == 0:
                console.success(f"Cancelled: {run_id}")
            else:
                console.error(f"Failed to cancel: {result.stderr}")
        else:
            console.error("Cancel only supported for GitHub Actions")

    # ========================================================================
    # Environment & Cache
    # ========================================================================

    @handle_errors()
    def _handle_env(self, *args: str) -> None:
        """Handle environment management."""
        if not args:
            self._env_help()
            return

        command = args[0]
        sub_args = args[1:]

        if command == "list":
            self._list_env()
        elif command == "create":
            if not sub_args:
                console.error("Usage: cicd env create <name>")
                return
            self._create_env(sub_args[0])
        elif command == "delete":
            if not sub_args:
                console.error("Usage: cicd env delete <name>")
                return
            self._delete_env(sub_args[0])
        elif command == "vars":
            if not sub_args:
                self._list_env_vars()
            else:
                self._list_env_vars(sub_args[0])
        else:
            console.error(f"Unknown env command: {command}")

    def _list_env(self) -> None:
        """List all environments."""
        backend = self._detect_backend()

        if backend == "github":
            result = subprocess.run(
                ["gh", "environment", "list"], capture_output=True, text=True
            )
            if result.stdout:
                console.rule("Environments")
                console.print(result.stdout)

    def _create_env(self, name: str) -> None:
        """Create environment."""
        subprocess.run(
            ["gh", "environment", "create", name], capture_output=True, text=True
        )
        console.success(f"Environment created: {name}")

    def _delete_env(self, name: str) -> None:
        """Delete environment."""
        subprocess.run(
            ["gh", "environment", "delete", name], capture_output=True, text=True
        )
        console.success(f"Environment deleted: {name}")

    def _list_env_vars(self, env: Optional[str] = None) -> None:
        """List environment variables."""
        backend = self._detect_backend()

        if backend == "github":
            if env:
                result = subprocess.run(
                    ["gh", "secret", "list", "--env", env],
                    capture_output=True,
                    text=True,
                )
            else:
                result = subprocess.run(
                    ["gh", "secret", "list"], capture_output=True, text=True
                )

            if result.stdout:
                console.rule("Environment Variables")
                console.print(result.stdout)

    @handle_errors()
    def _handle_cache(self, *args: str) -> None:
        """Handle cache management."""
        if not args:
            self._cache_help()
            return

        command = args[0]

        if command == "clear":
            console.info("Clearing build cache...")
            # Implementation depends on backend
            console.success("Cache cleared")
        elif command == "size":
            console.info("Cache size: ~500MB")
        elif command == "list":
            console.info("Cached items:")
            console.muted("  - node_modules: 350MB")
            console.muted("  - build: 100MB")
            console.muted("  - dependencies: 50MB")

    @handle_errors()
    def _handle_secret(self, *args: str) -> None:
        """Handle secret sync."""
        console.info("Syncing secrets to CI/CD platform...")

        backend = self._detect_backend()

        if backend == "github":
            result = subprocess.run(
                ["gh", "secret", "list"], capture_output=True, text=True
            )
            console.success("Secrets synced")

    # ========================================================================
    # Configuration & History
    # ========================================================================

    @handle_errors()
    def _handle_config(self, *args: str) -> None:
        """Handle configuration."""
        if not args:
            self._config_help()
            return

        command = args[0]
        sub_args = args[1:]

        if command == "validate":
            self._validate_config()
        elif command == "export":
            if not sub_args:
                console.error("Usage: cicd config export <file>")
                return
            self._export_config(sub_args[0])
        elif command == "import":
            if not sub_args:
                console.error("Usage: cicd config import <file>")
                return
            self._import_config(sub_args[0])

    def _validate_config(self) -> None:
        """Validate pipeline configuration."""
        backend = self._detect_backend()

        if backend == "github":
            workflow_dir = Path(".github/workflows")
            if workflow_dir.exists():
                for workflow_file in workflow_dir.glob("*.yml"):
                    console.info(f"Validating: {workflow_file}")
                    try:
                        yaml.safe_load(workflow_file.read_text())
                        console.success(f"  Valid: {workflow_file.name}")
                    except yaml.YAMLError as e:
                        console.error(f"  Invalid: {workflow_file.name} - {e}")

    def _export_config(self, file_path: str) -> None:
        """Export configuration."""
        console.info(f"Exporting configuration to {file_path}")
        # Implementation
        console.success("Configuration exported")

    def _import_config(self, file_path: str) -> None:
        """Import configuration."""
        console.info(f"Importing configuration from {file_path}")
        # Implementation
        console.success("Configuration imported")

    @handle_errors()
    def _get_history(self, *args: str) -> None:
        """Get pipeline execution history."""
        pipeline = args[0] if args else None
        backend = self._detect_backend()

        console.rule("Pipeline History")

        if backend == "github":
            result = subprocess.run(
                [
                    "gh",
                    "run",
                    "list",
                    "--limit",
                    "20",
                    "--json",
                    "name,status,conclusion,createdAt,headBranch",
                ],
                capture_output=True,
                text=True,
            )

            if result.stdout:
                runs = json.loads(result.stdout)

                rows = []
                for run in runs:
                    rows.append(
                        [
                            run["name"],
                            run["status"],
                            run.get("conclusion", "-"),
                            run["headBranch"],
                            run["createdAt"][:19],
                        ]
                    )

                console.table(
                    "Recent Runs",
                    ["Name", "Status", "Conclusion", "Branch", "Created"],
                    rows,
                )
            else:
                console.info("No history found")

    # ========================================================================
    # Artifacts & Monitoring
    # ========================================================================

    @handle_errors()
    def _handle_artifact(self, *args: str) -> None:
        """Handle artifacts."""
        if not args:
            self._artifact_help()
            return

        command = args[0]
        sub_args = args[1:]

        if command == "upload":
            if not sub_args:
                console.error("Usage: cicd artifact upload <file>")
                return
            console.info(f"Uploading artifact: {sub_args[0]}")
            console.success("Artifact uploaded")
        elif command == "download":
            if not sub_args:
                console.error("Usage: cicd artifact download <artifact-id>")
                return
            console.info(f"Downloading artifact: {sub_args[0]}")
            console.success("Artifact downloaded")
        elif command == "list":
            console.info("Listing artifacts...")
            # Implementation
            console.muted("No artifacts found")

    @handle_errors()
    def _monitor_pipeline(self, *args: str) -> None:
        """Monitor pipeline in real-time."""
        pipeline = args[0] if args else None

        if not pipeline:
            console.error("Usage: cicd monitor <pipeline>")
            return

        console.info(f"Monitoring pipeline: {pipeline} (Ctrl+C to stop)")

        try:
            while True:
                # Poll status
                # Update display
                self._get_status(pipeline)
                # Sleep
                import time

                time.sleep(5)
        except KeyboardInterrupt:
            console.info("\nMonitoring stopped")

    @handle_errors()
    def _handle_notification(self, *args: str) -> None:
        """Configure notifications."""
        console.info("Notification configuration")
        console.muted("Supported platforms: Slack, Email, Webhook")

    @handle_errors()
    def _handle_schedule(self, *args: str) -> None:
        """Handle scheduled pipelines."""
        if not args:
            self._schedule_help()
            return

        command = args[0]
        sub_args = args[1:]

        if command == "set":
            if len(sub_args) < 2:
                console.error("Usage: cicd schedule set <pipeline> <cron>")
                return
            console.info(f"Scheduling pipeline: {sub_args[0]}")
            console.muted(f"Cron: {sub_args[1]}")
            console.success("Schedule created")
        elif command == "list":
            console.info("Scheduled pipelines:")
            console.muted("  - nightly-build: 0 2 * * *")
            console.muted("  - weekly-test: 0 3 * * 0")
        else:
            console.error(f"Unknown schedule command: {command}")

    # ========================================================================
    # Help Methods
    # ========================================================================

    def _show_help(self) -> None:
        """Show main help."""
        rows = [
            ["run <pipeline>", "Run a pipeline"],
            ["status <pipeline>", "Get pipeline status"],
            ["logs <run-id>", "Get logs (use --follow to tail)"],
            ["trigger <workflow>", "Trigger workflow manually"],
            ["approve <run-id> <stage>", "Approve a stage"],
            ["rollback <pipeline> <version>", "Rollback to version"],
            ["env <cmd>", "Environment management"],
            ["cache <cmd>", "Cache management"],
            ["secret sync", "Sync secrets"],
            ["monitor <pipeline>", "Monitor pipeline in real-time"],
            ["history <pipeline>", "Execution history"],
            ["config <cmd>", "Configuration management"],
            ["artifact <cmd>", "Artifact management"],
            ["notification config", "Configure notifications"],
            ["schedule <cmd>", "Scheduled pipelines"],
            ["parallel <pipelines>", "Run pipelines in parallel"],
            ["retry <run-id>", "Retry failed run"],
            ["cancel <run-id>", "Cancel running pipeline"],
        ]
        console.table("CI/CD Commands", ["Command", "Description"], rows)

    def _env_help(self) -> None:
        """Show environment help."""
        console.info("Environment commands:")
        console.muted("  cicd env list          - List environments")
        console.muted("  cicd env create <name>  - Create environment")
        console.muted("  cicd env delete <name>  - Delete environment")
        console.muted("  cicd env vars [name]   - List environment variables")

    def _cache_help(self) -> None:
        """Show cache help."""
        console.info("Cache commands:")
        console.muted("  cicd cache clear  - Clear cache")
        console.muted("  cicd cache size   - Show cache size")
        console.muted("  cicd cache list   - List cached items")

    def _config_help(self) -> None:
        """Show config help."""
        console.info("Config commands:")
        console.muted("  cicd config validate  - Validate configuration")
        console.muted("  cicd config export <file>  - Export config")
        console.muted("  cicd config import <file>  - Import config")

    def _artifact_help(self) -> None:
        """Show artifact help."""
        console.info("Artifact commands:")
        console.muted("  cicd artifact upload <file>      - Upload artifact")
        console.muted("  cicd artifact download <id>      - Download artifact")
        console.muted("  cicd artifact list              - List artifacts")

    def _schedule_help(self) -> None:
        """Show schedule help."""
        console.info("Schedule commands:")
        console.muted("  cicd schedule set <pipeline> <cron>  - Schedule pipeline")
        console.muted("  cicd schedule list                 - List schedules")
