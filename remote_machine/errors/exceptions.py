"""Exception hierarchy for RemoteMachine."""

from remote_machine.models.command_result import CommandResult


class RemoteError(Exception):
    """Base exception for all RemoteMachine errors."""

    def __init__(self, message: str, result: CommandResult | None = None):
        self.message = message
        self.result = result
        super().__init__(message)


class ConnectionError(RemoteError):
    """Error establishing or maintaining connection to remote machine."""

    pass


class CommandError(RemoteError):
    """Error executing a remote command."""

    pass


class PermissionDenied(CommandError):
    """Operation denied due to insufficient permissions."""

    pass


class NotFound(CommandError):
    """Resource not found."""

    pass


class AlreadyExists(CommandError):
    """Resource already exists."""

    pass


class InvalidArgument(CommandError):
    """Invalid argument provided."""

    pass


class Timeout(CommandError):
    """Operation timed out."""

    pass


class ProtocolNotAvailable(RemoteError):
    """Protocol not available."""

    pass