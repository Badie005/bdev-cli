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


class GitMergePlugin(GitBasePlugin):
    """Merge branches."""

    @property
    def name(self) -> str:
        return "git_merge"

    @property
    def description(self) -> str:
        return "Merge branch into current (git_merge <branch>)"

    @handle_errors()
    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Merge a branch into current branch."""
        if not self._check_git_repo():
            console.error("Not a Git repository.")
            return None

        if not args:
            console.error("Usage: git_merge <branch>")
            return None

        branch = args[0]
        no_ff = "--no-ff" if len(args) > 1 and args[1] == "--no-ff" else ""

        console.info(f"Merging {branch} into current branch...")

        git_args = ["merge"]
        if no_ff:
            git_args.append(no_ff)
        git_args.append(branch)

        result = self._run_git(git_args)

        if result.returncode != 0:
            console.error(f"Merge failed: {result.stderr.strip()}")
            return False

        console.success(f"Merge completed: {branch}")
        return True


class GitRebasePlugin(GitBasePlugin):
    """Rebase operations."""

    @property
    def name(self) -> str:
        return "git_rebase"

    @property
    def description(self) -> str:
        return "Rebase current branch (git_rebase <branch>|--continue|--abort)"

    @handle_errors()
    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Handle rebase operations."""
        if not self._check_git_repo():
            console.error("Not a Git repository.")
            return None

        if not args:
            console.error("Usage: git_rebase <branch>|--continue|--abort")
            return None

        action = args[0]

        if action == "--continue":
            console.info("Continuing rebase...")
            result = self._run_git(["rebase", "--continue"])
        elif action == "--abort":
            console.info("Aborting rebase...")
            result = self._run_git(["rebase", "--abort"])
        else:
            console.info(f"Rebasing onto {action}...")
            result = self._run_git(["rebase", action])

        if result.returncode != 0:
            console.error(f"Rebase failed: {result.stderr.strip()}")
            return False

        console.success("Rebase completed")
        return True


class GitResetPlugin(GitBasePlugin):
    """Reset to previous state."""

    @property
    def name(self) -> str:
        return "git_reset"

    @property
    def description(self) -> str:
        return "Reset (git_reset [--soft|--mixed|--hard] <commit>)"

    @handle_errors()
    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Reset to a specific commit."""
        if not self._check_git_repo():
            console.error("Not a Git repository.")
            return None

        mode = "--mixed"
        commit = None

        if args:
            if args[0] in ["--soft", "--mixed", "--hard"]:
                mode = args[0]
                commit = args[1] if len(args) > 1 else "HEAD"
            else:
                commit = args[0]

        if not commit:
            console.error("Usage: git_reset [--soft|--mixed|--hard] <commit>")
            return None

        mode_desc = {
            "--soft": "Keep changes staged",
            "--mixed": "Keep changes unstaged (default)",
            "--hard": "Discard all changes",
        }

        console.warning(f"Resetting {mode_desc.get(mode, mode)} to {commit}")
        result = self._run_git(["reset", mode, commit])

        if result.returncode != 0:
            console.error(f"Reset failed: {result.stderr.strip()}")
            return False

        console.success(f"Reset to {commit}")
        return True


class GitRevertPlugin(GitBasePlugin):
    """Revert commits."""

    @property
    def name(self) -> str:
        return "git_revert"

    @property
    def description(self) -> str:
        return "Revert commit (git_revert <commit>)"

    @handle_errors()
    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Revert a specific commit."""
        if not self._check_git_repo():
            console.error("Not a Git repository.")
            return None

        if not args:
            console.error("Usage: git_revert <commit>")
            return None

        commit = args[0]
        no_edit = "--no-edit" if len(args) > 1 and args[1] == "--no-edit" else ""

        console.info(f"Reverting commit {commit}...")

        git_args = ["revert", commit]
        if no_edit:
            git_args.append(no_edit)

        result = self._run_git(git_args)

        if result.returncode != 0:
            console.error(f"Revert failed: {result.stderr.strip()}")
            return False

        console.success(f"Reverted commit {commit}")
        return True


class GitTagPlugin(GitBasePlugin):
    """Manage tags."""

    @property
    def name(self) -> str:
        return "git_tag"

    @property
    def description(self) -> str:
        return "List/create tags (git_tag [name] [message])"

    @handle_errors()
    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Handle tag operations."""
        if not self._check_git_repo():
            console.error("Not a Git repository.")
            return None

        if not args:
            return self._list_tags()

        tag_name = args[0]
        message = " ".join(args[1:]) if len(args) > 1 else None

        if message:
            return self._create_tag(tag_name, message)
        else:
            return self._show_tag(tag_name)

    def _list_tags(self) -> List[dict]:
        """List all tags."""
        result = self._run_git(["tag", "-l", "-n9"])

        if result.returncode != 0:
            console.error("Failed to list tags.")
            return []

        tags = []
        for line in result.stdout.strip().split("\n"):
            if line:
                parts = line.split(None, 1)
                tags.append(
                    {"name": parts[0], "message": parts[1] if len(parts) > 1 else ""}
                )

        if not tags:
            console.info("No tags found.")
            return []

        console.rule("Tags")
        rows = [[t["name"], t["message"][:40]] for t in tags]
        console.table("Tags", ["Name", "Message"], rows)

        return tags

    def _create_tag(self, name: str, message: str) -> bool:
        """Create a new tag."""
        result = self._run_git(["tag", "-a", name, "-m", message])

        if result.returncode != 0:
            console.error(f"Failed to create tag: {result.stderr.strip()}")
            return False

        console.success(f"Created tag: {name}")
        return True

    def _show_tag(self, name: str) -> bool:
        """Show tag details."""
        result = self._run_git(["show", name])

        if result.returncode != 0:
            console.error(f"Tag not found: {result.stderr.strip()}")
            return False

        console.rule(f"Tag: {name}")
        console.muted(result.stdout)
        return True


class GitBlamePlugin(GitBasePlugin):
    """Show blame information."""

    @property
    def name(self) -> str:
        return "git_blame"

    @property
    def description(self) -> str:
        return "Show blame info (git_blame <file> [line])"

    @handle_errors()
    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Show blame information for a file."""
        if not self._check_git_repo():
            console.error("Not a Git repository.")
            return None

        if not args:
            console.error("Usage: git_blame <file> [line]")
            return None

        file_path = args[0]

        result = self._run_git(["blame", file_path])

        if result.returncode != 0:
            console.error(f"Blame failed: {result.stderr.strip()}")
            return None

        console.rule(f"Blame: {file_path}")
        console.muted(result.stdout)
        return result.stdout


class GitShowPlugin(GitBasePlugin):
    """Show commit details."""

    @property
    def name(self) -> str:
        return "git_show"

    @property
    def description(self) -> str:
        return "Show commit details (git_show [commit])"

    @handle_errors()
    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Show commit details."""
        if not self._check_git_repo():
            console.error("Not a Git repository.")
            return None

        commit = args[0] if args else "HEAD"

        result = self._run_git(["show", commit])

        if result.returncode != 0:
            console.error(f"Show failed: {result.stderr.strip()}")
            return None

        console.rule(f"Commit: {commit}")
        console.muted(result.stdout)
        return result.stdout


class GitFetchPlugin(GitBasePlugin):
    """Fetch from remote."""

    @property
    def name(self) -> str:
        return "git_fetch"

    @property
    def description(self) -> str:
        return "Fetch from remote (git_fetch [remote])"

    @handle_errors()
    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Fetch changes from remote."""
        if not self._check_git_repo():
            console.error("Not a Git repository.")
            return None

        remote = args[0] if args else "origin"
        all_branches = "--all" if len(args) > 1 and args[1] == "--all" else ""

        console.info(f"Fetching from {remote}...")

        git_args = ["fetch", remote]
        if all_branches:
            git_args.append(all_branches)

        result = self._run_git(git_args)

        if result.returncode != 0:
            console.error(f"Fetch failed: {result.stderr.strip()}")
            return False

        console.success("Fetch completed")
        if result.stdout.strip():
            console.muted(result.stdout)

        return True


class GitCleanPlugin(GitBasePlugin):
    """Clean untracked files."""

    @property
    def name(self) -> str:
        return "git_clean"

    @property
    def description(self) -> str:
        return "Clean untracked files (git_clean [--dry-run|-d])"

    @handle_errors()
    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Clean untracked files."""
        if not self._check_git_repo():
            console.error("Not a Git repository.")
            return None

        dry_run = "--dry-run" if not args or args[0] == "--dry-run" else ""
        dirs = "-d" if any(a == "-d" for a in args) else ""

        git_args = ["clean", "-f"]
        if dirs:
            git_args.append(dirs)
        if dry_run:
            git_args.append(dry_run)

        console.info("Cleaning untracked files...")

        if dry_run:
            console.info("Dry run mode - no files will be deleted")

        result = self._run_git(git_args)

        if result.returncode != 0:
            console.error(f"Clean failed: {result.stderr.strip()}")
            return False

        if result.stdout.strip():
            console.muted(result.stdout)

        if not dry_run:
            console.success("Clean completed")
        else:
            console.info("Preview completed")

        return True


class GitConfigPlugin(GitBasePlugin):
    """Git configuration management."""

    @property
    def name(self) -> str:
        return "git_config"

    @property
    def description(self) -> str:
        return "Git config (git_config [key] [value]|--list)"

    @handle_errors()
    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Handle git configuration."""
        if not self._check_git_repo():
            console.error("Not a Git repository.")
            return None

        if not args:
            return self._list_config()

        if args[0] == "--list":
            return self._list_config()

        if len(args) == 1:
            return self._get_config(args[0])

        if len(args) >= 2:
            return self._set_config(args[0], " ".join(args[1:]))

    def _list_config(self) -> Dict[str, str]:
        """List all git configuration."""
        result = self._run_git(["config", "--list"])

        if result.returncode != 0:
            console.error("Failed to get config.")
            return {}

        config = {}
        for line in result.stdout.strip().split("\n"):
            if "=" in line:
                key, value = line.split("=", 1)
                config[key] = value

        console.rule("Git Configuration")
        rows = [[k, v] for k, v in sorted(config.items())]
        console.table("Config", ["Key", "Value"], rows)

        return config

    def _get_config(self, key: str) -> str:
        """Get a specific config value."""
        result = self._run_git(["config", key])

        if result.returncode != 0:
            console.error(f"Config not found: {key}")
            return ""

        console.info(f"{key} = {result.stdout.strip()}")
        return result.stdout.strip()

    def _set_config(self, key: str, value: str) -> bool:
        """Set a config value."""
        global_flag = "--global" if key.startswith("--global ") else ""
        if global_flag:
            key = key.replace("--global ", "")

        git_args = ["config"]
        if global_flag:
            git_args.append(global_flag)
        git_args.extend([key, value])

        result = self._run_git(git_args)

        if result.returncode != 0:
            console.error(f"Failed to set config: {result.stderr.strip()}")
            return False

        console.success(f"Set {key} = {value}")
        return True
