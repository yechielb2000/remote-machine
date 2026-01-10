"""SSH protocol implementation using Paramiko."""
import paramiko
from typing import Any

from remote_machine.errors.exceptions import ConnectionError
from remote_machine.models.command_result import CommandResult
from remote_machine.models.remote_state import RemoteState


class SSHProtocol:
    """SSH protocol wrapper using Paramiko.

    Paramiko is imported lazily inside `connect` so tests and environments
    that don't have paramiko installed won't fail at import time.
    """

    def __init__(self, host: str, user: str, key_path: str | None = None, password: str | None = None, port: int = 22):
        """Initialize SSH connection parameters.

        Args:
            host: Remote host address
            user: SSH username
            key_path: Path to private key file
            port: SSH port (default 22)
        """
        self.host = host
        self.user = user
        self.key_path = key_path
        self.password = password
        self.port = port
        self._client: Any | None = None

    def connect(self) -> None:
        """Establish SSH connection (imports paramiko lazily)."""
        try:
            self._client = paramiko.SSHClient()
            self._client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            if self.key_path:
                self._client.connect(
                    self.host,
                    port=self.port,
                    username=self.user,
                    key_filename=self.key_path,
                )
            else:
                self._client.connect(
                    self.host,
                    port=self.port,
                    username=self.user,
                    password=self.password,
                )
        except Exception as e:
            raise ConnectionError(f"Failed to connect to {self.host}: {e}")

    def disconnect(self) -> None:
        """Close SSH connection."""
        if self._client:
            self._client.close()
            self._client = None

    def exec(self, command: str, state: RemoteState) -> CommandResult:
        """Execute a command on the remote machine.

        Args:
            command: Command to execute
            state: Remote execution state (contains cwd, env)

        Returns:
            CommandResult with stdout, stderr, exit_code
        """
        if not self._client:
            raise ConnectionError("Not connected to remote machine")

        # Build full command with environment and cwd
        full_command = self._build_command(command, state)

        try:
            _, stdout, stderr = self._client.exec_command(full_command)
            exit_code = stdout.channel.recv_exit_status()

            return CommandResult(
                command=command,
                stdout=stdout.read().decode("utf-8", errors="replace"),
                stderr=stderr.read().decode("utf-8", errors="replace"),
                exit_code=exit_code,
            )
        except Exception as e:
            raise ConnectionError(f"Command execution failed: {e}")

    def _build_command(self, command: str, state: RemoteState) -> str:
        """Build full command with environment and cwd.

        Args:
            command: Original command
            state: Remote state with cwd and env

        Returns:
            Full command string
        """
        parts = []

        # Add environment variables
        for key, value in state.env.items():
            parts.append(f"export {key}='{value}'")

        # Add cwd
        parts.append(f"cd {state.cwd}")

        # Add original command
        parts.append(command)

        return " && ".join(parts)
