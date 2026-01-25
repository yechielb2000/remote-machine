"""Environment action result types."""

from dataclasses import dataclass


@dataclass(frozen=True)
class EnvVar:
    key: str
    value: str | None


@dataclass(frozen=True)
class EnvVars:
    vars: dict[str, str]
    count: int
