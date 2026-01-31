from typing import Dict, Optional, Union, List, Tuple
import json
import base64
from concurrent.futures import ThreadPoolExecutor, as_completed

from remote_machine.protocols.http import HTTPProtocol
from remote_machine.models import HTTPStatusResult, HTTPErrorResult, OperationResult, HTTPResultType, HTTPDownloadResultType



class HTTPAction:
    def __init__(self, protocol: HTTPProtocol, max_workers: int = 10):
        self.protocol = protocol
        self.max_workers = max_workers

    def request(self, method: str, path: str, headers: Optional[Dict[str, str]] = None, body: Optional[bytes] = None) -> HTTPResultType:
        res = self.protocol.request(method, path, headers=headers, body=body)
        if res.status_code >= 400:
            return HTTPErrorResult(url=res.url, method=method.upper(), status_code=res.status_code, reason="request failed", body=res.body)
        return res

    def get(self, path: str, headers: Optional[Dict[str, str]] = None) -> HTTPResultType:
        return self.request("GET", path, headers=headers)

    def post(self, path: str, body: bytes, headers: Optional[Dict[str, str]] = None) -> HTTPResultType:
        return self.request("POST", path, headers=headers, body=body)

    def put(self, path: str, body: bytes, headers: Optional[Dict[str, str]] = None) -> HTTPResultType:
        return self.request("PUT", path, headers=headers, body=body)

    def patch(self, path: str, body: bytes, headers: Optional[Dict[str, str]] = None) -> HTTPResultType:
        return self.request("PATCH", path, headers=headers, body=body)

    def delete(self, path: str, headers: Optional[Dict[str, str]] = None) -> HTTPResultType:
        return self.request("DELETE", path, headers=headers)

    def head(self, path: str) -> HTTPStatusResult:
        return self.protocol.head(path)

    def is_up(self, path: str) -> bool:
        return self.head(path).status_code == 200

    def expect_status(self, path: str, code: int) -> OperationResult:
        status = self.head(path).status_code
        return OperationResult(status == code, f"{status=}")

    def monitor(self, path: str, attempts: int = 3) -> bool:
        for _ in range(attempts):
            if self.is_up(path):
                return True
        return False

    def latency(self, path: str) -> int:
        return self.protocol.head(path).elapsed_ms

    def download(self, path: str, output_path: str, min_bytes: int = 1) -> HTTPDownloadResultType:
        res = self.protocol.download(path, output_path)
        if res.status_code >= 400 or res.bytes_written < min_bytes:
            return HTTPErrorResult(url=res.url, method="GET", status_code=res.status_code, reason="download failed")
        return res

    def upload(self, path: str, data: bytes, headers: Optional[Dict[str, str]] = None) -> HTTPResultType:
        return self.put(path, data, headers=headers)

    def get_json(self, path: str) -> Union[dict, HTTPErrorResult]:
        res = self.get(path)
        if isinstance(res, HTTPErrorResult):
            return res
        try:
            return json.loads(res.body)
        except Exception:
            return HTTPErrorResult(url=res.url, method="GET", status_code=res.status_code, reason="invalid json", body=res.body)

    def post_json(self, path: str, payload: dict, headers: Optional[Dict[str, str]] = None) -> HTTPResultType:
        h = headers.copy() if headers else {}
        h.setdefault("Content-Type", "application/json")
        body = json.dumps(payload).encode()
        return self.post(path, body, headers=h)

    def put_json(self, path: str, payload: dict, headers: Optional[Dict[str, str]] = None) -> HTTPResultType:
        h = headers.copy() if headers else {}
        h.setdefault("Content-Type", "application/json")
        body = json.dumps(payload).encode()
        return self.put(path, body, headers=h)

    def patch_json(self, path: str, payload: dict, headers: Optional[Dict[str, str]] = None) -> HTTPResultType:
        h = headers.copy() if headers else {}
        h.setdefault("Content-Type", "application/json")
        body = json.dumps(payload).encode()
        return self.patch(path, body, headers=h)

    def get_text(self, path: str, encoding: str = "utf-8") -> Union[str, HTTPErrorResult]:
        res = self.get(path)
        if isinstance(res, HTTPErrorResult):
            return res
        return res.body.decode(encoding, errors="replace")

    def post_text(self, path: str, text: str, headers: Optional[Dict[str, str]] = None) -> HTTPResultType:
        h = headers.copy() if headers else {}
        h.setdefault("Content-Type", "text/plain")
        return self.post(path, text.encode(), headers=h)

    def put_text(self, path: str, text: str, headers: Optional[Dict[str, str]] = None) -> HTTPResultType:
        h = headers.copy() if headers else {}
        h.setdefault("Content-Type", "text/plain")
        return self.put(path, text.encode(), headers=h)

    def fetch_headers(self, path: str) -> Dict[str, str]:
        res = self.protocol.request("HEAD", path)
        return res.headers

    def set_default_header(self, key: str, value: str):
        self.protocol.default_headers[key] = value

    def get_cookies(self) -> Dict[str, str]:
        return self.protocol._cookies.copy()

    def clear_cookies(self):
        self.protocol._cookies.clear()

    def set_basic_auth(self, username: str, password: str):
        token = base64.b64encode(f"{username}:{password}".encode()).decode()
        self.set_default_header("Authorization", f"Basic {token}")

    def set_bearer_token(self, token: str):
        self.set_default_header("Authorization", f"Bearer {token}")

    def reset_session(self):
        self.protocol.reset_session()

    def get_status(self, path: str) -> int:
        return self.head(path).status_code

    def get_all_json(self, paths: List[str]) -> List[Union[dict, HTTPErrorResult]]:
        results = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_path = {executor.submit(self.get_json, p): p for p in paths}
            for fut in as_completed(future_to_path):
                path = future_to_path[fut]
                try:
                    results.append(fut.result())
                except Exception as e:
                    results.append(HTTPErrorResult(url=path, method="GET", status_code=0, reason=str(e)))
        return results

    def get_all(self, paths: List[str]) -> List[Tuple[str, HTTPResultType]]:
        results = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_path = {executor.submit(self.get, p): p for p in paths}
            for fut in as_completed(future_to_path):
                path = future_to_path[fut]
                try:
                    results.append((path, fut.result()))
                except Exception as e:
                    results.append((path, HTTPErrorResult(url=path, method="GET", status_code=0, reason=str(e))))
        return results

    def post_all(self, payloads: List[Tuple[str, bytes]]) -> List[Tuple[str, HTTPResultType]]:
        results = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_path = {executor.submit(self.post, path, data): path for path, data in payloads}
            for fut in as_completed(future_to_path):
                path = future_to_path[fut]
                try:
                    results.append((path, fut.result()))
                except Exception as e:
                    results.append((path, HTTPErrorResult(url=path, method="POST", status_code=0, reason=str(e))))
        return results

    def check_all_up(self, paths: List[str]) -> List[Tuple[str, bool]]:
        results = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_path = {executor.submit(self.is_up, p): p for p in paths}
            for fut in as_completed(future_to_path):
                path = future_to_path[fut]
                try:
                    results.append((path, fut.result()))
                except Exception:
                    results.append((path, False))
        return results

    def check_content(self, path: str, substring: str) -> bool:
        text = self.get_text(path)
        if isinstance(text, HTTPErrorResult):
            return False
        return substring in text

    def check_json_key(self, path: str, key: str) -> bool:
        data = self.get_json(path)
        if isinstance(data, HTTPErrorResult):
            return False
        return key in data
