"""
Tests for Git Tools Plugin.

Comprehensive tests for all Git-related functionality.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from cli.plugins.git_tools import (
    GitStatusPlugin,
    GitLogPlugin,
    GitAddPlugin,
    GitCommitPlugin,
    GitDiffPlugin,
    GitDiffStagedPlugin,
    GitBranchPlugin,
    GitCheckoutPlugin,
    GitStashPlugin,
    GitPullPlugin,
    GitPushPlugin,
    GitRemotePlugin,
    GitMergePlugin,
    GitRebasePlugin,
    GitResetPlugin,
    GitRevertPlugin,
    GitTagPlugin,
    GitBlamePlugin,
    GitShowPlugin,
    GitFetchPlugin,
    GitCleanPlugin,
    GitConfigPlugin,
)
from cli.utils.errors import ValidationError


@pytest.fixture
def mock_git_result():
    """Create a mock git result."""
    result = Mock()
    result.returncode = 0
    result.stdout = ""
    result.stderr = ""
    return result


class TestGitStatusPlugin:
    """Tests for GitStatusPlugin."""

    @patch("cli.plugins.git_tools.subprocess.run")
    def test_status_clean(self, mock_run, mock_git_result):
        """Test git status with clean working tree."""
        mock_run.side_effect = [
            mock_git_result,  # rev-parse
            Mock(returncode=0, stdout=""),  # status
            Mock(returncode=1, stdout="", stderr=""),  # rev-list (no remote)
        ]

        plugin = GitStatusPlugin()
        result = plugin.execute()

        assert result is not None
        assert result["branch"] == ""
        assert result["files"] == []

    @patch("cli.plugins.git_tools.subprocess.run")
    def test_status_with_changes(self, mock_run):
        """Test git status with modified files."""
        mock_run.side_effect = [
            Mock(returncode=0, stdout="main"),  # branch
            Mock(returncode=0, stdout=" M test.py\nA newfile.txt"),  # status
            Mock(returncode=1, stdout="", stderr=""),  # rev-list (no remote)
        ]

        plugin = GitStatusPlugin()
        result = plugin.execute()

        assert result is not None
        assert len(result["files"]) == 2
        assert result["files"][0]["status"] == "Modified"
        assert result["files"][1]["status"] == "Added"


class TestGitLogPlugin:
    """Tests for GitLogPlugin."""

    @patch("cli.plugins.git_tools.subprocess.run")
    def test_log_default(self, mock_run):
        """Test git log with default count."""
        mock_run.side_effect = [
            Mock(returncode=0, stdout=""),  # rev-parse
            Mock(returncode=0, stdout="abc123|John Doe|2024-01-01|Fix bug\n"),  # log
        ]

        plugin = GitLogPlugin()
        result = plugin.execute()

        assert result is not None
        assert len(result) == 1
        assert result[0]["hash"] == "abc123"
        assert result[0]["author"] == "John Doe"

    @patch("cli.plugins.git_tools.subprocess.run")
    def test_log_custom_count(self, mock_run):
        """Test git log with custom count."""
        mock_run.side_effect = [
            Mock(returncode=0, stdout=""),  # rev-parse
            Mock(returncode=0, stdout=""),  # log
        ]

        plugin = GitLogPlugin()
        result = plugin.execute("10")

        assert mock_run.call_count == 2


class TestGitAddPlugin:
    """Tests for GitAddPlugin."""

    @patch("cli.plugins.git_tools.subprocess.run")
    def test_add_file(self, mock_run):
        """Test adding a single file."""
        mock_run.side_effect = [
            Mock(returncode=0),  # rev-parse
            Mock(returncode=0),  # add
        ]

        plugin = GitAddPlugin()
        result = plugin.execute("test.py")

        assert result is True
        mock_run.assert_called()

    @patch("cli.plugins.git_tools.subprocess.run")
    def test_add_all(self, mock_run):
        """Test adding all files."""
        mock_run.side_effect = [
            Mock(returncode=0),  # rev-parse
            Mock(returncode=0),  # add .
        ]

        plugin = GitAddPlugin()
        result = plugin.execute("all")

        assert result is True


class TestGitCommitPlugin:
    """Tests for GitCommitPlugin."""

    @patch("cli.plugins.git_tools.subprocess.run")
    def test_commit_valid(self, mock_run):
        """Test creating a valid commit."""
        mock_run.side_effect = [
            Mock(returncode=0),  # rev-parse
            Mock(returncode=0),  # commit
        ]

        plugin = GitCommitPlugin()
        result = plugin.execute("Initial commit")

        assert result is True

    def test_commit_short_message(self):
        """Test commit with message too short."""
        plugin = GitCommitPlugin()

        with pytest.raises(ValidationError):
            plugin.execute("ab")

    @patch("cli.plugins.git_tools.subprocess.run")
    def test_commit_no_message(self, mock_run):
        """Test commit without message."""
        mock_run.return_value = Mock(returncode=0)

        plugin = GitCommitPlugin()
        result = plugin.execute()

        assert result is None


class TestGitDiffPlugin:
    """Tests for GitDiffPlugin."""

    @patch("cli.plugins.git_tools.subprocess.run")
    def test_diff_no_changes(self, mock_run):
        """Test git diff with no changes."""
        mock_run.side_effect = [
            Mock(returncode=0),  # rev-parse
            Mock(returncode=0, stdout=""),  # diff
        ]

        plugin = GitDiffPlugin()
        result = plugin.execute()

        assert result is None

    @patch("cli.plugins.git_tools.subprocess.run")
    def test_diff_with_changes(self, mock_run):
        """Test git diff with changes."""
        mock_run.side_effect = [
            Mock(returncode=0),  # rev-parse
            Mock(returncode=0, stdout="- old line\n+ new line"),  # diff
        ]

        plugin = GitDiffPlugin()
        result = plugin.execute()

        assert result is not None
        assert "- old line" in result


class TestGitBranchPlugin:
    """Tests for GitBranchPlugin."""

    @patch("cli.plugins.git_tools.subprocess.run")
    def test_list_branches(self, mock_run):
        """Test listing branches."""
        mock_run.side_effect = [
            Mock(returncode=0),  # rev-parse
            Mock(returncode=0, stdout="  main\n* feature\n  develop"),  # branch -v
        ]

        plugin = GitBranchPlugin()
        result = plugin.execute()

        assert result is not None
        assert len(result) == 3
        assert any(b["current"] for b in result)

    @patch("cli.plugins.git_tools.subprocess.run")
    def test_create_branch(self, mock_run):
        """Test creating a new branch."""
        mock_run.side_effect = [
            Mock(returncode=0),  # rev-parse
            Mock(returncode=0),  # branch new-branch
        ]

        plugin = GitBranchPlugin()
        result = plugin.execute("new-branch")

        assert result is True


class TestGitStashPlugin:
    """Tests for GitStashPlugin."""

    @patch("cli.plugins.git_tools.subprocess.run")
    def test_stash_list_empty(self, mock_run):
        """Test listing stashes when empty."""
        mock_run.side_effect = [
            Mock(returncode=0),  # rev-parse
            Mock(returncode=0, stdout=""),  # stash list
        ]

        plugin = GitStashPlugin()
        result = plugin.execute("list")

        assert result == []

    @patch("cli.plugins.git_tools.subprocess.run")
    def test_stash_save(self, mock_run):
        """Test saving a stash."""
        mock_run.side_effect = [
            Mock(returncode=0),  # rev-parse
            Mock(returncode=0),  # stash push
        ]

        plugin = GitStashPlugin()
        result = plugin.execute("save", "WIP")

        assert result is True

    @patch("cli.plugins.git_tools.subprocess.run")
    def test_stash_pop(self, mock_run):
        """Test popping a stash."""
        mock_run.side_effect = [
            Mock(returncode=0),  # rev-parse
            Mock(returncode=0),  # stash pop
        ]

        plugin = GitStashPlugin()
        result = plugin.execute("pop")

        assert result is True


class TestGitCheckoutPlugin:
    """Tests for GitCheckoutPlugin."""

    @patch("cli.plugins.git_tools.subprocess.run")
    def test_checkout_branch(self, mock_run):
        """Test checking out a branch."""
        mock_run.side_effect = [
            Mock(returncode=0),  # rev-parse
            Mock(returncode=0),  # checkout
        ]

        plugin = GitCheckoutPlugin()
        result = plugin.execute("feature")

        assert result is True


class TestGitPullPlugin:
    """Tests for GitPullPlugin."""

    @patch("cli.plugins.git_tools.subprocess.run")
    def test_pull_success(self, mock_run):
        """Test successful pull."""
        mock_run.side_effect = [
            Mock(returncode=0),  # rev-parse
            Mock(returncode=0, stdout="Already up to date"),  # pull
        ]

        plugin = GitPullPlugin()
        result = plugin.execute()

        assert result is True


class TestGitPushPlugin:
    """Tests for GitPushPlugin."""

    @patch("cli.plugins.git_tools.subprocess.run")
    def test_push_success(self, mock_run):
        """Test successful push."""
        mock_run.side_effect = [
            Mock(returncode=0),  # rev-parse
            Mock(returncode=0, stdout="Everything up-to-date"),  # push
        ]

        plugin = GitPushPlugin()
        result = plugin.execute()

        assert result is True


class TestGitRemotePlugin:
    """Tests for GitRemotePlugin."""

    @patch("cli.plugins.git_tools.subprocess.run")
    def test_list_remotes(self, mock_run):
        """Test listing remotes."""
        mock_run.side_effect = [
            Mock(returncode=0),  # rev-parse
            Mock(
                returncode=0, stdout="origin\tgit@github.com:user/repo.git\n"
            ),  # remote -v
        ]

        plugin = GitRemotePlugin()
        result = plugin.execute()

        assert result is not None
        assert len(result) == 1
        assert result[0]["name"] == "origin"

    @patch("cli.plugins.git_tools.subprocess.run")
    def test_no_remotes(self, mock_run):
        """Test when no remotes configured."""
        mock_run.side_effect = [
            Mock(returncode=0),  # rev-parse
            Mock(returncode=0, stdout=""),  # remote -v
        ]

        plugin = GitRemotePlugin()
        result = plugin.execute()

        assert result == []


class TestGitMergePlugin:
    """Tests for GitMergePlugin."""

    @patch("cli.plugins.git_tools.subprocess.run")
    def test_merge_success(self, mock_run):
        """Test successful merge."""
        mock_run.side_effect = [
            Mock(returncode=0),  # rev-parse
            Mock(returncode=0),  # merge
        ]

        plugin = GitMergePlugin()
        result = plugin.execute("feature")

        assert result is True

    @patch("cli.plugins.git_tools.subprocess.run")
    def test_merge_no_ff(self, mock_run):
        """Test merge with --no-ff."""
        mock_run.side_effect = [
            Mock(returncode=0),  # rev-parse
            Mock(returncode=0),  # merge --no-ff
        ]

        plugin = GitMergePlugin()
        result = plugin.execute("feature", "--no-ff")

        assert result is True


class TestGitRebasePlugin:
    """Tests for GitRebasePlugin."""

    @patch("cli.plugins.git_tools.subprocess.run")
    def test_rebase_branch(self, mock_run):
        """Test rebase onto branch."""
        mock_run.side_effect = [
            Mock(returncode=0),  # rev-parse
            Mock(returncode=0),  # rebase
        ]

        plugin = GitRebasePlugin()
        result = plugin.execute("main")

        assert result is True

    @patch("cli.plugins.git_tools.subprocess.run")
    def test_rebase_continue(self, mock_run):
        """Test rebase --continue."""
        mock_run.side_effect = [
            Mock(returncode=0),  # rev-parse
            Mock(returncode=0),  # rebase --continue
        ]

        plugin = GitRebasePlugin()
        result = plugin.execute("--continue")

        assert result is True

    @patch("cli.plugins.git_tools.subprocess.run")
    def test_rebase_abort(self, mock_run):
        """Test rebase --abort."""
        mock_run.side_effect = [
            Mock(returncode=0),  # rev-parse
            Mock(returncode=0),  # rebase --abort
        ]

        plugin = GitRebasePlugin()
        result = plugin.execute("--abort")

        assert result is True


class TestGitResetPlugin:
    """Tests for GitResetPlugin."""

    @patch("cli.plugins.git_tools.subprocess.run")
    def test_reset_mixed(self, mock_run):
        """Test reset with --mixed."""
        mock_run.side_effect = [
            Mock(returncode=0),  # rev-parse
            Mock(returncode=0),  # reset --mixed
        ]

        plugin = GitResetPlugin()
        result = plugin.execute("HEAD~1")

        assert result is True

    @patch("cli.plugins.git_tools.subprocess.run")
    def test_reset_hard(self, mock_run):
        """Test reset with --hard."""
        mock_run.side_effect = [
            Mock(returncode=0),  # rev-parse
            Mock(returncode=0),  # reset --hard
        ]

        plugin = GitResetPlugin()
        result = plugin.execute("--hard", "HEAD~1")

        assert result is True

    @patch("cli.plugins.git_tools.subprocess.run")
    def test_reset_soft(self, mock_run):
        """Test reset with --soft."""
        mock_run.side_effect = [
            Mock(returncode=0),  # rev-parse
            Mock(returncode=0),  # reset --soft
        ]

        plugin = GitResetPlugin()
        result = plugin.execute("--soft", "HEAD~1")

        assert result is True


class TestGitRevertPlugin:
    """Tests for GitRevertPlugin."""

    @patch("cli.plugins.git_tools.subprocess.run")
    def test_revert_commit(self, mock_run):
        """Test revert commit."""
        mock_run.side_effect = [
            Mock(returncode=0),  # rev-parse
            Mock(returncode=0),  # revert
        ]

        plugin = GitRevertPlugin()
        result = plugin.execute("abc123")

        assert result is True

    @patch("cli.plugins.git_tools.subprocess.run")
    def test_revert_no_edit(self, mock_run):
        """Test revert with --no-edit."""
        mock_run.side_effect = [
            Mock(returncode=0),  # rev-parse
            Mock(returncode=0),  # revert --no-edit
        ]

        plugin = GitRevertPlugin()
        result = plugin.execute("abc123", "--no-edit")

        assert result is True


class TestGitTagPlugin:
    """Tests for GitTagPlugin."""

    @patch("cli.plugins.git_tools.subprocess.run")
    def test_list_tags(self, mock_run):
        """Test listing tags."""
        mock_run.side_effect = [
            Mock(returncode=0),  # rev-parse
            Mock(
                returncode=0, stdout="v1.0.0\tInitial release\nv2.0.0\tFeature update"
            ),  # tag -l
        ]

        plugin = GitTagPlugin()
        result = plugin.execute()

        assert result is not None
        assert len(result) == 2

    @patch("cli.plugins.git_tools.subprocess.run")
    def test_create_tag(self, mock_run):
        """Test creating a tag."""
        mock_run.side_effect = [
            Mock(returncode=0),  # rev-parse
            Mock(returncode=0),  # tag -a
        ]

        plugin = GitTagPlugin()
        result = plugin.execute("v1.0.0", "Initial release")

        assert result is True

    @patch("cli.plugins.git_tools.subprocess.run")
    def test_show_tag(self, mock_run):
        """Test showing tag details."""
        mock_run.side_effect = [
            Mock(returncode=0),  # rev-parse
            Mock(returncode=0, stdout="Tag: v1.0.0\n"),  # show
        ]

        plugin = GitTagPlugin()
        result = plugin.execute("v1.0.0")

        assert result is True


class TestGitBlamePlugin:
    """Tests for GitBlamePlugin."""

    @patch("cli.plugins.git_tools.subprocess.run")
    def test_blame_file(self, mock_run):
        """Test blaming a file."""
        mock_run.side_effect = [
            Mock(returncode=0),  # rev-parse
            Mock(
                returncode=0, stdout="abc123 (John Doe 2024-01-01 1) line content\n"
            ),  # blame
        ]

        plugin = GitBlamePlugin()
        result = plugin.execute("test.py")

        assert result is not None


class TestGitShowPlugin:
    """Tests for GitShowPlugin."""

    @patch("cli.plugins.git_tools.subprocess.run")
    def test_show_commit(self, mock_run):
        """Test showing commit details."""
        mock_run.side_effect = [
            Mock(returncode=0),  # rev-parse
            Mock(returncode=0, stdout="commit abc123\nAuthor: John Doe\n"),  # show
        ]

        plugin = GitShowPlugin()
        result = plugin.execute("abc123")

        assert result is not None

    @patch("cli.plugins.git_tools.subprocess.run")
    def test_show_head(self, mock_run):
        """Test showing HEAD commit."""
        mock_run.side_effect = [
            Mock(returncode=0),  # rev-parse
            Mock(returncode=0, stdout="commit def456\nAuthor: Jane Doe\n"),  # show
        ]

        plugin = GitShowPlugin()
        result = plugin.execute()

        assert result is not None


class TestGitFetchPlugin:
    """Tests for GitFetchPlugin."""

    @patch("cli.plugins.git_tools.subprocess.run")
    def test_fetch_default(self, mock_run):
        """Test fetch from default remote."""
        mock_run.side_effect = [
            Mock(returncode=0),  # rev-parse
            Mock(returncode=0),  # fetch
        ]

        plugin = GitFetchPlugin()
        result = plugin.execute()

        assert result is True

    @patch("cli.plugins.git_tools.subprocess.run")
    def test_fetch_remote(self, mock_run):
        """Test fetch from specific remote."""
        mock_run.side_effect = [
            Mock(returncode=0),  # rev-parse
            Mock(returncode=0),  # fetch origin
        ]

        plugin = GitFetchPlugin()
        result = plugin.execute("origin")

        assert result is True

    @patch("cli.plugins.git_tools.subprocess.run")
    def test_fetch_all(self, mock_run):
        """Test fetch all branches."""
        mock_run.side_effect = [
            Mock(returncode=0),  # rev-parse
            Mock(returncode=0),  # fetch origin --all
        ]

        plugin = GitFetchPlugin()
        result = plugin.execute("origin", "--all")

        assert result is True


class TestGitCleanPlugin:
    """Tests for GitCleanPlugin."""

    @patch("cli.plugins.git_tools.subprocess.run")
    def test_clean_dry_run(self, mock_run):
        """Test clean with dry run."""
        mock_run.side_effect = [
            Mock(returncode=0),  # rev-parse
            Mock(returncode=0, stdout="Would remove file.txt\n"),  # clean -f --dry-run
        ]

        plugin = GitCleanPlugin()
        result = plugin.execute("--dry-run")

        assert result is True

    @patch("cli.plugins.git_tools.subprocess.run")
    def test_clean_with_dirs(self, mock_run):
        """Test clean including directories."""
        mock_run.side_effect = [
            Mock(returncode=0),  # rev-parse
            Mock(returncode=0),  # clean -f -d
        ]

        plugin = GitCleanPlugin()
        result = plugin.execute("-d")

        assert result is True

    @patch("cli.plugins.git_tools.subprocess.run")
    def test_clean_actual(self, mock_run):
        """Test actual clean (not dry run)."""
        mock_run.side_effect = [
            Mock(returncode=0),  # rev-parse
            Mock(returncode=0),  # clean -f
        ]

        plugin = GitCleanPlugin()
        result = plugin.execute()

        assert result is True


class TestGitConfigPlugin:
    """Tests for GitConfigPlugin."""

    @patch("cli.plugins.git_tools.subprocess.run")
    def test_list_config(self, mock_run):
        """Test listing all config."""
        mock_run.side_effect = [
            Mock(returncode=0),  # rev-parse
            Mock(
                returncode=0, stdout="user.name=John Doe\nuser.email=john@example.com\n"
            ),  # config --list
        ]

        plugin = GitConfigPlugin()
        result = plugin.execute()

        assert result is not None
        assert len(result) == 2

    @patch("cli.plugins.git_tools.subprocess.run")
    def test_get_config(self, mock_run):
        """Test getting specific config."""
        mock_run.side_effect = [
            Mock(returncode=0),  # rev-parse
            Mock(returncode=0, stdout="John Doe\n"),  # config user.name
        ]

        plugin = GitConfigPlugin()
        result = plugin.execute("user.name")

        assert result == "John Doe"

    @patch("cli.plugins.git_tools.subprocess.run")
    def test_set_config(self, mock_run):
        """Test setting config."""
        mock_run.side_effect = [
            Mock(returncode=0),  # rev-parse
            Mock(returncode=0),  # config user.name
        ]

        plugin = GitConfigPlugin()
        result = plugin.execute("user.name", "John Doe")

        assert result is True

    @patch("cli.plugins.git_tools.subprocess.run")
    def test_set_global_config(self, mock_run):
        """Test setting global config."""
        mock_run.side_effect = [
            Mock(returncode=0),  # rev-parse
            Mock(returncode=0),  # config --global user.name
        ]

        plugin = GitConfigPlugin()
        result = plugin.execute("--global user.name", "John Doe")

        assert result is True
