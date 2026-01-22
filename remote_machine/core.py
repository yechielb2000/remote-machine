"""
Core RemoteMachine class with multi-hop SSH/proxy support.
"""

from __future__ import annotations
from typing import Dict, Any, Optional, List

from remote_machine import actions
from remote_machine.errors import ProtocolNotAvailable, PermissionDenied
from remote_machine.models.capabilities import Capabilities
from remote_machine.models.remote_state import RemoteState
from remote_machine.protocols.ssh import SSHProtocol


class RemoteMachine:
    """
    Main entry point for remote machine operations.

    Supports:
    - SSH connection and multi-hop chains
    - Proxies and tunnels
    - Remote state tracking (cwd, uid, sudo, proxies)
    - Action instances (fs, ps, net, env, sys, service, device)
    """

    parent: Optional["RemoteMachine"] = None

    def __init__(
        self,
        host: str,
        user: str,
        key_path: Optional[str] = None,
        password: Optional[str] = None,
        port: int = 22,
        parent: Optional["RemoteMachine"] = None,
    ):
        self._ssh_layers: List[SSHProtocol] = []
        self._protocols: Dict[str, Any] = {}
        self.parent = parent

        ssh = SSHProtocol(host=host, user=user, key_path=key_path, password=password, port=port)
        self._protocols["ssh"] = ssh
        self._ssh_layers.append(ssh)

        self.state = RemoteState()

        # Actions
        self.fs = actions.FSAction(ssh, self.state)
        self.ps = actions.PSAction(ssh, self.state)
        self.net = actions.NETAction(ssh, self.state)
        self.env = actions.ENVAction(ssh, self.state)
        self.sys = actions.SYSAction(ssh, self.state)
        self.service = actions.ServiceAction(ssh, self.state)
        self.device = actions.DeviceAction(ssh, self.state)
        self.docker = actions.DockerAction(ssh, self.state)
        self.git = actions.GitAction(ssh, self.state)
        self.firewall = actions.FirewallAction(ssh, self.state)
        self.cron = actions.CronAction(ssh, self.state)
        self.pythonenv = actions.PythonEnvAction(ssh, self.state)
        self.onie = actions.ONIEAction(ssh, self.state)
        self.proxy = actions.ProxyAction(self)

    def connection_layer(self, layer_index: int = -1) -> SSHProtocol:
        """Return SSHProtocol at a specific layer (supports multi-hop)."""
        return self._ssh_layers[layer_index]

    def protocol(self, name: str) -> Any:
        """Return a protocol by name."""
        if name not in self._protocols:
            raise ProtocolNotAvailable({name})
        return self._protocols[name]

    def ensure_root(self) -> None:
        if self.state.uid != 0:
            raise PermissionDenied("Root privileges required")

    def ensure_sudo(self) -> None:
        if not self.state.has_sudo:
            raise PermissionDenied("Sudo privileges required")

    def connect(self) -> None:
        """Connect all SSH layers and initialize remote state."""
        for ssh in self._ssh_layers:
            ssh.connect()
        self._initialize_state()

    def disconnect(self) -> None:
        """Disconnect all proxies and SSH layers."""
        # Stop all proxies
        for proxy in self.state.proxies:
            proxy.running = False
        # Disconnect all SSH layers
        for ssh in self._ssh_layers:
            ssh.disconnect()

    def expand_scp(self) -> None:
        """Attach SCP protocol using existing SSH transport."""
        if "ssh" not in self._protocols:
            raise ProtocolNotAvailable({"ssh"})

        from remote_machine.protocols.scp import SCPProtocol
        self._protocols["scp"] = SCPProtocol(self._protocols["ssh"])

    def capabilities(self) -> Capabilities:
        """Return currently available protocols and actions."""
        return Capabilities(
            protocols=set(self._protocols.keys()),
            actions={"fs", "ps", "net", "env", "sys", "service", "device", "docker", "git", "firewall", "cron"},
        )

    def __enter__(self) -> "RemoteMachine":
        self.connect()
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback) -> None:
        self.disconnect()

    def _initialize_state(self) -> None:
        """Populate RemoteState fields (cwd, uid, sudo)."""
        ssh: SSHProtocol = self._protocols["ssh"]

        # UID
        result = ssh.exec("id -u", self.state)
        self.state.uid = int(result.stdout.strip())

        # CWD
        result = ssh.exec("pwd", self.state)
        self.state.cwd = result.stdout.strip()

        # Sudo availability
        result = ssh.exec("sudo -n true", self.state)
        self.state.has_sudo = result.exit_code == 0

    def add_ssh_layer(self, ssh: SSHProtocol) -> None:
        """Add an SSHProtocol to the layers (for tunnel chaining)."""
        self._ssh_layers.append(ssh)
        self._protocols["ssh"] = ssh  # optional: latest layer replaces "ssh"
