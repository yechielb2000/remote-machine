from dataclasses import dataclass, field
from typing import Optional
import threading

@dataclass
class Proxy:
    local_host: str
    local_port: int
    remote_host: str
    remote_port: int
    mode: str  # "forward" or "reverse"
    running: bool = True
    _thread: Optional[threading.Thread] = field(default=None, repr=False)
    _channel: Optional[any] = field(default=None, repr=False)