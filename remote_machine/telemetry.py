from abc import ABC, abstractmethod


class TelemetryBackend(ABC):
    """Base interface for telemetry backends."""

    @abstractmethod
    def record_command(self, host: str, duration_ms: float, success: bool):
        """Record execution of a remote command."""

    @abstractmethod
    def record_connection(self, host: str):
        """Record a connection event."""