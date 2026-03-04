"""Base test class with common fixtures and utilities."""

import pytest
import sys
import types
from remote_machine.models.command_result import CommandResult
from remote_machine.models.remote_state import RemoteState


class BaseTest:
    """Base test class for remote-machine tests."""

    @pytest.fixture
    def fake_protocol(self):
        """Fixture for fake protocol with responses."""
        class FakeProtocol:
            def __init__(self, responses: dict[str, str]):
                self.responses = responses

            def exec(self, command: str, state: RemoteState) -> CommandResult:
                for key, out in self.responses.items():
                    if key in command:
                        return CommandResult(
                            command=command, stdout=out, stderr="", exit_code=0
                        )
                return CommandResult(
                    command=command, stdout="", stderr="", exit_code=0
                )

            def run_command(self, command: str, state: RemoteState, thread: bool = False) -> str:
                result = self.exec(command, state)
                if result.exit_code != 0:
                    raise Exception(f"Command failed: {result.stderr}")
                return result.stdout

        return FakeProtocol

    @pytest.fixture
    def setup_linux_parsers(self, monkeypatch):
        """Fixture to setup basic linux_parsers modules."""
        def _setup(parsers_config: dict):
            # Create base modules
            monkeypatch.setitem(sys.modules, "linux_parsers", types.ModuleType("linux_parsers"))
            monkeypatch.setitem(
                sys.modules, "linux_parsers.parsers", types.ModuleType("linux_parsers.parsers")
            )
            parsers_pkg = sys.modules["linux_parsers.parsers"]
            
            # Create subpackages
            filesystem_pkg = types.ModuleType("linux_parsers.parsers.filesystem")
            monkeypatch.setitem(sys.modules, "linux_parsers.parsers.filesystem", filesystem_pkg)
            setattr(parsers_pkg, "filesystem", filesystem_pkg)
            
            network_pkg = types.ModuleType("linux_parsers.parsers.network")
            monkeypatch.setitem(sys.modules, "linux_parsers.parsers.network", network_pkg)
            setattr(parsers_pkg, "network", network_pkg)

            process_pkg = types.ModuleType("linux_parsers.parsers.process")
            monkeypatch.setitem(sys.modules, "linux_parsers.parsers.process", process_pkg)
            setattr(parsers_pkg, "process", process_pkg)

            system_pkg = types.ModuleType("linux_parsers.parsers.system")
            monkeypatch.setitem(sys.modules, "linux_parsers.parsers.system", system_pkg)
            setattr(parsers_pkg, "system", system_pkg)

            session_pkg = types.ModuleType("linux_parsers.parsers.session")
            monkeypatch.setitem(sys.modules, "linux_parsers.parsers.session", session_pkg)
            setattr(parsers_pkg, "session", session_pkg)

            # Setup each parser module
            for module_name, config in parsers_config.items():
                if module_name in ["ip", "ss", "ping"]:
                    pkg = network_pkg
                    prefix = "linux_parsers.parsers.network"
                elif module_name in ["ls", "mount", "stat", "df"]:
                    pkg = filesystem_pkg
                    prefix = "linux_parsers.parsers.filesystem"
                elif module_name in ["ps"]:
                    pkg = process_pkg
                    prefix = "linux_parsers.parsers.process"
                elif module_name in ["free", "proc_uptime", "etc_os_release", "proc_cpuinfo"]:
                    pkg = system_pkg
                    prefix = "linux_parsers.parsers.system"
                elif module_name in ["who"]:
                    pkg = session_pkg
                    prefix = "linux_parsers.parsers.session"
                else:
                    continue
                mod = types.ModuleType(f"{prefix}.{module_name}")
                for func_name, func in config.items():
                    setattr(mod, func_name, func)
                monkeypatch.setitem(sys.modules, f"{prefix}.{module_name}", mod)
                setattr(pkg, module_name, mod)
            if "ls" not in parsers_config:
                ls_mod = types.ModuleType("linux_parsers.parsers.filesystem.ls")
                ls_mod.parse_ls = lambda out: []
                monkeypatch.setitem(sys.modules, "linux_parsers.parsers.filesystem.ls", ls_mod)
                setattr(filesystem_pkg, "ls", ls_mod)
            if "mount" not in parsers_config:
                mount_mod = types.ModuleType("linux_parsers.parsers.filesystem.mount")
                mount_mod.parse_mount = lambda out: []
                monkeypatch.setitem(sys.modules, "linux_parsers.parsers.filesystem.mount", mount_mod)
                setattr(filesystem_pkg, "mount", mount_mod)
            if "stat" not in parsers_config:
                stat_mod = types.ModuleType("linux_parsers.parsers.filesystem.stat")
                stat_mod.parse_stat = lambda out: {}
                monkeypatch.setitem(sys.modules, "linux_parsers.parsers.filesystem.stat", stat_mod)
                setattr(filesystem_pkg, "stat", stat_mod)
            if "df" not in parsers_config:
                df_mod = types.ModuleType("linux_parsers.parsers.filesystem.df")
                df_mod.parse_df = lambda out: []
                monkeypatch.setitem(sys.modules, "linux_parsers.parsers.filesystem.df", df_mod)
                setattr(filesystem_pkg, "df", df_mod)
            if "ps" not in parsers_config:
                ps_mod = types.ModuleType("linux_parsers.parsers.process.ps")
                ps_mod.parse_ps_aux = lambda out: []
                monkeypatch.setitem(sys.modules, "linux_parsers.parsers.process.ps", ps_mod)
                setattr(process_pkg, "ps", ps_mod)
            if "free" not in parsers_config:
                free_mod = types.ModuleType("linux_parsers.parsers.system.free")
                free_mod.parse_free_btlv = lambda out: {}
                monkeypatch.setitem(sys.modules, "linux_parsers.parsers.system.free", free_mod)
                setattr(system_pkg, "free", free_mod)
            if "proc_uptime" not in parsers_config:
                proc_uptime_mod = types.ModuleType("linux_parsers.parsers.system.proc_uptime")
                proc_uptime_mod.parse_proc_uptime_file = lambda out: {}
                monkeypatch.setitem(sys.modules, "linux_parsers.parsers.system.proc_uptime", proc_uptime_mod)
                setattr(system_pkg, "proc_uptime", proc_uptime_mod)
            if "etc_os_release" not in parsers_config:
                etc_os_release_mod = types.ModuleType("linux_parsers.parsers.system.etc_os_release")
                etc_os_release_mod.parse_etc_os_release_file = lambda out: {}
                monkeypatch.setitem(sys.modules, "linux_parsers.parsers.system.etc_os_release", etc_os_release_mod)
                setattr(system_pkg, "etc_os_release", etc_os_release_mod)
            if "proc_cpuinfo" not in parsers_config:
                proc_cpuinfo_mod = types.ModuleType("linux_parsers.parsers.system.proc_cpuinfo")
                proc_cpuinfo_mod.parse_proc_cpuinfo_file = lambda out: {}
                monkeypatch.setitem(sys.modules, "linux_parsers.parsers.system.proc_cpuinfo", proc_cpuinfo_mod)
                setattr(system_pkg, "proc_cpuinfo", proc_cpuinfo_mod)
            if "who" not in parsers_config:
                who_mod = types.ModuleType("linux_parsers.parsers.session.who")
                who_mod.parse_who_a = lambda out: []
                monkeypatch.setitem(sys.modules, "linux_parsers.parsers.session.who", who_mod)
                setattr(session_pkg, "who", who_mod)

            # Reload net module to pick up changes
            sys.modules.pop("remote_machine.actions.net", None)
            from importlib import reload
            import remote_machine.actions.net as _net_mod
            reload(_net_mod)

            return network_pkg

        return _setup

    @property
    def remote_state(self):
        """Get a default RemoteState instance."""
        return RemoteState()