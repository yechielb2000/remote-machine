"""Protocols package."""

from remote_machine.protocols.ssh import SSHProtocol
from remote_machine.protocols.scp import SCPProtocol
from remote_machine.protocols.http import HTTPProtocol

__all__ = [
    "SSHProtocol",
    "SCPProtocol",
    "HTTPProtocol",
]
