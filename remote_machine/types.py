"""Compatibility re-exports for simple types used in tests and public API."""

from remote_machine.models.remote_state import RemoteState
from remote_machine.models.command_result import CommandResult

__all__ = ["RemoteState", "CommandResult"]
