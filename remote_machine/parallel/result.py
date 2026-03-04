from dataclasses import dataclass
from typing import Any


@dataclass
class ParallelResult:
    host: str
    success: bool
    output: Any | None
    error: Exception | None
    duration_ms: float