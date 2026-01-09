"""Tests that SYSAction prefers linux_parsers when available."""
import sys
import types

from remote_machine.models.remote_state import RemoteState
from remote_machine.models.command_result import CommandResult


class FakeProtocol:
    def __init__(self, responses: dict[str, str]):
        self.responses = responses

    def exec(self, command: str, state: RemoteState) -> CommandResult:
        for key, out in self.responses.items():
            if key in command:
                return CommandResult(command=command, stdout=out, stderr="", exit_code=0)
        return CommandResult(command=command, stdout="", stderr="", exit_code=0)


def _mk_pkg_hierarchy(monkeypatch, package_path: str, module: types.ModuleType):
    """Ensure parent package modules exist in sys.modules for a nested module path."""
    parts = package_path.split('.')
    for i in range(1, len(parts)):
        pkg = '.'.join(parts[:i])
        if pkg not in sys.modules:
            monkeypatch.setitem(sys.modules, pkg, types.ModuleType(pkg))
    monkeypatch.setitem(sys.modules, package_path, module)


def test_uptime_uses_linux_parsers(monkeypatch):
    # Create fake linux_parsers.parsers.system.proc_uptime module
    proc_mod = types.ModuleType("linux_parsers.parsers.system.proc_uptime")

    def parse_proc(text: str):
        return {"uptime_seconds": 54321.0}

    proc_mod.parse = parse_proc

    # ensure package hierarchy exists
    _mk_pkg_hierarchy(monkeypatch, "linux_parsers.parsers.system.proc_uptime", proc_mod)

    proto = FakeProtocol({"/proc/uptime": "12345.67 67890.12\n"})
    s = SYSAction(proto, RemoteState())

    ut = s.uptime()
    assert abs(ut.seconds - 54321.0) < 1e-6


def test_memory_uses_linux_parsers(monkeypatch):
    # Create fake linux_parsers.parsers.system.free module
    free_mod = types.ModuleType("linux_parsers.parsers.system.free")

    def parse_free(text: str):
        return {"total": 8000000, "available": 4500000, "used": 3500000, "swap_total": 2000000, "swap_used": 10000}

    free_mod.parse_free = parse_free

    _mk_pkg_hierarchy(monkeypatch, "linux_parsers.parsers.system.free", free_mod)

    proto = FakeProtocol({"free -b": "fake output"})
    s = SYSAction(proto, RemoteState())

    mem = s.memory_info()
    assert mem.total == 8000000
    assert mem.swap_used == 10000


def test_cpu_info_uses_linux_parsers(monkeypatch):
    cpu_mod = types.ModuleType("linux_parsers.parsers.system.proc_cpuinfo")

    def parse_cpu(text: str):
        return {"processors": [{"processor": "0", "vendor_id": "ACME", "model name": "Test CPU", "cpu cores": 4, "cpu mhz": 2400.0, "flags": "fpu vme"}], "threads": 1}

    cpu_mod.parse = parse_cpu

    _mk_pkg_hierarchy(monkeypatch, "linux_parsers.parsers.system.proc_cpuinfo", cpu_mod)

    proto = FakeProtocol({"/proc/cpuinfo": "fake"})
    s = SYSAction(proto, RemoteState())

    cpu = s.cpu_info()
    assert cpu.model_name == "Test CPU"
    assert cpu.cores == 4
    assert cpu.cpu_mhz == 2400.0


def test_os_release_uses_linux_parsers(monkeypatch):
    os_mod = types.ModuleType("linux_parsers.parsers.system.etc_os_release")

    def parse_os(text: str):
        return {"name": "TestOS", "version": "1.2", "version_id": "1.2", "pretty_name": "TestOS 1.2", "id": "testos"}

    os_mod.parse = parse_os

    _mk_pkg_hierarchy(monkeypatch, "linux_parsers.parsers.system.etc_os_release", os_mod)

    proto = FakeProtocol({"/etc/os-release": "NAME=TestOS\nVERSION=1.2\n"})
    s = SYSAction(proto, RemoteState())

    osr = s.os_release()
    assert osr.name == "TestOS"
    assert osr.version == "1.2"


def test_loadavg_uses_linux_parsers(monkeypatch):
    la_mod = types.ModuleType("linux_parsers.parsers.system.proc_loadavg")

    def parse_la(text: str):
        return {"one": 0.1, "five": 0.2, "fifteen": 0.3, "running_processes": 2, "total_processes": 100}

    la_mod.parse = parse_la

    _mk_pkg_hierarchy(monkeypatch, "linux_parsers.parsers.system.proc_loadavg", la_mod)

    proto = FakeProtocol({"/proc/loadavg": "0.01 0.02 0.03 1/100 12345"})
    s = SYSAction(proto, RemoteState())

    la = s.load_average()
    assert la.one_minute == 0.1
    assert la.five_minutes == 0.2
    assert la.fifteen_minutes == 0.3
    assert la.running_processes == 2
