from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Optional, Union


@dataclass(frozen=True, slots=True)
class HTTPResponse:
    url: str
    method: str

    status_code: int
    headers: Dict[str, str]
    body: bytes

    elapsed_ms: int


@dataclass(slots=True)
class HTTPStatusResult:
    url: str
    status_code: int
    elapsed_ms: int


@dataclass(slots=True)
class HTTPDownloadResult:
    url: str
    output_path: str

    status_code: int
    bytes_written: int
    elapsed_ms: int


@dataclass(slots=True)
class HTTPErrorResult:
    url: str
    method: str
    status_code: int
    reason: str
    body: Optional[bytes] = None


HTTPResultType = Union[HTTPResponse, HTTPErrorResult]
HTTPDownloadResultType = Union[HTTPDownloadResult, HTTPErrorResult]