"""Environment variable actions."""
from __future__ import annotations

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

    def get(self, key: str, default: str | None = None) -> str | None:
        """Return environment variable `key` or `default` if absent. Args: key, default"""
        return self.state.env.get(key, default)

    def set(self, key: str, value: str) -> None:
        """Set environment variable `key` to `value`. Args: key, value"""
        self.state.env[key] = value

    def unset(self, key: str) -> None:
        """Remove environment variable `key`. Args: key"""
        self.state.env.pop(key, None)

    def all(self) -> dict[str, str]:
        """Return a copy of all environment variables as a dict."""
        return self.state.env.copy()

    def list(self) -> dict[str, str]:
        """Alias for `all()`; return env variables as dict."""
        return self.all()

    def clear(self) -> None:
        """Clear all environment variables."""
        self.state.env.clear()

    def update(self, variables: dict[str, str]) -> None:
        """Update env with `variables` dict. Args: variables"""
        self.state.env.update(variables)

    def exists(self, key: str) -> bool:
        """Return True if `key` exists in env, else False. Args: key"""
        return key in self.state.env

    def append(self, key: str, value: str, separator: str = ":") -> None:
        """Append `value` to env `key` using `separator`. Args: key, value, separator"""
        current = self.state.env.get(key, "")
        if current:
            self.state.env[key] = f"{current}{separator}{value}"
        else:
            self.state.env[key] = value

    def prepend(self, key: str, value: str, separator: str = ":") -> None:
        """Prepend `value` to env `key` using `separator`. Args: key, value, separator"""
        current = self.state.env.get(key, "")
        if current:
            self.state.env[key] = f"{value}{separator}{current}"
        else:
            self.state.env[key] = value

    def remove_from_path(self, key: str, value: str, separator: str = ":") -> None:
        """Remove `value` from path-like env `key`. Args: key, value, separator"""
        current = self.state.env.get(key, "")
        if current:
            parts = current.split(separator)
            parts = [p for p in parts if p != value]
            self.state.env[key] = separator.join(parts)
