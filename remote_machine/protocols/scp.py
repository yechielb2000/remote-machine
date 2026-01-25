"""SCP protocol implemented using Paramiko SFTP (transport-only).

This module implements a small SCPProtocol class which performs uploads
and chunked downloads via an active SSHProtocol (Paramiko SSHClient).

Notes:
- Uses Paramiko SFTP (open_sftp())
- Does not expose SFTP client objects
- Maps common exceptions to remote_machine error types
- All results are dataclasses (SCPResult)
"""

from __future__ import annotations

import paramiko
from pathlib import Path

from remote_machine.errors.exceptions import ConnectionError, NotFound, PermissionDenied
from remote_machine.models.scp_types import SCPResult
from remote_machine.protocols.ssh import SSHProtocol


class SCPProtocol:
    """SCP transport implemented over Paramiko SFTP.

    This class requires an already-instantiated SSHProtocol (which should
    already be connected if operations are to succeed).
    """

    def __init__(self, ssh: SSHProtocol | object):
        """Initialize with an object that acts like an SSH protocol wrapper.

        Accepts either an SSHProtocol or a duck-typed object that exposes a
        connected client via the `_client` attribute.
        """
        self._ssh = ssh
        self._sftp_client: paramiko.SFTPClient | None = None

    @property
    def sftp_client(self) -> paramiko.SFTPClient:
        """Return a new SFTP client created from the underlying SSH client.

        Raises:
            ConnectionError: if ssh client is not connected or paramiko raises.
        """
        if not self._ssh.is_connected:
            raise ConnectionError("SSH client is not connected")
        if self._sftp_client is None:
            try:
                self._sftp_client = self._ssh._client.open_sftp()
            except paramiko.SSHException as e:
                raise ConnectionError("Failed to create SFTP client") from e
        return self._sftp_client

    def download(
        self, remote_path: str, local_path: Path, chunk_size: int = 1024 * 1024
    ) -> SCPResult:
        """Download a remote file in fixed-size chunks and write to a local file.

        Args:
            remote_path: path on remote machine
            local_path: local path to write to
            chunk_size: size of each chunk to read (bytes)

        Returns:
            SCPResult with source, destination and bytes_transferred

        Raises:
            NotFound, PermissionDenied, CommandError, ConnectionError
        """
        bytes_transferred = 0

        try:
            with self.sftp_client.open(remote_path, "rb") as remote_file:
                with open(local_path, "wb") as local_file:
                    while True:
                        chunk = remote_file.read(chunk_size)
                        if not chunk:
                            break
                        local_file.write(chunk)
                        bytes_transferred += len(chunk)
                return SCPResult(
                    source=remote_path,
                    destination=str(local_path),
                    bytes_transferred=bytes_transferred,
                )

        except FileNotFoundError as e:
            raise NotFound(f"File not found: {remote_path}") from e
        except PermissionError as e:
            raise PermissionDenied(f"Permission denied for: {remote_path}") from e

    def upload(self, local_path: Path, remote_path: str) -> SCPResult:
        """Upload a local file to the remote path using SFTP put().

        Args:
            local_path: path to the local file (must exist)
            remote_path: destination path on remote

        Returns:
            SCPResult with source, destination and bytes_transferred

        Raises:
            NotFound, PermissionDenied, CommandError, ConnectionError
        """
        if not local_path.exists() or not local_path.is_file():
            raise NotFound(f"Local file not found: {local_path}")

        try:
            self.sftp_client.put(str(local_path), remote_path)
            bytes_transferred = local_path.stat().st_size
        finally:
            try:
                self.sftp_client.close()
            except Exception:
                pass

        return SCPResult(
            source=str(local_path), destination=remote_path, bytes_transferred=bytes_transferred
        )
