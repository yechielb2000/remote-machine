"""System actions."""

from __future__ import annotations

from typing import List
from datetime import datetime, timedelta

from remote_machine.models.remote_state import RemoteState
from remote_machine.protocols.ssh import SSHProtocol
from remote_machine.models.system_types import (
    UnameInfo,
    UptimeInfo,
    MemoryInfo,
    CPUInfo,
    LoadAverage,
    UserInfo,
    OSRelease,
    SystemInfo,
)

from linux_parsers.parsers.system.proc_uptime import parse_proc_uptime_file
from linux_parsers.parsers.system.etc_os_release import parse_etc_os_release_file
from linux_parsers.parsers.system.free import parse_free_btlv
from linux_parsers.parsers.system.proc_cpuinfo import parse_proc_cpuinfo_file
from linux_parsers.parsers.session.who import parse_who_a


class SYSAction:
    """System and machine operations."""

    def __init__(self, protocol: SSHProtocol, state: RemoteState):
        """Initialize system actions.

        Args:
            protocol: SSH protocol instance
            state: Remote execution state
        """
        self.protocol = protocol
        self.state = state

    def _run(self, command: str):
        """Run a command and raise mapped errors if it fails."""
        result = self.protocol.exec(command, self.state)
        ErrorMapper.raise_if_error(result)
        return result.stdout

    def info(self) -> SystemInfo:
        """Get a consolidated system information dataclass."""
        return SystemInfo(
            hostname=self.hostname(),
            os_release=self.os_release(),
            uname=self.uname(),
            uptime=self.uptime(),
            kernel_version=self.kernel_version(),
            cpu_info=self.cpu_info(),
            memory_info=self.memory_info(),
            load_average=self.load_average(),
        )

    def uname(self) -> UnameInfo:
        """Get system name and information as a dataclass."""
        sysname = self.protocol.run_command("uname -s", self.state)
        nodename = self.protocol.run_command("uname -n", self.state)
        release = self.protocol.run_command("uname -r", self.state)
        version = self.protocol.run_command("uname -v", self.state)
        machine = self.protocol.run_command("uname -m", self.state)

        return UnameInfo(
            sysname=sysname,
            nodename=nodename,
            release=release,
            version=version,
            machine=machine,
        )

    def uptime(self) -> UptimeInfo:
        """Get system uptime using /proc/uptime parser."""
        out = self.protocol.run_command("cat /proc/uptime", self.state)

        parsed = parse_proc_uptime_file(out)

        if parsed and "uptime" in parsed:
            seconds = float(parsed["uptime"])
        else:
            # Fallback: first value in /proc/uptime
            parts = out.split()
            seconds = float(parts[0]) if parts else 0.0

        uptime_delta = timedelta(seconds=int(seconds))
        return UptimeInfo(
            uptime=uptime_delta,
            boot_time=datetime.now() - uptime_delta,
            seconds=seconds,
            days=int(seconds // 86400),
            hours=int((seconds % 86400) // 3600),
            minutes=int((seconds % 3600) // 60),
        )

    def hostname(self) -> str:
        """Get system hostname."""
        return self.protocol.run_command("hostname", self.state)

    def set_hostname(self, hostname: str) -> None:
        """Set system hostname."""
        self.protocol.run_command(f"hostname {hostname}", self.state)

    def kernel_version(self) -> str:
        """Get kernel version string."""
        return self.protocol.run_command("uname -r", self.state)

    def os_release(self) -> OSRelease:
        """Parse /etc/os-release."""
        out = self.protocol.run_command("cat /etc/os-release", self.state)
        data = parse_etc_os_release_file(out)

        return OSRelease(
            name=data.get("NAME", ""),
            version=data.get("VERSION", ""),
            version_id=data.get("VERSION_ID", ""),
            pretty_name=data.get("PRETTY_NAME", data.get("NAME", "")),
            id=data.get("ID", ""),
            id_like=data.get("ID_LIKE"),
            home_url=data.get("HOME_URL"),
            bug_report_url=data.get("BUG_REPORT_URL"),
            support_url=data.get("SUPPORT_URL"),
        )

    def memory_info(self) -> MemoryInfo:
        """Parse memory info from `free -btlv`."""
        out = self.protocol.run_command("free -btlv", self.state)
        data = parse_free_btlv(out)

        mem = data.get("Mem", {})
        swap = data.get("Swap", {})

        total = int(mem.get("total") or 0)
        used = int(mem.get("used") or 0)
        free = int(mem.get("free") or 0)
        available = int(mem.get("available") or 0)
        buffers = int(mem.get("cache") or 0)
        cached = 0  # not provided separately by `free -btlv`

        swap_total = int(swap.get("total") or 0)
        swap_used = int(swap.get("used") or 0)

        percent = (used / total * 100.0) if total else 0.0
        swap_free = swap_total - swap_used
        swap_percent = (swap_used / swap_total * 100.0) if swap_total else 0.0

        def human(n: int) -> str:
            for unit in ("B", "KB", "MB", "GB", "TB"):
                if n < 1024:
                    return f"{n}{unit}"
                n //= 1024
            return f"{n}PB"

        return MemoryInfo(
            total=total,
            available=available,
            used=used,
            free=free,
            percent=percent,
            buffers=buffers,
            cached=cached,
            swap_total=swap_total,
            swap_used=swap_used,
            swap_free=swap_free,
            swap_percent=swap_percent,
            human_total=human(total),
            human_available=human(available),
            human_used=human(used),
        )

    def cpu_info(self) -> List[CPUInfo]:
        """Parse /proc/cpuinfo and return per-CPU info."""
        processors = parse_proc_cpuinfo_file(
            self.protocol.run_command("cat /proc/cpuinfo"), self.state
        )

        cpu_infos: List[CPUInfo] = []

        total_threads = len(processors)

        for cpu in processors:

            cpu_infos.append(
                CPUInfo(
                    processor=cpu.get("processor", "0"),
                    vendor_id=cpu.get("vendor_id", ""),
                    model_name=cpu.get("model name", ""),
                    cores=int(cpu.get("cpu cores", cpu.get("cores", "1"))),
                    threads=total_threads,
                    cpu_mhz=float(cpu.get("cpu mhz", cpu.get("mhz", "0"))),
                    l1_cache=cpu.get("l1 cache", ""),
                    l2_cache=cpu.get("l2 cache", ""),
                    l3_cache=cpu.get("cache size", ""),
                    stepping=int(cpu["stepping"]) if cpu.get("stepping", "").isdigit() else None,
                    flags=cpu.get("flags", "").split(),
                )
            )

        return cpu_infos

    def cpu_count(self) -> int:
        """Return the number of logical CPU threads."""
        out = self.protocol.run_command("cat /proc/cpuinfo", self.state)
        return out.count("processor\t:") or out.count("processor :") or out.count("processor")

    def load_average(self) -> LoadAverage:
        out = self.protocol.run_command("cat /proc/loadavg", self.state)

        parts = out.split()
        running_total = parts[3] if len(parts) > 3 else "0/0"
        running, total = running_total.split("/") if "/" in running_total else ("0", "0")

        return LoadAverage(
            one_minute=float(parts[0]) if len(parts) > 0 else 0.0,
            five_minutes=float(parts[1]) if len(parts) > 1 else 0.0,
            fifteen_minutes=float(parts[2]) if len(parts) > 2 else 0.0,
            running_processes=int(running),
            total_processes=int(total),
        )

    def timezone(self) -> str:
        """Get system timezone via timedatectl or /etc/localtime link (best-effort)."""
        try:
            out = self.protocol.run_command("timedatectl show -p Timezone --value", self.state)
            if out:
                return out
        except Exception:
            pass

        # fallback to readlink /etc/localtime
        try:
            out = self.protocol.run_command("readlink -f /etc/localtime", self.state)
            parts = out.split("zoneinfo/")
            if len(parts) == 2:
                return parts[1]
        except Exception:
            pass

        return ""

    def reboot(self, delay: int = 0) -> None:
        """Reboot the system (uses shutdown command with +delay)."""
        cmd = "reboot" if delay == 0 else f"shutdown -r +{int(delay // 60)}"
        self.protocol.run_command(cmd, self.state)

    def shutdown(self, delay: int = 0) -> None:
        """Shutdown the system (uses shutdown command with +delay)."""
        cmd = "shutdown -h now" if delay == 0 else f"shutdown -h +{int(delay // 60)}"
        self.protocol.run_command(cmd, self.state)

    def dmesg(self, lines: int = 100) -> str:
        """Return the last `lines` of kernel messages (best-effort)."""
        out = self.protocol.run_command(f"dmesg --color=never | tail -n {int(lines)}", self.state)
        return out

    def logged_in_users(self) -> List[UserInfo]:
        """Get currently logged in users using `who -a`."""
        parsed = parse_who_a(self.protocol.run_command("who -a"), self.state)

        users: List[UserInfo] = []

        for record in parsed.get("users_records", []):
            try:
                login_time = datetime.strptime(
                    f"{record['date']} {record['time']}", "%Y-%m-%d %H:%M"
                )
            except Exception:
                login_time = datetime.now()

            users.append(
                UserInfo(
                    username=record.get("event", ""),
                    tty=record.get("tty", ""),
                    hostname=record.get("from", ""),
                    login_time=login_time,
                    idle_time=None,
                )
            )

        return users

    def last_login(self, username: str | None = None) -> List:
        """Return last login history via `last` (not fully parsed)."""
        cmd = "last -w" + (f" {username}" if username else "")
        out = self.protocol.run_command(cmd, self.state)
        # returning raw lines for now
        lines = [l for l in out.splitlines() if l and not l.startswith("wtmp")]
        return lines
