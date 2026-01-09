"""Core RemoteMachine class."""

from remote_machine.actions.device import DeviceAction
from remote_machine.actions.env import ENVAction
from remote_machine.actions.fs import FSAction
from remote_machine.actions.net import NETAction
from remote_machine.actions.ps import PSAction
from remote_machine.actions.service import ServiceAction
from remote_machine.actions.sys import SYSAction
from remote_machine.models.capabilities import Capabilities
from remote_machine.models.remote_state import RemoteState
from remote_machine.protocols.ssh import SSHProtocol


class RemoteMachine:
    """Main entry point for remote machine operations."""

    def __init__(
        self,
        host: str,
        user: str,
        key_path: str | None = None,
        port: int = 22,
    ):
        """Initialize RemoteMachine connection.

        Args:
            host: Remote host address
            user: SSH username
            key_path: Path to private key file (optional)
            port: SSH port (default 22)
        """
        self.protocol = SSHProtocol(host, user, key_path, port)
        self.state = RemoteState()

        # Initialize action handlers
        self.fs = FSAction(self.protocol, self.state)
        self.ps = PSAction(self.protocol, self.state)
        self.net = NETAction(self.protocol, self.state)
        self.env = ENVAction(self.protocol, self.state)
        self.sys = SYSAction(self.protocol, self.state)
        self.service = ServiceAction(self.protocol, self.state)
        self.device = DeviceAction(self.protocol, self.state)

    def connect(self) -> None:
        """Establish connection to remote machine."""
        self.protocol.connect()

    def disconnect(self) -> None:
        """Close connection to remote machine."""
        self.protocol.disconnect()

    def capabilities(self) -> Capabilities:
        """Get available capabilities.

        Returns:
            Capabilities object with available protocols and actions
        """
        return Capabilities(
            protocols={"ssh"},
            actions={"fs", "ps", "net", "env", "sys", "service", "device"},
        )

    def __enter__(self) -> "RemoteMachine":
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.disconnect()
