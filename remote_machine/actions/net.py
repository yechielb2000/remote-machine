"""Network actions."""
from __future__ import annotations

from remote_machine.models.remote_state import RemoteState
from remote_machine.protocols.ssh import SSHProtocol
from remote_machine.utils.error_mapper import ErrorMapper

try:
    from linux_parsers.parsers.network.ip import parse_ip_a, parse_ip_r  # type: ignore
    from linux_parsers.parsers.network.ss import parse_ss_tulnap  # type: ignore
    from linux_parsers.parsers.network.ping import parse_ping  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    parse_ip_a = parse_ip_r = parse_ss_tulnap = parse_ping = None

# Data types
from remote_machine.models.network_types import (
    IPAddress,
    IPAddressList,
    Route,
    RoutingTable,
    TCPConnection,
    ConnectionList,
    ListeningPort,
    ListeningPortList,
    PingResult,
)


class NETAction:
    """Network operations."""

    def __init__(self, protocol: SSHProtocol, state: RemoteState):
        """Initialize network actions.

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

    def stat(self) -> dict:
        """Return high-level network statistics as a dict."""
        # Stub implementation - will be populated in Phase 2
        return {}

    def interfaces(self) -> list[str]:
        """Return list of network interface names."""
        if parse_ip_a:
            parsed = parse_ip_a(self._run("ip -o link"))
            if isinstance(parsed, list):
                return [p.get("ifname") or p.get("if_name") or p.get("interface") for p in parsed if isinstance(p, dict)]

        # Fallback: simple parse from `ip a`
        out = self._run("ip a")
        names = []
        for line in out.splitlines():
            if ": " in line and "@" not in line:
                parts = line.split(": ", 1)
                if parts and parts[0].isdigit():
                    # format: '2: eth0: <...>'
                    name = parts[1].split(":", 1)[0]
                    names.append(name)
        return names

    def interface_info(self, interface: str) -> dict:
        """Return details for `interface` as a dict. Args: interface"""
        # Stub implementation - will be populated in Phase 2
        return {}

    def ip_add(self, interface: str, address: str) -> None:
        """Add `address` to `interface` (CIDR ok). Args: interface, address"""
        # Stub implementation - will be populated in Phase 2
        pass

    def ip_delete(self, interface: str, address: str) -> None:
        """Remove `address` from `interface`. Args: interface, address"""
        # Stub implementation - will be populated in Phase 2
        pass

    def ip_list(self, interface: str | None = None) -> IPAddressList:
        """Return list of IP addresses; optionally filter by `interface`. Args: interface"""
        cmd = "ip a" if not interface else f"ip a show dev {interface}"

        if parse_ip_a:
            parsed = parse_ip_a(self._run(cmd))
        else:
            parsed = []

        from remote_machine.models.network_types import IPAddress, IPAddressList

        addresses: list[IPAddress] = []
        for p in parsed:
            # parser returns keys like 'interface' / 'ifname' and 'address'
            if_name = p.get("ifname") or p.get("interface") or p.get("if_name")
            addr = p.get("address") or p.get("addr") or p.get("inet")
            if not addr:
                continue
            # split CIDR if present
            ip_part, _, mask_part = addr.partition("/")
            family = "IPv6" if ":" in ip_part else "IPv4"
            addresses.append(
                IPAddress(
                    interface=if_name,
                    address=ip_part,
                    family=family,
                    netmask=mask_part or None,
                    broadcast=p.get("broadcast"),
                    gateway=p.get("gateway"),
                )
            )

        if interface:
            addresses = [a for a in addresses if a.interface == interface]

        return IPAddressList(addresses=addresses, count=len(addresses))

    def route_list(self) -> RoutingTable:
        """Return routing table entries as list of dicts."""
        cmd = "ip r"

        if parse_ip_r:
            parsed = parse_ip_r(self._run(cmd))
        else:
            parsed = []

        from remote_machine.models.network_types import Route, RoutingTable

        routes: list[Route] = []
        for r in parsed:
            routes.append(
                Route(
                    destination=r.get("dest") or r.get("destination") or r.get("dst", ""),
                    gateway=r.get("via") or r.get("gateway") or "",
                    netmask=r.get("mask") or "",
                    flags=r.get("flags", ""),
                    metric=int(r.get("metric", 0) or 0),
                    interface=r.get("dev") or r.get("device") or r.get("oif") or "",
                )
            )

        return RoutingTable(routes=routes, count=len(routes))

    def tcp_connections(self) -> "ConnectionList":
        """Return list of TCP connection dicts."""
        cmd = "ss -tnp"

        from linux_parsers.parsers.network.ss import parse_ss_tulnap  # type: ignore
        parsed = parse_ss_tulnap(self._run(cmd))

        from remote_machine.models.network_types import TCPConnection, ConnectionList

        conns: list[TCPConnection] = []
        for c in parsed:
            # support src/dst keys or LocalAddress_Port/PeerAddress_Port
            src = c.get("src") or c.get("LocalAddress_Port") or c.get("local")
            dst = c.get("dst") or c.get("PeerAddress_Port") or c.get("remote")
            def _split_addr(a: str | None):
                if not a:
                    return "", 0
                if ":" in a:
                    host, port = a.rsplit(":", 1)
                    try:
                        return host, int(port)
                    except Exception:
                        return a, 0
                return a, 0

            local_host, local_port = _split_addr(src)
            remote_host, remote_port = _split_addr(dst)

            conns.append(
                TCPConnection(
                    local_address=local_host,
                    local_port=local_port,
                    remote_address=remote_host,
                    remote_port=remote_port,
                    state=c.get("State") or c.get("state", ""),
                    pid=int(c.get("pid") or c.get("PID") or 0) or None,
                    process_name=c.get("process") or c.get("ProgramName"),
                )
            )

        return ConnectionList(connections=conns, count=len(conns))

    def listening_ports(self) -> "ListeningPortList":
        """Return listening port info as list of dicts."""
        cmd = "ss -tulnap"

        from linux_parsers.parsers.network.ss import parse_ss_tulnap  # type: ignore
        parsed = parse_ss_tulnap(self._run(cmd))

        from remote_machine.models.network_types import ListeningPort, ListeningPortList

        ports: list[ListeningPort] = []
        for p in parsed:
            local = p.get("local") or p.get("LocalAddress_Port") or p.get("LocalAddress")
            if not local:
                continue
            if ":" in local:
                addr, port_str = local.rsplit(":", 1)
                try:
                    port_num = int(port_str)
                except Exception:
                    port_num = 0
            else:
                addr = local
                port_num = 0

            ports.append(
                ListeningPort(
                    address=addr,
                    port=port_num,
                    protocol=(p.get("Proto") or p.get("protocol") or "tcp").lower(),
                    state=p.get("State") or p.get("state", ""),
                    pid=int(p.get("pid") or p.get("PID") or 0) or None,
                    process_name=p.get("process") or p.get("ProgramName"),
                )
            )

        return ListeningPortList(ports=ports, count=len(ports))

    def ping(self, host: str, count: int = 4, timeout: int = 5) -> PingResult:
        """Ping `host` and return summary dict; use `count` and `timeout`. Args: host, count, timeout"""
        cmd = f"ping -c {int(count)} -W {int(timeout)} {host}"
        out = self._run(cmd)

        from linux_parsers.parsers.network.ping import parse_ping  # type: ignore
        parsed = parse_ping(out)

        from remote_machine.models.network_types import PingResult

        transmitted = int(parsed.get("packets_transmitted") or parsed.get("transmitted") or 0)
        received = int(parsed.get("packets_received") or parsed.get("received") or 0)
        loss = int(transmitted - received)
        loss_percent = float(parsed.get("loss") or parsed.get("loss_percent") or 0.0)

        rtt = parsed.get("rtt") or {}
        min_time = float(rtt.get("min") or rtt.get("rtt_min") or 0.0)
        max_time = float(rtt.get("max") or rtt.get("rtt_max") or 0.0)
        avg_time = float(rtt.get("avg") or rtt.get("rtt_avg") or 0.0)
        stddev_time = float(rtt.get("mdev") or rtt.get("stddev") or 0.0) if (rtt.get("mdev") or rtt.get("stddev")) else None

        return PingResult(
            host=host,
            transmitted=transmitted,
            received=received,
            packets_lost=loss,
            loss_percent=loss_percent,
            min_time=min_time,
            max_time=max_time,
            avg_time=avg_time,
            stddev_time=stddev_time,
        )

    def up(self, interface: str) -> None:
        """Bring `interface` up. Args: interface"""
        # Stub implementation - will be populated in Phase 2
        pass

    def down(self, interface: str) -> None:
        """Bring `interface` down. Args: interface"""
        # Stub implementation - will be populated in Phase 2
        pass

    def dns_lookup(self, hostname: str) -> dict:
        """Resolve `hostname` and return DNS info dict. Args: hostname"""
        # Stub implementation - will be populated in Phase 2
        return {}

    def route_add(self, destination: str, gateway: str, interface: str | None = None) -> None:
        """Add route to `destination` via `gateway` (optionally `interface`). Args: destination, gateway, interface"""
        # Stub implementation - will be populated in Phase 2
        pass

    def route_delete(self, destination: str) -> None:
        """Remove route to `destination`. Args: destination"""
        # Stub implementation - will be populated in Phase 2
        pass

    def up(self, interface: str) -> None:
        """Bring `interface` up. Args: interface"""
        # Stub implementation - will be populated in Phase 2
        pass

    def down(self, interface: str) -> None:
        """Bring `interface` down. Args: interface"""
        # Stub implementation - will be populated in Phase 2
        pass

    def firewall_status(self) -> dict:
        """Return firewall status as a dict."""
        # Stub implementation - will be populated in Phase 2
        return {}

    def bandwidth(self, interface: str | None = None) -> dict:
        """Return bandwidth usage (optionally for `interface`). Args: interface"""
        # Stub implementation - will be populated in Phase 2
        return {}

    def firewall_status(self) -> dict:
        """Return firewall status as a dict."""
        # Stub implementation - will be populated in Phase 2
        return {}

    def bandwidth(self, interface: str | None = None) -> dict:
        """Return bandwidth usage (optionally for `interface`). Args: interface"""
        # Stub implementation - will be populated in Phase 2
        return {}
