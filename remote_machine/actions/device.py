"""Device management actions."""
from __future__ import annotations

from remote_machine.models.remote_state import RemoteState
from remote_machine.protocols.ssh import SSHProtocol
from remote_machine.utils.error_mapper import ErrorMapper


class DeviceAction:
    """Hardware device management operations."""

    def __init__(self, protocol: SSHProtocol, state: RemoteState):
        """Initialize device actions.

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

    def list(self) -> list[dict]:
        """Return list of device info dicts."""
        # Stub implementation - will be populated in Phase 2
        return []

    def list_pci(self) -> list[dict]:
        """Return list of PCI device dicts."""
        # Stub implementation - will be populated in Phase 2
        return []

    def list_usb(self) -> list[dict]:
        """Return list of USB device dicts."""
        # Stub implementation - will be populated in Phase 2
        return []

    def list_block(self) -> list[dict]:
        """Return list of block device dicts."""
        try:
            # prefer lsblk JSON output
            out = self._run("lsblk -J -o NAME,TYPE,SIZE,MOUNTPOINT")
            import json

            j = json.loads(out)
            # convert to a flat list of devices
            devices = []
            def walk(node):
                if isinstance(node, dict):
                    devices.append(node)
                    for c in node.get("children", []) or []:
                        walk(c)
            for d in j.get("blockdevices", []) or []:
                walk(d)
            return devices
        except Exception:
            # fallback to /proc/partitions (handle variable headers)
            out = self._run("cat /proc/partitions")
            devices = []
            for line in out.splitlines():
                if not line.strip() or line.strip().lower().startswith("major"):
                    continue
                parts = line.split()
                if len(parts) >= 4:
                    devices.append({"major": parts[0], "minor": parts[1], "blocks": parts[2], "name": parts[3]})
            return devices

    def get_device_info(self, device: str) -> dict:
        """Return detailed info for `device` as a dict.

        Args: device: device name or path
        """
        # Stub implementation - will be populated in Phase 2
        return {}

    def mount(self, device: str, path: str, fstype: str | None = None) -> None:
        """Mount `device` at `path` (optional fstype).

        Args: device, path, fstype
        """
        # Stub implementation - will be populated in Phase 2
        pass

    def unmount(self, path: str, force: bool = False) -> None:
        """Unmount filesystem at `path` (force if requested)."""
        # Stub implementation - will be populated in Phase 2
        pass

    def mounted(self) -> list[dict]:
        """Return list of mounted filesystem dicts."""
        out = self._run("cat /proc/mounts")
        try:
            from linux_parsers.parsers.filesystem.mount import parse as _parse_mount  # type: ignore
            parsed = _parse_mount(out)
            if isinstance(parsed, list):
                return parsed
        except Exception:
            pass

        # Fallback: simple parse
        mounts = []
        for line in out.splitlines():
            parts = line.split()
            if len(parts) >= 3:
                mounts.append({"device": parts[0], "mount_point": parts[1], "fstype": parts[2]})
        return mounts

    def mount_options(self, path: str) -> dict:
        """Return mount options for `path` as a dict.

        Args: path: mount point
        """
        mounts = self.mounted()
        for m in mounts:
            mp = m.get("mount_point") or m.get("mountpoint") or m.get("target")
            if mp == path:
                opts = m.get("options") or m.get("opts")
                return {"options": opts} if opts else {}
        return {}

    def fsck(self, device: str, fix: bool = False) -> dict:
        """Run fsck on `device`, optionally attempting fixes.

        Args: device, fix
        """
        # Stub implementation - will be populated in Phase 2
        return {}

    def mkfs(self, device: str, fstype: str) -> None:
        """Create filesystem `fstype` on `device`. Args: device, fstype"""
        # Stub implementation - will be populated in Phase 2
        pass

    def smartctl(self, device: str) -> dict:
        """Return SMART data for `device` as dict. Args: device"""
        # Stub implementation - will be populated in Phase 2
        return {}

    def temperature(self, device: str | None = None) -> dict:
        """Return temperature info for `device` or all devices as dict."""
        # Stub implementation - will be populated in Phase 2
        return {}

    def power_status(self, device: str | None = None) -> dict:
        """Return power status for `device` or all devices as dict."""
        # Stub implementation - will be populated in Phase 2
        return {}

    def enable_device(self, device: str) -> None:
        """Enable `device`. Args: device"""
        # Stub implementation - will be populated in Phase 2
        pass

    def disable_device(self, device: str) -> None:
        """Disable `device`. Args: device"""
        # Stub implementation - will be populated in Phase 2
        pass

    def rescan_bus(self, bus: str) -> None:
        """Rescan device `bus` (e.g., 'pci' or 'usb'). Args: bus"""
        # Stub implementation - will be populated in Phase 2
        pass

    def get_firmware(self, device: str) -> str:
        """Return firmware version string for `device`. Args: device"""
        # Stub implementation - will be populated in Phase 2
        return ""

    def update_firmware(self, device: str, firmware_path: str) -> None:
        """Update `device` firmware from `firmware_path`. Args: device, firmware_path"""
        # Stub implementation - will be populated in Phase 2
        pass

    def gpio_list(self) -> list[dict]:
        """Return list of GPIO pin info dicts."""
        # Stub implementation - will be populated in Phase 2
        return []

    def gpio_read(self, pin: int) -> int:
        """Read value of GPIO `pin` and return 0 or 1. Args: pin"""
        # Stub implementation - will be populated in Phase 2
        return 0

    def gpio_write(self, pin: int, value: int) -> None:
        """Write GPIO pin value.

        Args:
            pin: GPIO pin number
            value: Pin value to set (0 or 1)
        """
        # Stub implementation - will be populated in Phase 2
        pass