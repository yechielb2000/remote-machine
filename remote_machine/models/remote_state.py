"""Remote state tracking - cwd and environment variables."""

from dataclasses import dataclass, field
from copy import deepcopy
from typing import List

from remote_machine.models.proxy_types import Proxy


@dataclass
class RemoteState:
    """Tracks remote execution state: current working directory and environment variables."""

    cwd: str = "/"
    env: dict[str, str] = field(default_factory=dict)
    uid: int | None = None
    has_sudo: bool = False
    proxies: List[Proxy] = field(default_factory=list)

    def copy(self) -> "RemoteState":
        """Create a deep copy of the state."""
        return deepcopy(self)