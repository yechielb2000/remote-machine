"""Process action result types."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ProcessInfo:
    """Process information."""

    pid: int
    ppid: int
    name: str
    state: str
    user: str
    cpu_percent: float
    memory_percent: float
    memory_rss: int  # Resident set size in bytes
    memory_vms: int  # Virtual memory size in bytes
    started: datetime
    command: str


@dataclass(frozen=True)
class MemoryUsage:
    """Memory usage information."""

    total: int
    available: int
    used: int
    free: int
    percent: float
    buffers: int
    cached: int
    swap_total: int
    swap_used: int
    swap_free: int
    swap_percent: float


@dataclass(frozen=True)
class CPUUsage:
    """CPU usage information."""

    user_time: float
    system_time: float
    idle_time: float
    iowait_time: float
    irq_time: float
    softirq_time: float
    user_percent: float
    system_percent: float
    idle_percent: float
    iowait_percent: float
    count: int


@dataclass(frozen=True)
class ProcessResourceUsage:
    """Per-process CPU/memory usage."""

    pid: int
    cpu_percent: float
    memory_rss: int
    memory_vms: int


@dataclass(frozen=True)
class ProcessWaitResult:
    """Wait result for a process."""

    pid: int
    exit_code: int
    timed_out: bool


@dataclass(frozen=True)
class ProcessChildren:
    """Children PIDs list."""

    pid: int
    children: list[int]
    count: int


@dataclass(frozen=True)
class ProcessParent:
    """Parent PID info."""

    pid: int
    parent: int | None


@dataclass(frozen=True)
class ProcessList:
    """List of processes."""

    processes: list[ProcessInfo]
    count: int
