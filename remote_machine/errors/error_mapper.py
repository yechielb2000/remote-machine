"""Error mapping utilities."""

from remote_machine.errors.exceptions import (
    AlreadyExists,
    CommandError,
    InvalidArgument,
    NotFound,
    PermissionDenied,
    Timeout,
)
from remote_machine.models.command_result import CommandResult


class ErrorMapper:
    """Map command results to typed exceptions."""

    @staticmethod
    def map_error(result: CommandResult) -> Exception | None:
        """Map a failed CommandResult to a typed exception.

        Args:
            result: CommandResult from command execution

        Returns:
            Exception instance or None if not an error
        """
        if result.success:
            return None

        stderr_lower = result.stderr.lower()
        exit_code = result.exit_code

        # Permission denied (exit code 13) or stderr message
        if exit_code == 13 or "permission denied" in stderr_lower:
            return PermissionDenied(
                f"Permission denied executing '{result.command}'",
                result,
            )

        # Not found (exit code 1 or 127)
        if exit_code == 127 or "not found" in stderr_lower or "no such file" in stderr_lower:
            return NotFound(f"Resource not found in '{result.command}'", result)

        # Already exists (exit code 1)
        if "already exists" in stderr_lower or "file exists" in stderr_lower:
            return AlreadyExists(f"Resource already exists in '{result.command}'", result)

        # Invalid argument (exit code 2)
        if exit_code == 2 or "invalid argument" in stderr_lower:
            return InvalidArgument(f"Invalid argument in '{result.command}'", result)

        # Timeout (exit code 124)
        if exit_code == 124 or "timed out" in stderr_lower:
            return Timeout(f"Command timed out: '{result.command}'", result)

        # Generic command error
        return CommandError(f"Command failed: '{result.command}'", result)

    @staticmethod
    def raise_if_error(result: CommandResult) -> None:
        """Raise an exception if CommandResult indicates failure.

        Args:
            result: CommandResult from command execution

        Raises:
            Appropriate exception subclass if command failed
        """
        error = ErrorMapper.map_error(result)
        if error:
            raise error

    @staticmethod
    def map_result(result: CommandResult) -> None:
        """Backward-compatible alias used in tests.

        Historically tests and older code called `ErrorMapper.map_result` to
        raise on non-zero exit codes; provide the same behavior.
        """
        ErrorMapper.raise_if_error(result)
