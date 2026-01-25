"""Cron action result types."""

from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime


@dataclass(frozen=True)
class CronJob:
    """Cron job information."""

    minute: str  # 0-59, *, */5, etc.
    hour: str  # 0-23, *, */2, etc.
    day_of_month: str  # 1-31, *, etc.
    month: str  # 1-12, *, JAN-DEC, etc.
    day_of_week: str  # 0-7, *, MON-SUN, etc.
    command: str  # Command to execute
    comment: Optional[str]  # Comment/description


@dataclass(frozen=True)
class CronJobExecution:
    """Cron job execution information."""

    job_id: str  # Unique job identifier
    command: str  # Command executed
    start_time: datetime  # When job started
    end_time: Optional[datetime]  # When job ended
    exit_code: int  # Exit code of command
    stdout: str  # Standard output
    stderr: str  # Standard error
    duration_seconds: float  # Execution duration


@dataclass(frozen=True)
class CronSchedule:
    """Cron schedule representation."""

    minute: str
    hour: str
    day_of_month: str
    month: str
    day_of_week: str
    description: str  # Human-readable description


@dataclass(frozen=True)
class SystemCronFile:
    """System-level cron file information."""

    path: str  # File path (/etc/cron.d/*, /etc/crontab, etc.)
    jobs: List[CronJob]  # Jobs in this file


@dataclass(frozen=True)
class UserCronJobs:
    """All cron jobs for a user."""

    username: str
    jobs: List[CronJob]
    last_modified: Optional[datetime]
