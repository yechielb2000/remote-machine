"""Filesystem action result types."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class FileInfo:
    """File or directory information from stat."""

    path: str
    size: int
    mode: str
    owner: str
    group: str
    modified: datetime
    accessed: datetime
    created: datetime
    is_symlink: bool
    is_file: bool
    is_dir: bool


@dataclass(frozen=True)
class DirectoryEntry:
    """Entry in a directory listing."""

    name: str
    path: str
    type: str  # 'file', 'dir', 'link', etc.
    size: int
    modified: datetime
    owner: str
    permissions: str


@dataclass(frozen=True)
class DirectoryListing:
    """Result of listing a directory."""

    path: str
    entries: list[DirectoryEntry]
    count: int


@dataclass(frozen=True)
class DiskUsage:
    """Disk usage information."""

    path: str
    total: int
    used: int
    available: int
    percent: float
    human_total: str
    human_used: str
    human_available: str


@dataclass(frozen=True)
class FileFindResult:
    """Result of finding files."""

    pattern: str
    root_path: str
    matches: list[str]
    count: int
