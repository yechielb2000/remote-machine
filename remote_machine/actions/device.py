"""Device management actions."""
from __future__ import annotations
import shlex

from remote_machine.models.remote_state import RemoteState
from remote_machine.protocols.ssh import SSHProtocol
from remote_machine.errors.error_mapper import ErrorMapper

from remote_machine.models import (
    DeviceInfo
)

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

    def list(self) -> list[DeviceInfo]:
        """Return list of device info."""
        devices = []

        # Get basic device list from /sys/devices
        try:
            output = self._run("find /sys/devices -name 'modalias' 2>/dev/null | head -20")
            for line in output.splitlines():
                if line.strip():
                    device_path = line.replace("/modalias", "")
                    device_name = device_path.split("/")[-1]

                    devices.append(DeviceInfo(
                        name=device_name,
                        device_path=device_path,
                        vendor="unknown",
                        model="unknown",
                        driver=None,
                        enabled=True,
                        power_state="unknown"
                    ))
        except Exception:
            pass

        return devices

    def list_pci(self) -> list[dict]:
        """Return list of PCI device info."""
        try:
            from linux_parsers.parsers.hardware.lspci import parse as _parse_lspci
            output = self._run("lspci -v")
            parsed = _parse_lspci(output)

            if isinstance(parsed, list):
                return parsed
        except Exception:
            pass

        # Fallback parsing
        try:
            output = self._run("lspci")
            devices = []

            for line in output.splitlines():
                if not line.strip():
                    continue

                parts = line.split(" ", 2)
                if len(parts) >= 3:
                    devices.append({
                        "address": parts[0],
                        "class": parts[1].rstrip(":"),
                        "description": parts[2],
                        "vendor": "unknown",
                        "device": "unknown"
                    })

            return devices
        except Exception:
            return []

    def list_usb(self) -> list[dict]:
        """Return list of USB device info."""
        try:
            from linux_parsers.parsers.hardware.lsusb import parse as _parse_lsusb
            output = self._run("lsusb")
            parsed = _parse_lsusb(output)

            if isinstance(parsed, list):
                return parsed
        except Exception:
            pass

        # Fallback parsing
        try:
            output = self._run("lsusb")
            devices = []

            for line in output.splitlines():
                if "Bus" in line and "Device" in line:
                    parts = line.split()
                    if len(parts) >= 6:
                        bus = parts[1]
                        device = parts[3].rstrip(":")
                        vendor_product = parts[5]
                        description = " ".join(parts[6:]) if len(parts) > 6 else ""

                        vendor_id, product_id = vendor_product.split(":")

                        devices.append({
                            "bus": bus,
                            "device": device,
                            "vendor_id": vendor_id,
                            "product_id": product_id,
                            "description": description
                        })

            return devices
        except Exception:
            return []

    def list_block(self) -> list[dict]:
        """Return list of block device info."""
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
        """Return detailed info for `device`.

        Args: device: device name or path
        """
        try:
            # Try to get device info from multiple sources
            info = {"device": device}

            # Get basic info from /sys
            if not device.startswith("/dev/"):
                device_path = f"/dev/{device}"
            else:
                device_path = device

            try:
                # Get device size
                size_output = self._run(f"blockdev --getsize64 {device_path}")
                info["size"] = int(size_output.strip())
            except Exception:
                pass

            try:
                # Get device model/vendor
                sys_path = f"/sys/block/{device.replace('/dev/', '')}"
                model_output = self._run(f"cat {sys_path}/device/model 2>/dev/null || echo ''")
                vendor_output = self._run(f"cat {sys_path}/device/vendor 2>/dev/null || echo ''")

                info["model"] = model_output.strip()
                info["vendor"] = vendor_output.strip()
            except Exception:
                pass

            return info
        except Exception:
            return {"device": device}

    def mount(self, device: str, path: str, fstype: str | None = None) -> None:
        """Mount `device` at `path` (optional fstype).

        Args: device, path, fstype
        """
        cmd = f"mount"
        if fstype:
            cmd += f" -t {fstype}"
        cmd += f" {shlex.quote(device)} {shlex.quote(path)}"
        self._run(cmd)

    def unmount(self, path: str, force: bool = False) -> None:
        """Unmount filesystem at `path` (force if requested)."""
        cmd = f"umount"
        if force:
            cmd += " -f"
        cmd += f" {shlex.quote(path)}"
        self._run(cmd)

    def mounted(self) -> list[dict]:
        """Return list of mounted filesystem info."""
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
        """Return mount options for `path`.

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
        import shlex
        cmd = f"fsck"
        if fix:
            cmd += " -y"
        else:
            cmd += " -n"
        cmd += f" {shlex.quote(device)}"

        try:
            output = self._run(cmd)
            return {"status": "clean", "output": output, "device": device}
        except Exception as e:
            return {"status": "error", "output": str(e), "device": device}

    def mkfs(self, device: str, fstype: str) -> None:
        """Create filesystem `fstype` on `device`. Args: device, fstype"""
        self._run(f"mkfs.{fstype} {shlex.quote(device)}")

    def smartctl(self, device: str) -> dict:
        """Return SMART data for `device`. Args: device"""
        try:
            from linux_parsers.parsers.hardware.smartctl import parse as _parse_smart
            output = self._run(f"smartctl -a {shlex.quote(device)}")
            parsed = _parse_smart(output)

            if isinstance(parsed, dict):
                return parsed
        except Exception:
            pass

        # Fallback parsing
        try:
            output = self._run(f"smartctl -a {shlex.quote(device)}")
            return {"device": device, "output": output, "status": "unknown"}
        except Exception:
            return {"device": device, "status": "not_available"}

    def temperature(self, device: str | None = None) -> dict:
        """Return temperature info for `device` or all devices."""
        try:
            if device:
                output = self._run(f"hddtemp {shlex.quote(device)}")
                # Parse hddtemp output
                if ":" in output:
                    parts = output.split(":")
                    if len(parts) >= 3:
                        temp_str = parts[2].strip()
                        return {"device": device, "temperature": temp_str}
            else:
                # Get all device temperatures
                output = self._run("sensors")
                return {"output": output, "source": "sensors"}
        except Exception:
            pass

        return {"status": "not_available"}

    def power_status(self, device: str | None = None) -> dict:
        """Return power status for `device` or all devices."""
        try:
            if device:
                # Check device power state
                output = self._run(f"hdparm -C {shlex.quote(device)}")
                return {"device": device, "output": output}
            else:
                # System power status
                output = self._run("acpi -a")
                return {"output": output, "source": "acpi"}
        except Exception:
            return {"status": "not_available"}

    def enable_device(self, device: str) -> None:
        """Enable `device`. Args: device"""
        # This is hardware-specific and complex
        raise NotImplementedError("Device enable/disable requires hardware-specific commands")

    def disable_device(self, device: str) -> None:
        """Disable `device`. Args: device"""
        # This is hardware-specific and complex
        raise NotImplementedError("Device enable/disable requires hardware-specific commands")

    def rescan_bus(self, bus: str) -> None:
        """Rescan device `bus` (e.g., 'pci' or 'usb'). Args: bus"""
        if bus.lower() == "pci":
            self._run("echo 1 > /sys/bus/pci/rescan")
        elif bus.lower() == "usb":
            # USB bus rescan is more complex
            self._run("modprobe -r usb-storage && modprobe usb-storage")
        else:
            raise ValueError(f"Unsupported bus type: {bus}")

    def get_firmware(self, device: str) -> str:
        """Return firmware version string for `device`. Args: device"""
        try:
            # Try to get firmware info from DMI/BIOS
            output = self._run("dmidecode -t bios")
            return output.strip()
        except Exception:
            return ""

    def update_firmware(self, device: str, firmware_path: str) -> None:
        """Update `device` firmware from `firmware_path`. Args: device, firmware_path"""
        # Firmware updates are extremely device-specific and dangerous
        raise NotImplementedError("Firmware updates require device-specific tools and procedures")

    def gpio_list(self) -> list[dict]:
        """Return list of GPIO pin info."""
        try:
            # Try to read GPIO info from /sys/class/gpio
            output = self._run("ls /sys/class/gpio/")
            gpio_pins = []

            for line in output.splitlines():
                if line.startswith("gpio"):
                    pin_num = line.replace("gpio", "")
                    if pin_num.isdigit():
                        try:
                            direction = self._run(f"cat /sys/class/gpio/gpio{pin_num}/direction").strip()
                            value = int(self._run(f"cat /sys/class/gpio/gpio{pin_num}/value").strip())

                            gpio_pins.append({
                                "pin": int(pin_num),
                                "direction": direction,
                                "value": value
                            })
                        except Exception:
                            continue

            return gpio_pins
        except Exception:
            return []

    def gpio_read(self, pin: int) -> int:
        """Read value of GPIO `pin` and return 0 or 1. Args: pin"""
        try:
            output = self._run(f"cat /sys/class/gpio/gpio{pin}/value")
            return int(output.strip())
        except Exception:
            return 0

    def gpio_write(self, pin: int, value: int) -> None:
        """Write GPIO pin value.

        Args:
            pin: GPIO pin number
            value: Pin value to set (0 or 1)
        """
        if value not in [0, 1]:
            raise ValueError("GPIO value must be 0 or 1")

        try:
            self._run(f"echo {value} > /sys/class/gpio/gpio{pin}/value")
        except Exception as e:
            raise RuntimeError(f"Failed to write GPIO pin {pin}: {e}")