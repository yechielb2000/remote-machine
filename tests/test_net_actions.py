"""Tests for NETAction linux_parsers usage."""
import sys
import types

# NETAction will be imported per-test after monkeypatching linux_parsers into sys.modules


class FakeProtocol:
    def __init__(self, responses: dict[str, str]):
        self.responses = responses

    def exec(self, command: str, state):
        for key, out in self.responses.items():
            if key in command:
                return types.SimpleNamespace(command=command, stdout=out, stderr="", exit_code=0, success=True)
        return types.SimpleNamespace(command=command, stdout="", stderr="", exit_code=0, success=True)


def test_interfaces_uses_parser(monkeypatch):
    ip_mod = types.ModuleType("linux_parsers.parsers.network.ip")

    def parse_ip_a(out: str):
        return [{"ifname": "eth0"}, {"ifname": "lo"}]

    def parse_ip_r(out: str):
        return []

    ip_mod.parse_ip_a = parse_ip_a
    ip_mod.parse_ip_r = parse_ip_r

    monkeypatch.setitem(sys.modules, "linux_parsers", types.ModuleType("linux_parsers"))
    monkeypatch.setitem(sys.modules, "linux_parsers.parsers", types.ModuleType("linux_parsers.parsers"))
    network_pkg = types.ModuleType("linux_parsers.parsers.network")
    monkeypatch.setitem(sys.modules, "linux_parsers.parsers.network", network_pkg)
    monkeypatch.setitem(sys.modules, "linux_parsers.parsers.network.ip", ip_mod)
    # create minimal stubs for other network parser modules so top-level imports in net.py succeed
    ss_mod = types.ModuleType("linux_parsers.parsers.network.ss")
    ss_mod.parse_ss_tulnap = lambda out: []
    ping_mod = types.ModuleType("linux_parsers.parsers.network.ping")
    ping_mod.parse_ping = lambda out: {}
    monkeypatch.setitem(sys.modules, "linux_parsers.parsers.network.ss", ss_mod)
    monkeypatch.setitem(sys.modules, "linux_parsers.parsers.network.ping", ping_mod)
    # attach submodules to parent package object so `from linux_parsers.parsers.network.* import ...` works
    sys.modules["linux_parsers.parsers.network"].ip = ip_mod
    sys.modules["linux_parsers.parsers.network"].ss = ss_mod
    sys.modules["linux_parsers.parsers.network"].ping = ping_mod
    sys.modules.pop("remote_machine.actions.net", None)
    from importlib import reload
    import remote_machine.actions.net as _net_mod
    reload(_net_mod)
    from remote_machine.actions.net import NETAction
    from remote_machine.models.remote_state import RemoteState
    proto = FakeProtocol({"ip -o link": ""})
    n = NETAction(proto, RemoteState())

    ifs = n.interfaces()
    assert "eth0" in ifs
    assert "lo" in ifs


def test_ip_list_uses_parser(monkeypatch):
    ip_mod = types.ModuleType("linux_parsers.parsers.network.ip")

    def parse_ip_a(out: str):
        return [{"interface": "eth0", "address": "10.0.0.1/24"}]

    def parse_ip_r(out: str):
        return []

    ip_mod.parse_ip_a = parse_ip_a
    ip_mod.parse_ip_r = parse_ip_r

    monkeypatch.setitem(sys.modules, "linux_parsers", types.ModuleType("linux_parsers"))
    monkeypatch.setitem(sys.modules, "linux_parsers.parsers", types.ModuleType("linux_parsers.parsers"))
    network_pkg = types.ModuleType("linux_parsers.parsers.network")
    monkeypatch.setitem(sys.modules, "linux_parsers.parsers.network", network_pkg)
    monkeypatch.setitem(sys.modules, "linux_parsers.parsers.network.ip", ip_mod)
    # create minimal stubs for other network parser modules so top-level imports in net.py succeed
    ss_mod = types.ModuleType("linux_parsers.parsers.network.ss")
    ss_mod.parse_ss_tulnap = lambda out: []
    ping_mod = types.ModuleType("linux_parsers.parsers.network.ping")
    ping_mod.parse_ping = lambda out: {}
    monkeypatch.setitem(sys.modules, "linux_parsers.parsers.network.ss", ss_mod)
    monkeypatch.setitem(sys.modules, "linux_parsers.parsers.network.ping", ping_mod)
    # attach submodules to parent package object so `from linux_parsers.parsers.network.* import ...` works
    sys.modules["linux_parsers.parsers.network"].ip = ip_mod
    sys.modules["linux_parsers.parsers.network"].ss = ss_mod
    sys.modules["linux_parsers.parsers.network"].ping = ping_mod
    sys.modules.pop("remote_machine.actions.net", None)
    from importlib import reload
    import remote_machine.actions.net as _net_mod
    reload(_net_mod)
    from remote_machine.actions.net import NETAction
    from remote_machine.models.remote_state import RemoteState
    proto = FakeProtocol({"ip a": ""})
    n = NETAction(proto, RemoteState())

    res = n.ip_list()
    from remote_machine.models.network_types import IPAddressList

    assert isinstance(res, IPAddressList)
    assert res.addresses[0].interface == "eth0"


def test_listening_ports_uses_parser(monkeypatch):
    ss_mod = types.ModuleType("linux_parsers.parsers.network.ss")

    def parse_ss_tulnap(out: str):
        return [{"local": "0.0.0.0:22", "pid": 1234}]

    ss_mod.parse_ss_tulnap = parse_ss_tulnap

    monkeypatch.setitem(sys.modules, "linux_parsers", types.ModuleType("linux_parsers"))
    monkeypatch.setitem(sys.modules, "linux_parsers.parsers", types.ModuleType("linux_parsers.parsers"))
    network_pkg = types.ModuleType("linux_parsers.parsers.network")
    monkeypatch.setitem(sys.modules, "linux_parsers.parsers.network", network_pkg)
    monkeypatch.setitem(sys.modules, "linux_parsers.parsers.network.ss", ss_mod)
    # create minimal stubs for other network parser modules so top-level imports in net.py succeed
    ip_mod = types.ModuleType("linux_parsers.parsers.network.ip")
    ip_mod.parse_ip_a = lambda out: []
    ip_mod.parse_ip_r = lambda out: []
    ping_mod = types.ModuleType("linux_parsers.parsers.network.ping")
    ping_mod.parse_ping = lambda out: {}
    monkeypatch.setitem(sys.modules, "linux_parsers.parsers.network.ip", ip_mod)
    monkeypatch.setitem(sys.modules, "linux_parsers.parsers.network.ping", ping_mod)
    # attach submodules to parent package object so `from linux_parsers.parsers.network.* import ...` works
    sys.modules["linux_parsers.parsers.network"].ip = ip_mod
    sys.modules["linux_parsers.parsers.network"].ss = ss_mod
    sys.modules["linux_parsers.parsers.network"].ping = ping_mod
    from remote_machine.actions.net import NETAction
    from remote_machine.models.remote_state import RemoteState
    proto = FakeProtocol({"ss -tulnap": ""})
    n = NETAction(proto, RemoteState())

    ports = n.listening_ports()
    from remote_machine.models.network_types import ListeningPortList

    assert isinstance(ports, ListeningPortList)
    assert ports.ports[0].address == "0.0.0.0"
    assert ports.ports[0].port == 22


def test_tcp_connections_uses_parser(monkeypatch):
    ss_mod = types.ModuleType("linux_parsers.parsers.network.ss")

    def parse_ss_tulnap(out: str):
        return [{"src": "1.2.3.4:12345", "dst": "5.6.7.8:80"}]

    ss_mod.parse_ss_tulnap = parse_ss_tulnap

    monkeypatch.setitem(sys.modules, "linux_parsers", types.ModuleType("linux_parsers"))
    monkeypatch.setitem(sys.modules, "linux_parsers.parsers", types.ModuleType("linux_parsers.parsers"))
    network_pkg = types.ModuleType("linux_parsers.parsers.network")
    monkeypatch.setitem(sys.modules, "linux_parsers.parsers.network", network_pkg)
    monkeypatch.setitem(sys.modules, "linux_parsers.parsers.network.ss", ss_mod)
    # create minimal stubs for other network parser modules so top-level imports in net.py succeed
    ip_mod = types.ModuleType("linux_parsers.parsers.network.ip")
    ip_mod.parse_ip_a = lambda out: []
    ip_mod.parse_ip_r = lambda out: []
    ping_mod = types.ModuleType("linux_parsers.parsers.network.ping")
    ping_mod.parse_ping = lambda out: {}
    monkeypatch.setitem(sys.modules, "linux_parsers.parsers.network.ip", ip_mod)
    monkeypatch.setitem(sys.modules, "linux_parsers.parsers.network.ping", ping_mod)
    # attach submodules to parent package object so `from linux_parsers.parsers.network.* import ...` works
    sys.modules["linux_parsers.parsers.network"].ip = ip_mod
    sys.modules["linux_parsers.parsers.network"].ss = ss_mod
    sys.modules["linux_parsers.parsers.network"].ping = ping_mod
    from remote_machine.actions.net import NETAction
    from remote_machine.models.remote_state import RemoteState
    proto = FakeProtocol({"ss -tnp": ""})
    n = NETAction(proto, RemoteState())

    conns = n.tcp_connections()
    from remote_machine.models.network_types import ConnectionList

    assert isinstance(conns, ConnectionList)
    assert conns.connections[0].local_address == "1.2.3.4"


def test_route_list_uses_parser(monkeypatch):
    ip_mod = types.ModuleType("linux_parsers.parsers.network.ip")

    def parse_ip_r(out: str):
        return [{"dest": "default", "via": "192.168.1.1"}]

    def parse_ip_a(out: str):
        return []

    ip_mod.parse_ip_r = parse_ip_r
    ip_mod.parse_ip_a = parse_ip_a

    monkeypatch.setitem(sys.modules, "linux_parsers", types.ModuleType("linux_parsers"))
    monkeypatch.setitem(sys.modules, "linux_parsers.parsers", types.ModuleType("linux_parsers.parsers"))
    network_pkg = types.ModuleType("linux_parsers.parsers.network")
    monkeypatch.setitem(sys.modules, "linux_parsers.parsers.network", network_pkg)
    monkeypatch.setitem(sys.modules, "linux_parsers.parsers.network.ip", ip_mod)
    # create minimal stubs for other network parser modules so top-level imports in net.py succeed
    ss_mod = types.ModuleType("linux_parsers.parsers.network.ss")
    ss_mod.parse_ss_tulnap = lambda out: []
    ping_mod = types.ModuleType("linux_parsers.parsers.network.ping")
    ping_mod.parse_ping = lambda out: {}
    monkeypatch.setitem(sys.modules, "linux_parsers.parsers.network.ss", ss_mod)
    monkeypatch.setitem(sys.modules, "linux_parsers.parsers.network.ping", ping_mod)
    # attach submodule to parent package object so `from linux_parsers.parsers.network.ip import ...` works
    sys.modules["linux_parsers.parsers.network"].ip = ip_mod
    sys.modules["linux_parsers.parsers.network"].ss = ss_mod
    sys.modules["linux_parsers.parsers.network"].ping = ping_mod
    sys.modules.pop("remote_machine.actions.net", None)
    from importlib import reload
    import remote_machine.actions.net as _net_mod
    reload(_net_mod)
    from remote_machine.actions.net import NETAction
    from remote_machine.models.remote_state import RemoteState
    proto = FakeProtocol({"ip r": ""})
    n = NETAction(proto, RemoteState())

    routes = n.route_list()
    from remote_machine.models.network_types import RoutingTable

    assert isinstance(routes, RoutingTable)
    assert routes.routes[0].gateway == "192.168.1.1"


def test_ping_uses_parser(monkeypatch):
    ping_mod = types.ModuleType("linux_parsers.parsers.network.ping")

    def parse_ping(out: str):
        return {"packets_transmitted": 4, "packets_received": 4}

    ping_mod.parse_ping = parse_ping

    monkeypatch.setitem(sys.modules, "linux_parsers", types.ModuleType("linux_parsers"))
    monkeypatch.setitem(sys.modules, "linux_parsers.parsers", types.ModuleType("linux_parsers.parsers"))
    network_pkg = types.ModuleType("linux_parsers.parsers.network")
    monkeypatch.setitem(sys.modules, "linux_parsers.parsers.network", network_pkg)
    monkeypatch.setitem(sys.modules, "linux_parsers.parsers.network.ping", ping_mod)
    # create minimal stubs for other network parser modules so top-level imports in net.py succeed
    ip_mod = types.ModuleType("linux_parsers.parsers.network.ip")
    ip_mod.parse_ip_a = lambda out: []
    ip_mod.parse_ip_r = lambda out: []
    ss_mod = types.ModuleType("linux_parsers.parsers.network.ss")
    ss_mod.parse_ss_tulnap = lambda out: []
    monkeypatch.setitem(sys.modules, "linux_parsers.parsers.network.ip", ip_mod)
    monkeypatch.setitem(sys.modules, "linux_parsers.parsers.network.ss", ss_mod)
    # attach submodule to parent package object so `from linux_parsers.parsers.network.ping import ...` works
    sys.modules["linux_parsers.parsers.network"].ping = ping_mod
    sys.modules["linux_parsers.parsers.network"].ip = ip_mod
    sys.modules["linux_parsers.parsers.network"].ss = ss_mod
    sys.modules.pop("remote_machine.actions.net", None)
    from importlib import reload
    import remote_machine.actions.net as _net_mod
    reload(_net_mod)
    from remote_machine.actions.net import NETAction
    from remote_machine.models.remote_state import RemoteState
    proto = FakeProtocol({"ping": "PING\n---"})
    n = NETAction(proto, RemoteState())

    res = n.ping("example.com", count=4, timeout=2)
    from remote_machine.models.network_types import PingResult

    assert isinstance(res, PingResult)
    assert res.received == 4
