"""Tests for Git actions."""

import pytest
from unittest.mock import Mock
from datetime import datetime

from remote_machine.actions.git import GitAction
from remote_machine.models.remote_state import RemoteState
from remote_machine.models.command_result import CommandResult


class FakeProtocol:
    """Fake SSH protocol for testing."""

    def __init__(self):
        self.commands = []

    def exec(self, command: str, state: RemoteState) -> CommandResult:
        self.commands.append(command)

        # Mock git status - branch
        if "rev-parse --abbrev-ref HEAD" in command:
            return CommandResult(exit_code=0, stdout="main\n", stderr="")

        # Mock git status - commit hash
        if "rev-parse HEAD" in command:
            return CommandResult(
                exit_code=0,
                stdout="abc123def456789abcdef\n",
                stderr="",
            )

        # Mock git diff (modified files)
        if "diff --name-only" in command and "--cached" not in command:
            return CommandResult(
                exit_code=0,
                stdout="file1.py\nfile2.py\n",
                stderr="",
            )

        # Mock git ls-files (untracked files)
        if "ls-files --others" in command:
            return CommandResult(
                exit_code=0,
                stdout="untracked1.py\nuntracked2.py\n",
                stderr="",
            )

        # Mock git diff --cached (staged files)
        if "diff --cached --name-only" in command:
            return CommandResult(
                exit_code=0,
                stdout="staged1.py\n",
                stderr="",
            )

        # Mock git rev-list (ahead/behind)
        if "rev-list --left-right --count" in command:
            return CommandResult(
                exit_code=0,
                stdout="2 3\n",
                stderr="",
            )

        # Mock git log
        if "git log" in command and "--format=" in command:
            return CommandResult(
                exit_code=0,
                stdout="abc123def456789abcdef\nabc123\nJohn Doe\njohn@example.com\n2024-01-20T10:00:00Z\nInitial commit\n---\ndef456abc789def456abc\ndef456\nJane Smith\njane@example.com\n2024-01-19T10:00:00Z\nAdd feature X\n---\n",
                stderr="",
            )

        # Mock git branch
        if (
            "branch" in command
            and "-a" not in command
            and "create" not in command
            and "delete" not in command
        ):
            return CommandResult(
                exit_code=0,
                stdout="* main\n  develop\n  feature/new-feature\n",
                stderr="",
            )

        # Mock git remote -v
        if "remote -v" in command:
            return CommandResult(
                exit_code=0,
                stdout="origin\thttps://github.com/user/repo.git (fetch)\norigin\thttps://github.com/user/repo.git (push)\nupstream\thttps://github.com/upstream/repo.git (fetch)\n",
                stderr="",
            )

        # Mock git clone
        if "git clone" in command:
            return CommandResult(
                exit_code=0,
                stdout="Cloning into 'repo'...\nremote: Counting objects: 100%, done.\n",
                stderr="",
            )

        # Mock git commit
        if "git commit" in command:
            return CommandResult(
                exit_code=0,
                stdout="[main abc123d] Add feature X\n 1 file changed, 10 insertions(+), 5 deletions(-)",
                stderr="",
            )

        # Mock git add
        if "git add" in command:
            return CommandResult(exit_code=0, stdout="", stderr="")

        # Mock git push
        if "git push" in command:
            return CommandResult(
                exit_code=0,
                stdout="Counting objects: 3, done.\nDelta compression using up to 8 threads.\nTo https://github.com/user/repo.git\n   abc123d..def456e  main -> main",
                stderr="",
            )

        # Mock git pull
        if "git pull" in command:
            return CommandResult(
                exit_code=0,
                stdout="From https://github.com/user/repo.git\n   abc123d..def456e  main       -> origin/main\nUpdating abc123d..def456e\nFast-forward\n file.py | 10 ++++++++--\n 1 file changed, 8 insertions(+), 2 deletions(-)",
                stderr="",
            )

        # Mock git checkout
        if "git checkout" in command:
            return CommandResult(
                exit_code=0,
                stdout="Switched to branch 'develop'\n",
                stderr="",
            )

        # Mock git branch create
        if "git branch" in command and "-D" not in command and "-d" not in command:
            return CommandResult(exit_code=0, stdout="", stderr="")

        # Mock git branch delete
        if "git branch" in command and ("-D" in command or "-d" in command):
            return CommandResult(
                exit_code=0,
                stdout="Deleted branch feature/test (was abc123d).\n",
                stderr="",
            )

        # Mock git diff
        if "git diff" in command and "--stat" not in command:
            return CommandResult(
                exit_code=0,
                stdout="diff --git a/file.py b/file.py\nindex abc123..def456 100644\n--- a/file.py\n+++ b/file.py\n@@ -1,5 +1,6 @@\n def hello():\n     print('Hello')\n+    print('World')\n",
                stderr="",
            )

        # Mock git diff --stat
        if "git diff --stat" in command:
            return CommandResult(
                exit_code=0,
                stdout=" file1.py | 10 ++++++++--\n file2.py |  5 ++++-\n file3.py |  2 +-\n 3 files changed, 14 insertions(+), 3 deletions(-)\n",
                stderr="",
            )

        # Default
        return CommandResult(exit_code=0, stdout="", stderr="")


def test_git_status():
    """Test getting repository status."""
    protocol = FakeProtocol()
    state = RemoteState()
    action = GitAction(protocol, state)

    status = action.status()

    assert status.branch == "main"
    assert status.commit_hash == "abc123def456789abcdef"
    assert status.modified_files == 2
    assert status.untracked_files == 2
    assert status.staged_files == 1
    assert status.is_dirty is True


def test_git_log():
    """Test getting commit log."""
    protocol = FakeProtocol()
    state = RemoteState()
    action = GitAction(protocol, state)

    commits = action.log(limit=10)

    assert len(commits) == 2
    assert commits[0].hash == "abc123def456789abcdef"
    assert commits[0].short_hash == "abc123"
    assert commits[0].author == "John Doe"
    assert commits[0].message == "Initial commit"


def test_git_list_branches():
    """Test listing branches."""
    protocol = FakeProtocol()
    state = RemoteState()
    action = GitAction(protocol, state)

    branches = action.list_branches()

    assert len(branches) == 3
    assert branches[0].name == "main"
    assert branches[0].is_current is True
    assert branches[1].name == "develop"
    assert branches[2].name == "feature/new-feature"


def test_git_list_remotes():
    """Test listing remotes."""
    protocol = FakeProtocol()
    state = RemoteState()
    action = GitAction(protocol, state)

    remotes = action.list_remotes()

    assert len(remotes) >= 1
    assert remotes[0].name == "origin"
    assert "github.com" in remotes[0].url


def test_git_clone():
    """Test cloning a repository."""
    protocol = FakeProtocol()
    state = RemoteState()
    action = GitAction(protocol, state)

    result = action.clone(
        repository_url="https://github.com/user/repo.git",
        target_path="/tmp/repo",
    )

    assert result.success is True
    assert "cloned" in result.message.lower()


def test_git_commit():
    """Test committing changes."""
    protocol = FakeProtocol()
    state = RemoteState()
    action = GitAction(protocol, state)

    result = action.commit(message="Add feature X")

    assert result.success is True
    assert "Add feature X" in result.message or "changed" in result.message


def test_git_add():
    """Test adding files for commit."""
    protocol = FakeProtocol()
    state = RemoteState()
    action = GitAction(protocol, state)

    result = action.add(paths=["file1.py", "file2.py"])

    assert result.success is True
    assert "staged" in result.message.lower()


def test_git_push():
    """Test pushing commits."""
    protocol = FakeProtocol()
    state = RemoteState()
    action = GitAction(protocol, state)

    result = action.push(remote="origin", branch="main")

    assert result.success is True


def test_git_pull():
    """Test pulling changes."""
    protocol = FakeProtocol()
    state = RemoteState()
    action = GitAction(protocol, state)

    result = action.pull(remote="origin")

    assert result.success is True


def test_git_checkout():
    """Test checking out a branch."""
    protocol = FakeProtocol()
    state = RemoteState()
    action = GitAction(protocol, state)

    result = action.checkout(ref="develop")

    assert result.success is True
    assert "develop" in result.message


def test_git_create_branch():
    """Test creating a new branch."""
    protocol = FakeProtocol()
    state = RemoteState()
    action = GitAction(protocol, state)

    result = action.create_branch(branch_name="feature/new-feature")

    assert result.success is True
    assert "created" in result.message.lower()


def test_git_delete_branch():
    """Test deleting a branch."""
    protocol = FakeProtocol()
    state = RemoteState()
    action = GitAction(protocol, state)

    result = action.delete_branch(branch_name="feature/test", force=False)

    assert result.success is True


def test_git_diff():
    """Test getting diff of changes."""
    protocol = FakeProtocol()
    state = RemoteState()
    action = GitAction(protocol, state)

    diff = action.diff()

    assert "diff --git" in diff
    assert "hello()" in diff


def test_git_diff_stat():
    """Test getting diff statistics."""
    protocol = FakeProtocol()
    state = RemoteState()
    action = GitAction(protocol, state)

    stats = action.diff_stat()

    assert len(stats) == 3
    assert stats[0].file == "file1.py"
    assert stats[0].insertions == 10
    assert stats[0].deletions == 2
