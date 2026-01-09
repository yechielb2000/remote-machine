"""Remote state tracking - cwd and environment variables."""

from dataclasses import dataclass, field


@dataclass
class RemoteState:
    """Tracks remote execution state: current working directory and environment variables."""

    cwd: str = "/"
    env: dict[str, str] = field(default_factory=dict)

    def copy(self) -> "RemoteState":
        """Create a deep copy of the state."""
        return RemoteState(cwd=self.cwd, env=self.env.copy())
