"""Docker action result types."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List


@dataclass(frozen=True)
class Container:
    """Docker container information."""

    id: str
    name: str
    image: str
    status: str
    state: str
    created: datetime
    started: Optional[datetime]
    ports: List[str]
    command: str


@dataclass(frozen=True)
class Image:
    """Docker image information."""

    id: str
    repository: str
    tag: str
    created: datetime
    size: int  # in bytes
    virtual_size: int  # in bytes


@dataclass(frozen=True)
class ContainerStats:
    """Docker container resource statistics."""

    container_id: str
    cpu_percent: float
    memory_usage: int  # in bytes
    memory_limit: int  # in bytes
    memory_percent: float
    network_input: int  # in bytes
    network_output: int  # in bytes
    block_input: int  # in bytes
    block_output: int  # in bytes


@dataclass(frozen=True)
class DockerInfo:
    """Docker system information."""

    containers: int
    containers_running: int
    containers_paused: int
    containers_stopped: int
    images: int
    driver: str
    memory_total: int
    memory_available: int
    cpus: int
    kernel_version: str
    os: str
