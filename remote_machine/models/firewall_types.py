"""Firewall action result types."""

from dataclasses import dataclass
from typing import List, Optional


@dataclass(frozen=True)
class FirewallRule:
    """Firewall rule information."""

    rule_number: Optional[int]  # Line number in iptables (if available)
    protocol: str  # tcp, udp, icmp, all
    source: str  # Source IP or CIDR
    destination: str  # Destination IP or CIDR
    source_port: Optional[str]  # Source port or port range
    destination_port: Optional[str]  # Destination port or port range
    action: str  # ACCEPT, DROP, REJECT, etc.
    comment: Optional[str]  # Rule comment/description


@dataclass(frozen=True)
class FirewallChain:
    """Firewall chain information."""

    name: str  # Chain name (INPUT, OUTPUT, FORWARD, etc.)
    policy: str  # Default policy (ACCEPT, DROP, REJECT)
    packet_count: int  # Number of packets processed
    byte_count: int  # Number of bytes processed
    rules: List[FirewallRule]  # Rules in this chain


@dataclass(frozen=True)
class OpenPort:
    """Open/listening port information."""

    port: int
    protocol: str  # tcp or udp
    state: str  # OPEN, ESTABLISHED, LISTENING, etc.
    service: Optional[str]  # Service name (http, ssh, etc.)


@dataclass(frozen=True)
class FirewallStatus:
    """Overall firewall status."""

    enabled: bool  # Is firewall active
    chains: List[FirewallChain]  # All chains
    open_ports: List[OpenPort]  # Open ports
    total_rules: int  # Total rules across all chains
