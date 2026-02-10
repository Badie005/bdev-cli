"""
GitHub Plugin for B.DEV CLI

Provides GitHub API integration for workflows, releases, repository management,
and more using the GitHub CLI (gh) or direct API calls.
"""

import subprocess
import json
import os
from typing import Any, List, Dict, Optional
from pathlib import Path

from cli.plugins import PluginBase
from cli.utils.ui import console


class GitHubBase(PluginBase):
    """Base class for GitHub plugins."""

    _is_base = True

    def _run_gh(self, args: List[str]) -> subprocess.CompletedProcess:
        """Run GitHub CLI command."""
        cmd = ["gh"] + args
        return subprocess.run(cmd, capture_output=True, text=True)

    def _check_gh_installed(self) -> bool:
        """Check if GitHub CLI is installed."""
        result = self._run_gh(["--version"])
        return result.returncode == 0

    def _check_auth(self) -> bool:
        """Check if GitHub CLI is authenticated."""
        result = self._run_gh(["auth", "status"])
        return result.returncode == 0


# ============================================================================
# GitHub Workflows
# ============================================================================


class GitHubWorkflowPlugin(GitHubBase):
    """GitHub Actions workflow management."""

    @property
    def name(self) -> str:
        return "github_workflow"

    @property
    def description(self) -> str:
        return "GitHub Actions workflow management (list, run, logs, disable, enable)"

    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Handle workflow commands."""
        if not self._check_gh_installed():
            console.error(
                "GitHub CLI (gh) is not installed. Install from https://cli.github.com/"
            )
            return None

        if not self._check_auth():
            console.error("Not authenticated with GitHub. Run: gh auth login")
            return None

        if not args:
            self._show_help()
            return

        command = args[0].lower()
        sub_args = args[1:]

        try:
            if command == "list":
                self._list_workflows(*sub_args)
            elif command == "run":
                self._run_workflow(*sub_args)
            elif command == "logs":
                self._workflow_logs(*sub_args)
            elif command == "view":
                self._view_workflow(*sub_args)
            elif command == "disable":
                self._disable_workflow(*sub_args)
            elif command == "enable":
                self._enable_workflow(*sub_args)
            elif command == "status":
                self._workflow_status(*sub_args)
            elif command == "rerun":
                self._rerun_workflow(*sub_args)
            elif command == "cancel":
                self._cancel_workflow(*sub_args)
            else:
                console.error(f"Unknown workflow command: {command}")
                self._show_help()
        except Exception as e:
            console.error(f"Workflow command failed: {e}")

    def _list_workflows(self, *args: str) -> None:
        """List all workflows."""
        state = args[0] if args else "all"
        console.info(f"Listing {state} workflows...")

        cmd = ["workflow", "list"]
        if state != "all":
            cmd.extend(["--state", state])

        result = self._run_gh(cmd)

        if result.stdout:
            console.rule("Workflows")
            console.muted(result.stdout)
        else:
            console.info("No workflows found")

    def _run_workflow(self, *args: str) -> None:
        """Run a workflow manually."""
        if len(args) < 1:
            console.error("Usage: github_workflow run <workflow_file> [inputs]")
            return

        workflow_file = args[0]
        inputs = args[1:]

        console.info(f"Running workflow: {workflow_file}")

        cmd = ["workflow", "run", workflow_file]
        for i in range(0, len(inputs), 2):
            if i + 1 < len(inputs):
                cmd.extend(["-f", f"{inputs[i]}={inputs[i + 1]}"])

        result = self._run_gh(cmd)

        if result.returncode == 0:
            console.success("Workflow triggered")
            console.muted(result.stdout)
        else:
            console.error(f"Failed to trigger workflow: {result.stderr}")

    def _workflow_logs(self, *args: str) -> None:
        """Show workflow logs."""
        if not args:
            console.error("Usage: github_workflow logs <run_id>")
            return

        run_id = args[0]
        console.info(f"Fetching logs for run {run_id}...")

        result = self._run_gh(["run", "view", run_id, "--log"])

        if result.stdout:
            console.rule(f"Logs for run {run_id}")
            console.muted(result.stdout)
        else:
            console.info("No logs found")

    def _view_workflow(self, *args: str) -> None:
        """View workflow details."""
        if not args:
            console.error("Usage: github_workflow view <workflow_file>")
            return

        workflow_file = args[0]
        console.info(f"Viewing workflow: {workflow_file}")

        result = self._run_gh(["workflow", "view", workflow_file])

        if result.stdout:
            console.muted(result.stdout)
        else:
            console.info("Workflow not found")

    def _disable_workflow(self, *args: str) -> None:
        """Disable a workflow."""
        if not args:
            console.error("Usage: github_workflow disable <workflow_file>")
            return

        workflow_file = args[0]
        console.warning(f"Disabling workflow: {workflow_file}")

        result = self._run_gh(["workflow", "disable", workflow_file])

        if result.returncode == 0:
            console.success(f"Workflow {workflow_file} disabled")
        else:
            console.error(f"Failed to disable: {result.stderr}")

    def _enable_workflow(self, *args: str) -> None:
        """Enable a workflow."""
        if not args:
            console.error("Usage: github_workflow enable <workflow_file>")
            return

        workflow_file = args[0]
        console.info(f"Enabling workflow: {workflow_file}")

        result = self._run_gh(["workflow", "enable", workflow_file])

        if result.returncode == 0:
            console.success(f"Workflow {workflow_file} enabled")
        else:
            console.error(f"Failed to enable: {result.stderr}")

    def _workflow_status(self, *args: str) -> None:
        """Show workflow status."""
        run_id = args[0] if args else None

        if run_id:
            result = self._run_gh(["run", "view", run_id])
        else:
            result = self._run_gh(["run", "list", "--limit", "10"])

        if result.stdout:
            console.rule("Workflow Status")
            console.muted(result.stdout)
        else:
            console.info("No workflow runs found")

    def _rerun_workflow(self, *args: str) -> None:
        """Rerun a failed workflow."""
        if not args:
            console.error("Usage: github_workflow rerun <run_id>")
            return

        run_id = args[0]
        console.info(f"Rerunning workflow: {run_id}")

        result = self._run_gh(["run", "rerun", run_id])

        if result.returncode == 0:
            console.success("Workflow rerun triggered")
        else:
            console.error(f"Failed to rerun: {result.stderr}")

    def _cancel_workflow(self, *args: str) -> None:
        """Cancel a running workflow."""
        if not args:
            console.error("Usage: github_workflow cancel <run_id>")
            return

        run_id = args[0]
        console.warning(f"Cancelling workflow: {run_id}")

        result = self._run_gh(["run", "cancel", run_id])

        if result.returncode == 0:
            console.success(f"Workflow {run_id} cancelled")
        else:
            console.error(f"Failed to cancel: {result.stderr}")

    def _show_help(self) -> None:
        rows = [
            ["list [state]", "List workflows (all/active/inactive/completed/failed)"],
            ["run <file> [inputs]", "Manually run workflow"],
            ["logs <run_id>", "Show workflow logs"],
            ["view <file>", "View workflow YAML"],
            ["disable <file>", "Disable workflow"],
            ["enable <file>", "Enable workflow"],
            ["status [run_id]", "Show workflow/run status"],
            ["rerun <run_id>", "Rerun failed workflow"],
            ["cancel <run_id>", "Cancel running workflow"],
        ]
        console.table("Workflow Commands", ["Command", "Description"], rows)


# ============================================================================
# GitHub Releases
# ============================================================================


class GitHubReleasePlugin(GitHubBase):
    """GitHub release management."""

    @property
    def name(self) -> str:
        return "github_release"

    @property
    def description(self) -> str:
        return (
            "GitHub release management (create, list, view, delete, upload, download)"
        )

    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Handle release commands."""
        if not self._check_gh_installed():
            console.error(
                "GitHub CLI (gh) is not installed. Install from https://cli.github.com/"
            )
            return None

        if not self._check_auth():
            console.error("Not authenticated with GitHub. Run: gh auth login")
            return None

        if not args:
            self._show_help()
            return

        command = args[0].lower()
        sub_args = args[1:]

        try:
            if command == "create":
                self._create_release(*sub_args)
            elif command == "list":
                self._list_releases(*sub_args)
            elif command == "view":
                self._view_release(*sub_args)
            elif command == "delete":
                self._delete_release(*sub_args)
            elif command == "upload":
                self._upload_asset(*sub_args)
            elif command == "download":
                self._download_asset(*sub_args)
            elif command == "edit":
                self._edit_release(*sub_args)
            else:
                console.error(f"Unknown release command: {command}")
                self._show_help()
        except Exception as e:
            console.error(f"Release command failed: {e}")

    def _create_release(self, *args: str) -> None:
        """Create a new release."""
        if len(args) < 2:
            console.error(
                "Usage: github_release create <tag> <title> [notes] [--draft] [--prerelease]"
            )
            return

        tag = args[0]
        title = args[1]
        notes = " ".join([a for a in args[2:] if not a.startswith("--")])

        is_draft = "--draft" in args or "-d" in args
        is_prerelease = "--prerelease" in args or "-p" in args

        console.info(f"Creating release: {title} (tag: {tag})")

        cmd = ["release", "create", tag, "--title", title]
        if notes:
            cmd.extend(["--notes", notes])
        if is_draft:
            cmd.append("--draft")
        if is_prerelease:
            cmd.append("--prerelease")

        result = self._run_gh(cmd)

        if result.returncode == 0:
            console.success("Release created")
            console.muted(result.stdout)
        else:
            console.error(f"Failed to create release: {result.stderr}")

    def _list_releases(self, *args: str) -> None:
        """List all releases."""
        limit = args[0] if args and args[0].isdigit() else "20"

        console.info(f"Listing last {limit} releases...")

        result = self._run_gh(["release", "list", "--limit", limit])

        if result.stdout:
            console.rule("Releases")
            console.muted(result.stdout)
        else:
            console.info("No releases found")

    def _view_release(self, *args: str) -> None:
        """View release details."""
        if not args:
            console.error("Usage: github_release view <tag>")
            return

        tag = args[0]
        console.info(f"Viewing release: {tag}")

        result = self._run_gh(["release", "view", tag])

        if result.stdout:
            console.muted(result.stdout)
        else:
            console.info(f"Release {tag} not found")

    def _delete_release(self, *args: str) -> None:
        """Delete a release."""
        if not args:
            console.error("Usage: github_release delete <tag>")
            return

        tag = args[0]
        console.warning(f"Deleting release: {tag}")

        confirmation = input(
            f"Are you sure you want to delete release {tag}? (yes/no): "
        )
        if confirmation.lower() != "yes":
            console.info("Operation cancelled")
            return

        result = self._run_gh(["release", "delete", tag])

        if result.returncode == 0:
            console.success(f"Release {tag} deleted")
        else:
            console.error(f"Failed to delete: {result.stderr}")

    def _upload_asset(self, *args: str) -> None:
        """Upload asset to release."""
        if len(args) < 2:
            console.error("Usage: github_release upload <tag> <file>")
            return

        tag = args[0]
        file_path = args[1]

        console.info(f"Uploading {file_path} to release {tag}...")

        result = self._run_gh(["release", "upload", tag, file_path])

        if result.returncode == 0:
            console.success("Asset uploaded")
        else:
            console.error(f"Upload failed: {result.stderr}")

    def _download_asset(self, *args: str) -> None:
        """Download asset from release."""
        if len(args) < 2:
            console.error("Usage: github_release download <tag> <pattern>")
            return

        tag = args[0]
        pattern = args[1]

        console.info(f"Downloading {pattern} from release {tag}...")

        result = self._run_gh(["release", "download", tag, "--pattern", pattern])

        if result.returncode == 0:
            console.success("Asset downloaded")
            console.muted(result.stdout)
        else:
            console.error(f"Download failed: {result.stderr}")

    def _edit_release(self, *args: str) -> None:
        """Edit release."""
        if len(args) < 2:
            console.error("Usage: github_release edit <tag> <title> [notes]")
            return

        tag = args[0]
        title = args[1]
        notes = " ".join(args[2:])

        console.info(f"Editing release: {tag}")

        cmd = ["release", "edit", tag, "--title", title]
        if notes:
            cmd.extend(["--notes", notes])

        result = self._run_gh(cmd)

        if result.returncode == 0:
            console.success("Release updated")
        else:
            console.error(f"Failed to edit: {result.stderr}")

    def _show_help(self) -> None:
        rows = [
            ["create <tag> <title> [notes]", "Create new release"],
            ["list [limit]", "List releases"],
            ["view <tag>", "View release details"],
            ["delete <tag>", "Delete release"],
            ["upload <tag> <file>", "Upload asset"],
            ["download <tag> <pattern>", "Download asset"],
            ["edit <tag> <title> [notes]", "Edit release"],
        ]
        console.table("Release Commands", ["Command", "Description"], rows)


# ============================================================================
# GitHub Repository
# ============================================================================


class GitHubRepoPlugin(GitHubBase):
    """GitHub repository management."""

    @property
    def name(self) -> str:
        return "github_repo"

    @property
    def description(self) -> str:
        return "GitHub repository management (view, create, clone, fork, star, watch)"

    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Handle repo commands."""
        if not self._check_gh_installed():
            console.error(
                "GitHub CLI (gh) is not installed. Install from https://cli.github.com/"
            )
            return None

        if not self._check_auth():
            console.error("Not authenticated with GitHub. Run: gh auth login")
            return None

        if not args:
            self._show_help()
            return

        command = args[0].lower()
        sub_args = args[1:]

        try:
            if command == "view":
                self._view_repo(*sub_args)
            elif command == "create":
                self._create_repo(*sub_args)
            elif command == "clone":
                self._clone_repo(*sub_args)
            elif command == "fork":
                self._fork_repo(*sub_args)
            elif command == "star":
                self._star_repo(*sub_args)
            elif command == "unstar":
                self._unstar_repo(*sub_args)
            elif command == "watch":
                self._watch_repo(*sub_args)
            elif command == "visibility":
                self._set_visibility(*sub_args)
            elif command == "archive":
                self._archive_repo(*sub_args)
            elif command == "delete":
                self._delete_repo(*sub_args)
            elif command == "topics":
                self._manage_topics(*sub_args)
            else:
                console.error(f"Unknown repo command: {command}")
                self._show_help()
        except Exception as e:
            console.error(f"Repo command failed: {e}")

    def _view_repo(self, *args: str) -> None:
        """View repository information."""
        repo = args[0] if args else ""

        cmd = ["repo", "view"]
        if repo:
            cmd.append(repo)

        result = self._run_gh(cmd)

        if result.stdout:
            console.rule("Repository Information")
            console.muted(result.stdout)
        else:
            console.info("Repository not found")

    def _create_repo(self, *args: str) -> None:
        """Create a new repository."""
        name = args[0] if args else None

        if not name:
            console.error(
                "Usage: github_repo create <name> [--public] [--private] [--description <desc>]"
            )
            return

        is_public = "--public" in args
        is_private = "--private" in args
        description = ""
        for i, arg in enumerate(args):
            if arg == "--description" and i + 1 < len(args):
                description = args[i + 1]

        visibility = "public" if is_public else "private"

        console.info(f"Creating {visibility} repository: {name}")

        cmd = ["repo", "create", name, f"--{visibility}"]
        if description:
            cmd.extend(["--description", description])

        result = self._run_gh(cmd)

        if result.returncode == 0:
            console.success("Repository created")
            console.muted(result.stdout)
        else:
            console.error(f"Failed to create: {result.stderr}")

    def _clone_repo(self, *args: str) -> None:
        """Clone a repository."""
        if not args:
            console.error("Usage: github_repo clone <repo>")
            return

        repo = args[0]
        console.info(f"Cloning repository: {repo}")

        result = self._run_gh(["repo", "clone", repo])

        if result.returncode == 0:
            console.success("Repository cloned")
        else:
            console.error(f"Failed to clone: {result.stderr}")

    def _fork_repo(self, *args: str) -> None:
        """Fork a repository."""
        repo = args[0] if args else None

        cmd = ["repo", "fork"]
        if repo:
            cmd.append(repo)

        console.info("Forking repository...")

        result = self._run_gh(cmd)

        if result.returncode == 0:
            console.success("Repository forked")
            console.muted(result.stdout)
        else:
            console.error(f"Failed to fork: {result.stderr}")

    def _star_repo(self, *args: str) -> None:
        """Star a repository."""
        repo = args[0] if args else None

        cmd = ["api", "--method", "PUT", "/user/starred/"]
        if repo:
            cmd.append(repo.replace("https://github.com/", ""))
        else:
            result = self._run_git(["remote", "get-url", "origin"])
            repo = (
                result.stdout.strip()
                .replace(".git", "")
                .replace("https://github.com/", "")
            )
            cmd.append(repo)

        result = self._run_gh(cmd)

        if result.returncode == 0:
            console.success("Repository starred")
        else:
            console.error(f"Failed to star: {result.stderr}")

    def _unstar_repo(self, *args: str) -> None:
        """Unstar a repository."""
        repo = args[0] if args else None

        if not repo:
            result = self._run_git(["remote", "get-url", "origin"])
            repo = (
                result.stdout.strip()
                .replace(".git", "")
                .replace("https://github.com/", "")
            )

        console.warning(f"Unstarring: {repo}")
        result = self._run_gh(["api", "--method", "DELETE", f"/user/starred/{repo}"])

        if result.returncode == 0:
            console.success("Repository unstarred")

    def _watch_repo(self, *args: str) -> None:
        """Watch a repository."""
        repo = args[0] if args else None

        if not repo:
            result = self._run_git(["remote", "get-url", "origin"])
            repo = (
                result.stdout.strip()
                .replace(".git", "")
                .replace("https://github.com/", "")
            )

        console.info(f"Watching: {repo}")
        result = self._run_gh(["api", "--method", "PUT", f"/repos/{repo}/subscription"])

        if result.returncode == 0:
            console.success("Repository watched")

    def _set_visibility(self, *args: str) -> None:
        """Set repository visibility."""
        if len(args) < 2:
            console.error("Usage: github_repo visibility <public|private> <repo>")
            return

        visibility = args[0]
        repo = args[1]

        console.info(f"Setting {repo} to {visibility}...")

        result = self._run_gh(
            [
                "api",
                "--method",
                "PATCH",
                f"/repos/{repo}",
                "-f",
                f'{{"visibility": "{visibility}"}}',
            ]
        )

        if result.returncode == 0:
            console.success(f"Repository set to {visibility}")
        else:
            console.error(f"Failed to set visibility: {result.stderr}")

    def _archive_repo(self, *args: str) -> None:
        """Archive a repository."""
        repo = args[0] if args else None

        if not repo:
            console.error("Usage: github_repo archive <repo>")
            return

        console.warning(f"Archiving repository: {repo}")

        result = self._run_gh(
            ["api", "--method", "PATCH", f"/repos/{repo}", "-f", '{"archived": true}']
        )

        if result.returncode == 0:
            console.success("Repository archived")
        else:
            console.error(f"Failed to archive: {result.stderr}")

    def _delete_repo(self, *args: str) -> None:
        """Delete a repository."""
        repo = args[0] if args else None

        if not repo:
            console.error("Usage: github_repo delete <repo>")
            return

        console.warning(f"[!] DELETING repository: {repo}")
        confirmation = input("This action cannot be undone. Type 'DELETE' to confirm: ")

        if confirmation != "DELETE":
            console.info("Operation cancelled")
            return

        result = self._run_gh(["api", "--method", "DELETE", f"/repos/{repo}"])

        if result.returncode == 0:
            console.success("Repository deleted")
        else:
            console.error(f"Failed to delete: {result.stderr}")

    def _manage_topics(self, *args: str) -> None:
        """Manage repository topics."""
        action = args[0] if args else "list"
        repo = args[1] if len(args) > 1 else None

        if not repo:
            result = self._run_git(["remote", "get-url", "origin"])
            repo = (
                result.stdout.strip()
                .replace(".git", "")
                .replace("https://github.com/", "")
            )

        if action == "list":
            result = self._run_gh(
                ["repo", "view", repo, "--json", "topics", "--jq", ".topics"]
            )

            if result.stdout:
                topics = json.loads(result.stdout)
                console.rule(f"Topics for {repo}")
                console.muted(", ".join(topics))
            else:
                console.info("No topics found")

        elif action == "add":
            if len(args) < 3:
                console.error("Usage: github_repo topics add <topic> [repo]")
                return

            topic = args[2]
            result = self._run_gh(
                ["api", "--method", "PUT", f"/repos/{repo}/topics/{topic}"]
            )

            if result.returncode == 0:
                console.success(f"Topic '{topic}' added")

        elif action == "remove":
            if len(args) < 3:
                console.error("Usage: github_repo topics remove <topic> [repo]")
                return

            topic = args[2]
            result = self._run_gh(
                ["api", "--method", "DELETE", f"/repos/{repo}/topics/{topic}"]
            )

            if result.returncode == 0:
                console.success(f"Topic '{topic}' removed")

    def _show_help(self) -> None:
        rows = [
            ["view [repo]", "View repository information"],
            ["create <name> [--public|private]", "Create new repository"],
            ["clone <repo>", "Clone repository"],
            ["fork [repo]", "Fork repository"],
            ["star [repo]", "Star repository"],
            ["unstar [repo]", "Unstar repository"],
            ["watch [repo]", "Watch repository"],
            ["visibility <public|private> <repo>", "Set visibility"],
            ["archive <repo>", "Archive repository"],
            ["delete <repo>", "Delete repository"],
            ["topics <list|add|remove> [repo]", "Manage topics"],
        ]
        console.table("Repository Commands", ["Command", "Description"], rows)


# ============================================================================
# GitHub Issues & PRs
# ============================================================================


class GitHubIssuesPlugin(GitHubBase):
    """GitHub issues and PRs management."""

    @property
    def name(self) -> str:
        return "github_issues"

    @property
    def description(self) -> str:
        return "GitHub issues and PRs management (list, create, close, comment, lock, assign)"

    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Handle issues commands."""
        if not self._check_gh_installed():
            console.error(
                "GitHub CLI (gh) is not installed. Install from https://cli.github.com/"
            )
            return None

        if not self._check_auth():
            console.error("Not authenticated with GitHub. Run: gh auth login")
            return None

        if not args:
            self._show_help()
            return

        command = args[0].lower()
        sub_args = args[1:]

        try:
            if command == "list":
                self._list_issues(*sub_args)
            elif command == "view":
                self._view_issue(*sub_args)
            elif command == "create":
                self._create_issue(*sub_args)
            elif command == "close":
                self._close_issue(*sub_args)
            elif command == "comment":
                self._comment_issue(*sub_args)
            elif command == "lock":
                self._lock_issue(*sub_args)
            elif command == "unlock":
                self._unlock_issue(*sub_args)
            elif command == "assign":
                self._assign_issue(*sub_args)
            elif command == "label":
                self._label_issue(*sub_args)
            elif command == "milestone":
                self._milestone_issue(*sub_args)
            else:
                console.error(f"Unknown issue command: {command}")
                self._show_help()
        except Exception as e:
            console.error(f"Issue command failed: {e}")

    def _list_issues(self, *args: str) -> None:
        """List issues."""
        state = args[0] if args else "open"
        limit = args[1] if len(args) > 1 and args[1].isdigit() else "20"
        is_pr = "--pr" in args

        console.info(f"Listing {state} {'PRs' if is_pr else 'issues'}...")

        cmd = ["issue", "list", "--state", state, "--limit", limit]
        if is_pr:
            cmd.append("--pr")

        result = self._run_gh(cmd)

        if result.stdout:
            console.rule(f"{state.capitalize()} {'PRs' if is_pr else 'Issues'}")
            console.muted(result.stdout)
        else:
            console.info(f"No {state} {'PRs' if is_pr else 'issues'} found")

    def _view_issue(self, *args: str) -> None:
        """View issue details."""
        if not args:
            console.error("Usage: github_issues view <number>")
            return

        number = args[0]
        console.info(f"Viewing issue #{number}")

        result = self._run_gh(["issue", "view", number])

        if result.stdout:
            console.muted(result.stdout)
        else:
            console.info(f"Issue #{number} not found")

    def _create_issue(self, *args: str) -> None:
        """Create an issue."""
        if not args:
            console.error(
                "Usage: github_issues create <title> [body] [--assignee <user>] [--label <label>]"
            )
            return

        title = args[0]
        body = ""
        assignee = None
        labels = []

        for i, arg in enumerate(args[1:]):
            if arg == "--body" and i + 1 < len(args[1:]):
                body = args[1:][i + 1]
            elif arg == "--assignee" and i + 1 < len(args[1:]):
                assignee = args[1:][i + 1]
            elif arg == "--label" and i + 1 < len(args[1:]):
                labels.append(args[1:][i + 1])

        console.info(f"Creating issue: {title}")

        cmd = ["issue", "create", "--title", title]
        if body:
            cmd.extend(["--body", body])
        if assignee:
            cmd.extend(["--assignee", assignee])
        if labels:
            cmd.extend(["--label", ",".join(labels)])

        result = self._run_gh(cmd)

        if result.returncode == 0:
            console.success("Issue created")
            console.muted(result.stdout)
        else:
            console.error(f"Failed to create: {result.stderr}")

    def _close_issue(self, *args: str) -> None:
        """Close an issue."""
        if not args:
            console.error("Usage: github_issues close <number>")
            return

        number = args[0]
        console.warning(f"Closing issue #{number}")

        result = self._run_gh(["issue", "close", number])

        if result.returncode == 0:
            console.success(f"Issue #{number} closed")
        else:
            console.error(f"Failed to close: {result.stderr}")

    def _comment_issue(self, *args: str) -> None:
        """Comment on an issue."""
        if len(args) < 2:
            console.error("Usage: github_issues comment <number> <comment>")
            return

        number = args[0]
        comment = " ".join(args[1:])

        console.info(f"Commenting on issue #{number}...")

        result = self._run_gh(["issue", "comment", number, "--body", comment])

        if result.returncode == 0:
            console.success("Comment added")
        else:
            console.error(f"Failed to comment: {result.stderr}")

    def _lock_issue(self, *args: str) -> None:
        """Lock an issue."""
        if not args:
            console.error("Usage: github_issues lock <number> [reason]")
            return

        number = args[0]
        reason = args[1] if len(args) > 1 else ""

        console.warning(f"Locking issue #{number}...")

        cmd = ["issue", "lock", number]
        if reason:
            cmd.extend(["--reason", reason])

        result = self._run_gh(cmd)

        if result.returncode == 0:
            console.success(f"Issue #{number} locked")
        else:
            console.error(f"Failed to lock: {result.stderr}")

    def _unlock_issue(self, *args: str) -> None:
        """Unlock an issue."""
        if not args:
            console.error("Usage: github_issues unlock <number>")
            return

        number = args[0]
        console.info(f"Unlocking issue #{number}...")

        result = self._run_gh(["issue", "unlock", number])

        if result.returncode == 0:
            console.success(f"Issue #{number} unlocked")
        else:
            console.error(f"Failed to unlock: {result.stderr}")

    def _assign_issue(self, *args: str) -> None:
        """Assign an issue."""
        if len(args) < 2:
            console.error("Usage: github_issues assign <number> <user>")
            return

        number = args[0]
        user = args[1]

        console.info(f"Assigning issue #{number} to {user}...")

        result = self._run_gh(["issue", "edit", number, "--add-assignee", user])

        if result.returncode == 0:
            console.success(f"Issue #{number} assigned to {user}")
        else:
            console.error(f"Failed to assign: {result.stderr}")

    def _label_issue(self, *args: str) -> None:
        """Add/Remove labels from an issue."""
        if len(args) < 2:
            console.error("Usage: github_issues label <add|remove> <number> <label>")
            return

        action = args[0]
        number = args[1]
        label = args[2]

        if action == "add":
            result = self._run_gh(["issue", "edit", number, "--add-label", label])
            console.success(f"Label '{label}' added to issue #{number}")
        elif action == "remove":
            result = self._run_gh(["issue", "edit", number, "--remove-label", label])
            console.success(f"Label '{label}' removed from issue #{number}")
        else:
            console.error("Unknown action. Use: add or remove")

    def _milestone_issue(self, *args: str) -> None:
        """Set milestone for an issue."""
        if len(args) < 2:
            console.error("Usage: github_issues milestone <number> <milestone>")
            return

        number = args[0]
        milestone = args[1]

        console.info(f"Setting milestone '{milestone}' for issue #{number}...")

        result = self._run_gh(["issue", "edit", number, "--milestone", milestone])

        if result.returncode == 0:
            console.success(f"Milestone set for issue #{number}")
        else:
            console.error(f"Failed to set milestone: {result.stderr}")

    def _show_help(self) -> None:
        rows = [
            ["list [state] [limit] [--pr]", "List issues/PRs"],
            ["view <number>", "View issue details"],
            ["create <title> [body]", "Create issue"],
            ["close <number>", "Close issue"],
            ["comment <number> <text>", "Add comment"],
            ["lock <number> [reason]", "Lock issue"],
            ["unlock <number>", "Unlock issue"],
            ["assign <number> <user>", "Assign issue"],
            ["label <add|remove> <number> <label>", "Manage labels"],
            ["milestone <number> <title>", "Set milestone"],
        ]
        console.table("Issue Commands", ["Command", "Description"], rows)
