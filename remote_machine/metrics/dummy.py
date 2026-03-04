from remote_machine.telemetry import TelemetryBackend


class DummyTelemetry(TelemetryBackend):
    """Dummy telemetry backend for testing."""

    def __init__(self):
        self.calls = []

    def record_command(self, host: str, duration_ms: float, success: bool):
        self.calls.append(("command", host, duration_ms, success))

    def record_connection(self, host: str):
        self.calls.append(("connection", host))