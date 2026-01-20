"""Git action result types."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List


@dataclass(frozen=True)
class Commit:
    """Git commit information."""

    hash: str
    short_hash: str
    author: str
    email: str
    date: datetime
    message: str
    branch: Optional[str] = None


@dataclass(frozen=True)
class Branch:
    """Git branch information."""

    name: str
    is_current: bool
    tracking: Optional[str] = None
    last_commit: Optional[str] = None


@dataclass(frozen=True)
class RepositoryStatus:
    """Git repository status."""

    branch: str
    commit_hash: str
    modified_files: int
    untracked_files: int
    staged_files: int
    ahead: int
    behind: int
    is_dirty: bool


@dataclass(frozen=True)
class RemoteInfo:
    """Git remote information."""

    name: str
    url: str
    fetch_url: str
    push_url: str


@dataclass(frozen=True)
class DiffStat:
    """Git diff statistics."""

    file: str
    insertions: int
    deletions: int
    changes: int
