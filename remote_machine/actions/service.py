"""Service management actions."""
from __future__ import annotations

import shlex

from remote_machine.models.remote_state import RemoteState
from remote_machine.protocols.ssh import SSHProtocol
from remote_machine.models.common_types import BoolResult, OperationResult, IDResult
from remote_machine.models.service_types import (
    ServiceStatus,
    ServiceList,
    ServiceConfig,
    ServiceLog,
    ServiceLogList,
    ServiceDependencies,
    ServiceDependency,
)


from datetime import datetime


class ServiceAction:
    """System service management operations."""

    def __init__(self, protocol: SSHProtocol, state: RemoteState):
        """Initialize service actions.

        Args:
            protocol: SSH protocol instance
            state: Remote execution state
        """
        self.protocol = protocol
        self.state = state

    def list(self) -> ServiceList:
        """Return list of services as ServiceList dataclass."""
        out = self.protocol.exec("systemctl list-units --type=service --all --no-legend --no-pager", self.state)
        ErrorMapper.raise_if_error(out)
        lines = out.stdout.splitlines()
        services: list[ServiceStatus] = []
        for line in lines:
            if not line.strip():
                continue
            parts = line.split(None, 4)
            if len(parts) < 5:
                continue
            name, load, active, sub, desc = parts
            services.append(ServiceStatus(
                name=name,
                state=active,
                enabled=(True if active.lower() == "active" else False),
                active=(active.lower() == "active"),
                loaded=(load.lower() == "loaded"),
                pid=None,
                memory=None,
                cpu_percent=None,
                uptime=None,
            ))
        return ServiceList(services=services, count=len(services))

    def status(self, service: str) -> ServiceStatus:
        """Return status for `service` as ServiceStatus dataclass."""
        out = self.protocol.run_command(f"systemctl show {shlex.quote(service)} --no-page -p ActiveState -p SubState -p LoadState -p MainPID -p MemoryCurrent -p CPUUsageNSec -p ExecMainStartTimestamp", self.state)
        data: dict = {}
        for line in out.splitlines():
            if "=" in line:
                k, v = line.split("=", 1)
                data[k] = v
        active = data.get("ActiveState") or "unknown"
        sub = data.get("SubState") or "unknown"
        pid = int(data.get("MainPID")) if data.get("MainPID") and data.get("MainPID").isdigit() else None
        mem = int(data.get("MemoryCurrent")) if data.get("MemoryCurrent") and data.get("MemoryCurrent").isdigit() else None
        cpu_nsec = int(data.get("CPUUsageNSec")) if data.get("CPUUsageNSec") and data.get("CPUUsageNSec").isdigit() else None
        cpu_percent = (cpu_nsec / 1e9 * 100) if cpu_nsec is not None else None
        uptime = None
        return ServiceStatus(
            name=service,
            state=active,
            enabled=False,
            active=(active == "active"),
            loaded=(data.get("LoadState") == "loaded"),
            pid=pid,
            memory=mem,
            cpu_percent=cpu_percent,
            uptime=uptime,
        )

    def is_running(self, service: str) -> BoolResult:
        """Return BoolResult indicating if `service` is running."""
        try:
            res = self.protocol.exec(f"systemctl is-active {shlex.quote(service)}", self.state)
            running = res.stdout.strip().lower() == "active"
            return BoolResult(key=service, result=running)
        except Exception:
            return BoolResult(key=service, result=False)

    def is_enabled(self, service: str) -> BoolResult:
        """Return BoolResult indicating if `service` is enabled at boot."""
        try:
            res = self.protocol.exec(f"systemctl is-enabled {shlex.quote(service)}", self.state)
            enabled = res.stdout.strip().lower() in ("enabled", "static")
            return BoolResult(key=service, result=enabled)
        except Exception:
            return BoolResult(key=service, result=False)

    def start(self, service: str) -> ServiceStatus:
        """Start `service` and return status."""
        self.protocol.run_command(f"systemctl start {shlex.quote(service)}", self.state)
        return self.status(service)

    def stop(self, service: str) -> ServiceStatus:
        """Stop `service` and return status."""
        self.protocol.run_command(f"systemctl stop {shlex.quote(service)}", self.state)
        return self.status(service)

    def restart(self, service: str) -> ServiceStatus:
        """Restart `service` and return status."""
        self.protocol.run_command(f"systemctl restart {shlex.quote(service)}", self.state)
        return self.status(service)

    def reload(self, service: str) -> ServiceStatus:
        """Reload `service` configuration and return status."""
        self.protocol.run_command(f"systemctl reload {shlex.quote(service)}", self.state)
        return self.status(service)

    def enable(self, service: str) -> ServiceStatus:
        """Enable `service` at boot and return status."""
        self.protocol.run_command(f"systemctl enable {shlex.quote(service)}", self.state)
        return self.status(service)

    def disable(self, service: str) -> ServiceStatus:
        """Disable `service` at boot and return status."""
        self.protocol.run_command(f"systemctl disable {shlex.quote(service)}", self.state)
        return self.status(service)

    def logs(self, service: str, lines: int = 100, follow: bool = False) -> ServiceLogList:
        """Return last `lines` of `service` logs as ServiceLogList dataclass; `follow` is not supported."""
        if follow:
            raise NotImplementedError("Follow streaming logs is not supported in this API")
        out = self.protocol.run_command(f"journalctl -u {shlex.quote(service)} -n {int(lines)} --no-pager --output=short", self.state)
        logs: list[ServiceLog] = []
        for line in out.splitlines():
            # Very lax parsing: try to split timestamp and message
            if not line.strip():
                continue
            ts = None
            msg = line
            try:
                # journalctl short output often starts with 'Jan 01 00:00:00 hostname unit[pid]: message'
                parts = line.split(None, 4)
                # last part is message
                msg = parts[-1]
                ts = datetime.now()
            except Exception:
                pass
            logs.append(ServiceLog(timestamp=ts or datetime.now(), level="info", message=msg, unit=service))
        return ServiceLogList(service=service, logs=logs, count=len(logs))

    def get_config(self, service: str) -> ServiceConfig:
        """Return service configuration content as ServiceConfig dataclass."""
        out = self.protocol.run_command(f"systemctl cat {shlex.quote(service)}", self.state)
        path = f"/etc/systemd/system/{service}.service"
        valid = True
        return ServiceConfig(name=service, path=path, content=out, valid=valid)

    def edit_config(self, service: str, content: str) -> OperationResult:
        """Replace `service` config with `content` and reload systemd."""
        path = f"/etc/systemd/system/{service}.service"
        escaped = content.replace("'", "'\"'\"'")
        try:
            self.protocol.run_command(f"printf '%s' '{escaped}' > {shlex.quote(path)}", self.state)
            self.protocol.run_command("systemctl daemon-reload", self.state)
            return OperationResult(success=True, message=None)
        except Exception as e:
            return OperationResult(success=False, message=str(e))

    def validate_config(self, service: str) -> OperationResult:
        """Validate `service` configuration; return OperationResult."""
        # systemd provides 'systemd-analyze verify' for unit files
        path = f"/etc/systemd/system/{service}.service"
        try:
            self.protocol.run_command(f"systemd-analyze verify {shlex.quote(path)}", self.state)
            return OperationResult(success=True, message=None)
        except Exception as e:
            return OperationResult(success=False, message=str(e))

    def get_pid(self, service: str) -> IDResult:
        """Return PID of `service` or None if not running as IDResult."""
        st = self.status(service)
        return IDResult(key=service, id=st.pid)

    def get_port(self, service: str) -> IDResult:
        """Attempt to discover listening port for `service` and return as IDResult."""
        # try ss to find process owning sockets and extract port; best-effort
        try:
            out = self.protocol.run_command("ss -tulnp", self.state)
            for line in out.splitlines():
                if service in line or f"/{service}" in line:
                    parts = line.split()
                    # Local address is usually in column 4
                    if len(parts) >= 4:
                        addr = parts[3]
                        if ":" in addr:
                            try:
                                port = int(addr.rsplit(":", 1)[1])
                                return IDResult(key=service, id=port)
                            except Exception:
                                continue
        except Exception:
            pass
        return IDResult(key=service, id=None)

    def mask(self, service: str) -> ServiceStatus:
        """Mask `service` to prevent it starting and return status."""
        self.protocol.run_command(f"systemctl mask {shlex.quote(service)}", self.state)
        return self.status(service)

    def unmask(self, service: str) -> ServiceStatus:
        """Unmask `service` and return status."""
        self.protocol.run_command(f"systemctl unmask {shlex.quote(service)}", self.state)
        return self.status(service)

    def dependencies(self, service: str) -> ServiceDependencies:
        """Get service dependencies (requires/systemd) and return ServiceDependencies."""
        out = self.protocol.run_command(f"systemctl list-dependencies {shlex.quote(service)} --no-pager", self.state)
        dependencies: list[ServiceDependency] = []
        dependents: list[str] = []
        for line in out.splitlines():
            line = line.strip()
            if not line:
                continue
            # lines include hierarchical glyphs; we just take service names
            if line.endswith('.service'):
                # choose whether this is a dependency or dependent based on indentation
                if line.startswith('\u2502') or line.startswith(' '):
                    dependencies.append(ServiceDependency(name=line, type='Requires', is_satisfied=True))
                else:
                    dependents.append(line)
        return ServiceDependencies(service=service, dependencies=dependencies, dependents=dependents)