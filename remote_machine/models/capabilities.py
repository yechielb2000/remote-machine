"""Machine capabilities."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Capabilities:
    """Available protocols and actions on a remote machine."""

    protocols: set[str]
    actions: set[str]
