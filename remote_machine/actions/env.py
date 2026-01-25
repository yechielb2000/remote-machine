"""Environment variable actions."""

from __future__ import annotations

from remote_machine.models.common_types import BoolResult, OperationResult
from remote_machine.models.env_types import EnvVar, EnvVars, EnvVars
from remote_machine.models.remote_state import RemoteState
from remote_machine.protocols.ssh import SSHProtocol


class ENVAction:
    """Environment variable operations."""

    def __init__(self, protocol: SSHProtocol, state: RemoteState):
        """Initialize environment actions.

        Args:
            protocol: SSH protocol instance
            state: Remote execution state
        """
        self.protocol = protocol
        self.state = state

    def get(self, key: str, default: str | None = None) -> EnvVar:
        """Return environment variable `key` as EnvVar dataclass."""
        return EnvVar(key=key, value=self.state.env.get(key, default))

    def set(self, key: str, value: str) -> OperationResult:
        """Set environment variable `key` to `value` and return OperationResult."""
        self.state.env[key] = value
        return OperationResult(success=True, message=None)

    def unset(self, key: str) -> OperationResult:
        """Remove environment variable `key` and return OperationResult."""
        self.state.env.pop(key, None)
        return OperationResult(success=True, message=None)

    def all(self) -> EnvVars:
        """Return a copy of all environment variables as EnvVars dataclass."""
        return EnvVars(vars=self.state.env.copy(), count=len(self.state.env))

    def list(self) -> EnvVars:
        """Alias for `all()`; return env variables as EnvVars dataclass."""
        return self.all()

    def clear(self) -> OperationResult:
        """Clear all environment variables and return OperationResult."""
        self.state.env.clear()
        return OperationResult(success=True, message=None)

    def update(self, variables: dict[str, str]) -> OperationResult:
        """Update env with `variables` dict and return OperationResult."""
        self.state.env.update(variables)
        return OperationResult(success=True, message=None)

    def exists(self, key: str) -> BoolResult:
        """Return BoolResult if `key` exists in env."""
        return BoolResult(key=key, result=(key in self.state.env))

    def append(self, key: str, value: str, separator: str = ":") -> OperationResult:
        """Append `value` to env `key` using `separator` and return OperationResult."""
        current = self.state.env.get(key, "")
        if current:
            self.state.env[key] = f"{current}{separator}{value}"
        else:
            self.state.env[key] = value
        return OperationResult(success=True, message=None)

    def prepend(self, key: str, value: str, separator: str = ":") -> OperationResult:
        """Prepend `value` to env `key` using `separator` and return OperationResult."""
        current = self.state.env.get(key, "")
        if current:
            self.state.env[key] = f"{value}{separator}{current}"
        else:
            self.state.env[key] = value
        return OperationResult(success=True, message=None)

    def remove_from_path(self, key: str, value: str, separator: str = ":") -> OperationResult:
        """Remove `value` from path-like env `key` and return OperationResult."""
        current = self.state.env.get(key, "")
        if current:
            parts = current.split(separator)
            parts = [p for p in parts if p != value]
            self.state.env[key] = separator.join(parts)
        return OperationResult(success=True, message=None)
