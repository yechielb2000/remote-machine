"""Common lightweight result types used across actions."""

from dataclasses import dataclass


@dataclass(frozen=True)
class BoolResult:
    """A simple boolean result with an optional name/key."""

    key: str | None
    result: bool


@dataclass(frozen=True)
class OperationResult:
    """Generic operation result indicating success/failure and message."""

    success: bool
    message: str | None


@dataclass(frozen=True)
class CountResult:
    """Simple count wrapper."""

    key: str | None
    count: int


@dataclass(frozen=True)
class IDResult:
    """Simple integer result wrapper (e.g., PID, port)."""

    key: str | None
    id: int | None


@dataclass(frozen=True)
class StringResult:
    """Simple string wrapper."""

    key: str | None
    value: str | None
