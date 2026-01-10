"""Process actions."""
from __future__ import annotations

import time
from typing import List

from remote_machine.models.remote_state import RemoteState
from remote_machine.protocols.ssh import SSHProtocol
from remote_machine.errors.error_mapper import ErrorMapper

from linux_parsers.parsers.process.ps import parse_ps_aux

from datetime import datetime

from linux_parsers.parsers.system.free import parse_free_btlv

from remote_machine.models.common_types import BoolResult, OperationResult, CountResult
from remote_machine.models.process_types import (
    ProcessInfo,
    MemoryUsage,
    CPUUsage,
    ProcessResourceUsage,
    ProcessWaitResult,
    ProcessChildren,
    ProcessParent,
)


class PSAction:
    """Process management operations."""

    def __init__(self, protocol: SSHProtocol, state: RemoteState):
        """Initialize process actions.

        Args:
            protocol: SSH protocol instance
            state: Remote execution state
        """
        self.protocol = protocol
        self.state = state

    def _run(self, cmd: str) -> str:
        """Run a command and raise mapped errors."""
        result = self.protocol.exec(cmd, self.state)
        ErrorMapper.raise_if_error(result)
        return result.stdout

    def list(self) -> List[ProcessInfo]:
        """Return list of process info dataclasses (uses linux_parsers)."""
        output = self._run("ps aux")
        parsed = parse_ps_aux(output)

        return [
            ProcessInfo(
                pid=int(p.get("pid") or 0),
                ppid=int(p.get("ppid") or 0),
                name=(cmd := p.get("command") or "") and cmd.split()[0] or "",
                state=p.get("stat") or "",
                user=p.get("user") or p.get("USER") or "",
                cpu_percent=float(p.get("cpu") or 0.0),
                memory_percent=float(p.get("mem") or 0.0),
                memory_rss=int(p.get("rss") or 0),
                memory_vms=int(p.get("vsz") or 0),
                started=datetime.fromtimestamp(0),
                command=cmd,
            )
            for p in parsed
        ]

    def list_by_user(self, user: str) -> List[ProcessInfo]:
        """Return processes for `user` as a list of ProcessInfo dataclasses. Args: user"""
        return [p for p in self.list() if p.user == user]

    def kill(self, pid: int, signal: int = 15) -> None:
        """Send `signal` to `pid`. Args: pid, signal"""
        self._run(f"kill -{int(signal)} {int(pid)}")

    def find(self, name: str) -> List[ProcessInfo]:
        """Return processes matching `name` as a list of ProcessInfo dataclasses. Args: name"""
        lower = name.lower()
        return [p for p in self.list() if lower in (p.command or "").lower()]

    def get_info(self, pid: int) -> ProcessInfo | None:
        """Return process details for `pid` or None if not found. Args: pid"""
        return [p for p in self.list() if p.pid == pid][0]

    def is_running(self, pid: int) -> BoolResult:
        """Return BoolResult indicating if `pid` is running."""
        try:
            res = self.protocol.exec(f"kill -0 {int(pid)}", self.state)
            return BoolResult(key=str(pid), result=(res.exit_code == 0))
        except Exception:
            # Fallback to /proc check
            res = self.protocol.exec(f"test -d /proc/{int(pid)}", self.state)
            return BoolResult(key=str(pid), result=(res.exit_code == 0))

    def wait(self, pid: int, timeout: int | None = None) -> ProcessWaitResult:
        """Wait for `pid` (optional timeout) and return ProcessWaitResult."""

        start = time.time()
        while True:
            r = self.protocol.exec(f"kill -0 {int(pid)}", self.state)
            if r.exit_code != 0:
                # process gone
                return ProcessWaitResult(pid=int(pid), exit_code=0, timed_out=False)
            if timeout is not None and (time.time() - start) >= timeout:
                return ProcessWaitResult(pid=int(pid), exit_code=-1, timed_out=True)
            time.sleep(0.2)

    def count(self, user: str | None = None) -> CountResult:
        """Return a number of processes (optionally for `user`)."""
        ps = self.list()
        ps_count = len(ps)
        if user:
            ps_count = sum(1 for p in ps if p.user == user)
        return CountResult(key=user, count=ps_count)

    def memory_usage(self, pid: int | None = None):
        """Return MemoryUsage system-wide or ProcessResourceUsage for pid."""
        if pid is None:
            mem = parse_free_btlv(self._run("free -btlv")).get("Mem", {})
            total = int(mem.get("total") or 0)
            used = int(mem.get("used") or 0)
            swap_total = int(mem.get("swap_total") or 0)
            swap_used = int(mem.get("swap_used") or 0)
            return MemoryUsage(
                total=total,
                available=int(mem.get("available") or 0),
                used=used,
                free=int(mem.get("free") or 0),
                percent=(used / total * 100) if total else 0.0,
                buffers=int(mem.get("buffers") or 0),
                cached=int(mem.get("cached") or 0),
                swap_total=swap_total,
                swap_used=swap_used,
                swap_free=max(swap_total - swap_used, 0),
                swap_percent=(swap_used / swap_total * 100) if swap_total else 0.0,
            )

        out = self._run(f"ps -o pid=,rss=,vsz=,pcpu= -p {pid}").split()
        return ProcessResourceUsage(
            pid=pid,
            cpu_percent=0.0,
            memory_rss=int(out[1]) * 1024 if len(out) > 1 else 0,
            memory_vms=int(out[2]) * 1024 if len(out) > 2 else 0
        )

    def cpu_usage(self, pid: int | None = None):
        """Return CPU usage system-wide or per-process."""
        if pid is None:
            # parse /proc/stat for aggregate CPU times
            out = self._run("cat /proc/stat")
            lines = [l for l in out.splitlines() if l.startswith("cpu ")]
            if not lines:
                return CPUUsage(0, 0, 0, 0, 0, 0, 0.0, 0.0, 0.0, 0.0, 0)
            values = lines[0].split()[1:]
            vals = [float(v) for v in values]
            user_time = vals[0]
            system_time = vals[2] if len(vals) > 2 else 0.0
            idle_time = vals[3] if len(vals) > 3 else 0.0
            iowait_time = vals[4] if len(vals) > 4 else 0.0
            irq_time = vals[5] if len(vals) > 5 else 0.0
            softirq_time = vals[6] if len(vals) > 6 else 0.0
            total = sum(vals)
            user_percent = (user_time / total * 100) if total else 0.0
            system_percent = (system_time / total * 100) if total else 0.0
            idle_percent = (idle_time / total * 100) if total else 0.0
            iowait_percent = (iowait_time / total * 100) if total else 0.0
            return CPUUsage(
                user_time=user_time,
                system_time=system_time,
                idle_time=idle_time,
                iowait_time=iowait_time,
                irq_time=irq_time,
                softirq_time=softirq_time,
                user_percent=user_percent,
                system_percent=system_percent,
                idle_percent=idle_percent,
                iowait_percent=iowait_percent,
                count=self.cpu_count() if hasattr(self, "cpu_count") else 1,
            )
        else:
            # per-process use ps to get %CPU
            out = self._run(f"ps -o pid=,rss=,vsz=,pcpu= -p {int(pid)}")
            parts = out.strip().split()
            if not parts:
                return ProcessResourceUsage(pid=int(pid), cpu_percent=0.0, memory_rss=0, memory_vms=0)
            try:
                cpu = float(parts[3]) if len(parts) > 3 else 0.0
            except Exception:
                cpu = 0.0
            try:
                rss = int(parts[1]) * 1024 if len(parts) > 1 else 0
                vsz = int(parts[2]) * 1024 if len(parts) > 2 else 0
            except Exception:
                rss = vsz = 0
            return ProcessResourceUsage(pid=int(pid), cpu_percent=cpu, memory_rss=rss, memory_vms=vsz)

    def get_children(self, pid: int) -> ProcessChildren:
        """Return child PIDs of `pid`. Args: pid"""
        children = [p.pid for p in self.list() if p.ppid == int(pid)]
        return ProcessChildren(pid=int(pid), children=children, count=len(children))

    def get_parent(self, pid: int) -> ProcessParent:
        """Return parent PID for `pid` or None. Args: pid"""
        for p in self.list():
            if p.pid == int(pid):
                return ProcessParent(pid=int(pid), parent=p.ppid if p.ppid != 0 else None)
        return ProcessParent(pid=int(pid), parent=None)

    def nice(self, pid: int, priority: int) -> OperationResult:
        """Set a nice ` priority ` for `pid`. Args: pid, priority"""
        try:
            self._run(f"renice {int(priority)} -p {int(pid)}")
            return OperationResult(success=True, message=None)
        except Exception as e:
            return OperationResult(success=False, message=str(e))
