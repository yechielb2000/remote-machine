"""Models package - all dataclasses."""

# Core models
from remote_machine.models.capabilities import Capabilities
from remote_machine.models.command_result import CommandResult
from remote_machine.models.remote_state import RemoteState

# Filesystem types
from remote_machine.models.filesystem_types import (
    DiskUsage,
    DirectoryEntry,
    DirectoryListing,
    FileInfo,
    FileFindResult,
)

# Process types
from remote_machine.models.process_types import (
    CPUUsage,
    MemoryUsage,
    ProcessInfo,
    ProcessList,
)

# Network types
from remote_machine.models.network_types import (
    BandwidthInfo,
    ConnectionList,
    DNSResult,
    IPAddress,
    IPAddressList,
    InterfaceInfo,
    ListeningPort,
    ListeningPortList,
    NetworkStats,
    PingResult,
    Route,
    RoutingTable,
    TCPConnection,
)

# System types
from remote_machine.models.system_types import (
    CPUInfo,
    DiskPartition,
    LoadAverage,
    LoginHistory,
    MemoryInfo,
    OSRelease,
    SystemInfo,
    UnameInfo,
    UptimeInfo,
    UserInfo,
)

# Service types
from remote_machine.models.service_types import (
    ServiceConfig,
    ServiceDependencies,
    ServiceDependency,
    ServiceInfo,
    ServiceList,
    ServiceLog,
    ServiceLogList,
    ServiceStatus,
)

# Device types
from remote_machine.models.device_types import (
    BlockDevice,
    DeviceInfo,
    FSCKResult,
    FirmwareInfo,
    GPIOInfo,
    GPIOPin,
    MountPoint,
    MountedList,
    PCIDevice,
    PowerStatus,
    SMARTAttribute,
    SMARTData,
    TemperatureInfo,
    USBDevice,
)

__all__ = [
    # Core
    "Capabilities",
    "CommandResult",
    "RemoteState",
    # Filesystem
    "FileInfo",
    "DirectoryEntry",
    "DirectoryListing",
    "DiskUsage",
    "FileFindResult",
    # Process
    "ProcessInfo",
    "MemoryUsage",
    "CPUUsage",
    "ProcessList",
    # Network
    "InterfaceInfo",
    "IPAddress",
    "IPAddressList",
    "Route",
    "RoutingTable",
    "TCPConnection",
    "ConnectionList",
    "ListeningPort",
    "ListeningPortList",
    "DNSResult",
    "PingResult",
    "BandwidthInfo",
    "NetworkStats",
    # System
    "CPUInfo",
    "MemoryInfo",
    "DiskPartition",
    "LoadAverage",
    "UptimeInfo",
    "OSRelease",
    "UnameInfo",
    "SystemInfo",
    "UserInfo",
    "LoginHistory",
    # Service
    "ServiceStatus",
    "ServiceList",
    "ServiceConfig",
    "ServiceLog",
    "ServiceLogList",
    "ServiceDependency",
    "ServiceDependencies",
    "ServiceInfo",
    # Device
    "DeviceInfo",
    "PCIDevice",
    "USBDevice",
    "BlockDevice",
    "MountPoint",
    "MountedList",
    "FSCKResult",
    "SMARTAttribute",
    "SMARTData",
    "TemperatureInfo",
    "PowerStatus",
    "FirmwareInfo",
    "GPIOPin",
    "GPIOInfo",
]
