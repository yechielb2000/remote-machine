"""Device management actions."""
from __future__ import annotations
import shlex
import json

from remote_machine.models.remote_state import RemoteState
from remote_machine.protocols.ssh import SSHProtocol
from remote_machine.errors.error_mapper import ErrorMapper

from remote_machine.models.device_types import (
    BlockDevice,
    MountedList,
    MountPoint,
    FSCKResult,
    DeviceInfo,
    TemperatureInfo,
    PowerStatus,
    GPIOPin,
    GPIOInfo,
)
from remote_machine.models.common_types import IDResult


from linux_parsers.parsers.filesystem.mount import parse_mount

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

    def list_block(self) -> list[BlockDevice]:
        """Return list of block device info as BlockDevice dataclasses."""
        try:
            # prefer lsblk JSON output
            out = self._run("lsblk -J -o NAME,TYPE,SIZE,MOUNTPOINT,RO,FSTYPE,UUID,LABEL,MODEL,SERIAL")
            j = json.loads(out)
            devices: list[BlockDevice] = []

            def walk(node):
                if isinstance(node, dict):
                    name = node.get("name") or node.get("NAME") or ""
                    path = f"/dev/{name}" if name else ""
                    size_raw = node.get("size") or node.get("SIZE") or "0"
                    # try to normalize size to bytes if numeric
                    try:
                        size = int(node.get("size_bytes") or 0)
                    except Exception:
                        size = 0
                    ro = bool(node.get("ro") or node.get("RO") or False)
                    fstype = node.get("fstype") or node.get("FSTYPE") or None
                    uuid = node.get("uuid") or node.get("UUID") or None
                    label = node.get("label") or node.get("LABEL") or None
                    model = node.get("model") or None
                    serial = node.get("serial") or None
                    devices.append(BlockDevice(name=name, path=path, size=size, ro=ro, fstype=fstype, uuid=uuid, label=label, model=model, serial=serial))
                    for c in node.get("children", []) or []:
                        walk(c)
            for d in j.get("blockdevices", []) or []:
                walk(d)
            return devices
        except Exception:
            # fallback to /proc/partitions (handle variable headers)
            out = self._run("cat /proc/partitions")
            devices: list[BlockDevice] = []
            for line in out.splitlines():
                if not line.strip() or line.strip().lower().startswith("major"):
                    continue
                parts = line.split()
                if len(parts) >= 4:
                    name = parts[3]
                    devices.append(BlockDevice(name=name, path=f"/dev/{name}", size=int(parts[2]) * 1024, ro=False, fstype=None, uuid=None, label=None, model=None, serial=None))
            return devices
    def get_device_info(self, device: str) -> BlockDevice | DeviceInfo:
        """Return detailed info for `device` as BlockDevice or DeviceInfo dataclass.

        Args: device: device name or path
        """
        try:
            if not device.startswith("/dev/"):
                device_path = f"/dev/{device}"
            else:
                device_path = device

            # attempt to fetch block device info via lsblk
            try:
                out = self._run(f"lsblk -J -o NAME,TYPE,SIZE,RO,FSTYPE,UUID,LABEL,MODEL,SERIAL {shlex.quote(device_path)}")
                j = json.loads(out)
                # find the device
                if j.get("blockdevices"):
                    for d in j.get("blockdevices"):
                        if d.get("name") and (f"/dev/{d.get('name')}" == device_path or d.get("name") == device.replace('/dev/', '')):
                            size = int(d.get("size_bytes") or 0) if d.get("size_bytes") else 0
                            return BlockDevice(
                                name=d.get("name"),
                                path=device_path,
                                size=size,
                                ro=bool(d.get("ro") or False),
                                fstype=d.get("fstype") or None,
                                uuid=d.get("uuid") or None,
                                label=d.get("label") or None,
                                model=d.get("model") or None,
                                serial=d.get("serial") or None,
                            )
            except Exception:
                pass

            # fallback to basic DeviceInfo
            info = DeviceInfo(
                name=device.replace('/dev/', ''),
                device_path=device_path,
                vendor="",
                model="",
                driver=None,
                enabled=True,
                power_state="unknown",
            )
            return info
        except Exception:
            return DeviceInfo(name=device, device_path=device, vendor="", model="", driver=None, enabled=False, power_state="unknown")

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

    def mounted(self) -> MountedList:
        """Return list of mounted filesystem info as MountedList dataclass."""
        parsed = parse_mount(self._run("cat /proc/mounts"))

        mount_points: list[MountPoint] = [
            MountPoint(
                device=m.get("device", ""),
                mount_point=m.get("mount_point", ""),
                fstype=m.get("filesystem_type", ""),
                total_size=0,
                used=0,
                available=0,
                percent=0.0,
                options=",".join(m.get("mount_options", [])),
            )
            for m in parsed
        ]

        return MountedList(mount_points=mount_points, count=len(mount_points))
    
    def fsck(self, device: str, fix: bool = False) -> FSCKResult:
        """Run fsck on `device`, optionally attempting fixes and return FSCKResult."""
        cmd = f"fsck"
        if fix:
            cmd += " -y"
        else:
            cmd += " -n"
        cmd += f" {shlex.quote(device)}"

        try:
            output = self._run(cmd)
            status = "clean" if "clean" in output.lower() else "unknown"
            return FSCKResult(device=device, status=status, errors_found=0, errors_fixed=0, inodes_checked=0, blocks_checked=0, fragments=0)
        except Exception as e:
            return FSCKResult(device=device, status="error", errors_found=1, errors_fixed=0, inodes_checked=0, blocks_checked=0, fragments=0)

    def mkfs(self, device: str, fstype: str) -> None:
        """Create filesystem `fstype` on `device`. Args: device, fstype"""
        self._run(f"mkfs.{fstype} {shlex.quote(device)}")
        
    def temperature(self, device: str | None = None) -> TemperatureInfo | dict:
        """Return temperature info for `device` or a generic structure."""
        try:
            if device:
                output = self._run(f"hddtemp {shlex.quote(device)}")
                if ":" in output:
                    parts = output.split(":")
                    if len(parts) >= 3:
                        temp_str = parts[2].strip()
                        try:
                            c = float(temp_str.split(" ")[0])
                        except Exception:
                            c = 0.0
                        f = c * 9.0 / 5.0 + 32.0
                        return TemperatureInfo(device=device, celsius=c, fahrenheit=f, high_threshold=None, critical_threshold=None, status="ok")
            else:
                output = self._run("sensors")
                # best-effort: return first numeric temperature found
                for line in output.splitlines():
                    if "+" in line and "°C" in line:
                        try:
                            part = line.split("+")[-1]
                            val = float(part.split("°C")[0].strip())
                            f = val * 9.0 / 5.0 + 32.0
                            return TemperatureInfo(device="system", celsius=val, fahrenheit=f, high_threshold=None, critical_threshold=None, status="ok")
                        except Exception:
                            continue
                return {"output": output, "source": "sensors"}
        except Exception:
            pass

        return {"status": "not_available"}

    def power_status(self, device: str | None = None) -> PowerStatus | dict:
        """Return power status for `device` or a generic structure."""
        try:
            if device:
                output = self._run(f"hdparm -C {shlex.quote(device)}")
                return PowerStatus(device=device, status=output.strip(), power_consumption=None, power_supply=None)
            else:
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

    def gpio_list(self) -> GPIOInfo:
        """Return list of GPIO pin info as GPIOInfo dataclass."""
        try:
            output = self._run("ls /sys/class/gpio/")
            pins: list[GPIOPin] = []

            for line in output.splitlines():
                if line.startswith("gpio"):
                    pin_num = line.replace("gpio", "")
                    if pin_num.isdigit():
                        try:
                            direction = self._run(f"cat /sys/class/gpio/gpio{pin_num}/direction").strip()
                            value = int(self._run(f"cat /sys/class/gpio/gpio{pin_num}/value").strip())

                            pins.append(GPIOPin(pin=int(pin_num), value=value, direction=direction, active_low=False, available=True))
                        except Exception:
                            continue

            return GPIOInfo(pins=pins, total=len(pins), available=len(pins))
        except Exception:
            return GPIOInfo(pins=[], total=0, available=0)
    def gpio_read(self, pin: int) -> IDResult:
        """Read value of GPIO `pin` and return as IDResult (0 or 1). Args: pin"""
        try:
            output = self._run(f"cat /sys/class/gpio/gpio{int(pin)}/value")
            return IDResult(key=str(pin), id=int(output.strip()))
        except Exception:
            return IDResult(key=str(pin), id=None)

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