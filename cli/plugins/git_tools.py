"""
Git Tools Plugin.

Provides comprehensive Git integration with status, log, diff, add, commit,
branch, checkout, stash, pull, and push commands.
"""

import subprocess
from typing import Any, List, Dict, Optional
from pathlib import Path

from cli.plugins import PluginBase
from cli.utils.ui import console
from cli.utils.errors import handle_errors, ValidationError
from cli.core.security import security, SecurityError


class GitBasePlugin(PluginBase):
    """Base class for all Git plugins with common functionality."""

    _is_base = True  # Flag to skip registration

    def _run_git(self, args: List[str]) -> subprocess.CompletedProcess:
        """
        Run a git command and return the result.

        Args:
            args: Git command arguments (without 'git').

        Returns:
            CompletedProcess with stdout, stderr, and returncode.

        Raises:
            SecurityError: If command is blocked by security policy.
        """
        cmd = ["git"] + args

        try:
            security.guard.check_command(" ".join(cmd))
        except SecurityError:
            raise SecurityError(
                f"Git command '{args[0]}' is blocked by security policy"
            )

        return subprocess.run(cmd, capture_output=True, text=True)

    def _check_git_repo(self) -> bool:
        """Check if current directory is a Git repository."""
        result = self._run_git(["rev-parse", "--git-dir"])
        return result.returncode == 0


class GitStatusPlugin(GitBasePlugin):
    """Display Git repository status with remote tracking."""

    @property
    def name(self) -> str:
        return "git_status"

    @property
    def description(self) -> str:
        return "Show Git branch, changes, and remote status"

    @handle_errors()
    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Run git status and display formatted output."""
        if not self._check_git_repo():
            console.error("Not a Git repository or Git not installed.")
            return None

        branch_result = self._run_git(["rev-parse", "--abbrev-ref", "HEAD"])
        if branch_result.returncode != 0:
            console.error("Failed to get current branch.")
            return None

        branch = branch_result.stdout.strip()

        status_result = self._run_git(["status", "--porcelain"])
        files = self._parse_status(status_result.stdout)

        remote_info = self._get_remote_info(branch)

        console.rule(f"Git Status: {branch}")

        if remote_info:
            if remote_info["ahead"]:
                console.warning(f"Ahead of remote by {remote_info['ahead']} commit(s)")
            if remote_info["behind"]:
                console.warning(f"Behind remote by {remote_info['behind']} commit(s)")

        if not files:
            console.success("Working tree clean.")
            return {"branch": branch, "files": [], "remote": remote_info}

        rows = [[f["status"], f["file"]] for f in files]
        console.table("Changes", ["Status", "File"], rows)

        return {"branch": branch, "files": files, "remote": remote_info}

    def _parse_status(self, output: str) -> List[dict]:
        """Parse git status porcelain output."""
        files = []
        status_map = {
            "M": "Modified",
            "A": "Added",
            "D": "Deleted",
            "R": "Renamed",
            "C": "Copied",
            "U": "Unmerged",
            "?": "Untracked",
        }

        for line in output.strip().split("\n"):
            if not line:
                continue
            status_code = line[0:2].strip()
            filename = line[3:]
            status = status_map.get(status_code[0], status_code)
            files.append({"status": status, "file": filename})

        return files

    def _get_remote_info(self, branch: str) -> Dict[str, int]:
        """Get ahead/behind info for current branch."""
        result = self._run_git(
            ["rev-list", "--count", "--left-right", f"@{{u}}...HEAD"]
        )
        if result.returncode != 0:
            return {}

        parts = result.stdout.strip().split()
        if len(parts) == 2:
            behind, ahead = map(int, parts)
            info = {}
            if ahead > 0:
                info["ahead"] = ahead
            if behind > 0:
                info["behind"] = behind
            return info

        return {}


class GitLogPlugin(GitBasePlugin):
    """Display recent Git commits with configurable count."""

    @property
    def name(self) -> str:
        return "git_log"

    @property
    def description(self) -> str:
        return "Show recent Git commits (git_log [n])"

    @handle_errors()
    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Run git log and display formatted output."""
        if not self._check_git_repo():
            console.error("Not a Git repository.")
            return None

        count = 5
        if args and args[0].isdigit():
            count = int(args[0])

        result = self._run_git(
            ["log", f"-{count}", "--pretty=format:%h|%an|%ad|%s", "--date=short"]
        )

        if result.returncode != 0:
            console.error("Failed to get Git log.")
            return None

        commits = self._parse_log(result.stdout)

        if not commits:
            console.warning("No commits found.")
            return []

        console.rule(f"Recent {len(commits)} Commits")
        rows = [[c["hash"], c["author"], c["date"], c["message"][:40]] for c in commits]
        console.table("Git Log", ["Hash", "Author", "Date", "Message"], rows)

        return commits

    def _parse_log(self, output: str) -> List[dict]:
        """Parse git log output."""
        commits = []
        for line in output.strip().split("\n"):
            if not line:
                continue
            parts = line.split("|", 3)
            if len(parts) == 4:
                commits.append(
                    {
                        "hash": parts[0],
                        "author": parts[1],
                        "date": parts[2],
                        "message": parts[3],
                    }
                )
        return commits


class GitAddPlugin(GitBasePlugin):
    """Stage files for commit."""

    @property
    def name(self) -> str:
        return "git_add"

    @property
    def description(self) -> str:
        return "Stage files (git_add <file|all>)"

    @handle_errors()
    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Add files to staging area."""
        if not self._check_git_repo():
            console.error("Not a Git repository.")
            return None

        if not args:
            console.error("Usage: git_add <file|all>")
            return None

        target = args[0]

        if target == "all":
            result = self._run_git(["add", "."])
            console.success("Staged all changes")
        else:
            result = self._run_git(["add", target])
            console.success(f"Staged: {target}")

        if result.returncode != 0:
            console.error(f"Failed to add: {result.stderr.strip()}")
            return False

        return True


class GitCommitPlugin(GitBasePlugin):
    """Create a commit with a message."""

    @property
    def name(self) -> str:
        return "git_commit"

    @property
    def description(self) -> str:
        return "Create commit (git_commit <message>)"

    @handle_errors()
    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Create a new commit."""
        if not self._check_git_repo():
            console.error("Not a Git repository.")
            return None

        if not args:
            console.error("Usage: git_commit <message>")
            return None

        message = " ".join(args)

        if len(message) < 3:
            raise ValidationError("Commit message too short (min 3 chars)")

        result = self._run_git(["commit", "-m", message])

        if result.returncode != 0:
            console.error(f"Failed to commit: {result.stderr.strip()}")
            return False

        console.success(f"Committed: {message[:50]}...")
        return True


class GitDiffPlugin(GitBasePlugin):
    """Show changes between commits, working tree, etc."""

    @property
    def name(self) -> str:
        return "git_diff"

    @property
    def description(self) -> str:
        return "Show diff (git_diff [file])"

    @handle_errors()
    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Show unstaged changes."""
        if not self._check_git_repo():
            console.error("Not a Git repository.")
            return None

        git_args = ["diff"]

        if args:
            git_args.append(args[0])

        result = self._run_git(git_args)

        if not result.stdout.strip():
            console.info("No unstaged changes.")
            return None

        console.rule("Unstaged Changes")
        console.muted(result.stdout)
        return result.stdout


class GitDiffStagedPlugin(GitBasePlugin):
    """Show staged changes."""

    @property
    def name(self) -> str:
        return "git_diff_staged"

    @property
    def description(self) -> str:
        return "Show staged changes"

    @handle_errors()
    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Show staged changes."""
        if not self._check_git_repo():
            console.error("Not a Git repository.")
            return None

        result = self._run_git(["diff", "--staged"])

        if not result.stdout.strip():
            console.info("No staged changes.")
            return None

        console.rule("Staged Changes")
        console.muted(result.stdout)
        return result.stdout


class GitBranchPlugin(GitBasePlugin):
    """List, create, or delete branches."""

    @property
    def name(self) -> str:
        return "git_branch"

    @property
    def description(self) -> str:
        return "List/create branches (git_branch [new_name])"

    @handle_errors()
    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Handle branch operations."""
        if not self._check_git_repo():
            console.error("Not a Git repository.")
            return None

        if not args:
            return self._list_branches()

        action = args[0]

        if action == "-d" and len(args) > 1:
            return self._delete_branch(args[1])
        else:
            return self._create_branch(action)

    def _list_branches(self) -> List[dict]:
        """List all branches."""
        result = self._run_git(["branch", "-v"])

        if result.returncode != 0:
            console.error("Failed to list branches.")
            return []

        branches = []
        current_marker = "* "

        for line in result.stdout.strip().split("\n"):
            if line.startswith(current_marker):
                name = line[len(current_marker) :].split()[0]
                is_current = True
            else:
                name = line.strip().split()[0]
                is_current = False

            branches.append({"name": name, "current": is_current})

        console.rule("Branches")
        rows = [["*" if b["current"] else "", b["name"]] for b in branches]
        console.table("Branches", ["Current", "Name"], rows)

        return branches

    def _create_branch(self, name: str) -> bool:
        """Create a new branch."""
        result = self._run_git(["branch", name])

        if result.returncode != 0:
            console.error(f"Failed to create branch: {result.stderr.strip()}")
            return False

        console.success(f"Created branch: {name}")
        console.muted("Use 'git_checkout <name>' to switch to it")
        return True

    def _delete_branch(self, name: str) -> bool:
        """Delete a branch."""
        result = self._run_git(["branch", "-d", name])

        if result.returncode != 0:
            console.error(f"Failed to delete branch: {result.stderr.strip()}")
            return False

        console.success(f"Deleted branch: {name}")
        return True


class GitCheckoutPlugin(GitBasePlugin):
    """Switch branches or restore files."""

    @property
    def name(self) -> str:
        return "git_checkout"

    @property
    def description(self) -> str:
        return "Switch branch (git_checkout <branch>)"

    @handle_errors()
    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Checkout a branch."""
        if not self._check_git_repo():
            console.error("Not a Git repository.")
            return None

        if not args:
            console.error("Usage: git_checkout <branch>")
            return None

        branch = args[0]

        result = self._run_git(["checkout", branch])

        if result.returncode != 0:
            console.error(f"Failed to checkout: {result.stderr.strip()}")
            return False

        console.success(f"Switched to branch: {branch}")
        return True


class GitStashPlugin(GitBasePlugin):
    """Stash changes temporarily."""

    @property
    def name(self) -> str:
        return "git_stash"

    @property
    def description(self) -> str:
        return "Stash operations (git_stash [save|pop|list])"

    @handle_errors()
    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Handle stash operations."""
        if not self._check_git_repo():
            console.error("Not a Git repository.")
            return None

        action = args[0] if args else "list"

        if action == "save" or action == "push":
            message = " ".join(args[1:]) if len(args) > 1 else "WIP"
            return self._stash_save(message)
        elif action == "pop":
            return self._stash_pop()
        elif action == "list":
            return self._stash_list()
        else:
            console.error("Usage: git_stash [save|pop|list]")
            return None

    def _stash_save(self, message: str) -> bool:
        """Save current changes to stash."""
        result = self._run_git(["stash", "push", "-m", message])

        if result.returncode != 0:
            console.error(f"Failed to stash: {result.stderr.strip()}")
            return False

        console.success(f"Stashed: {message}")
        return True

    def _stash_pop(self) -> bool:
        """Pop the most recent stash."""
        result = self._run_git(["stash", "pop"])

        if result.returncode != 0:
            console.error(f"Failed to pop stash: {result.stderr.strip()}")
            return False

        console.success("Stash popped")
        return True

    def _stash_list(self) -> List[str]:
        """List all stashes."""
        result = self._run_git(["stash", "list"])

        if result.returncode != 0:
            console.error("Failed to list stashes.")
            return []

        stashes = result.stdout.strip().split("\n") if result.stdout.strip() else []

        if not stashes:
            console.info("No stashes found.")
            return []

        console.rule("Stashes")
        rows = [[s[:60]] for s in stashes]
        console.table("Stash List", ["Entry"], rows)

        return stashes


class GitPullPlugin(GitBasePlugin):
    """Pull changes from remote."""

    @property
    def name(self) -> str:
        return "git_pull"

    @property
    def description(self) -> str:
        return "Pull changes from remote"

    @handle_errors()
    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Pull changes from remote repository."""
        if not self._check_git_repo():
            console.error("Not a Git repository.")
            return None

        console.info("Pulling changes from remote...")

        result = self._run_git(["pull"])

        if result.returncode != 0:
            console.error(f"Pull failed: {result.stderr.strip()}")
            return False

        console.success("Pull completed")
        if result.stdout.strip():
            console.muted(result.stdout)

        return True


class GitPushPlugin(GitBasePlugin):
    """Push changes to remote."""

    @property
    def name(self) -> str:
        return "git_push"

    @property
    def description(self) -> str:
        return "Push changes to remote"

    @handle_errors()
    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Push changes to remote repository."""
        if not self._check_git_repo():
            console.error("Not a Git repository.")
            return None

        console.info("Pushing changes to remote...")

        result = self._run_git(["push"])

        if result.returncode != 0:
            console.error(f"Push failed: {result.stderr.strip()}")
            return False

        console.success("Push completed")
        if result.stdout.strip():
            console.muted(result.stdout)

        return True


class GitRemotePlugin(GitBasePlugin):
    """Manage remote repositories."""

    @property
    def name(self) -> str:
        return "git_remote"

    @property
    def description(self) -> str:
        return "Show remote repositories"

    @handle_errors()
    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Show remote repositories."""
        if not self._check_git_repo():
            console.error("Not a Git repository.")
            return None

        result = self._run_git(["remote", "-v"])

        if result.returncode != 0:
            console.error("Failed to get remotes.")
            return None

        if not result.stdout.strip():
            console.info("No remotes configured.")
            return []

        remotes = []
        for line in result.stdout.strip().split("\n"):
            parts = line.split()
            if len(parts) >= 2:
                remotes.append({"name": parts[0], "url": parts[1]})

        console.rule("Remotes")
        rows = [[r["name"], r["url"]] for r in remotes]
        console.table("Remote Repositories", ["Name", "URL"], rows)

        return remotes
