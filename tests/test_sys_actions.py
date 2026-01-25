"""Unit tests for SYSAction parsing behavior."""

import os
import sys

# Make the package importable in tests run in this environment
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from datetime import datetime, timedelta

import pytest

from remote_machine.actions.sys import SYSAction
from remote_machine.models.command_result import CommandResult
from remote_machine.models.remote_state import RemoteState


class FakeProtocol:
    def __init__(self, responses: dict[str, str]):
        self.responses = responses

    def exec(self, command: str, state: RemoteState) -> CommandResult:
        # return mapped stdout if key matches a known command
        for key, out in self.responses.items():
            if key in command:
                return CommandResult(command=command, stdout=out, stderr="", exit_code=0)
        # default empty
        return CommandResult(command=command, stdout="", stderr="", exit_code=0)


def test_uname_parsing():
    responses = {
        "uname -s": "Linux\n",
        "uname -n": "myhost\n",
        "uname -r": "5.19.0\n",
        "uname -v": "#1 SMP\n",
        "uname -m": "x86_64\n",
    }
    proto = FakeProtocol(responses)
    state = RemoteState()
    s = SYSAction(proto, state)

    uname = s.uname()
    assert uname.sysname == "Linux"
    assert uname.nodename == "myhost"
    assert uname.release == "5.19.0"
    assert uname.machine == "x86_64"


def test_uptime_parsing():
    responses = {"cat /proc/uptime": "12345.67 67890.12\n"}
    proto = FakeProtocol(responses)
    s = SYSAction(proto, RemoteState())

    ut = s.uptime()
    assert abs(ut.seconds - 12345.67) < 1e-6
    assert ut.days == int(12345.67 // 86400)


def test_load_average_parsing():
    responses = {"cat /proc/loadavg": "0.10 0.05 0.01 2/100 12345\n"}
    proto = FakeProtocol(responses)
    s = SYSAction(proto, RemoteState())

    load = s.load_average()
    assert load.one_minute == 0.10
    assert load.five_minutes == 0.05
    assert load.fifteen_minutes == 0.01
    assert load.running_processes == 2
    assert load.total_processes == 100


def test_memory_parsing():
    free_out = (
        "              total        used        free      shared  buff/cache   available\n"
        "Mem:        8000000     3000000     2000000          0     3000000     4500000\n"
        "Swap:       2000000       10000     1990000\n"
    )
    responses = {"free -b": free_out}
    proto = FakeProtocol(responses)
    s = SYSAction(proto, RemoteState())

    mem = s.memory_info()
    assert mem.total == 8000000
    assert mem.available == 4500000
    assert mem.swap_total == 2000000
    assert mem.swap_used == 10000


def test_cpu_info_parsing():
    cpuinfo = (
        "processor\t: 0\n"
        "vendor_id\t: GenuineIntel\n"
        "model name\t: Test CPU\n"
        "cpu cores\t: 4\n"
        "cpu MHz\t: 2400.000\n"
        "flags\t: fpu vme de\n"
        "cache size\t: 8192 KB\n"
        "stepping\t: 10\n"
        "\n"
        "processor\t: 1\n"
        "\n"
    )
    responses = {"cat /proc/cpuinfo": cpuinfo}
    proto = FakeProtocol(responses)
    s = SYSAction(proto, RemoteState())

    cpu = s.cpu_info()
    assert cpu.model_name == "Test CPU"
    assert cpu.cores == 4
    assert cpu.threads == 2
    assert cpu.cpu_mhz == 2400.0


if __name__ == "__main__":
    pytest.main([__file__])
