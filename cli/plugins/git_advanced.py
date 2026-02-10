"""
Git Advanced Plugin for B.DEV CLI

Provides comprehensive advanced Git operations including PRs, issues, rebase,
cherry-pick, blame, bisect, advanced branch management, submodules, worktrees, etc.
"""

import subprocess
import json
import os
from typing import Any, List, Dict, Optional, Tuple
from pathlib import Path
from datetime import datetime

from cli.plugins import PluginBase
from cli.utils.ui import console
from cli.utils.errors import handle_errors, ValidationError
from cli.core.security import security, SecurityError


class GitAdvancedBase(PluginBase):
    """Base class for all advanced Git plugins."""

    _is_base = True

    def _run_git(self, args: List[str]) -> subprocess.CompletedProcess:
        """Run a git command and return the result."""
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


# ============================================================================
# Pull Requests & Issues
# ============================================================================


class GitPRPlugin(GitAdvancedBase):
    """Pull Request management."""

    @property
    def name(self) -> str:
        return "git_pr"

    @property
    def description(self) -> str:
        return "Pull Request management (list, create, merge, close, view, checkout)"

    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Handle PR commands."""
        if not self._check_git_repo():
            console.error("Not a Git repository.")
            return None

        if not args:
            self._show_help()
            return

        command = args[0].lower()
        sub_args = args[1:]

        try:
            if command == "list":
                self._list_prs(*sub_args)
            elif command == "create":
                self._create_pr(*sub_args)
            elif command == "merge":
                self._merge_pr(*sub_args)
            elif command == "close":
                self._close_pr(*sub_args)
            elif command == "view":
                self._view_pr(*sub_args)
            elif command == "checkout":
                self._checkout_pr(*sub_args)
            elif command == "diff":
                self._diff_pr(*sub_args)
            else:
                console.error(f"Unknown PR command: {command}")
                self._show_help()
        except Exception as e:
            console.error(f"PR command failed: {e}")

    def _list_prs(self, *args: str) -> None:
        """List all PRs."""
        state = args[0] if args else "open"
        console.info(f"Listing {state} PRs...")

        if state in ["open", "closed", "merged"]:
            result = self._run_git(
                [
                    "log",
                    "--all",
                    "--oneline",
                    "--grep",
                    f"Merge pull request",
                    "--grep",
                    f"PR #{state}",
                ]
            )

            console.rule(f"{state.capitalize()} Pull Requests")
            if result.stdout.strip():
                console.print(result.stdout)
            else:
                console.info(f"No {state} PRs found")
        else:
            console.error("Invalid state. Use: open, closed, merged")

    def _create_pr(self, *args: str) -> None:
        """Create a new PR."""
        if len(args) < 2:
            console.error("Usage: git_pr create <title> <base_branch>")
            return

        title = args[0]
        base = args[1]
        description = " ".join(args[2:]) if len(args) > 2 else ""

        console.info(f"Creating PR: {title} -> {base}")
        console.muted("Opening GitHub/GitLab to create PR...")

        try:
            repo_url = self._run_git(["remote", "get-url", "origin"]).stdout.strip()
            branch = self._run_git(["rev-parse", "--abbrev-ref", "HEAD"]).stdout.strip()

            if "github.com" in repo_url:
                import webbrowser

                url = f"{repo_url.replace('.git', '')}/compare/{base}...{branch}"
                webbrowser.open(url)
                console.success(f"Opened PR creation page: {url}")
            else:
                console.warning("PR creation only supported for GitHub repositories")
        except Exception as e:
            console.error(f"Failed to create PR: {e}")

    def _merge_pr(self, *args: str) -> None:
        """Merge a PR."""
        if not args:
            console.error("Usage: git_pr merge <pr_number_or_branch>")
            return

        pr_ref = args[0]
        strategy = args[1] if len(args) > 1 else "merge"

        console.info(f"Merging {pr_ref} with {strategy} strategy...")

        if strategy == "merge":
            result = self._run_git(["merge", pr_ref])
        elif strategy == "squash":
            result = self._run_git(["merge", "--squash", pr_ref])
            self._run_git(["commit", "-m", f"Merge PR {pr_ref}"])
        elif strategy == "ff":
            result = self._run_git(["merge", "--ff-only", pr_ref])
        else:
            console.error(f"Unknown strategy: {strategy}")
            return

        if result.returncode == 0:
            console.success(f"Successfully merged {pr_ref}")
        else:
            console.error(f"Merge failed: {result.stderr}")

    def _close_pr(self, *args: str) -> None:
        """Close a PR."""
        console.muted("Closing PR manually (no force push)...")

    def _view_pr(self, *args: str) -> None:
        """View PR details."""
        if not args:
            console.error("Usage: git_pr view <pr_number>")
            return

        console.info(f"Viewing PR {args[0]}")

    def _checkout_pr(self, *args: str) -> None:
        """Checkout a PR branch."""
        if not args:
            console.error("Usage: git_pr checkout <pr_number>")
            return

        pr_num = args[0]
        branch_name = f"pr/{pr_num}"

        console.info(f"Checking out PR {pr_num} as {branch_name}")

        result = self._run_git(["fetch", "origin", f"pull/{pr_num}/head:{branch_name}"])
        if result.returncode == 0:
            self._run_git(["checkout", branch_name])
            console.success(f"Checked out PR {pr_num}")
        else:
            console.error(f"Failed to checkout PR: {result.stderr}")

    def _diff_pr(self, *args: str) -> None:
        """Show diff for a PR."""
        if not args:
            console.error("Usage: git_pr diff <pr_number>")
            return

        pr_num = args[0]
        result = self._run_git(["diff", "HEAD", f"origin/pr/{pr_num}"])

        if result.stdout:
            console.rule(f"PR {pr_num} Diff")
            console.muted(result.stdout)
        else:
            console.info("No diff found")

    def _show_help(self) -> None:
        rows = [
            ["list [open|closed|merged]", "List PRs by state"],
            ["create <title> <base>", "Create new PR"],
            ["merge <ref> [strategy]", "Merge PR (merge/squash/ff)"],
            ["close <number>", "Close PR"],
            ["view <number>", "View PR details"],
            ["checkout <number>", "Checkout PR branch"],
            ["diff <number>", "Show PR diff"],
        ]
        console.table("PR Commands", ["Command", "Description"], rows)


class GitIssuePlugin(GitAdvancedBase):
    """Issue management."""

    @property
    def name(self) -> str:
        return "git_issue"

    @property
    def description(self) -> str:
        return "Issue management (list, create, close, comment)"

    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Handle issue commands."""
        if not self._check_git_repo():
            console.error("Not a Git repository.")
            return None

        if not args:
            self._show_help()
            return

        command = args[0].lower()
        sub_args = args[1:]

        try:
            if command == "list":
                self._list_issues(*sub_args)
            elif command == "create":
                self._create_issue(*sub_args)
            elif command == "close":
                self._close_issue(*sub_args)
            elif command == "comment":
                self._comment_issue(*sub_args)
            else:
                console.error(f"Unknown issue command: {command}")
                self._show_help()
        except Exception as e:
            console.error(f"Issue command failed: {e}")

    def _list_issues(self, *args: str) -> None:
        """List issues."""
        state = args[0] if args else "open"
        console.info(f"Listing {state} issues...")

        try:
            repo_url = self._run_git(["remote", "get-url", "origin"]).stdout.strip()
            import webbrowser

            url = f"{repo_url.replace('.git', '')}/issues?q=is:issue+is:{state}"
            webbrowser.open(url)
            console.success(f"Opened issues page: {url}")
        except:
            console.warning("Issue listing only supported for GitHub/GitLab")

    def _create_issue(self, *args: str) -> None:
        """Create an issue."""
        if len(args) < 1:
            console.error("Usage: git_issue create <title>")
            return

        title = " ".join(args)
        console.info(f"Creating issue: {title}")

        try:
            repo_url = self._run_git(["remote", "get-url", "origin"]).stdout.strip()
            import webbrowser

            url = f"{repo_url.replace('.git', '')}/issues/new?title={title}"
            webbrowser.open(url)
            console.success("Opened issue creation page")
        except:
            console.warning("Issue creation only supported for GitHub/GitLab")

    def _close_issue(self, *args: str) -> None:
        """Close an issue."""
        if not args:
            console.error("Usage: git_issue close <issue_number>")
            return

        console.info(f"Closing issue {args[0]}")

    def _comment_issue(self, *args: str) -> None:
        """Comment on an issue."""
        if len(args) < 2:
            console.error("Usage: git_issue comment <issue_number> <comment>")
            return

        issue_num = args[0]
        comment = " ".join(args[1:])
        console.info(f"Commenting on issue {issue_num}")

    def _show_help(self) -> None:
        rows = [
            ["list [open|closed]", "List issues by state"],
            ["create <title>", "Create new issue"],
            ["close <number>", "Close issue"],
            ["comment <number> <text>", "Add comment"],
        ]
        console.table("Issue Commands", ["Command", "Description"], rows)


# ============================================================================
# Advanced Git Operations
# ============================================================================


class GitRebasePlugin(GitAdvancedBase):
    """Rebase operations."""

    @property
    def name(self) -> str:
        return "git_rebase"

    @property
    def description(self) -> str:
        return "Rebase operations (interactive, auto, continue, abort)"

    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Handle rebase commands."""
        if not self._check_git_repo():
            console.error("Not a Git repository.")
            return None

        if not args:
            self._show_help()
            return

        command = args[0].lower()
        sub_args = args[1:]

        try:
            if command == "interactive":
                self._rebase_interactive(*sub_args)
            elif command == "auto":
                self._rebase_auto(*sub_args)
            elif command == "continue":
                self._rebase_continue()
            elif command == "abort":
                self._rebase_abort()
            elif command == "skip":
                self._rebase_skip()
            else:
                console.error(f"Unknown rebase command: {command}")
                self._show_help()
        except Exception as e:
            console.error(f"Rebase command failed: {e}")

    def _rebase_interactive(self, *args: str) -> None:
        """Interactive rebase."""
        commit_count = args[0] if args else "5"
        console.info(f"Starting interactive rebase for last {commit_count} commits")

        result = self._run_git(["rebase", "-i", f"HEAD~{commit_count}"])
        if result.returncode != 0:
            console.error(f"Rebase failed: {result.stderr}")

    def _rebase_auto(self, *args: str) -> None:
        """Auto rebase with squash or fixup."""
        if not args:
            console.error("Usage: git_rebase auto <squash|fixup> <base>")
            return

        mode = args[0]
        base = args[1] if len(args) > 1 else "main"

        if mode == "squash":
            console.info(f"Auto-squashing commits onto {base}")
        elif mode == "fixup":
            console.info(f"Auto-fixup commits onto {base}")
        else:
            console.error(f"Unknown mode: {mode}")
            return

    def _rebase_continue(self) -> None:
        """Continue rebase after conflicts."""
        console.info("Continuing rebase...")
        result = self._run_git(["rebase", "--continue"])
        if result.returncode == 0:
            console.success("Rebase continued successfully")
        else:
            console.error("Rebase continue failed")

    def _rebase_abort(self) -> None:
        """Abort rebase."""
        console.warning("Aborting rebase...")
        result = self._run_git(["rebase", "--abort"])
        if result.returncode == 0:
            console.success("Rebase aborted")
        else:
            console.error("Rebase abort failed")

    def _rebase_skip(self) -> None:
        """Skip current commit in rebase."""
        console.info("Skipping current commit...")
        result = self._run_git(["rebase", "--skip"])
        if result.returncode == 0:
            console.success("Commit skipped")
        else:
            console.error("Skip failed")

    def _show_help(self) -> None:
        rows = [
            ["interactive [n]", "Interactive rebase last n commits"],
            ["auto <squash|fixup> <base>", "Auto squash/fixup"],
            ["continue", "Continue rebase after conflicts"],
            ["abort", "Abort rebase"],
            ["skip", "Skip current commit"],
        ]
        console.table("Rebase Commands", ["Command", "Description"], rows)


class GitCherryPickPlugin(GitAdvancedBase):
    """Cherry-pick operations."""

    @property
    def name(self) -> str:
        return "git_cherry_pick"

    @property
    def description(self) -> str:
        return "Cherry-pick commits from other branches"

    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Handle cherry-pick commands."""
        if not self._check_git_repo():
            console.error("Not a Git repository.")
            return None

        if not args:
            console.error("Usage: git_cherry_pick <commit_hash> [commit_hash...]")
            return

        commits = args
        console.info(f"Cherry-picking {len(commits)} commit(s)...")

        for commit in commits:
            result = self._run_git(["cherry-pick", commit])
            if result.returncode == 0:
                console.success(f"Cherry-picked {commit}")
            else:
                console.error(f"Failed to cherry-pick {commit}: {result.stderr}")

    def _show_help(self) -> None:
        console.muted("Usage: git_cherry_pick <commit_hash> [commit_hash...]")


class GitMergePlugin(GitAdvancedBase):
    """Merge operations with strategies."""

    @property
    def name(self) -> str:
        return "git_merge"

    @property
    def description(self) -> str:
        return "Merge with strategies (merge, squash, ff, ours, theirs)"

    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Handle merge commands."""
        if not self._check_git_repo():
            console.error("Not a Git repository.")
            return None

        if not args:
            self._show_help()
            return

        strategy = args[0].lower()
        branch = args[1] if len(args) > 1 else None

        if not branch:
            console.error("Usage: git_merge <strategy> <branch>")
            return

        console.info(f"Merging {branch} with {strategy} strategy...")

        cmd = ["merge"]
        if strategy == "squash":
            cmd.append("--squash")
        elif strategy == "ff":
            cmd.append("--ff-only")
        elif strategy == "no-ff":
            cmd.append("--no-ff")
        elif strategy == "ours":
            cmd.append("-Xours")
        elif strategy == "theirs":
            cmd.append("-Xtheirs")
        else:
            console.warning(f"Unknown strategy: {strategy}, using default")

        cmd.append(branch)
        result = self._run_git(cmd)

        if result.returncode == 0:
            console.success(f"Merged {branch} successfully")
        else:
            console.error(f"Merge failed: {result.stderr}")

    def _show_help(self) -> None:
        rows = [
            ["merge <branch>", "Normal merge"],
            ["squash <branch>", "Squash merge"],
            ["ff <branch>", "Fast-forward only"],
            ["no-ff <branch>", "No fast-forward"],
            ["ours <branch>", "Prefer our changes"],
            ["theirs <branch>", "Prefer their changes"],
        ]
        console.table("Merge Strategies", ["Command", "Description"], rows)


# ============================================================================
# History & Analysis
# ============================================================================


class GitBlamePlugin(GitAdvancedBase):
    """Git blame to see who changed what."""

    @property
    def name(self) -> str:
        return "git_blame"

    @property
    def description(self) -> str:
        return "Show who changed each line of a file"

    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Handle blame commands."""
        if not self._check_git_repo():
            console.error("Not a Git repository.")
            return None

        if not args:
            console.error("Usage: git_blame <file> [line_number]")
            return

        file_path = args[0]
        line_num = int(args[1]) if len(args) > 1 else None

        console.info(f"Blaming {file_path}...")

        cmd = ["blame", file_path]
        if line_num:
            cmd.extend(["-L", f"{line_num},{line_num}"])

        result = self._run_git(cmd)

        if result.stdout:
            console.rule(f"Blame: {file_path}")
            console.muted(result.stdout)
        else:
            console.info("No blame information found")


class GitBisectPlugin(GitAdvancedBase):
    """Binary search for bugs using git bisect."""

    @property
    def name(self) -> str:
        return "git_bisect"

    @property
    def description(self) -> str:
        return "Binary search for bugs (start, good, bad, skip, reset)"

    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Handle bisect commands."""
        if not self._check_git_repo():
            console.error("Not a Git repository.")
            return None

        if not args:
            self._show_help()
            return

        command = args[0].lower()
        sub_args = args[1:]

        try:
            if command == "start":
                self._bisect_start(*sub_args)
            elif command == "good":
                self._bisect_mark("good", *sub_args)
            elif command == "bad":
                self._bisect_mark("bad", *sub_args)
            elif command == "skip":
                self._bisect_skip()
            elif command == "reset":
                self._bisect_reset()
            elif command == "run":
                self._bisect_run(*sub_args)
            else:
                console.error(f"Unknown bisect command: {command}")
                self._show_help()
        except Exception as e:
            console.error(f"Bisect command failed: {e}")

    def _bisect_start(self, *args: str) -> None:
        """Start bisect session."""
        console.info("Starting bisect session...")
        result = self._run_git(["bisect", "start"])

        if len(args) >= 2:
            bad_commit = args[0]
            good_commit = args[1]
            self._run_git(["bisect", "bad", bad_commit])
            self._run_git(["bisect", "good", good_commit])
            console.success(
                f"Bisect started between {good_commit} (good) and {bad_commit} (bad)"
            )
        else:
            console.success("Bisect started. Mark commits as good or bad.")

    def _bisect_mark(self, state: str, *args: str) -> None:
        """Mark commit as good or bad."""
        commit = args[0] if args else "HEAD"
        console.info(f"Marking {commit} as {state}...")
        result = self._run_git(["bisect", state, commit])

        if result.returncode == 0:
            console.success(f"Marked {commit} as {state}")
        else:
            console.error(f"Failed to mark: {result.stderr}")

    def _bisect_skip(self) -> None:
        """Skip current commit."""
        console.info("Skipping current commit...")
        result = self._run_git(["bisect", "skip"])
        if result.returncode == 0:
            console.success("Skipped current commit")

    def _bisect_reset(self) -> None:
        """Reset bisect session."""
        console.warning("Resetting bisect session...")
        result = self._run_git(["bisect", "reset"])
        if result.returncode == 0:
            console.success("Bisect reset")

    def _bisect_run(self, *args: str) -> None:
        """Automated bisect run."""
        if not args:
            console.error("Usage: git_bisect run <command>")
            return

        test_cmd = " ".join(args)
        console.info(f"Running automated bisect with command: {test_cmd}")
        result = self._run_git(["bisect", "run", test_cmd])

        if result.returncode == 0:
            console.success("Automated bisect completed")
        else:
            console.error("Automated bisect failed")

    def _show_help(self) -> None:
        rows = [
            ["start [good] [bad]", "Start bisect session"],
            ["good [commit]", "Mark commit as good"],
            ["bad [commit]", "Mark commit as bad"],
            ["skip", "Skip current commit"],
            ["reset", "Reset bisect session"],
            ["run <command>", "Automated bisect"],
        ]
        console.table("Bisect Commands", ["Command", "Description"], rows)


class GitSearchPlugin(GitAdvancedBase):
    """Search in git history."""

    @property
    def name(self) -> str:
        return "git_search"

    @property
    def description(self) -> str:
        return "Search in commit history and code"

    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Handle search commands."""
        if not self._check_git_repo():
            console.error("Not a Git repository.")
            return None

        if not args:
            console.error("Usage: git_search <query> [type]")
            return

        query = args[0]
        search_type = args[1] if len(args) > 1 else "log"

        console.info(f"Searching for '{query}' in {search_type}...")

        if search_type == "log":
            result = self._run_git(["log", "--all", "--grep", query, "--oneline"])
        elif search_type == "code":
            result = self._run_git(["log", "--all", "-S", query, "--oneline"])
        elif search_type == "author":
            result = self._run_git(["log", "--all", "--author", query, "--oneline"])
        elif search_type == "message":
            result = self._run_git(["log", "--all", "--oneline", f"--grep={query}"])
        else:
            console.error(f"Unknown search type: {search_type}")
            return

        if result.stdout:
            console.rule(f"Search Results: {query}")
            console.muted(result.stdout)
        else:
            console.info("No matches found")


class GitLogGraphPlugin(GitAdvancedBase):
    """Graphical commit history."""

    @property
    def name(self) -> str:
        return "git_log_graph"

    @property
    def description(self) -> str:
        return "Show commit history graph"

    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Show graphical log."""
        if not self._check_git_repo():
            console.error("Not a Git repository.")
            return None

        count = args[0] if args and args[0].isdigit() else "20"
        console.info(f"Showing commit graph (last {count} commits)...")

        result = self._run_git(
            [
                "log",
                f"-{count}",
                "--graph",
                "--pretty=format:%Cred%h%Creset -%C(yellow)%d%Creset %s %Cgreen(%cr) %C(bold blue)<%an>%Creset",
                "--abbrev-commit",
            ]
        )

        if result.stdout:
            console.rule("Commit Graph")
            console.muted(result.stdout)
        else:
            console.info("No commits found")


class GitContributorsPlugin(GitAdvancedBase):
    """List all contributors to the repository."""

    @property
    def name(self) -> str:
        return "git_contributors"

    @property
    def description(self) -> str:
        return "List repository contributors with statistics"

    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Show contributors."""
        if not self._check_git_repo():
            console.error("Not a Git repository.")
            return None

        console.info("Calculating contributors...")

        result = self._run_git(["shortlog", "-sn", "--all", "--no-merges"])

        if result.stdout:
            console.rule("Contributors")
            lines = result.stdout.strip().split("\n")
            rows = []
            for line in lines:
                parts = line.strip().split("\t")
                if len(parts) == 2:
                    rows.append([parts[0], parts[1]])
            console.table("Contributors", ["Commits", "Author"], rows)
        else:
            console.info("No contributors found")


class GitFileHistoryPlugin(GitAdvancedBase):
    """Show complete history of a file."""

    @property
    def name(self) -> str:
        return "git_file_history"

    @property
    def description(self) -> str:
        return "Show complete history of a file"

    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Show file history."""
        if not self._check_git_repo():
            console.error("Not a Git repository.")
            return None

        if not args:
            console.error("Usage: git_file_history <file>")
            return

        file_path = args[0]
        console.info(f"History of {file_path}...")

        result = self._run_git(
            [
                "log",
                "--follow",
                "--pretty=format:%h | %an | %ad | %s",
                "--date=short",
                "--",
                file_path,
            ]
        )

        if result.stdout:
            console.rule(f"File History: {file_path}")
            console.muted(result.stdout)
        else:
            console.info("No history found for this file")


# ============================================================================
# Advanced Branch Management
# ============================================================================


class GitRemoteBranchesPlugin(GitAdvancedBase):
    """List and manage remote branches."""

    @property
    def name(self) -> str:
        return "git_remote_branches"

    @property
    def description(self) -> str:
        return "List and manage remote branches"

    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Handle remote branch commands."""
        if not self._check_git_repo():
            console.error("Not a Git repository.")
            return None

        action = args[0] if args else "list"

        if action == "list":
            self._list_remote_branches()
        elif action == "track":
            self._track_remote_branch(*args[1:])
        elif action == "prune":
            self._prune_remote_branches()
        else:
            console.error(f"Unknown action: {action}")

    def _list_remote_branches(self) -> None:
        """List all remote branches."""
        console.info("Fetching remote branches...")
        self._run_git(["fetch", "--all"])

        result = self._run_git(["branch", "-r"])
        if result.stdout:
            console.rule("Remote Branches")
            branches = result.stdout.strip().split("\n")
            rows = []
            for branch in branches:
                b = branch.strip()
                if b and not b.startswith("HEAD"):
                    rows.append([b])
            console.table("Remote Branches", ["Branch"], rows)

    def _track_remote_branch(self, *args: str) -> None:
        """Track a remote branch."""
        if not args:
            console.error(
                "Usage: git_remote_branches track <remote/branch> [local_name]"
            )
            return

        remote_branch = args[0]
        local_name = args[1] if len(args) > 1 else remote_branch.split("/")[-1]

        console.info(f"Tracking {remote_branch} as {local_name}...")
        result = self._run_git(["branch", "--track", local_name, remote_branch])

        if result.returncode == 0:
            console.success(f"Now tracking {remote_branch} as {local_name}")
        else:
            console.error(f"Failed to track branch: {result.stderr}")

    def _prune_remote_branches(self) -> None:
        """Prune stale remote branches."""
        console.info("Pruning stale remote branches...")
        result = self._run_git(["remote", "prune", "origin"])
        if result.returncode == 0:
            console.success("Pruned stale branches")
        else:
            console.error("Prune failed")


class GitBranchComparePlugin(GitAdvancedBase):
    """Compare branches."""

    @property
    def name(self) -> str:
        return "git_branch_compare"

    @property
    def description(self) -> str:
        return "Compare branches"

    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Compare branches."""
        if not self._check_git_repo():
            console.error("Not a Git repository.")
            return None

        if len(args) < 2:
            console.error("Usage: git_branch_compare <branch1> <branch2>")
            return

        branch1 = args[0]
        branch2 = args[1]

        console.info(f"Comparing {branch1} and {branch2}...")

        # Get commits in branch1 but not in branch2
        result = self._run_git(["log", f"{branch2}..{branch1}", "--oneline"])

        if result.stdout:
            console.rule(f"Commits in {branch1} but not in {branch2}")
            console.muted(result.stdout)
        else:
            console.info(f"No differences between {branch1} and {branch2}")


class GitBranchTrackingPlugin(GitAdvancedBase):
    """Show branch tracking information."""

    @property
    def name(self) -> str:
        return "git_branch_tracking"

    @property
    def description(self) -> str:
        return "Show branch tracking status"

    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Show tracking info."""
        if not self._check_git_repo():
            console.error("Not a Git repository.")
            return None

        result = self._run_git(["branch", "-vv"])

        if result.stdout:
            console.rule("Branch Tracking")
            console.muted(result.stdout)


class GitBranchRenamePlugin(GitAdvancedBase):
    """Rename branches."""

    @property
    def name(self) -> str:
        return "git_branch_rename"

    @property
    def description(self) -> str:
        return "Rename a branch"

    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Rename branch."""
        if not self._check_git_repo():
            console.error("Not a Git repository.")
            return None

        if len(args) < 2:
            console.error("Usage: git_branch_rename <old_name> <new_name>")
            return

        old_name = args[0]
        new_name = args[1]

        console.info(f"Renaming {old_name} to {new_name}...")
        result = self._run_git(["branch", "-m", old_name, new_name])

        if result.returncode == 0:
            console.success(f"Renamed {old_name} to {new_name}")
        else:
            console.error(f"Rename failed: {result.stderr}")


class GitBranchCleanupPlugin(GitAdvancedBase):
    """Clean up merged branches."""

    @property
    def name(self) -> str:
        return "git_branch_cleanup"

    @property
    def description(self) -> str:
        return "Remove merged branches"

    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Clean up merged branches."""
        if not self._check_git_repo():
            console.error("Not a Git repository.")
            return None

        keep_branches = ["main", "master", "develop", "staging", "production"]
        console.info("Finding merged branches...")

        result = self._run_git(["branch", "--merged"])
        if result.stdout:
            branches = result.stdout.strip().split("\n")
            to_delete = []

            for branch in branches:
                b = branch.strip().replace("*", "").strip()
                if b and b not in keep_branches:
                    to_delete.append(b)

            if to_delete:
                console.warning(f"Found {len(to_delete)} merged branches to delete:")
                for b in to_delete:
                    console.muted(f"  - {b}")

                confirmation = input("Delete these branches? (yes/no): ")
                if confirmation.lower() == "yes":
                    for b in to_delete:
                        self._run_git(["branch", "-d", b])
                        console.success(f"Deleted {b}")
            else:
                console.info("No merged branches to clean up")


# ============================================================================
# Tags & Releases
# ============================================================================


class GitTagListPlugin(GitAdvancedBase):
    """List and manage tags."""

    @property
    def name(self) -> str:
        return "git_tag_list"

    @property
    def description(self) -> str:
        return "List all tags"

    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """List tags."""
        if not self._check_git_repo():
            console.error("Not a Git repository.")
            return None

        console.info("Fetching tags...")
        self._run_git(["fetch", "--tags"])

        result = self._run_git(["tag", "-l", "-n9"])
        if result.stdout:
            console.rule("Tags")
            console.muted(result.stdout)
        else:
            console.info("No tags found")


class GitTagCreatePlugin(GitAdvancedBase):
    """Create tags."""

    @property
    def name(self) -> str:
        return "git_tag_create"

    @property
    def description(self) -> str:
        return "Create a new tag"

    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Create tag."""
        if not self._check_git_repo():
            console.error("Not a Git repository.")
            return None

        if not args:
            console.error("Usage: git_tag_create <tag_name> [message] [--annotated]")
            return

        tag_name = args[0]
        annotated = "--annotated" in args or "-a" in args
        message = " ".join([a for a in args[1:] if a not in ["--annotated", "-a"]])

        console.info(f"Creating tag: {tag_name}")

        cmd = ["tag"]
        if annotated:
            cmd.extend(["-a", "-m", message if message else f"Tag {tag_name}"])
        else:
            cmd.append(tag_name)

        result = self._run_git(cmd)
        if result.returncode == 0:
            console.success(f"Tag {tag_name} created")
        else:
            console.error(f"Failed to create tag: {result.stderr}")


class GitTagDeletePlugin(GitAdvancedBase):
    """Delete tags."""

    @property
    def name(self) -> str:
        return "git_tag_delete"

    @property
    def description(self) -> str:
        return "Delete tags"

    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Delete tags."""
        if not self._check_git_repo():
            console.error("Not a Git repository.")
            return None

        if not args:
            console.error("Usage: git_tag_delete <tag_name> [--remote]")
            return

        tag_name = args[0]
        remote = "--remote" in args or "-r" in args

        console.info(f"Deleting tag: {tag_name}")

        if remote:
            result = self._run_git(
                ["push", "origin", f"--delete", f"refs/tags/{tag_name}"]
            )
        else:
            result = self._run_git(["tag", "-d", tag_name])

        if result.returncode == 0:
            console.success(f"Tag {tag_name} deleted")
        else:
            console.error(f"Failed to delete tag: {result.stderr}")


class GitTagPushPlugin(GitAdvancedBase):
    """Push tags to remote."""

    @property
    def name(self) -> str:
        return "git_tag_push"

    @property
    def description(self) -> str:
        return "Push tags to remote"

    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Push tags."""
        if not self._check_git_repo():
            console.error("Not a Git repository.")
            return None

        tag_name = args[0] if args else None
        console.info(f"Pushing tags to remote...")

        if tag_name:
            result = self._run_git(["push", "origin", tag_name])
        else:
            result = self._run_git(["push", "--tags"])

        if result.returncode == 0:
            console.success("Tags pushed successfully")
        else:
            console.error(f"Push failed: {result.stderr}")


class GitReleasePlugin(GitAdvancedBase):
    """Create releases."""

    @property
    def name(self) -> str:
        return "git_release"

    @property
    def description(self) -> str:
        return "Create a release"

    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Create release."""
        if not self._check_git_repo():
            console.error("Not a Git repository.")
            return None

        if len(args) < 2:
            console.error("Usage: git_release <tag> <title> [description]")
            return

        tag = args[0]
        title = args[1]
        description = " ".join(args[2:]) if len(args) > 2 else ""

        console.info(f"Creating release: {title}")
        console.muted("Opening GitHub/GitLab to create release...")

        try:
            repo_url = self._run_git(["remote", "get-url", "origin"]).stdout.strip()
            import webbrowser

            url = f"{repo_url.replace('.git', '')}/releases/new?tag={tag}"
            webbrowser.open(url)
            console.success(f"Opened release creation page: {url}")
        except Exception as e:
            console.error(f"Failed to open release page: {e}")


class GitReleaseNotesPlugin(GitAdvancedBase):
    """Generate release notes."""

    @property
    def name(self) -> str:
        return "git_release_notes"

    @property
    def description(self) -> str:
        return "Generate release notes from commits"

    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Generate release notes."""
        if not self._check_git_repo():
            console.error("Not a Git repository.")
            return None

        since_tag = args[0] if args else None

        console.info("Generating release notes...")

        if since_tag:
            result = self._run_git(
                ["log", f"{since_tag}..HEAD", "--pretty=format:- %s"]
            )
        else:
            result = self._run_git(["log", "-20", "--pretty=format:- %s"])

        if result.stdout:
            console.rule("Release Notes")
            console.muted(result.stdout)
        else:
            console.info("No commits found")


# ============================================================================
# Git Utilities
# ============================================================================


class GitUndoCommitPlugin(GitAdvancedBase):
    """Undo last commit."""

    @property
    def name(self) -> str:
        return "git_undo_commit"

    @property
    def description(self) -> str:
        return "Undo last commit (keep changes)"

    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Undo commit."""
        if not self._check_git_repo():
            console.error("Not a Git repository.")
            return None

        console.warning("Undoing last commit (keeping changes)...")
        result = self._run_git(["reset", "--soft", "HEAD~1"])

        if result.returncode == 0:
            console.success("Last commit undone. Changes are staged.")
        else:
            console.error("Undo failed")


class GitAmendPlugin(GitAdvancedBase):
    """Amend last commit."""

    @property
    def name(self) -> str:
        return "git_amend"

    @property
    def description(self) -> str:
        return "Amend last commit"

    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Amend commit."""
        if not self._check_git_repo():
            console.error("Not a Git repository.")
            return None

        message = " ".join(args) if args else None

        console.warning("Amending last commit...")

        if message:
            result = self._run_git(["commit", "--amend", "-m", message])
        else:
            result = self._run_git(["commit", "--amend", "--no-edit"])

        if result.returncode == 0:
            console.success("Commit amended")
        else:
            console.error("Amend failed")


class GitResetPlugin(GitAdvancedBase):
    """Reset operations."""

    @property
    def name(self) -> str:
        return "git_reset"

    @property
    def description(self) -> str:
        return "Reset operations (soft, hard, mixed)"

    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Handle reset commands."""
        if not self._check_git_repo():
            console.error("Not a Git repository.")
            return None

        if not args:
            self._show_help()
            return

        mode = args[0].lower()
        ref = args[1] if len(args) > 1 else "HEAD~1"

        console.warning(f"Resetting {mode} to {ref}...")

        if mode == "soft":
            result = self._run_git(["reset", "--soft", ref])
        elif mode == "hard":
            result = self._run_git(["reset", "--hard", ref])
        elif mode == "mixed":
            result = self._run_git(["reset", "--mixed", ref])
        else:
            console.error(f"Unknown reset mode: {mode}")
            return

        if result.returncode == 0:
            console.success(f"Reset {mode} completed")
        else:
            console.error(f"Reset failed: {result.stderr}")

    def _show_help(self) -> None:
        rows = [
            ["soft [ref]", "Reset index, keep changes (HEAD~1)"],
            ["hard [ref]", "Reset index and working tree"],
            ["mixed [ref]", "Reset index only (default)"],
        ]
        console.table("Reset Modes", ["Command", "Description"], rows)


class GitRevertPlugin(GitAdvancedBase):
    """Revert commits."""

    @property
    def name(self) -> str:
        return "git_revert"

    @property
    def description(self) -> str:
        return "Revert commits"

    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Revert commits."""
        if not self._check_git_repo():
            console.error("Not a Git repository.")
            return None

        if not args:
            console.error("Usage: git_revert <commit_hash> [--no-commit]")
            return

        commit = args[0]
        no_commit = "--no-commit" in args or "-n" in args

        console.info(f"Reverting commit {commit}...")

        cmd = ["revert"]
        if no_commit:
            cmd.append("--no-commit")
        cmd.append(commit)

        result = self._run_git(cmd)
        if result.returncode == 0:
            console.success(f"Reverted {commit}")
        else:
            console.error(f"Revert failed: {result.stderr}")


class GitCleanPlugin(GitAdvancedBase):
    """Clean untracked files."""

    @property
    def name(self) -> str:
        return "git_clean"

    @property
    def description(self) -> str:
        return "Clean untracked files"

    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Clean files."""
        if not self._check_git_repo():
            console.error("Not a Git repository.")
            return None

        dry_run = "--dry-run" in args or "-n" in args
        force = "--force" in args or "-f" in args
        dirs = "--dirs" in args or "-d" in args

        console.info("Finding untracked files...")

        cmd = ["clean"]
        if dry_run:
            cmd.append("-n")
        if force:
            cmd.append("-f")
        if dirs:
            cmd.append("-d")

        result = self._run_git(cmd)

        if result.stdout:
            console.rule("Untracked Files")
            console.muted(result.stdout)

            if not dry_run and force:
                confirmation = input("Delete these files? (yes/no): ")
                if confirmation.lower() == "yes":
                    result = self._run_git(["clean", "-f", "-d"])
                    console.success("Files cleaned")
        else:
            console.info("No untracked files to clean")


class GitGcPlugin(GitAdvancedBase):
    """Garbage collection."""

    @property
    def name(self) -> str:
        return "git_gc"

    @property
    def description(self) -> str:
        return "Git garbage collection"

    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Run garbage collection."""
        if not self._check_git_repo():
            console.error("Not a Git repository.")
            return None

        console.info("Running garbage collection...")
        console.warning("This may take a while...")

        result = self._run_git(["gc", "--aggressive", "--prune=now"])

        if result.returncode == 0:
            console.success("Garbage collection completed")
        else:
            console.error("GC failed")


# ============================================================================
# Submodules & Worktrees
# ============================================================================


class GitSubmodulePlugin(GitAdvancedBase):
    """Submodule management."""

    @property
    def name(self) -> str:
        return "git_submodule"

    @property
    def description(self) -> str:
        return "Submodule management (add, update, remove)"

    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Handle submodule commands."""
        if not self._check_git_repo():
            console.error("Not a Git repository.")
            return None

        if not args:
            self._show_help()
            return

        command = args[0].lower()
        sub_args = args[1:]

        try:
            if command == "add":
                self._submodule_add(*sub_args)
            elif command == "update":
                self._submodule_update(*sub_args)
            elif command == "remove":
                self._submodule_remove(*sub_args)
            elif command == "init":
                self._submodule_init()
            elif command == "status":
                self._submodule_status()
            elif command == "sync":
                self._submodule_sync()
            else:
                console.error(f"Unknown submodule command: {command}")
                self._show_help()
        except Exception as e:
            console.error(f"Submodule command failed: {e}")

    def _submodule_add(self, *args: str) -> None:
        """Add submodule."""
        if not args:
            console.error("Usage: git_submodule add <url> [path]")
            return

        url = args[0]
        path = args[1] if len(args) > 1 else None

        console.info(f"Adding submodule: {url}")

        cmd = ["submodule", "add"]
        if path:
            cmd.extend([url, path])
        else:
            cmd.append(url)

        result = self._run_git(cmd)
        if result.returncode == 0:
            console.success("Submodule added")
        else:
            console.error(f"Failed to add submodule: {result.stderr}")

    def _submodule_update(self, *args: str) -> None:
        """Update submodules."""
        init = "--init" in args or "-i" in args
        recursive = "--recursive" in args or "-r" in args

        console.info("Updating submodules...")

        cmd = ["submodule", "update"]
        if init:
            cmd.append("--init")
        if recursive:
            cmd.append("--recursive")

        result = self._run_git(cmd)
        if result.returncode == 0:
            console.success("Submodules updated")
        else:
            console.error("Update failed")

    def _submodule_remove(self, *args: str) -> None:
        """Remove submodule."""
        if not args:
            console.error("Usage: git_submodule remove <path>")
            return

        path = args[0]
        console.warning(f"Removing submodule: {path}")

        self._run_git(["submodule", "deinit", "-f", path])
        self._run_git(["rm", "-f", path])
        self._run_git(["config", "--remove-section", f"submodule.{path}"])
        self._run_git(["rm", "-f", ".git/modules/{path}"])

        console.success(f"Submodule {path} removed")

    def _submodule_init(self) -> None:
        """Initialize submodules."""
        console.info("Initializing submodules...")
        result = self._run_git(["submodule", "init"])
        if result.returncode == 0:
            console.success("Submodules initialized")

    def _submodule_status(self) -> None:
        """Show submodule status."""
        result = self._run_git(["submodule", "status"])
        if result.stdout:
            console.rule("Submodule Status")
            console.muted(result.stdout)

    def _submodule_sync(self) -> None:
        """Sync submodules."""
        console.info("Syncing submodules...")
        result = self._run_git(["submodule", "sync"])
        if result.returncode == 0:
            console.success("Submodules synced")

    def _show_help(self) -> None:
        rows = [
            ["add <url> [path]", "Add submodule"],
            ["update [--init] [--recursive]", "Update submodules"],
            ["remove <path>", "Remove submodule"],
            ["init", "Initialize submodules"],
            ["status", "Show submodule status"],
            ["sync", "Sync submodules"],
        ]
        console.table("Submodule Commands", ["Command", "Description"], rows)


class GitWorktreePlugin(GitAdvancedBase):
    """Worktree management."""

    @property
    def name(self) -> str:
        return "git_worktree"

    @property
    def description(self) -> str:
        return "Worktree management (add, list, remove)"

    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Handle worktree commands."""
        if not self._check_git_repo():
            console.error("Not a Git repository.")
            return None

        if not args:
            self._show_help()
            return

        command = args[0].lower()
        sub_args = args[1:]

        try:
            if command == "add":
                self._worktree_add(*sub_args)
            elif command == "list":
                self._worktree_list()
            elif command == "remove":
                self._worktree_remove(*sub_args)
            elif command == "prune":
                self._worktree_prune()
            else:
                console.error(f"Unknown worktree command: {command}")
                self._show_help()
        except Exception as e:
            console.error(f"Worktree command failed: {e}")

    def _worktree_add(self, *args: str) -> None:
        """Add worktree."""
        if not args:
            console.error("Usage: git_worktree add <branch> <path>")
            return

        branch = args[0]
        path = args[1] if len(args) > 1 else branch.replace("/", "_")

        console.info(f"Adding worktree: {branch} -> {path}")

        result = self._run_git(["worktree", "add", "-b", branch, path])
        if result.returncode == 0:
            console.success(f"Worktree added at {path}")
        else:
            console.error(f"Failed to add worktree: {result.stderr}")

    def _worktree_list(self) -> None:
        """List worktrees."""
        result = self._run_git(["worktree", "list"])
        if result.stdout:
            console.rule("Worktrees")
            console.muted(result.stdout)
        else:
            console.info("No worktrees found")

    def _worktree_remove(self, *args: str) -> None:
        """Remove worktree."""
        if not args:
            console.error("Usage: git_worktree remove <path>")
            return

        path = args[0]
        console.warning(f"Removing worktree: {path}")

        result = self._run_git(["worktree", "remove", path])
        if result.returncode == 0:
            console.success(f"Worktree removed: {path}")
        else:
            console.error(f"Failed to remove worktree: {result.stderr}")

    def _worktree_prune(self) -> None:
        """Prune worktrees."""
        console.info("Pruning worktrees...")
        result = self._run_git(["worktree", "prune"])
        if result.returncode == 0:
            console.success("Worktrees pruned")

    def _show_help(self) -> None:
        rows = [
            ["add <branch> <path>", "Add worktree"],
            ["list", "List worktrees"],
            ["remove <path>", "Remove worktree"],
            ["prune", "Prune worktrees"],
        ]
        console.table("Worktree Commands", ["Command", "Description"], rows)


# ============================================================================
# Git LFS & Ignore
# ============================================================================


class GitLfsPlugin(GitAdvancedBase):
    """Git LFS management."""

    @property
    def name(self) -> str:
        return "git_lfs"

    @property
    def description(self) -> str:
        return "Git LFS management (install, track, pull)"

    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Handle LFS commands."""
        if not self._check_git_repo():
            console.error("Not a Git repository.")
            return None

        if not args:
            self._show_help()
            return

        command = args[0].lower()
        sub_args = args[1:]

        try:
            if command == "install":
                self._lfs_install()
            elif command == "track":
                self._lfs_track(*sub_args)
            elif command == "pull":
                self._lfs_pull()
            elif command == "push":
                self._lfs_push()
            elif command == "status":
                self._lfs_status()
            else:
                console.error(f"Unknown LFS command: {command}")
                self._show_help()
        except Exception as e:
            console.error(f"LFS command failed: {e}")

    def _lfs_install(self) -> None:
        """Install LFS."""
        console.info("Installing Git LFS...")
        result = self._run_git(["lfs", "install"])
        if result.returncode == 0:
            console.success("Git LFS installed")
        else:
            console.error("LFS install failed (may need to install git-lfs first)")

    def _lfs_track(self, *args: str) -> None:
        """Track files with LFS."""
        if not args:
            console.error("Usage: git_lfs track <pattern>")
            return

        pattern = args[0]
        console.info(f"Tracking {pattern} with LFS")

        result = self._run_git(["lfs", "track", pattern])
        if result.returncode == 0:
            console.success(f"Now tracking {pattern}")
        else:
            console.error(f"Failed to track: {result.stderr}")

    def _lfs_pull(self) -> None:
        """Pull LFS files."""
        console.info("Pulling LFS files...")
        result = self._run_git(["lfs", "pull"])
        if result.returncode == 0:
            console.success("LFS files pulled")
        else:
            console.error("LFS pull failed")

    def _lfs_push(self) -> None:
        """Push LFS files."""
        console.info("Pushing LFS files...")
        result = self._run_git(["lfs", "push", "origin", "--all"])
        if result.returncode == 0:
            console.success("LFS files pushed")
        else:
            console.error("LFS push failed")

    def _lfs_status(self) -> None:
        """Show LFS status."""
        result = self._run_git(["lfs", "status"])
        if result.stdout:
            console.rule("LFS Status")
            console.muted(result.stdout)
        else:
            console.info("No LFS files")

    def _show_help(self) -> None:
        rows = [
            ["install", "Install Git LFS"],
            ["track <pattern>", "Track pattern with LFS"],
            ["pull", "Pull LFS files"],
            ["push", "Push LFS files"],
            ["status", "Show LFS status"],
        ]
        console.table("LFS Commands", ["Command", "Description"], rows)


class GitIgnorePlugin(GitAdvancedBase):
    """Git ignore management."""

    @property
    def name(self) -> str:
        return "git_ignore"

    @property
    def description(self) -> str:
        return "Git ignore management (add, list, check)"

    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Handle ignore commands."""
        if not self._check_git_repo():
            console.error("Not a Git repository.")
            return None

        if not args:
            self._show_help()
            return

        command = args[0].lower()
        sub_args = args[1:]

        try:
            if command == "add":
                self._ignore_add(*sub_args)
            elif command == "list":
                self._ignore_list()
            elif command == "check":
                self._ignore_check(*sub_args)
            else:
                console.error(f"Unknown ignore command: {command}")
                self._show_help()
        except Exception as e:
            console.error(f"Ignore command failed: {e}")

    def _ignore_add(self, *args: str) -> None:
        """Add pattern to gitignore."""
        if not args:
            console.error("Usage: git_ignore add <pattern>")
            return

        pattern = args[0]

        gitignore_path = Path(".gitignore")
        patterns = []

        if gitignore_path.exists():
            patterns = gitignore_path.read_text().splitlines()

        if pattern not in patterns:
            patterns.append(pattern)
            gitignore_path.write_text("\n".join(patterns) + "\n")
            console.success(f"Added {pattern} to .gitignore")
        else:
            console.warning(f"{pattern} already in .gitignore")

    def _ignore_list(self) -> None:
        """List gitignore patterns."""
        gitignore_path = Path(".gitignore")

        if gitignore_path.exists():
            console.rule(".gitignore")
            console.muted(gitignore_path.read_text())
        else:
            console.info(".gitignore not found")

    def _ignore_check(self, *args: str) -> None:
        """Check if file is ignored."""
        if not args:
            console.error("Usage: git_ignore check <file>")
            return

        file_path = args[0]
        result = self._run_git(["check-ignore", "-v", file_path])

        if result.returncode == 0:
            console.warning(f"{file_path} is ignored: {result.stdout.strip()}")
        else:
            console.success(f"{file_path} is NOT ignored")

    def _show_help(self) -> None:
        rows = [
            ["add <pattern>", "Add pattern to .gitignore"],
            ["list", "List .gitignore patterns"],
            ["check <file>", "Check if file is ignored"],
        ]
        console.table("Ignore Commands", ["Command", "Description"], rows)
