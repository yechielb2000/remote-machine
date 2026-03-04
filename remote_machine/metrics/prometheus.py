from prometheus_client import Counter, Histogram
from ..telemetry import TelemetryBackend


command_counter = Counter(
    "remote_machine_commands_total",
    "Total executed remote commands",
    ["host", "status"],
)

command_duration = Histogram(
    "remote_machine_command_duration_seconds",
    "Duration of remote commands",
    ["host"],
)


class PrometheusTelemetry(TelemetryBackend):
    def record_command(self, host: str, duration_ms: float, success: bool):
        status = "success" if success else "error"
        command_counter.labels(host=host, status=status).inc()
        command_duration.labels(host=host).observe(duration_ms / 1000)

    def record_connection(self, host: str):
        pass