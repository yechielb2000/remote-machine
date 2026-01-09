"""System actions."""
from __future__ import annotations

from typing import List
from datetime import datetime, timedelta

from remote_machine.models.remote_state import RemoteState
from remote_machine.protocols.ssh import SSHProtocol
from remote_machine.errors.error_mapper import ErrorMapper
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

try:
    from linux_parsers.parsers.system.proc_uptime import parse as parse_proc_uptime  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    parse_proc_uptime = None

try:
    from linux_parsers.parsers.system.etc_os_release import parse as parse_etc_os_release  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    parse_etc_os_release = None

try:
    from linux_parsers.parsers.system.free import parse_free as parse_free  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    parse_free = None

try:
    from linux_parsers.parsers.system.proc_cpuinfo import parse as parse_proc_cpuinfo  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    parse_proc_cpuinfo = None

try:
    from linux_parsers.parsers.system.proc_loadavg import parse as parse_proc_loadavg  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    parse_proc_loadavg = None


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
        sysname = self._run("uname -s").strip()
        nodename = self._run("uname -n").strip()
        release = self._run("uname -r").strip()
        version = self._run("uname -v").strip()
        machine = self._run("uname -m").strip()

        return UnameInfo(
            sysname=sysname,
            nodename=nodename,
            release=release,
            version=version,
            machine=machine,
        )

    def uptime(self) -> UptimeInfo:
        """Get system uptime, prefer linux_parsers if available."""
        out = self._run("cat /proc/uptime").strip()

        # Try runtime import to allow tests to monkeypatch sys.modules after import
        seconds = None
        if parse_proc_uptime is not None:
            parsed = parse_proc_uptime(out)
        else:
            try:
                import importlib

                mod = importlib.import_module("linux_parsers.parsers.system.proc_uptime")
                _parse = getattr(mod, "parse", None) or getattr(mod, "parse_proc_uptime_file", None)
            except Exception:
                _parse = None

            parsed = _parse(out) if _parse else None
        # Accept common key names
        for k in ("uptime", "uptime_seconds", "seconds", "secs", "value"):
            if isinstance(parsed, dict) and k in parsed:
                seconds = float(parsed[k])
                break

        if seconds is None:
            parts = out.split()
            seconds = float(parts[0]) if parts else 0.0

        uptime_delta = timedelta(seconds=int(seconds))
        boot_time = datetime.now() - uptime_delta

        days = int(seconds // 86400)
        hours = int((seconds % 86400) // 3600)
        minutes = int((seconds % 3600) // 60)

        return UptimeInfo(
            uptime=uptime_delta,
            boot_time=boot_time,
            seconds=seconds,
            days=days,
            hours=hours,
            minutes=minutes,
        )

    def hostname(self) -> str:
        """Get system hostname."""
        return self._run("hostname").strip()

    def set_hostname(self, hostname: str) -> None:
        """Set system hostname."""
        self._run(f"hostname {hostname}")

    def kernel_version(self) -> str:
        """Get kernel version string."""
        return self._run("uname -r").strip()

    def os_release(self) -> OSRelease:
        """Parse /etc/os-release, prefer linux_parsers when available."""
        out = self._run("cat /etc/os-release")

        # Try runtime import to allow tests to monkeypatch sys.modules after import
        data = {}
        if parse_etc_os_release is not None:
            parsed = parse_etc_os_release(out)
        else:
            try:
                import importlib

                mod = importlib.import_module("linux_parsers.parsers.system.etc_os_release")
                _parse = getattr(mod, "parse", None) or getattr(mod, "parse_etc_os_release_file", None)
            except Exception:
                _parse = None

            parsed = _parse(out) if _parse else None
        if parsed:
            # Normalized keys
            data["name"] = parsed.get("NAME") or parsed.get("name") or parsed.get("pretty_name") or parsed.get("id") or ""
            data["version"] = parsed.get("VERSION") or parsed.get("version") or parsed.get("version_id") or ""
            data["version_id"] = parsed.get("VERSION_ID") or parsed.get("version_id") or parsed.get("version") or ""
            data["pretty_name"] = parsed.get("PRETTY_NAME") or parsed.get("pretty_name") or data.get("name", "")
            data["id"] = parsed.get("ID") or parsed.get("id") or ""
            data["id_like"] = parsed.get("ID_LIKE") or parsed.get("id_like")
            data["home_url"] = parsed.get("HOME_URL") or parsed.get("home_url")
            data["bug_report_url"] = parsed.get("BUG_REPORT_URL") or parsed.get("bug_report_url")
            data["support_url"] = parsed.get("SUPPORT_URL") or parsed.get("support_url")

        if not data:
            for line in out.splitlines():
                if "=" not in line:
                    continue
                k, v = line.split("=", 1)
                v = v.strip().strip('"')
                data[k.lower()] = v

        return OSRelease(
            name=data.get("name", ""),
            version=data.get("version", ""),
            version_id=data.get("version_id", ""),
            pretty_name=data.get("pretty_name", data.get("name", "")),
            id=data.get("id", ""),
            id_like=data.get("id_like"),
            home_url=data.get("home_url"),
            bug_report_url=data.get("bug_report_url"),
            support_url=data.get("support_url"),
        )

    def memory_info(self) -> MemoryInfo:
        """Parse memory info (prefer linux_parsers when available)."""
        out = self._run("free -b")

        # Try runtime import to allow tests to monkeypatch sys.modules after import
        if parse_free is not None:
            parsed = parse_free(out)
        else:
            try:
                import importlib

                mod = importlib.import_module("linux_parsers.parsers.system.free")
                _parse = getattr(mod, "parse_free", None) or getattr(mod, "parse_free_btlv", None) or getattr(mod, "parse", None)
            except Exception:
                _parse = None

            parsed = _parse(out) if _parse else None

        if parsed:
            # Accept multiple key shapes
            if isinstance(parsed, dict) and "Mem" in parsed:
                mem_parsed = parsed.get("Mem", {})
            else:
                mem_parsed = parsed

            total = int(mem_parsed.get("total") or mem_parsed.get("mem_total") or mem_parsed.get("memory_total") or 0)
            available = int(mem_parsed.get("available") or mem_parsed.get("mem_available") or mem_parsed.get("memory_available") or 0)
            used = int(mem_parsed.get("used") or mem_parsed.get("mem_used") or (total - available if total else 0))
            free = int(mem_parsed.get("free") or mem_parsed.get("mem_free") or 0)
            buffers = int(mem_parsed.get("buffers") or mem_parsed.get("buff_cache") or 0)
            cached = int(mem_parsed.get("cached") or 0)
            swap_total = int(mem_parsed.get("swap_total") or mem_parsed.get("swap_total_bytes") or 0)
            swap_used = int(mem_parsed.get("swap_used") or mem_parsed.get("swap_used_bytes") or 0)
        else:
            # fallback to `free -b` parsing
            lines = [l for l in out.splitlines() if l.strip()]
            mem = {}
            swap = {}
            for line in lines:
                if line.startswith("Mem:") or line.startswith("Mem "):
                    parts = line.split()
                    # Mem: total used free shared buff/cache available
                    if len(parts) >= 7:
                        mem["total"] = int(parts[1])
                        mem["used"] = int(parts[2])
                        mem["free"] = int(parts[3])
                        mem["buffers"] = int(parts[5])
                        mem["available"] = int(parts[6])
                if line.startswith("Swap:") or line.startswith("Swap "):
                    parts = line.split()
                    if len(parts) >= 4:
                        swap["total"] = int(parts[1])
                        swap["used"] = int(parts[2])
                        swap["free"] = int(parts[3])

            total = mem.get("total", 0)
            available = mem.get("available", 0)
            used = mem.get("used", total - available if total else 0)
            free = mem.get("free", 0)
            buffers = mem.get("buffers", 0)
            cached = 0
            swap_total = swap.get("total", 0)
            swap_used = swap.get("used", 0)

        percent = (used / total * 100) if total else 0.0
        swap_free = swap_total - swap_used if swap_total else 0
        swap_percent = (swap_used / swap_total * 100) if swap_total else 0.0

        def human(n: int) -> str:
            # simple human readable in bytes
            for unit in ["B", "KB", "MB", "GB", "TB"]:
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

    def cpu_info(self) -> CPUInfo:
        """Parse /proc/cpuinfo (prefer linux_parsers when available)."""
        out = self._run("cat /proc/cpuinfo")

        # Try runtime import to allow tests to monkeypatch sys.modules after import
        if parse_proc_cpuinfo is not None:
            parsed = parse_proc_cpuinfo(self._run("cat /proc/cpuinfo"))
        else:
            try:
                import importlib

                mod = importlib.import_module("linux_parsers.parsers.system.proc_cpuinfo")
                _parse = getattr(mod, "parse", None) or getattr(mod, "parse_proc_cpuinfo_file", None)
            except Exception:
                _parse = None

            parsed = _parse(self._run("cat /proc/cpuinfo")) if _parse else None

        if parsed:
            # linux_parsers may return a list of processors or a dict with processors list or summary
            if isinstance(parsed, list):
                processors = parsed
            else:
                processors = parsed.get("processors") or parsed.get("cpus") or parsed.get("processors_list") or parsed

            if isinstance(processors, list) and processors:
                first = processors[0]
                threads = len(processors)
            else:
                first = processors if isinstance(processors, dict) else {}
                # if processors not provided, infer threads from count
                threads = int(first.get("threads", 1)) if isinstance(first, dict) else 1

            cores = int(first.get("cpu cores", first.get("cores", threads))) if (isinstance(first, dict) and (first.get("cpu cores") or first.get("cores"))) else threads
            model = (first.get("model name") or first.get("model") or "") if isinstance(first, dict) else ""
            vendor = (first.get("vendor_id") or first.get("vendor") or "") if isinstance(first, dict) else ""
            mhz = float(first.get("cpu mhz") or first.get("mhz") or 0.0) if isinstance(first, dict) else 0.0
            flags = (first.get("flags") or "").split() if isinstance(first, dict) else []
            stepping = int(first.get("stepping")) if (isinstance(first, dict) and first.get("stepping") and str(first.get("stepping")).isdigit()) else None

            l1_cache = first.get("l1 cache", "") if isinstance(first, dict) else ""
            l2_cache = first.get("l2 cache", "") if isinstance(first, dict) else ""
            l3_cache = first.get("cache size", "") if isinstance(first, dict) else ""

            return CPUInfo(
                processor=str(first.get("processor", "0")) if isinstance(first, dict) else "0",
                vendor_id=vendor,
                model_name=model,
                cores=cores,
                threads=threads,
                cpu_mhz=mhz,
                l1_cache=l1_cache,
                l2_cache=l2_cache,
                l3_cache=l3_cache,
                stepping=stepping,
                flags=flags,
            )

        # Fallback to local parsing
        out = self._run("cat /proc/cpuinfo")
        processors = []
        current = {}
        for line in out.splitlines():
            if not line.strip():
                if current:
                    processors.append(current)
                    current = {}
                continue
            if ":" in line:
                k, v = line.split(":", 1)
                current[k.strip().lower()] = v.strip()
        if current:
            processors.append(current)

        threads = len(processors)
        first = processors[0] if processors else {}
        cores = int(first.get("cpu cores", threads)) if first.get("cpu cores") else threads
        model = first.get("model name", "")
        vendor = first.get("vendor_id", "")
        mhz = float(first.get("cpu mhz", "0.0")) if first.get("cpu mhz") else 0.0
        flags = first.get("flags", "").split()
        stepping = int(first.get("stepping")) if first.get("stepping") and first.get("stepping").isdigit() else None

        # cache fields are not always available; set as empty strings
        l1_cache = first.get("l1 cache", "")
        l2_cache = first.get("l2 cache", "")
        l3_cache = first.get("cache size", "")

        return CPUInfo(
            processor=first.get("processor", "0"),
            vendor_id=vendor,
            model_name=model,
            cores=cores,
            threads=threads,
            cpu_mhz=mhz,
            l1_cache=l1_cache,
            l2_cache=l2_cache,
            l3_cache=l3_cache,
            stepping=stepping,
            flags=flags,
        )

    def cpu_count(self) -> int:
        """Return the number of logical CPU threads."""
        out = self._run("cat /proc/cpuinfo")
        return out.count("processor\t:") or out.count("processor :") or out.count("processor")

    def load_average(self) -> LoadAverage:
        """Parse /proc/loadavg (prefer linux_parsers when available)."""
        out = self._run("cat /proc/loadavg").strip()

        # Try runtime import to allow tests to monkeypatch sys.modules after import
        if parse_proc_loadavg is not None:
            parsed = parse_proc_loadavg(out)
        else:
            try:
                import importlib

                mod = importlib.import_module("linux_parsers.parsers.system.proc_loadavg")
                _parse = getattr(mod, "parse", None) or getattr(mod, "parse_proc_loadavg_file", None)
            except Exception:
                _parse = None

            parsed = _parse(out) if _parse else None

        if parsed:
            one = float(parsed.get("one") or parsed.get("1min") or parsed.get("load_1") or parsed.get("load_1m") or 0.0)
            five = float(parsed.get("five") or parsed.get("5min") or parsed.get("load_5") or 0.0)
            fifteen = float(parsed.get("fifteen") or parsed.get("15min") or parsed.get("load_15") or 0.0)
            running = int(parsed.get("running_processes") or parsed.get("running") or parsed.get("procs_running") or 0)
            total = int(parsed.get("total_processes") or parsed.get("total") or parsed.get("procs_total") or 0)
            return LoadAverage(one_minute=one, five_minutes=five, fifteen_minutes=fifteen, running_processes=running, total_processes=total)

        parts = out.split()
        one = float(parts[0]) if len(parts) > 0 else 0.0
        five = float(parts[1]) if len(parts) > 1 else 0.0
        fifteen = float(parts[2]) if len(parts) > 2 else 0.0
        running_total = parts[3] if len(parts) > 3 else "0/0"
        running, total = running_total.split("/") if "/" in running_total else ("0", "0")

        return LoadAverage(
            one_minute=one,
            five_minutes=five,
            fifteen_minutes=fifteen,
            running_processes=int(running),
            total_processes=int(total),
        )

    def timezone(self) -> str:
        """Get system timezone via timedatectl or /etc/localtime link (best-effort)."""
        try:
            out = self._run("timedatectl show -p Timezone --value").strip()
            if out:
                return out
        except Exception:
            pass

        # fallback to readlink /etc/localtime
        try:
            out = self._run("readlink -f /etc/localtime").strip()
            parts = out.split("zoneinfo/")
            if len(parts) == 2:
                return parts[1]
        except Exception:
            pass

        return ""

    def reboot(self, delay: int = 0) -> None:
        """Reboot the system (uses shutdown command with +delay)."""
        cmd = "reboot" if delay == 0 else f"shutdown -r +{int(delay // 60)}"
        self._run(cmd)

    def shutdown(self, delay: int = 0) -> None:
        """Shutdown the system (uses shutdown command with +delay)."""
        cmd = "shutdown -h now" if delay == 0 else f"shutdown -h +{int(delay // 60)}"
        self._run(cmd)

    def dmesg(self, lines: int = 100) -> str:
        """Return the last `lines` of kernel messages (best-effort)."""
        out = self._run(f"dmesg --color=never | tail -n {int(lines)}")
        return out

    def logged_in_users(self) -> List[UserInfo]:
        """Get currently logged in users using `who` output."""
        out = self._run("who --no-headers -u")
        users: List[UserInfo] = []
        for line in out.splitlines():
            parts = line.split()
            if len(parts) < 3:
                continue
            username = parts[0]
            tty = parts[1]
            # date + time are usually parts[2] and parts[3]
            time_parts = parts[2:4]
            try:
                login_time = datetime.strptime(" ".join(time_parts), "%Y-%m-%d %H:%M")
            except Exception:
                # fallback to current time
                login_time = datetime.now()
            users.append(UserInfo(username=username, tty=tty, hostname="", login_time=login_time, idle_time=None))
        return users

    def last_login(self, username: str | None = None) -> List:
        """Return last login history via `last` (not fully parsed)."""
        cmd = "last -w" + (f" {username}" if username else "")
        out = self._run(cmd)
        # returning raw lines for now
        lines = [l for l in out.splitlines() if l and not l.startswith("wtmp")] 
        return lines