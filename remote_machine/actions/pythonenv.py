"""Python environment actions (clean, separated functions)."""
from __future__ import annotations
import shlex
from typing import List, Optional
from remote_machine.protocols.ssh import SSHProtocol
from remote_machine.models.remote_state import RemoteState
from remote_machine.errors.error_mapper import ErrorMapper
from remote_machine.models.common_types import OperationResult


class PythonEnvAction:
    def __init__(self, protocol: SSHProtocol, state: RemoteState, venv_path: Optional[str] = None):
        self.protocol = protocol
        self.state = state
        self._venv_path = venv_path

    @property
    def venv_path(self) -> str:
        if not self._venv_path:
            raise ValueError("venv_path is not set, please call set_venv_path() first")
        return self._venv_path

    def set_venv_path(self, path: str) -> None:
        if not path or not isinstance(path, str):
            raise ValueError("venv_path must be a non-empty string")
        self._venv_path = path

    def _run(self, cmd: str) -> str:
        result = self.protocol.exec(cmd, self.state)
        ErrorMapper.raise_if_error(result)
        return result.stdout

    def _venv_python(self) -> str:
        return f"{shlex.quote(self.venv_path)}/bin/python"

    def _venv_pip(self) -> str:
        return f"{shlex.quote(self.venv_path)}/bin/pip"

    def create_venv(self, python: str = "python3", uv: bool = False, clear: bool = False, with_pip: bool = True) -> OperationResult:
        """Create a virtual environment using venv or uv."""
        if uv:
            self._run(f"uv venv {shlex.quote(self.venv_path)} --python {shlex.quote(python)}")
        else:
            flags = []
            if clear:
                flags.append("--clear")
            if not with_pip:
                flags.append("--without-pip")
            flag_str = " ".join(flags)
            self._run(f"{python} -m venv {flag_str} {shlex.quote(self.venv_path)}")
        return OperationResult(True, f"venv created at {self.venv_path}")

    def install(self, packages: List[str], upgrade: bool = False) -> OperationResult:
        flags = "--upgrade" if upgrade else ""
        pkgs = " ".join(shlex.quote(p) for p in packages)
        self._run(f"{self._venv_pip()} install {flags} {pkgs}")
        return OperationResult(True, "Packages installed")

    def activate(self) -> OperationResult:
        self._run(f"source {shlex.quote(self.venv_path)}/bin/activate")
        return OperationResult(True, "venv activated")

    def install_editable(self, path: str) -> OperationResult:
        self._run(f"{self._venv_pip()} install -e {shlex.quote(path)}")
        return OperationResult(True, "Editable install completed")

    def uninstall(self, packages: List[str], yes: bool = True) -> OperationResult:
        flags = "-y" if yes else ""
        pkgs = " ".join(shlex.quote(p) for p in packages)
        self._run(f"{self._venv_pip()} uninstall {flags} {pkgs}")
        return OperationResult(True, "Packages uninstalled")

    def freeze(self) -> str:
        return self._run(f"{self._venv_pip()} freeze")

    def list(self, outdated: bool = False) -> str:
        flag = "--outdated" if outdated else ""
        return self._run(f"{self._venv_pip()} list {flag}")

    def show(self, package: str) -> str:
        return self._run(f"{self._venv_pip()} show {shlex.quote(package)}")

    def check(self) -> str:
        return self._run(f"{self._venv_pip()} check")

    def upgrade_pip(self) -> OperationResult:
        self._run(f"{self._venv_python()} -m pip install --upgrade pip")
        return OperationResult(True, "pip upgraded")

    def purge_cache(self) -> OperationResult:
        self._run(f"{self._venv_pip()} cache purge")
        return OperationResult(True, "pip cache purged")

    def remove_venv(self) -> OperationResult:
        self._run(f"rm -rf {shlex.quote(self.venv_path)}")
        return OperationResult(True, f"venv at {self.venv_path} removed")
    
    def set_index_url(self, url: str) -> OperationResult:
        self._run(f"{self._venv_pip()} config set global.index-url {shlex.quote(url)}")
        return OperationResult(True, f"Index URL set to {url}")

    def set_trusted_host(self, host: str) -> OperationResult:
        self._run(f"{self._venv_pip()} config set global.trusted-host {shlex.quote(host)}")
        return OperationResult(True, f"Trusted host set to {host}")
    
    def set_ssl_version(self, version: str) -> OperationResult:
        self._run(f"{self._venv_pip()} config set global.ssl-version {shlex.quote(version)}")
        return OperationResult(True, f"SSL version set to {version}")
    
    def set_retries(self, retries: int) -> OperationResult:
        self._run(f"{self._venv_pip()} config set global.retries {retries}")
        return OperationResult(True, f"Retries set to {retries}")
    
    def set_timeout(self, timeout: int) -> OperationResult:
        self._run(f"{self._venv_pip()} config set global.timeout {timeout}")
        return OperationResult(True, f"Timeout set to {timeout}")
    
    def set_proxy(self, proxy: str) -> OperationResult:
        self._run(f"{self._venv_pip()} config set global.proxy {shlex.quote(proxy)}")
        return OperationResult(True, f"Proxy set to {proxy}")
    
    def set_cert(self, cert: str) -> OperationResult:
        self._run(f"{self._venv_pip()} config set global.cert {shlex.quote(cert)}")
        return OperationResult(True, f"Cert set to {cert}")
    
    def set_cache(self, cache: str) -> OperationResult:
        self._run(f"{self._venv_pip()} config set global.cache-dir {shlex.quote(cache)}")
        return OperationResult(True, f"Cache set to {cache}")
    
    def set_config(self, key: str, value: str) -> OperationResult:
        self._run(f"{self._venv_pip()} config set {shlex.quote(key)} {shlex.quote(value)}")
        return OperationResult(True, f"Config {key} set to {value}")

    def uv_version(self) -> str:
        return self._run("uv --version")
    
    def uv_add(self, package: str) -> OperationResult:
        self._run(f"uv add {shlex.quote(package)}")
        return OperationResult(True, f"Package {package} added")
    
    def uv_remove(self, package: str) -> OperationResult:
        self._run(f"uv remove {shlex.quote(package)}")
        return OperationResult(True, f"Package {package} removed")
