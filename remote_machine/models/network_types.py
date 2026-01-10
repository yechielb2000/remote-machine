"""Network action result types."""

from dataclasses import dataclass
from ipaddress import IPv4Address, IPv6Address


@dataclass(frozen=True)
class InterfaceInfo:
    """Network interface information."""

    name: str
    mtu: int
    isup: bool
    is_running: bool
    mac_address: str
    ipv4_addresses: list[IPv4Address]
    ipv6_addresses: list[IPv6Address]
    broadcast: str | None
    netmask: str | None
    speed: int | None  # in Mbps


@dataclass(frozen=True)
class IPAddress:
    """IP address information."""

    interface: str
    address: str
    family: str  # 'IPv4' or 'IPv6'
    netmask: str | None
    broadcast: str | None
    gateway: str | None


@dataclass(frozen=True)
class IPAddressList:
    """List of IP addresses."""

    addresses: list[IPAddress]
    count: int


@dataclass(frozen=True)
class Route:
    """Routing table entry."""

    destination: str
    gateway: str
    netmask: str
    flags: str
    metric: int
    interface: str


@dataclass(frozen=True)
class RoutingTable:
    """Routing table information."""

    routes: list[Route]
    count: int


@dataclass(frozen=True)
class TCPConnection:
    """TCP connection information."""

    local_address: str
    local_port: int
    remote_address: str
    remote_port: int
    state: str  # 'ESTABLISHED', 'LISTEN', etc.
    pid: int | None
    process_name: str | None


@dataclass(frozen=True)
class ConnectionList:
    """List of TCP connections."""

    connections: list[TCPConnection]
    count: int


@dataclass(frozen=True)
class ListeningPort:
    """Listening port information."""

    address: str
    port: int
    protocol: str  # 'tcp', 'udp'
    state: str
    pid: int | None
    process_name: str | None


@dataclass(frozen=True)
class ListeningPortList:
    """List of listening ports."""

    ports: list[ListeningPort]
    count: int


@dataclass(frozen=True)
class DNSResult:
    """DNS lookup result."""

    hostname: str
    ipv4_addresses: list[str]
    ipv6_addresses: list[str]
    canonical_name: str | None


@dataclass(frozen=True)
class PingResult:
    """Ping result information."""

    host: str
    transmitted: int
    received: int
    packets_lost: int
    loss_percent: float
    min_time: float
    max_time: float
    avg_time: float
    stddev_time: str | None


@dataclass(frozen=True)
class BandwidthInfo:
    """Bandwidth usage information."""

    interface: str | None
    bytes_sent: int
    bytes_received: int
    packets_sent: int
    packets_received: int
    errors_in: int
    errors_out: int
    dropped_in: int
    dropped_out: int


@dataclass(frozen=True)
class BandwidthList:
    """List of bandwidth usage entries."""

    items: list[BandwidthInfo]
    count: int


@dataclass(frozen=True)
class FirewallStatus:
    """Firewall backend status."""

    backend: str
    status: str | None
    raw: str | None


@dataclass(frozen=True)
class NetworkStats:
    """Network statistics."""

    interfaces: list[str]
    total_bytes_sent: int
    total_bytes_received: int
    total_packets_sent: int
    total_packets_received: int


@dataclass(frozen=True)
class InterfaceList:
    """List of interface names."""

    interfaces: list[str]
    count: int
