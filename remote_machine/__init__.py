"""RemoteMachine - Pythonic SSH library for remote machine control."""

from remote_machine.core import RemoteMachine
from remote_machine.errors import (
    AlreadyExists,
    CommandError,
    ConnectionError,
    InvalidArgument,
    NotFound,
    PermissionDenied,
    RemoteError,
    Timeout,
)
from remote_machine.models import Capabilities, CommandResult, RemoteState
from remote_machine.protocols import SSHProtocol
from remote_machine.utils import ErrorMapper, PathResolver

__version__ = "0.1.0"

__all__ = [
    "RemoteMachine",
    "RemoteState",
    "CommandResult",
    "Capabilities",
    "SSHProtocol",
    "RemoteError",
    "ConnectionError",
    "CommandError",
    "PermissionDenied",
    "NotFound",
    "AlreadyExists",
    "InvalidArgument",
    "Timeout",
    "ErrorMapper",
    "PathResolver",
]
