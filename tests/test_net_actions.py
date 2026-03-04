"""Tests for NETAction linux_parsers usage."""

import pytest
pytestmark = [pytest.mark.actions, pytest.mark.net]

from tests.base_test import BaseTest


class TestNETActions(BaseTest):
    """Test NETAction parser usage."""

    def test_interfaces_uses_parser(self, monkeypatch, fake_protocol, setup_linux_parsers):
        parsers_config = {
            "ip": {
                "parse_ip_a": lambda out, state=None: {
                    "eth0": {"iface": "eth0"},
                    "lo": {"iface": "lo"}
                },
                "parse_ip_r": lambda out, state=None: [],
            },
            "ss": {"parse_ss_tulnap": lambda out: []},
            "ping": {"parse_ping": lambda out: {}},
        }
        setup_linux_parsers(parsers_config)

        from remote_machine.actions.net import NETAction

        proto = fake_protocol({"ip -o link": ""})
        n = NETAction(proto, self.remote_state)

        ifs = n.interfaces()
        assert "eth0" in ifs
        assert "lo" in ifs

    def test_ip_list_uses_parser(self, monkeypatch, fake_protocol, setup_linux_parsers):
        parsers_config = {
            "ip": {
                "parse_ip_a": lambda out, state=None: {
                    "eth0": {
                        "iface": "eth0",
                        "addresses": [{"ip": "10.0.0.1/24", "brd": None}]
                    }
                },
                "parse_ip_r": lambda out, state=None: [],
            },
            "ss": {"parse_ss_tulnap": lambda out: []},
            "ping": {"parse_ping": lambda out: {}},
        }
        setup_linux_parsers(parsers_config)

        from remote_machine.actions.net import NETAction

        proto = fake_protocol({"ip a": ""})
        n = NETAction(proto, self.remote_state)

        res = n.ip_list()
        from remote_machine.models.network_types import IPAddressList

        assert isinstance(res, IPAddressList)
        assert res.addresses[0].interface == "eth0"

    def test_listening_ports_uses_parser(self, monkeypatch, fake_protocol, setup_linux_parsers):
        parsers_config = {
            "ip": {
                "parse_ip_a": lambda out, state=None: {},
                "parse_ip_r": lambda out, state=None: [],
            },
            "ss": {"parse_ss_tulnap": lambda out: [{"local": "0.0.0.0:22", "pid": 1234}]},
            "ping": {"parse_ping": lambda out: {}},
        }
        setup_linux_parsers(parsers_config)

        from remote_machine.actions.net import NETAction

        proto = fake_protocol({"ss -tulnap": ""})
        n = NETAction(proto, self.remote_state)

        ports = n.listening_ports()
        from remote_machine.models.network_types import ListeningPortList

        assert isinstance(ports, ListeningPortList)
        assert ports.ports[0].address == "0.0.0.0"
        assert ports.ports[0].port == 22

    def test_tcp_connections_uses_parser(self, monkeypatch, fake_protocol, setup_linux_parsers):
        parsers_config = {
            "ip": {
                "parse_ip_a": lambda out, state=None: {},
                "parse_ip_r": lambda out, state=None: [],
            },
            "ss": {"parse_ss_tulnap": lambda out: [{"src": "1.2.3.4:12345", "dst": "5.6.7.8:80"}]},
            "ping": {"parse_ping": lambda out: {}},
        }
        setup_linux_parsers(parsers_config)

        from remote_machine.actions.net import NETAction

        proto = fake_protocol({"ss -tnp": ""})
        n = NETAction(proto, self.remote_state)

        conns = n.tcp_connections()
        from remote_machine.models.network_types import ConnectionList

        assert isinstance(conns, ConnectionList)
        assert conns.connections[0].local_address == "1.2.3.4"

    def test_route_list_uses_parser(self, monkeypatch, fake_protocol, setup_linux_parsers):
        parsers_config = {
            "ip": {
                "parse_ip_a": lambda out, state=None: {},
                "parse_ip_r": lambda out, state=None: [{"dest": "default", "via": "192.168.1.1"}],
            },
            "ss": {"parse_ss_tulnap": lambda out: []},
            "ping": {"parse_ping": lambda out: {}},
        }
        setup_linux_parsers(parsers_config)

        from remote_machine.actions.net import NETAction

        proto = fake_protocol({"ip r": ""})
        n = NETAction(proto, self.remote_state)

        routes = n.route_list()
        from remote_machine.models.network_types import RoutingTable

        assert isinstance(routes, RoutingTable)
        assert routes.routes[0].gateway == "192.168.1.1"

    def test_ping_uses_parser(self, monkeypatch, fake_protocol, setup_linux_parsers):
        parsers_config = {
            "ip": {
                "parse_ip_a": lambda out, state=None: {},
                "parse_ip_r": lambda out, state=None: [],
            },
            "ss": {"parse_ss_tulnap": lambda out: []},
            "ping": {"parse_ping": lambda out: {
                "statistics": {"transmitted": 4, "received": 4, "loss": 0.0},
                "rtt": {"min": 10.0, "avg": 20.0, "max": 30.0, "mdev": 5.0}
            }},
        }
        setup_linux_parsers(parsers_config)

        from remote_machine.actions.net import NETAction

        proto = fake_protocol({"ping": "PING\n---"})
        n = NETAction(proto, self.remote_state)

        res = n.ping("example.com", count=4, timeout=2)
        from remote_machine.models.network_types import PingResult

        assert isinstance(res, PingResult)
        assert res.received == 4
