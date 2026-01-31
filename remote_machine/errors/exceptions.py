"""Exception hierarchy for RemoteMachine."""

from remote_machine.models.command_result import CommandResult


class RemoteError(Exception):
    """Base exception for all RemoteMachine errors."""

    def __init__(self, message: str, result: CommandResult | None = None):
        self.message = message
        self.result = result
        super().__init__(message)


class CommandError(RemoteError):
    """Error executing a remote command."""


class PermissionDenied(CommandError):
    """Operation denied due to insufficient permissions."""

class NotFound(CommandError):
    """Resource not found."""


class AlreadyExists(CommandError):
    """Resource already exists."""


class InvalidArgument(CommandError):
    """Invalid argument provided."""


class Timeout(CommandError):
    """Operation timed out."""


class ProtocolNotAvailable(RemoteError):
    """Protocol not available."""
