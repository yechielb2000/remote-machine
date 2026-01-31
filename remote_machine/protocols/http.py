from __future__ import annotations
import http.client
import ssl
import urllib.parse
from typing import Dict, Optional
import time

from remote_machine.models import HTTPResponse, HTTPStatusResult, HTTPDownloadResult


class HTTPProtocol:
    def __init__(
        self,
        base_url: str,
        verify_tls: bool = True,
        default_headers: Optional[Dict[str, str]] = None,
        default_timeout: Optional[float] = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.verify_tls = verify_tls
        self.default_headers = default_headers or {}
        self.default_timeout = default_timeout
        self._cookies: Dict[str, str] = {}
        self._conn: Optional[http.client.HTTPConnection] = None
        self._host: Optional[str] = None
        self._port: Optional[int] = None
        self._scheme: Optional[str] = None
        self._init_connection()

    def _init_connection(self):
        parsed = urllib.parse.urlparse(self.base_url)
        self._host = parsed.hostname
        self._port = parsed.port
        self._scheme = parsed.scheme
        if parsed.scheme == "https":
            context = ssl.create_default_context()
            if not self.verify_tls:
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
            self._conn = http.client.HTTPSConnection(
                self._host,
                self._port or 443,
                timeout=self.default_timeout,
                context=context,
            )
        else:
            self._conn = http.client.HTTPConnection(
                self._host,
                self._port or 80,
                timeout=self.default_timeout,
            )

    def reset_session(self):
        if self._conn:
            self._conn.close()
        self._cookies.clear()
        self._init_connection()

    def _build_headers(self, headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        h = self.default_headers.copy()
        if headers:
            h.update(headers)
        if self._cookies:
            h["Cookie"] = "; ".join(f"{k}={v}" for k, v in self._cookies.items())
        return h

    def _update_cookies(self, response_headers: Dict[str, str]):
        set_cookie = response_headers.get("set-cookie")
        if set_cookie:
            parts = set_cookie.split(";")
            for part in parts:
                if "=" in part:
                    k, v = part.split("=", 1)
                    self._cookies[k.strip()] = v.strip()

    def request(
        self,
        method: str,
        path: str,
        headers: Optional[Dict[str, str]] = None,
        body: Optional[bytes] = None,
        timeout: Optional[float] = None,
    ) -> HTTPResponse:
        if not self._conn:
            self._init_connection()

        url_path = path if path.startswith("/") else "/" + path
        hdrs = self._build_headers(headers)

        start = time.monotonic()
        self._conn.request(method.upper(), url_path, body=body, headers=hdrs)
        res = self._conn.getresponse()
        data = res.read()
        elapsed = int((time.monotonic() - start) * 1000)

        headers_dict = {k.lower(): v for k, v in res.getheaders()}
        self._update_cookies(headers_dict)

        return HTTPResponse(
            url=f"{self._scheme}://{self._host}{url_path}",
            method=method.upper(),
            status_code=res.status,
            headers=headers_dict,
            body=data,
            elapsed_ms=elapsed,
        )

    def head(self, path: str) -> HTTPStatusResult:
        res = self.request("HEAD", path)
        return HTTPStatusResult(
            url=res.url,
            status_code=res.status_code,
            elapsed_ms=res.elapsed_ms,
        )

    def download(self, path: str, output_path: str) -> HTTPDownloadResult:
        res = self.request("GET", path)
        with open(output_path, "wb") as f:
            f.write(res.body)
        return HTTPDownloadResult(
            url=res.url,
            output_path=output_path,
            status_code=res.status_code,
            bytes_written=len(res.body),
            elapsed_ms=res.elapsed_ms,
        )
