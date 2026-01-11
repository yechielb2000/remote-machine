"""
ProxyAction for RemoteMachine.

Supports:
- Local forward
- Remote forward (reverse)
- Connecting new RemoteMachine over a tunnel
- Proxy tracking in state.proxies
"""

import socket
import threading
import select
from typing import Optional

import paramiko

from remote_machine.models.proxy_types import Proxy
from remote_machine.protocols.ssh import SSHProtocol


class ProxyAction:
    """Manage SSH tunnels over an existing RemoteMachine."""

    def __init__(self, rm: "RemoteMachine"):
        self._rm = rm

    def forward(
        self,
        local_port: int,
        remote_host: str,
        remote_port: int,
        local_host: str = "127.0.0.1",
    ) -> Proxy:
        """
        Local forward: local_host:local_port -> remote_host:remote_port
        """
        ssh: SSHProtocol = self._rm.connection_layer()

        proxy = Proxy(
            local_host=local_host,
            local_port=local_port,
            remote_host=remote_host,
            remote_port=remote_port,
            mode="forward",
        )

        def _loop():
            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server.bind((proxy.local_host, proxy.local_port))
            server.listen(5)
            proxy.running = True

            try:
                while proxy.running and ssh.is_connected():
                    try:
                        client_sock, addr = server.accept()
                    except OSError:
                        break
                    chan = ssh.transport.open_channel(
                        "direct-tcpip", (proxy.remote_host, proxy.remote_port), addr
                    )
                    proxy._channel = chan
                    threading.Thread(
                        target=self._pipe, args=(client_sock, chan, proxy), daemon=True
                    ).start()
            finally:
                server.close()
                proxy.running = False

        proxy._thread = threading.Thread(target=_loop, daemon=True)
        proxy._thread.start()
        self._rm.state.proxies.append(proxy)
        return proxy

    def reverse(
        self,
        remote_port: int,
        local_host: str,
        local_port: int,
    ) -> Proxy:
        """
        Remote forward: remote_port on SSH host -> local_host:local_port
        """
        ssh: SSHProtocol = self._rm.connection_layer()

        proxy = Proxy(
            local_host=local_host,
            local_port=local_port,
            remote_host="0.0.0.0",
            remote_port=remote_port,
            mode="reverse",
        )

        def _loop():
            transport = ssh.transport
            transport.request_port_forward("0.0.0.0", remote_port)
            proxy.running = True
            while proxy.running and ssh.is_connected():
                chan = transport.accept(timeout=1)
                if not chan:
                    continue
                sock = socket.create_connection((local_host, local_port))
                threading.Thread(target=self._pipe, args=(chan, sock, proxy), daemon=True).start()
            proxy.running = False

        proxy._thread = threading.Thread(target=_loop, daemon=True)
        proxy._thread.start()
        self._rm.state.proxies.append(proxy)
        return proxy

    @staticmethod
    def _pipe(a: socket.socket | paramiko.Channel, b: socket.socket | paramiko.Channel, proxy: Proxy):
        """Pipe data between two sockets/channels."""
        sockets = [a, b]
        try:
            while proxy.running:
                r, _, _ = select.select(sockets, [], [], 1)
                for s in r:
                    data = s.recv(4096)
                    if not data:
                        return
                    if s is a:
                        b.sendall(data)
                    else:
                        a.sendall(data)
        finally:
            try: a.close()
            except: pass
            try: b.close()
            except: pass
            proxy.running = False

    def connect_tunnel(
        self,
        proxy: Proxy,
        user: str,
        key_path: Optional[str] = None,
        password: Optional[str] = None,
        port: int = 22,
    ) -> "RemoteMachine":
        """
        Connect a new RemoteMachine over the given tunnel.

        Returns:
            RemoteMachine connected over the tunnel, automatically chained.
        """
        sock = socket.create_connection((proxy.local_host, proxy.local_port))
        transport = paramiko.Transport(sock)
        transport.start_client(timeout=10)

        if key_path:
            key = paramiko.RSAKey.from_private_key_file(key_path)
            transport.auth_publickey(user, key)
        elif password:
            transport.auth_password(user, password)
        else:
            raise ValueError("Must provide key_path or password for auth")

        # New SSHProtocol over the tunnel
        ssh_proto = SSHProtocol.__new__(SSHProtocol)
        ssh_proto.transport = transport
        ssh_proto.host = proxy.remote_host
        ssh_proto.user = user
        ssh_proto.port = port

        from remote_machine.core import RemoteMachine
        
        # New RemoteMachine
        rm2 = RemoteMachine.__new__(RemoteMachine)
        rm2._ssh_layers = self._rm._ssh_layers + [ssh_proto]  # append new layer
        rm2._protocols = dict(self._rm._protocols)
        rm2._protocols["ssh"] = ssh_proto
        rm2.state = self._rm.state  # share state optionally
        rm2.fs = rm2.fs.__class__(rm2, rm2.state)
        rm2.ps = rm2.ps.__class__(rm2, rm2.state)
        rm2.net = rm2.net.__class__(rm2, rm2.state)
        rm2.env = rm2.env.__class__(rm2, rm2.state)
        rm2.sys = rm2.sys.__class__(rm2, rm2.state)
        rm2.service = rm2.service.__class__(rm2, rm2.state)
        rm2.device = rm2.device.__class__(rm2, rm2.state)
        rm2.proxy = ProxyAction(rm2)
        rm2.parent = self._rm  # track chain

        return rm2
