"""SCP related result types."""

from dataclasses import dataclass


@dataclass(frozen=True)
class SCPResult:
    """Result of an SCP transfer.

    Attributes:
        source: Remote source path (string)
        destination: Destination path (string)
        bytes_transferred: Number of bytes transferred
    """

    source: str
    destination: str
    bytes_transferred: int
