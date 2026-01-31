"""RemoteMachine - Pythonic SSH library for remote machine control.

This package uses lazy imports for heavy submodules to avoid importing
optional runtime dependencies during simple introspection or when
running unit tests that stub those dependencies.
"""

from remote_machine.errors import (
    AlreadyExists,
    CommandError,
    InvalidArgument,
    NotFound,
    PermissionDenied,
    RemoteError,
    Timeout,
)
from remote_machine.models import Capabilities, CommandResult, RemoteState
from remote_machine.errors.error_mapper import ErrorMapper
from remote_machine.utils import PathResolver

__version__ = "0.1.0"

__all__ = [
    "RemoteState",
    "CommandResult",
    "Capabilities",
    "RemoteError",
    "CommandError",
    "PermissionDenied",
    "NotFound",
    "AlreadyExists",
    "InvalidArgument",
    "Timeout",
    "ErrorMapper",
    "PathResolver",
]


def __getattr__(name: str):
    # Lazy import expensive modules only when requested
    if name == "RemoteMachine":
        from .core import RemoteMachine as _RM

        return _RM
    if name == "SSHProtocol":
        from .protocols.ssh import SSHProtocol as _SSH

        return _SSH
    raise AttributeError(name)
