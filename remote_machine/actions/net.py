"""Network actions."""

from __future__ import annotations

import shlex

from remote_machine.models.remote_state import RemoteState
from remote_machine.protocols.ssh import SSHProtocol

from linux_parsers.parsers.network.ip import parse_ip_a, parse_ip_r
from linux_parsers.parsers.network.ping import parse_ping
from linux_parsers.parsers.network.ss import parse_ss_tulnap

from remote_machine.models.network_types import (
    InterfaceInfo,
    IPAddressList,
    RoutingTable,
    ConnectionList,
    ListeningPortList,
    ListeningPort,
    PingResult,
    DNSResult,
    BandwidthList,
    BandwidthInfo,
    FirewallStatus,
    NetworkStats,
    Route,
    IPAddress,
    TCPConnection,
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

    def stat(self) -> NetworkStats:
        """Return high-level network statistics as a dataclass."""
        try:
            iface_names = self.interfaces()
        except Exception:
            iface_names = []

        try:
            iplist = self.ip_list()
            ip_count = (
                iplist.count if hasattr(iplist, "count") else len(getattr(iplist, "addresses", []))
            )
        except Exception:
            ip_count = 0

        try:
            routes = self.route_list()
            routes_count = (
                routes.count if hasattr(routes, "count") else len(getattr(routes, "routes", []))
            )
        except Exception:
            routes_count = 0

        try:
            conns = self.tcp_connections()
            conns_count = (
                conns.count if hasattr(conns, "count") else len(getattr(conns, "connections", []))
            )
        except Exception:
            conns_count = 0

        try:
            ports = self.listening_ports()
            ports_count = (
                ports.count if hasattr(ports, "count") else len(getattr(ports, "ports", []))
            )
        except Exception:
            ports_count = 0

        # aggregate bandwidth totals
        try:
            bw_list = self.bandwidth()
            total_sent = sum(item.bytes_sent for item in bw_list.items)
            total_received = sum(item.bytes_received for item in bw_list.items)
            total_packets_sent = sum(item.packets_sent for item in bw_list.items)
            total_packets_received = sum(item.packets_received for item in bw_list.items)
        except Exception:
            total_sent = total_received = total_packets_sent = total_packets_received = 0

        return NetworkStats(
            interfaces=iface_names,
            total_bytes_sent=total_sent,
            total_bytes_received=total_received,
            total_packets_sent=total_packets_sent,
            total_packets_received=total_packets_received,
        )

    def interfaces(self) -> list[str]:
        """Return list of network interface names."""
        out = self.protocol.run_command("ip a", self.state)
        parsed = parse_ip_a(out)

        return [
            iface_data.get("iface", "")
            for iface_data in parsed.values()
            if isinstance(iface_data, dict) and iface_data.get("iface")
        ]

    def interface_info(self, interface: str) -> InterfaceInfo:
        """Return details for `interface` as an InterfaceInfo dataclass."""
        out = self.protocol.run_command(f"ip -d a show dev {shlex.quote(interface)}", self.state)
        parsed = parse_ip_a(out)

        iface = next(iter(parsed.values()), {})

        mtu = int(iface.get("mtu") or 0)
        state = (iface.get("state") or "").lower()
        flags = iface.get("flags", "")

        link = iface.get("link", {})
        mac = link.get("ip", "")

        ipv4: list[str] = []
        ipv6: list[str] = []
        broadcast = None

        for addr in iface.get("addresses", []):
            ip = addr.get("ip", "")
            if not ip:
                continue

            ip_part, _, _ = ip.partition("/")
            if ":" in ip_part:
                ipv6.append(ip_part)
            else:
                ipv4.append(ip_part)
                broadcast = addr.get("brd") or broadcast

        return InterfaceInfo(
            name=iface.get("iface", interface),
            mtu=mtu,
            isup=state in ("up", "running"),
            is_running=state == "running",
            mac_address=mac,
            ipv4_addresses=ipv4,
            ipv6_addresses=ipv6,
            broadcast=broadcast,
            netmask=None,
            speed=None,
        )

    def ip_add(self, interface: str, address: str) -> None:
        """Add `address` to `interface` (CIDR ok). Args: interface, address"""
        self.protocol.run_command(
            f"ip addr add {shlex.quote(address)} dev {shlex.quote(interface)}", self.state
        )

    def ip_delete(self, interface: str, address: str) -> None:
        """Remove `address` from `interface`. Args: interface, address"""
        self.protocol.run_command(
            f"ip addr del {shlex.quote(address)} dev {shlex.quote(interface)}", self.state
        )

    def ip_list(self, interface: str | None = None) -> IPAddressList:
        """Return a list of IP addresses; optionally filtered by interface."""
        cmd = "ip a" if interface is None else f"ip a show dev {shlex.quote(interface)}"
        parsed = parse_ip_a(self.protocol.run_command(cmd), self.state)

        addresses: list[IPAddress] = []

        for iface in parsed.values():
            iface_name = iface.get("iface", "")

            for addr in iface.get("addresses", []):
                ip = addr.get("ip", "")
                if not ip:
                    continue

                ip_part, _, mask = ip.partition("/")
                family = "IPv6" if ":" in ip_part else "IPv4"

                addresses.append(
                    IPAddress(
                        interface=iface_name,
                        address=ip_part,
                        family=family,
                        netmask=mask or None,
                        broadcast=addr.get("brd"),
                        gateway=None,
                    )
                )

        return IPAddressList(addresses=addresses, count=len(addresses))

    def route_list(self) -> RoutingTable:
        """Return routing table entries as a list of dicts."""
        cmd = "ip r"

        parsed = parse_ip_r(self.protocol.run_command(cmd), self.state)

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

    def tcp_connections(self) -> ConnectionList:
        """Return a list of TCP connection dicts."""
        cmd = "ss -tulnap"

        out = self.protocol.run_command(cmd, self.state)
        parsed = parse_ss_tulnap(out)

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

    def listening_ports(self) -> ListeningPortList:
        """Return listening port info as a list of dicts."""
        cmd = "ss -tulnap"

        out = self.protocol.run_command(cmd, self.state)
        parsed = parse_ss_tulnap(out)

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
        """Ping `host` and return the summary as PingResult."""
        out = self.protocol.run_command(f"ping -c {count} -W {timeout} {host}", self.state)
        parsed = parse_ping(out)

        stats = parsed.get("statistics", {})
        rtt = parsed.get("rtt", {})

        transmitted = int(stats.get("transmitted") or 0)
        received = int(stats.get("received") or 0)

        return PingResult(
            host=host,
            transmitted=transmitted,
            received=received,
            packets_lost=transmitted - received,
            loss_percent=float(stats.get("loss") or 0.0),
            min_time=float(rtt.get("min") or 0.0),
            max_time=float(rtt.get("max") or 0.0),
            avg_time=float(rtt.get("avg") or 0.0),
            stddev_time=rtt.get("mdev") or rtt.get("stddev") or "0.0" if rtt else None,
        )

    def up(self, interface: str) -> None:
        """Bring `interface` up. Args: interface"""
        self.protocol.run_command(f"ip link set dev {shlex.quote(interface)} up", self.state)

    def down(self, interface: str) -> None:
        """Bring `interface` down. Args: interface"""
        self.protocol.run_command(f"ip link set dev {shlex.quote(interface)} down", self.state)

    def dns_lookup(self, hostname: str) -> DNSResult:
        """Resolve `hostname` and return DNSResult dataclass. Args: hostname"""
        out = self.protocol.run_command(f"getent hosts {shlex.quote(hostname)}", self.state)
        ipv4: list[str] = []
        ipv6: list[str] = []
        cname: str | None = None
        for line in out.splitlines():
            parts = line.split()
            if not parts:
                continue
            ip = parts[0]
            if ":" in ip:
                ipv6.append(ip)
            else:
                ipv4.append(ip)
            if not cname and len(parts) > 1:
                cname = parts[1]

        if not (ipv4 or ipv6):
            try:
                dig = self.protocol.run_command(f"dig +short {shlex.quote(hostname)}", self.state)
                for line in dig.splitlines():
                    ip = line.strip()
                    if ip:
                        if ":" in ip:
                            ipv6.append(ip)
                        else:
                            ipv4.append(ip)
            except Exception:
                pass

        return DNSResult(
            hostname=hostname, ipv4_addresses=ipv4, ipv6_addresses=ipv6, canonical_name=cname
        )

    def route_add(self, destination: str, gateway: str, interface: str | None = None) -> None:
        """Add a route to `destination` via `gateway` (optionally `interface`). Args: destination, gateway, interface"""
        cmd = f"ip route add {shlex.quote(destination)} via {shlex.quote(gateway)}"
        if interface:
            cmd += f" dev {shlex.quote(interface)}"
        self.protocol.run_command(cmd, self.state)

    def route_delete(self, destination: str) -> None:
        """Remove route to `destination`. Args: destination"""
        self.protocol.run_command(f"ip route del {shlex.quote(destination)}", self.state)

    def firewall_status(self) -> FirewallStatus:
        """Return firewall status as a FirewallStatus dataclass; tries nftables, ufw, iptables."""
        # try nftables first
        try:
            out = self.protocol.run_command("nft list ruleset", self.state)
            if out.strip():
                return FirewallStatus(backend="nft", status="active", raw=out)
        except Exception:
            pass
        # try ufw
        try:
            out = self.protocol.run_command("ufw status", self.state)
            if "active" in out.lower():
                return FirewallStatus(backend="ufw", status="active", raw=out)
            return FirewallStatus(backend="ufw", status="inactive", raw=out)
        except Exception:
            pass
        # fallback to iptables
        try:
            out = self.protocol.run_command("iptables -L", self.state)
            return FirewallStatus(backend="iptables", status="unknown", raw=out)
        except Exception:
            pass
        return FirewallStatus(backend="unknown", status=None, raw=None)

    def bandwidth(self, interface: str | None = None) -> BandwidthList:
        """Return bandwidth (bytes) RX/TX for all interfaces or a single `interface` using /proc/net/dev."""
        out = self.protocol.run_command("cat /proc/net/dev", self.state)
        items: list[BandwidthInfo] = []
        for line in out.splitlines():
            if ":" not in line:
                continue
            iface, data = line.split(":", 1)
            name = iface.strip()
            parts = data.split()
            if not parts:
                continue
            try:
                rx = int(parts[0])
            except Exception:
                rx = 0
            try:
                tx = int(parts[8]) if len(parts) > 8 else 0
            except Exception:
                tx = 0
            # packets and errors fields may be present at indices; best-effort
            try:
                packets_rx = int(parts[1]) if len(parts) > 1 else 0
            except Exception:
                packets_rx = 0
            try:
                packets_tx = int(parts[9]) if len(parts) > 9 else 0
            except Exception:
                packets_tx = 0
            try:
                errs_in = int(parts[2]) if len(parts) > 2 else 0
            except Exception:
                errs_in = 0
            try:
                errs_out = int(parts[10]) if len(parts) > 10 else 0
            except Exception:
                errs_out = 0
            try:
                drop_in = int(parts[3]) if len(parts) > 3 else 0
            except Exception:
                drop_in = 0
            try:
                drop_out = int(parts[11]) if len(parts) > 11 else 0
            except Exception:
                drop_out = 0

            if interface and name != interface:
                continue

            items.append(
                BandwidthInfo(
                    interface=name,
                    bytes_sent=tx,
                    bytes_received=rx,
                    packets_sent=packets_tx,
                    packets_received=packets_rx,
                    errors_in=errs_in,
                    errors_out=errs_out,
                    dropped_in=drop_in,
                    dropped_out=drop_out,
                )
            )

        return BandwidthList(items=items, count=len(items))
