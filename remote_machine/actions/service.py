"""Service management actions."""
from __future__ import annotations

from remote_machine.models.remote_state import RemoteState
from remote_machine.protocols.ssh import SSHProtocol


class ServiceAction:
    """System service management operations."""

    def __init__(self, protocol: SSHProtocol, state: RemoteState):
        """Initialize service actions.

        Args:
            protocol: SSH protocol instance
            state: Remote execution state
        """
        self.protocol = protocol
        self.state = state

    def list(self) -> list[dict]:
        """Return list of service info dicts."""
        # Stub implementation - will be populated in Phase 2
        return []

    def status(self, service: str) -> dict:
        """Return status dict for `service`. Args: service"""
        # Stub implementation - will be populated in Phase 2
        return {}

    def is_running(self, service: str) -> bool:
        """Return True if `service` is running. Args: service"""
        # Stub implementation - will be populated in Phase 2
        return False

    def is_enabled(self, service: str) -> bool:
        """Return True if `service` is enabled at boot. Args: service"""
        # Stub implementation - will be populated in Phase 2
        return False

    def start(self, service: str) -> None:
        """Start `service`. Args: service"""
        # Stub implementation - will be populated in Phase 2
        pass

    def stop(self, service: str) -> None:
        """Stop `service`. Args: service"""
        # Stub implementation - will be populated in Phase 2
        pass

    def restart(self, service: str) -> None:
        """Restart `service`. Args: service"""
        # Stub implementation - will be populated in Phase 2
        pass

    def reload(self, service: str) -> None:
        """Reload `service` configuration. Args: service"""
        # Stub implementation - will be populated in Phase 2
        pass

    def enable(self, service: str) -> None:
        """Enable `service` at boot. Args: service"""
        # Stub implementation - will be populated in Phase 2
        pass

    def disable(self, service: str) -> None:
        """Disable `service` at boot. Args: service"""
        # Stub implementation - will be populated in Phase 2
        pass

    def logs(self, service: str, lines: int = 100, follow: bool = False) -> str:
        """Return last `lines` of `service` logs; `follow` to stream."""
        # Stub implementation - will be populated in Phase 2
        return ""

    def get_config(self, service: str) -> str:
        """Return service configuration content. Args: service"""
        # Stub implementation - will be populated in Phase 2
        return ""

    def edit_config(self, service: str, content: str) -> None:
        """Replace `service` config with `content`. Args: service, content"""
        # Stub implementation - will be populated in Phase 2
        pass

    def validate_config(self, service: str) -> bool:
        """Return True if `service` configuration is valid. Args: service"""
        # Stub implementation - will be populated in Phase 2
        return False

    def get_pid(self, service: str) -> int | None:
        """Return PID of `service` or None if not running. Args: service"""
        # Stub implementation - will be populated in Phase 2
        return None

    def get_port(self, service: str) -> int | None:
        """Return listening port of `service` or None. Args: service"""
        # Stub implementation - will be populated in Phase 2
        return None

    def mask(self, service: str) -> None:
        """Mask `service` to prevent it starting. Args: service"""
        # Stub implementation - will be populated in Phase 2
        pass

    def unmask(self, service: str) -> None:
        """Unmask `service`. Args: service"""
        # Stub implementation - will be populated in Phase 2
        pass

    def dependencies(self, service: str) -> list[str]:
        """Get service dependencies.

        Args:
            service: Service name

        Returns:
            List of dependent services
        """
        # Stub implementation - will be populated in Phase 2
        return []