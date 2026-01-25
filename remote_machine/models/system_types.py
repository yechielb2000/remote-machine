"""System action result types."""

from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass(frozen=True)
class CPUInfo:
    """CPU information."""

    processor: str
    vendor_id: str
    model_name: str
    cores: int
    threads: int
    cpu_mhz: float
    l1_cache: str
    l2_cache: str
    l3_cache: str
    stepping: int | None
    flags: list[str]


@dataclass(frozen=True)
class MemoryInfo:
    """Memory information."""

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
    human_total: str
    human_available: str
    human_used: str


@dataclass(frozen=True)
class DiskPartition:
    """Disk partition information."""

    device: str
    mount_point: str
    fstype: str
    total: int
    used: int
    free: int
    percent: float
    read_only: bool


@dataclass(frozen=True)
class LoadAverage:
    """Load average information."""

    one_minute: float
    five_minutes: float
    fifteen_minutes: float
    running_processes: int
    total_processes: int


@dataclass(frozen=True)
class UptimeInfo:
    """System uptime information."""

    uptime: timedelta
    boot_time: datetime
    seconds: float
    days: int
    hours: int
    minutes: int


@dataclass(frozen=True)
class OSRelease:
    """OS release information."""

    name: str
    version: str
    version_id: str
    pretty_name: str
    id: str
    id_like: str | None
    home_url: str | None
    bug_report_url: str | None
    support_url: str | None


@dataclass(frozen=True)
class UnameInfo:
    """Uname system information."""

    sysname: str
    nodename: str
    release: str
    version: str
    machine: str


@dataclass(frozen=True)
class SystemInfo:
    """Complete system information."""

    hostname: str
    os_release: OSRelease
    uname: UnameInfo
    uptime: UptimeInfo
    kernel_version: str
    cpu_info: CPUInfo
    memory_info: MemoryInfo
    load_average: LoadAverage


@dataclass(frozen=True)
class UserInfo:
    """Logged in user information."""

    username: str
    tty: str
    hostname: str
    login_time: datetime
    idle_time: timedelta | None


@dataclass(frozen=True)
class LoginHistory:
    """User login history entry."""

    username: str
    tty: str
    hostname: str
    login_time: datetime
    logout_time: datetime | None
    duration: timedelta | None
