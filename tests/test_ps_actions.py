"""Tests for PSAction linux_parsers usage."""

import sys
import types

from remote_machine.models.remote_state import RemoteState
from remote_machine.models.command_result import CommandResult

# Note: PSAction imports linux_parsers at module level, so tests must monkeypatch sys.modules before importing it.


class FakeProtocol:
    def __init__(self, responses: dict[str, str]):
        self.responses = responses

    def exec(self, command: str, state: RemoteState) -> CommandResult:
        for key, out in self.responses.items():
            if key in command:
                return CommandResult(command=command, stdout=out, stderr="", exit_code=0)
        return CommandResult(command=command, stdout="", stderr="", exit_code=0)


def test_list_uses_parser(monkeypatch):
    ps_mod = types.ModuleType("linux_parsers.parsers.process.ps")

    def parse_ps_aux(out: str):
        return [
            {"USER": "root", "PID": "1", "COMMAND": "init"},
            {"USER": "alice", "PID": "123", "COMMAND": "python"},
        ]

    ps_mod.parse_ps_aux = parse_ps_aux

    monkeypatch.setitem(sys.modules, "linux_parsers", types.ModuleType("linux_parsers"))
    monkeypatch.setitem(
        sys.modules, "linux_parsers.parsers", types.ModuleType("linux_parsers.parsers")
    )
    monkeypatch.setitem(
        sys.modules,
        "linux_parsers.parsers.process",
        types.ModuleType("linux_parsers.parsers.process"),
    )
    monkeypatch.setitem(sys.modules, "linux_parsers.parsers.process.ps", ps_mod)

    # import after monkeypatching so module-level imports succeed
    sys.modules.pop("remote_machine.actions.ps", None)
    from importlib import reload
    import remote_machine.actions.ps as _ps_mod

    reload(_ps_mod)
    from remote_machine.actions.ps import PSAction

    proto = FakeProtocol({"ps aux": ""})
    p = PSAction(proto, RemoteState())

    ps = p.list()
    assert any(x.user == "alice" for x in ps.processes)


def test_list_by_user_and_find(monkeypatch):
    ps_mod = types.ModuleType("linux_parsers.parsers.process.ps")

    def parse_ps_aux(out: str):
        return [
            {"USER": "root", "PID": "1", "COMMAND": "init"},
            {"USER": "alice", "PID": "123", "COMMAND": "python app.py"},
        ]

    ps_mod.parse_ps_aux = parse_ps_aux

    monkeypatch.setitem(sys.modules, "linux_parsers", types.ModuleType("linux_parsers"))
    monkeypatch.setitem(
        sys.modules, "linux_parsers.parsers", types.ModuleType("linux_parsers.parsers")
    )
    monkeypatch.setitem(
        sys.modules,
        "linux_parsers.parsers.process",
        types.ModuleType("linux_parsers.parsers.process"),
    )
    monkeypatch.setitem(sys.modules, "linux_parsers.parsers.process.ps", ps_mod)

    # import after monkeypatching so module-level imports succeed
    sys.modules.pop("remote_machine.actions.ps", None)
    from importlib import reload
    import remote_machine.actions.ps as _ps_mod

    reload(_ps_mod)
    from remote_machine.actions.ps import PSAction

    proto = FakeProtocol({"ps aux": ""})
    p = PSAction(proto, RemoteState())

    alice = p.list_by_user("alice")
    assert len(alice) == 1
    found = p.find("python")
    assert any("python" in (x.command or "") for x in found)


def test_get_info_and_kill(monkeypatch):
    ps_mod = types.ModuleType("linux_parsers.parsers.process.ps")

    def parse_ps_aux(out: str):
        return [{"USER": "root", "PID": "42", "COMMAND": "sleep 100"}]

    ps_mod.parse_ps_aux = parse_ps_aux

    monkeypatch.setitem(sys.modules, "linux_parsers", types.ModuleType("linux_parsers"))
    monkeypatch.setitem(
        sys.modules, "linux_parsers.parsers", types.ModuleType("linux_parsers.parsers")
    )
    monkeypatch.setitem(
        sys.modules,
        "linux_parsers.parsers.process",
        types.ModuleType("linux_parsers.parsers.process"),
    )
    monkeypatch.setitem(sys.modules, "linux_parsers.parsers.process.ps", ps_mod)

    # import after monkeypatching so module-level imports succeed
    sys.modules.pop("remote_machine.actions.ps", None)
    from importlib import reload
    import remote_machine.actions.ps as _ps_mod

    reload(_ps_mod)
    from remote_machine.actions.ps import PSAction

    proto = FakeProtocol({"ps aux": "", "kill -9 42": ""})
    p = PSAction(proto, RemoteState())

    info = p.get_info(42)
    assert info is not None and info.pid == 42
    p.kill(42, signal=9)  # should not raise
