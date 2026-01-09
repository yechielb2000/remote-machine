"""Command execution result."""

from dataclasses import dataclass


@dataclass(frozen=True)
class CommandResult:
    """Result of a remote command execution."""

    command: str
    stdout: str
    stderr: str
    exit_code: int

    @property
    def success(self) -> bool:
        """Check if command executed successfully."""
        return self.exit_code == 0
