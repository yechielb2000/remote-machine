"""Firewall actions."""
from __future__ import annotations

import shlex
from typing import List, Optional

from remote_machine.models.remote_state import RemoteState
from remote_machine.protocols.ssh import SSHProtocol
from remote_machine.models.common_types import OperationResult
from remote_machine.models.firewall_types import (
    FirewallRule,
    FirewallChain,
    OpenPort,
    FirewallStatus,
)


class FirewallAction:
    """Firewall operations (iptables)."""

    def __init__(self, protocol: SSHProtocol, state: RemoteState):
        """Initialize firewall actions.

        Args:
            protocol: SSH protocol instance
            state: Remote execution state
        """
        self.protocol = protocol
        self.state = state

    def list_rules(self, chain: Optional[str] = None, table: str = "filter") -> List[FirewallRule]:
        """List firewall rules.

        Args:
            chain: Specific chain to list (e.g., INPUT, OUTPUT, FORWARD). If None, list all.
            table: Iptables table (filter, nat, mangle, raw)

        Returns:
            List of FirewallRule objects
        """
        if chain:
            cmd = f"sudo iptables -t {table} -L {chain} -v -n"
        else:
            cmd = f"sudo iptables -t {table} -L -v -n"

        output = self.protocol.run_command(cmd, self.state)
        rules = []

        lines = output.strip().split("\n")
        # Skip header lines
        for line in lines[2:]:
            if not line.strip():
                continue

            parts = line.split()
            if len(parts) < 6:
                continue

            try:
                rule = FirewallRule(
                    rule_number=int(parts[0]) if parts[0].isdigit() else None,
                    protocol=parts[2],
                    source=parts[3] if len(parts) > 3 else "",
                    destination=parts[4] if len(parts) > 4 else "",
                    source_port=None,
                    destination_port=None,
                    action=parts[1],
                    comment=None,
                )
                rules.append(rule)
            except (ValueError, IndexError):
                continue

        return rules

    def get_chains(self, table: str = "filter") -> List[FirewallChain]:
        """Get all chains and their rules.

        Args:
            table: Iptables table (filter, nat, mangle, raw)

        Returns:
            List of FirewallChain objects with rules
        """
        chains = []
        chain_names = ["INPUT", "OUTPUT", "FORWARD"]

        for chain_name in chain_names:
            rules = self.list_rules(chain=chain_name, table=table)

            # Get default policy
            cmd = f"sudo iptables -t {table} -L {chain_name} | head -1"
            policy_line = self.protocol.run_command(cmd, self.state)
            policy = "ACCEPT"  # Default
            if "DROP" in policy_line:
                policy = "DROP"
            elif "REJECT" in policy_line:
                policy = "REJECT"

            chain = FirewallChain(
                name=chain_name,
                policy=policy,
                packet_count=0,  # Would require parsing from verbose output
                byte_count=0,
                rules=rules,
            )
            chains.append(chain)

        return chains

    def add_rule(
        self,
        chain: str,
        protocol: str,
        destination_port: Optional[str] = None,
        action: str = "ACCEPT",
        source: Optional[str] = None,
        table: str = "filter",
    ) -> OperationResult:
        """Add a firewall rule.

        Args:
            chain: Chain name (INPUT, OUTPUT, FORWARD)
            protocol: Protocol (tcp, udp, icmp, all)
            destination_port: Destination port or port range
            action: Action (ACCEPT, DROP, REJECT)
            source: Source IP or CIDR (optional)
            table: Iptables table

        Returns:
            OperationResult indicating success or failure
        """
        cmd_parts = ["sudo", "iptables", "-t", table, "-A", chain]

        if protocol != "all":
            cmd_parts.extend(["-p", protocol])

        if source:
            cmd_parts.extend(["-s", shlex.quote(source)])

        if destination_port:
            cmd_parts.extend(["--dport", shlex.quote(destination_port)])

        cmd_parts.extend(["-j", action])

        self.protocol.run_command(" ".join(cmd_parts), self.state)
        return OperationResult(success=True, message=f"Rule added to {chain}")

    def delete_rule(
        self,
        chain: str,
        protocol: str,
        destination_port: Optional[str] = None,
        action: str = "ACCEPT",
        source: Optional[str] = None,
        table: str = "filter",
    ) -> OperationResult:
        """Delete a firewall rule.

        Args:
            chain: Chain name (INPUT, OUTPUT, FORWARD)
            protocol: Protocol (tcp, udp, icmp, all)
            destination_port: Destination port or port range
            action: Action (ACCEPT, DROP, REJECT)
            source: Source IP or CIDR (optional)
            table: Iptables table

        Returns:
            OperationResult indicating success or failure
        """
        cmd_parts = ["sudo", "iptables", "-t", table, "-D", chain]

        if protocol != "all":
            cmd_parts.extend(["-p", protocol])

        if source:
            cmd_parts.extend(["-s", shlex.quote(source)])

        if destination_port:
            cmd_parts.extend(["--dport", shlex.quote(destination_port)])

        cmd_parts.extend(["-j", action])

        self.protocol.run_command(" ".join(cmd_parts), self.state)
        return OperationResult(success=True, message=f"Rule deleted from {chain}")

    def delete_rule_by_number(self, chain: str, rule_number: int, table: str = "filter") -> OperationResult:
        """Delete a firewall rule by line number.

        Args:
            chain: Chain name (INPUT, OUTPUT, FORWARD)
            rule_number: Line number of rule to delete
            table: Iptables table

        Returns:
            OperationResult indicating success or failure
        """
        cmd = f"sudo iptables -t {table} -D {chain} {rule_number}"
        self.protocol.run_command(cmd, self.state)
        return OperationResult(success=True, message=f"Rule {rule_number} deleted from {chain}")

    def open_port(
        self, port: int, protocol: str = "tcp", source: Optional[str] = None
    ) -> OperationResult:
        """Open a port in the firewall.

        Args:
            port: Port number
            protocol: Protocol (tcp or udp)
            source: Source IP or CIDR (optional, if None allows all)

        Returns:
            OperationResult indicating success or failure
        """
        return self.add_rule(
            chain="INPUT",
            protocol=protocol,
            destination_port=str(port),
            action="ACCEPT",
            source=source,
        )

    def close_port(
        self, port: int, protocol: str = "tcp", source: Optional[str] = None
    ) -> OperationResult:
        """Close a port in the firewall.

        Args:
            port: Port number
            protocol: Protocol (tcp or udp)
            source: Source IP or CIDR (optional)

        Returns:
            OperationResult indicating success or failure
        """
        return self.delete_rule(
            chain="INPUT",
            protocol=protocol,
            destination_port=str(port),
            action="ACCEPT",
            source=source,
        )

    def set_default_policy(
        self, chain: str, policy: str, table: str = "filter"
    ) -> OperationResult:
        """Set default policy for a chain.

        Args:
            chain: Chain name (INPUT, OUTPUT, FORWARD)
            policy: Policy (ACCEPT, DROP, REJECT)
            table: Iptables table

        Returns:
            OperationResult indicating success or failure
        """
        cmd = f"sudo iptables -t {table} -P {chain} {policy}"
        self.protocol.run_command(cmd, self.state)
        return OperationResult(success=True, message=f"Default policy for {chain} set to {policy}")

    def flush_chain(self, chain: Optional[str] = None, table: str = "filter") -> OperationResult:
        """Flush (clear) all rules from a chain.

        Args:
            chain: Chain name. If None, flushes all chains.
            table: Iptables table

        Returns:
            OperationResult indicating success or failure
        """
        if chain:
            cmd = f"sudo iptables -t {table} -F {chain}"
            msg = f"Chain {chain} flushed"
        else:
            cmd = f"sudo iptables -t {table} -F"
            msg = "All chains flushed"

        self.protocol.run_command(cmd, self.state)
        return OperationResult(success=True, message=msg)

    def save_rules(self) -> OperationResult:
        """Save firewall rules to persistent storage.

        Returns:
            OperationResult indicating success or failure
        """
        # Try iptables-save first
        try:
            self.protocol.run_command("sudo iptables-save | sudo tee /etc/iptables/rules.v4 > /dev/null", self.state)
            return OperationResult(success=True, message="Rules saved to /etc/iptables/rules.v4")
        except:
            # Fallback to other methods
            try:
                self.protocol.run_command("sudo sh -c 'iptables-save > /etc/iptables.rules'", self.state)
                return OperationResult(success=True, message="Rules saved to /etc/iptables.rules")
            except:
                return OperationResult(
                    success=False,
                    message="Could not save rules - ensure iptables-persistent is installed"
                )

    def restore_rules(self, rules_file: str = "/etc/iptables/rules.v4") -> OperationResult:
        """Restore firewall rules from file.

        Args:
            rules_file: Path to rules file

        Returns:
            OperationResult indicating success or failure
        """
        cmd = f"sudo iptables-restore < {shlex.quote(rules_file)}"
        self.protocol.run_command(cmd, self.state)
        return OperationResult(success=True, message=f"Rules restored from {rules_file}")

    def get_status(self) -> FirewallStatus:
        """Get overall firewall status.

        Returns:
            FirewallStatus object with all information
        """
        # Check if firewall is enabled
        try:
            self.protocol.run_command("sudo iptables -L -n > /dev/null 2>&1", self.state)
            enabled = True
        except:
            enabled = False

        chains = self.get_chains() if enabled else []

        # Count total rules
        total_rules = sum(len(chain.rules) for chain in chains)

        # Try to get open ports (simplified)
        open_ports = []
        for chain in chains:
            if chain.name == "INPUT":
                for rule in chain.rules:
                    if rule.action == "ACCEPT" and rule.destination_port:
                        try:
                            port = int(rule.destination_port)
                            open_ports.append(
                                OpenPort(
                                    port=port,
                                    protocol=rule.protocol,
                                    state="OPEN",
                                    service=None,
                                )
                            )
                        except ValueError:
                            continue

        return FirewallStatus(
            enabled=enabled,
            chains=chains,
            open_ports=open_ports,
            total_rules=total_rules,
        )

    def enable_ufw(self) -> OperationResult:
        """Enable UFW (Uncomplicated Firewall).

        Returns:
            OperationResult indicating success or failure
        """
        self.protocol.run_command("sudo ufw enable", self.state)
        return OperationResult(success=True, message="UFW enabled")

    def disable_ufw(self) -> OperationResult:
        """Disable UFW.

        Returns:
            OperationResult indicating success or failure
        """
        self.protocol.run_command("sudo ufw disable", self.state)
        return OperationResult(success=True, message="UFW disabled")

    def ufw_allow_port(self, port: int, protocol: str = "tcp") -> OperationResult:
        """Allow port using UFW.

        Args:
            port: Port number
            protocol: Protocol (tcp or udp)

        Returns:
            OperationResult indicating success or failure
        """
        cmd = f"sudo ufw allow {port}/{protocol}"
        self.protocol.run_command(cmd, self.state)
        return OperationResult(success=True, message=f"Port {port}/{protocol} allowed via UFW")

    def ufw_deny_port(self, port: int, protocol: str = "tcp") -> OperationResult:
        """Deny port using UFW.

        Args:
            port: Port number
            protocol: Protocol (tcp or udp)

        Returns:
            OperationResult indicating success or failure
        """
        cmd = f"sudo ufw deny {port}/{protocol}"
        self.protocol.run_command(cmd, self.state)
        return OperationResult(success=True, message=f"Port {port}/{protocol} denied via UFW")

    def ufw_status(self) -> str:
        """Get UFW status.

        Returns:
            UFW status output
        """
        return self.protocol.run_command("sudo ufw status verbose", self.state)
