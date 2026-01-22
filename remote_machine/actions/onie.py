"""ONIE actions."""
from __future__ import annotations

import shlex
from typing import Literal

from remote_machine.protocols.ssh import SSHProtocol
from remote_machine.models.remote_state import RemoteState
from remote_machine.errors.error_mapper import ErrorMapper
from remote_machine.models.common_types import OperationResult


class ONIEAction:
    """ONIE (Open Network Install Environment) operations."""

    def __init__(self, protocol: SSHProtocol, state: RemoteState):
        self.protocol = protocol
        self.state = state

    def _run(self, cmd: str) -> str:
        result = self.protocol.exec(cmd, self.state)
        ErrorMapper.raise_if_error(result)
        return result.stdout

    def version(self) -> str:
        """Get ONIE version."""
        return self._run("onie-version")

    def discovery_start(self) -> OperationResult:
        self._run("onie-discovery-start")
        return OperationResult(True, "ONIE discovery started")

    def discovery_stop(self) -> OperationResult:
        self._run("onie-discovery-stop")
        return OperationResult(True, "ONIE discovery stopped")

    def install(
        self,
        image_url: str,
        automated: bool = True,
        force: bool = False,
        nos_install: bool = False,
    ) -> OperationResult:
        """
        Install a NOS using ONIE.

        Args:
            image_url: URL to image
            automated: Use -a
            force: Use -f
            nos_install: Use --nos-install (vendor specific)
        """
        flags = []
        if automated:
            flags.append("-a")
        if force:
            flags.append("-f")
        if nos_install:
            flags.append("--nos-install")

        flag_str = " ".join(flags)
        self._run(f"onie-install {flag_str} {shlex.quote(image_url)}")
        return OperationResult(True, f"ONIE install started: {image_url}")

    def uninstall(self, force: bool = False) -> OperationResult:
        flag = "-f" if force else ""
        self._run(f"onie-uninstall {flag}")
        return OperationResult(True, "NOS uninstall initiated")

    def get_boot_mode(self) -> str:
        """Get current ONIE boot mode."""
        return self._run("onie-boot-mode -g").strip()

    def set_boot_mode(self, mode: Literal["install", "rescue", "uninstall", "normal", "update"]) -> OperationResult:
        """Set ONIE boot mode."""
        self._run(f"onie-boot-mode -s {shlex.quote(mode)}")
        return OperationResult(True, f"Boot mode set to {mode}")

    def clear_boot_mode(self) -> OperationResult:
        self._run("onie-boot-mode -c")
        return OperationResult(True, "Boot mode cleared")

    def self_update(self) -> OperationResult:
        self._run("onie-self-update")
        return OperationResult(True, "ONIE self-update triggered")

    def rescue(self) -> OperationResult:
        """Enter ONIE rescue environment."""
        self._run("onie-rescue")
        return OperationResult(True, "Entered ONIE rescue mode")

    def reboot(self) -> OperationResult:
        self._run("reboot")
        return OperationResult(True, "System reboot initiated")

    def poweroff(self) -> OperationResult:
        self._run("poweroff")
        return OperationResult(True, "System powered off")
