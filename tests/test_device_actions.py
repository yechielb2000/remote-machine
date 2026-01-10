"""Tests for DeviceAction linux_parsers usage."""
import sys
import types

from remote_machine.actions.device import DeviceAction
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


def test_mounted_uses_parser(monkeypatch):
    mount_mod = types.ModuleType("linux_parsers.parsers.filesystem.mount")

    def parse_mount(text: str):
        return [{"device": "/dev/sda1", "mount_point": "/", "fstype": "ext4", "options": "rw"}]

    mount_mod.parse = parse_mount
    # ensure package hierarchy
    monkeypatch.setitem(sys.modules, "linux_parsers", types.ModuleType("linux_parsers"))
    monkeypatch.setitem(sys.modules, "linux_parsers.parsers.filesystem.mount", mount_mod)

    proto = FakeProtocol({"/proc/mounts": "/dev/sda1 / ext4 rw,relatime 0 0\n"})
    d = DeviceAction(proto, RemoteState())

    mounts = d.mounted()
    assert mounts.mount_points[0].mount_point == "/"


def test_list_block_json_and_fallback(monkeypatch):
    proto = FakeProtocol({"lsblk -J": '{"blockdevices": [{"name": "sda", "type": "disk", "children": [{"name": "sda1", "type": "part", "mountpoint": "/"}]}]}'})
    d = DeviceAction(proto, RemoteState())

    devs = d.list_block()
    assert any(d.name == "sda" for d in devs)

    # fallback to /proc/partitions
    proto2 = FakeProtocol({"lsblk -J": "", "cat /proc/partitions": "major minor  #blocks  name\n   8 0 488386584 sda\n"})
    d2 = DeviceAction(proto2, RemoteState())
    devs2 = d2.list_block()
    assert any(d.name == "sda" for d in devs2)
