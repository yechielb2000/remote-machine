"""Unit tests for RemoteState and PathResolver."""

import pytest
from remote_machine.types import RemoteState, CommandResult
from remote_machine.utils import PathResolver


class TestRemoteState:
    """Tests for RemoteState."""

    def test_default_state(self):
        """Test default RemoteState initialization."""
        state = RemoteState()
        assert state.cwd == "/"
        assert state.env == {}

    def test_custom_state(self):
        """Test RemoteState with custom values."""
        env = {"DEBUG": "1", "HOME": "/home/user"}
        state = RemoteState(cwd="/var/log", env=env)
        assert state.cwd == "/var/log"
        assert state.env == env

    def test_state_copy(self):
        """Test RemoteState copy functionality."""
        env = {"DEBUG": "1"}
        state = RemoteState(cwd="/var/log", env=env)
        copy = state.copy()
        
        assert copy.cwd == state.cwd
        assert copy.env == state.env
        
        # Modify copy and ensure original is unchanged
        copy.env["DEBUG"] = "0"
        assert state.env["DEBUG"] == "1"


class TestPathResolver:
    """Tests for PathResolver."""

    def test_absolute_path(self):
        """Test resolution of absolute paths."""
        resolver = PathResolver()
        assert resolver.resolve("/var/log", "/home") == "/var/log"
        assert resolver.resolve("/etc/passwd") == "/etc/passwd"

    def test_relative_path(self):
        """Test resolution of relative paths."""
        resolver = PathResolver()
        assert resolver.resolve("logs", "/var") == "/var/logs"
        assert resolver.resolve(".", "/home") == "/home"

    def test_parent_directory(self):
        """Test resolution with parent directory (..)."""
        resolver = PathResolver()
        assert resolver.resolve("..", "/var/log") == "/var"
        assert resolver.resolve("../etc", "/var/log") == "/var/etc"

    def test_normalize(self):
        """Test path normalization."""
        resolver = PathResolver()
        assert resolver.normalize("/var/./log") == "/var/log"
        assert resolver.normalize("/var/log/") == "/var/log"


class TestCommandResult:
    """Tests for CommandResult."""

    def test_command_result_frozen(self):
        """Test that CommandResult is immutable."""
        result = CommandResult(
            command="ls -l",
            stdout="file.txt",
            stderr="",
            exit_code=0
        )
        
        with pytest.raises(AttributeError):
            result.exit_code = 1

    def test_command_result_repr(self):
        """Test CommandResult string representation."""
        result = CommandResult(
            command="ls -l",
            stdout="file.txt",
            stderr="",
            exit_code=0
        )
        
        repr_str = repr(result)
        assert "CommandResult" in repr_str
        assert "exit_code=0" in repr_str
