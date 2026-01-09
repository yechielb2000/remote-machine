"""Error mapping and exception tests."""

import pytest
from remote_machine.types import CommandResult
from remote_machine.errors import (
    CommandError,
    PermissionDenied,
    NotFound,
    AlreadyExists,
    InvalidArgument,
    Timeout,
)
from remote_machine.utils.error_mapper import ErrorMapper


class TestErrorMapper:
    """Tests for ErrorMapper."""

    def test_success_no_error(self):
        """Test that exit code 0 raises no error."""
        result = CommandResult(
            command="ls -l",
            stdout="file.txt",
            stderr="",
            exit_code=0
        )
        
        # Should not raise
        ErrorMapper.map_result(result)

    def test_permission_denied(self):
        """Test PermissionDenied mapping."""
        result = CommandResult(
            command="cat /root/secret",
            stdout="",
            stderr="cat: /root/secret: Permission denied",
            exit_code=1
        )
        
        with pytest.raises(PermissionDenied):
            ErrorMapper.map_result(result)

    def test_not_found(self):
        """Test NotFound mapping."""
        result = CommandResult(
            command="cat /nonexistent",
            stdout="",
            stderr="cat: /nonexistent: No such file or directory",
            exit_code=2
        )
        
        with pytest.raises(NotFound):
            ErrorMapper.map_result(result)

    def test_already_exists(self):
        """Test AlreadyExists mapping."""
        result = CommandResult(
            command="mkdir /tmp/test",
            stdout="",
            stderr="mkdir: cannot create directory '/tmp/test': File exists",
            exit_code=1
        )
        
        with pytest.raises(AlreadyExists):
            ErrorMapper.map_result(result)

    def test_timeout(self):
        """Test Timeout mapping."""
        result = CommandResult(
            command="sleep 100",
            stdout="",
            stderr="Command timed out",
            exit_code=124
        )
        
        with pytest.raises(Timeout):
            ErrorMapper.map_result(result)

    def test_invalid_argument(self):
        """Test InvalidArgument mapping."""
        result = CommandResult(
            command="ls -X",
            stdout="",
            stderr="ls: invalid option -- 'X'",
            exit_code=2
        )
        
        with pytest.raises(InvalidArgument):
            ErrorMapper.map_result(result)

    def test_command_error_has_result(self):
        """Test that CommandError exceptions include the result."""
        result = CommandResult(
            command="ls -l",
            stdout="",
            stderr="error message",
            exit_code=1
        )
        
        try:
            ErrorMapper.map_result(result)
        except CommandError as e:
            assert e.result == result
