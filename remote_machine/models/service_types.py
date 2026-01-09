"""Service action result types."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ServiceStatus:
    """Service status information."""

    name: str
    state: str  # 'running', 'stopped', 'failed', etc.
    enabled: bool
    active: bool
    loaded: bool
    pid: int | None
    memory: int | None
    cpu_percent: float | None
    uptime: int | None  # seconds


@dataclass(frozen=True)
class ServiceList:
    """List of services."""

    services: list[ServiceStatus]
    count: int


@dataclass(frozen=True)
class ServiceConfig:
    """Service configuration."""

    name: str
    path: str
    content: str
    valid: bool


@dataclass(frozen=True)
class ServiceLog:
    """Service log entry."""

    timestamp: datetime
    level: str  # 'info', 'warn', 'error', etc.
    message: str
    unit: str | None


@dataclass(frozen=True)
class ServiceLogList:
    """List of service log entries."""

    service: str
    logs: list[ServiceLog]
    count: int


@dataclass(frozen=True)
class ServiceDependency:
    """Service dependency information."""

    name: str
    type: str  # 'Requires', 'Wants', 'Before', 'After', etc.
    is_satisfied: bool


@dataclass(frozen=True)
class ServiceDependencies:
    """Service dependencies."""

    service: str
    dependencies: list[ServiceDependency]
    dependents: list[str]


@dataclass(frozen=True)
class ServiceInfo:
    """Complete service information."""

    name: str
    status: ServiceStatus
    config: ServiceConfig | None
    dependencies: ServiceDependencies | None
    active_since: datetime | None
    restart_count: int
    last_restart: datetime | None
