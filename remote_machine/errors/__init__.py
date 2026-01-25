"""Error handling exports."""

from remote_machine.errors.exceptions import (
    AlreadyExists,
    CommandError,
    ConnectionError,
    InvalidArgument,
    NotFound,
    PermissionDenied,
    ProtocolNotAvailable,
    RemoteError,
    Timeout,
)

__all__ = [
    "RemoteError",
    "ConnectionError",
    "CommandError",
    "PermissionDenied",
    "NotFound",
    "AlreadyExists",
    "InvalidArgument",
    "ProtocolNotAvailable",
    "Timeout",
]
