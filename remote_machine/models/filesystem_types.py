"""Filesystem action result types."""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class PermissionBits:

    read: bool
    write: bool
    execute: bool


@dataclass
class Permissions:

    entry_type: str
    owner: PermissionBits
    group: PermissionBits
    others: PermissionBits
    raw: str


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
    group: str
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
    filesystem: str
    blocks: int
    mounted: str
    used: int
    available: int
    percent: float

    @property
    def total(self) -> int:
        return self.used + self.available

    @property
    def human_total(self) -> str:
        return self._humanize(self.total)

    @property
    def human_used(self) -> str:
        return self._humanize(self.used)

    @property
    def human_available(self) -> str:
        return self._humanize(self.available)

    @staticmethod
    def _humanize(size: int):
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size < 1024.0:
                return f"{size:.1f}{unit}"
            size /= 1024.0
        return f"{size:.1f}PB"


@dataclass(frozen=True)
class FileFindResult:
    """Result of finding files."""

    pattern: str
    root_path: str
    matches: list[str]
    count: int


@dataclass(frozen=True)
class FileContent:
    """File contents wrapper."""

    path: str
    content: str
