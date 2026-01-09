"""Device action result types."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class DeviceInfo:
    """Hardware device information."""

    name: str
    device_path: str
    vendor: str
    model: str
    driver: str | None
    enabled: bool
    power_state: str


@dataclass(frozen=True)
class PCIDevice:
    """PCI device information."""

    address: str
    vendor_id: str
    device_id: str
    vendor_name: str
    device_name: str
    class_name: str
    driver: str | None


@dataclass(frozen=True)
class USBDevice:
    """USB device information."""

    bus: str
    device: str
    vendor_id: str
    product_id: str
    vendor_name: str
    product_name: str
    speed: str


@dataclass(frozen=True)
class BlockDevice:
    """Block device (disk) information."""

    name: str
    path: str
    size: int
    ro: bool
    fstype: str | None
    uuid: str | None
    label: str | None
    model: str | None
    serial: str | None


@dataclass(frozen=True)
class MountPoint:
    """Mounted filesystem information."""

    device: str
    mount_point: str
    fstype: str
    total_size: int
    used: int
    available: int
    percent: float
    options: str


@dataclass(frozen=True)
class MountedList:
    """List of mounted filesystems."""

    mount_points: list[MountPoint]
    count: int


@dataclass(frozen=True)
class FSCKResult:
    """Filesystem check result."""

    device: str
    status: str  # 'clean', 'errors_fixed', 'errors_not_fixed', 'system_should_reboot'
    errors_found: int
    errors_fixed: int
    inodes_checked: int
    blocks_checked: int
    fragments: int


@dataclass(frozen=True)
class SMARTAttribute:
    """S.M.A.R.T. attribute."""

    id: int
    name: str
    value: int
    worst: int
    threshold: int
    status: str  # 'ok', 'warning', 'critical'


@dataclass(frozen=True)
class SMARTData:
    """S.M.A.R.T. information."""

    device: str
    model: str
    serial_number: str
    firmware_version: str
    overall_health: str  # 'passed', 'failed'
    temperature_celsius: float
    power_on_hours: int
    power_cycle_count: int
    attributes: list[SMARTAttribute]


@dataclass(frozen=True)
class TemperatureInfo:
    """Device temperature information."""

    device: str
    celsius: float
    fahrenheit: float
    high_threshold: float | None
    critical_threshold: float | None
    status: str  # 'ok', 'warning', 'critical'


@dataclass(frozen=True)
class PowerStatus:
    """Device power status."""

    device: str
    status: str  # 'on', 'off', 'sleep', 'standby'
    power_consumption: float | None  # watts
    power_supply: str | None


@dataclass(frozen=True)
class FirmwareInfo:
    """Device firmware information."""

    device: str
    current_version: str
    available_version: str | None
    release_date: datetime | None
    update_available: bool


@dataclass(frozen=True)
class GPIOPin:
    """GPIO pin information."""

    pin: int
    value: int  # 0 or 1
    direction: str  # 'in' or 'out'
    active_low: bool
    available: bool


@dataclass(frozen=True)
class GPIOInfo:
    """GPIO pins information."""

    pins: list[GPIOPin]
    total: int
    available: int
