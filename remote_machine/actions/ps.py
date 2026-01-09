"""Process actions."""
from __future__ import annotations

from remote_machine.models.remote_state import RemoteState
from remote_machine.protocols.ssh import SSHProtocol
from remote_machine.utils.error_mapper import ErrorMapper


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

    def list(self) -> list[dict]:
        """Return list of process info dicts."""
        cmd = "ps aux"
        try:
            from linux_parsers.parsers.process.ps import parse_ps_aux  # type: ignore
            parsed = parse_ps_aux(self._run(cmd))
            if isinstance(parsed, list):
                return parsed
        except Exception:
            pass

        # Fallback: basic parsing of ps aux
        out = self._run(cmd)
        results = []
        lines = [l for l in out.splitlines() if l.strip()]
        if not lines:
            return results
        # header columns
        header = lines[0]
        cols = header.split()
        for line in lines[1:]:
            parts = line.split(None, len(cols) - 1)
            entry = {cols[i]: parts[i] for i in range(min(len(cols), len(parts)))}
            results.append(entry)
        return results

    def list_by_user(self, user: str) -> list[dict]:
        """Return processes for `user` as list of dicts. Args: user"""
        ps = self.list()
        return [p for p in ps if p.get("USER") == user or p.get("user") == user]

    def kill(self, pid: int, signal: int = 15) -> None:
        """Send `signal` to `pid`. Args: pid, signal"""
        self._run(f"kill -{int(signal)} {int(pid)}")

    def find(self, name: str) -> list[dict]:
        """Return processes matching `name`. Args: name"""
        ps = self.list()
        lower = name.lower()
        return [p for p in ps if lower in (p.get("COMMAND", "") or p.get("command", "")).lower()]

    def get_info(self, pid: int) -> dict:
        """Return process details dict for `pid`. Args: pid"""
        ps = self.list()
        for p in ps:
            try:
                ppid = int(p.get("PID") or p.get("pid"))
            except Exception:
                ppid = None
            if ppid == int(pid):
                return p
        return {}

    def is_running(self, pid: int) -> bool:
        """Return True if `pid` is running. Args: pid"""
        # Stub implementation - will be populated in Phase 2
        return False

    def wait(self, pid: int, timeout: int | None = None) -> int:
        """Wait for `pid` (optional timeout) and return exit code. Args: pid, timeout"""
        # Stub implementation - will be populated in Phase 2
        return 0

    def count(self, user: str | None = None) -> int:
        """Return number of processes (optionally for `user`). Args: user"""
        # Stub implementation - will be populated in Phase 2
        return 0

    def memory_usage(self, pid: int | None = None) -> dict:
        """Return memory usage dict for `pid` or all processes. Args: pid"""
        # Stub implementation - will be populated in Phase 2
        return {}

    def cpu_usage(self, pid: int | None = None) -> dict:
        """Return CPU usage dict for `pid` or all processes. Args: pid"""
        # Stub implementation - will be populated in Phase 2
        return {}

    def get_children(self, pid: int) -> list[int]:
        """Return child PIDs of `pid`. Args: pid"""
        # Stub implementation - will be populated in Phase 2
        return []

    def get_parent(self, pid: int) -> int | None:
        """Return parent PID for `pid` or None. Args: pid"""
        # Stub implementation - will be populated in Phase 2
        return None

    def nice(self, pid: int, priority: int) -> None:
        """Set nice `priority` for `pid`. Args: pid, priority"""
        # Stub implementation - will be populated in Phase 2
        pass
