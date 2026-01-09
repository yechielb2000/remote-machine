# RemoteMachine Result Types Reference

Complete reference of all result/return types used across the RemoteMachine library actions. These are frozen dataclasses that provide type-safe, structured return values.

## Overview

- **Total Result Types**: 54 dataclasses
- **Organized by**: Action module
- **Immutable**: All types are frozen (immutable)
- **Hashable**: Can be used as dictionary keys

---

## Filesystem Result Types (5)

Located in `models.filesystem_types`

### FileInfo
File or directory information from stat operations.
```python
FileInfo(
    path: str,
    size: int,
    mode: str,
    owner: str,
    group: str,
    modified: datetime,
    accessed: datetime,
    created: datetime,
    is_symlink: bool,
    is_file: bool,
    is_dir: bool,
)
```

### DirectoryEntry
Single entry in a directory listing.
```python
DirectoryEntry(
    name: str,
    path: str,
    type: str,  # 'file', 'dir', 'link'
    size: int,
    modified: datetime,
    owner: str,
    permissions: str,
)
```

### DirectoryListing
Complete directory listing result.
```python
DirectoryListing(
    path: str,
    entries: list[DirectoryEntry],
    count: int,
)
```

### DiskUsage
Disk usage information for a path.
```python
DiskUsage(
    path: str,
    total: int,
    used: int,
    available: int,
    percent: float,
    human_total: str,
    human_used: str,
    human_available: str,
)
```

### FileFindResult
Result of finding files matching criteria.
```python
FileFindResult(
    pattern: str,
    root_path: str,
    matches: list[str],
    count: int,
)
```

---

## Process Result Types (4)

Located in `models.process_types`

### ProcessInfo
Information about a single process.
```python
ProcessInfo(
    pid: int,
    ppid: int,
    name: str,
    state: str,
    user: str,
    cpu_percent: float,
    memory_percent: float,
    memory_rss: int,  # bytes
    memory_vms: int,  # bytes
    started: datetime,
    command: str,
)
```

### MemoryUsage
Memory usage statistics.
```python
MemoryUsage(
    total: int,
    available: int,
    used: int,
    free: int,
    percent: float,
    buffers: int,
    cached: int,
    swap_total: int,
    swap_used: int,
    swap_free: int,
    swap_percent: float,
)
```

### CPUUsage
CPU usage statistics.
```python
CPUUsage(
    user_time: float,
    system_time: float,
    idle_time: float,
    iowait_time: float,
    irq_time: float,
    softirq_time: float,
    user_percent: float,
    system_percent: float,
    idle_percent: float,
    iowait_percent: float,
    count: int,
)
```

### ProcessList
Collection of processes with count.
```python
ProcessList(
    processes: list[ProcessInfo],
    count: int,
)
```

---

## Network Result Types (13)

Located in `models.network_types`

### InterfaceInfo
Network interface information.
```python
InterfaceInfo(
    name: str,
    mtu: int,
    isup: bool,
    is_running: bool,
    mac_address: str,
    ipv4_addresses: list[str],
    ipv6_addresses: list[str],
    broadcast: str | None,
    netmask: str | None,
    speed: int | None,  # Mbps
)
```

### IPAddress
Single IP address information.
```python
IPAddress(
    interface: str,
    address: str,
    family: str,  # 'IPv4' or 'IPv6'
    netmask: str | None,
    broadcast: str | None,
    gateway: str | None,
)
```

### IPAddressList
Collection of IP addresses.
```python
IPAddressList(
    addresses: list[IPAddress],
    count: int,
)
```

### Route
Routing table entry.
```python
Route(
    destination: str,
    gateway: str,
    netmask: str,
    flags: str,
    metric: int,
    interface: str,
)
```

### RoutingTable
Complete routing table.
```python
RoutingTable(
    routes: list[Route],
    count: int,
)
```

### TCPConnection
TCP connection information.
```python
TCPConnection(
    local_address: str,
    local_port: int,
    remote_address: str,
    remote_port: int,
    state: str,  # 'ESTABLISHED', 'LISTEN', etc.
    pid: int | None,
    process_name: str | None,
)
```

### ConnectionList
Collection of TCP connections.
```python
ConnectionList(
    connections: list[TCPConnection],
    count: int,
)
```

### ListeningPort
Listening port information.
```python
ListeningPort(
    address: str,
    port: int,
    protocol: str,  # 'tcp', 'udp'
    state: str,
    pid: int | None,
    process_name: str | None,
)
```

### ListeningPortList
Collection of listening ports.
```python
ListeningPortList(
    ports: list[ListeningPort],
    count: int,
)
```

### DNSResult
DNS lookup result.
```python
DNSResult(
    hostname: str,
    ipv4_addresses: list[str],
    ipv6_addresses: list[str],
    canonical_name: str | None,
)
```

### PingResult
Ping command result.
```python
PingResult(
    host: str,
    transmitted: int,
    received: int,
    packets_lost: int,
    loss_percent: float,
    min_time: float,
    max_time: float,
    avg_time: float,
    stddev_time: float | None,
)
```

### BandwidthInfo
Bandwidth usage information.
```python
BandwidthInfo(
    interface: str | None,
    bytes_sent: int,
    bytes_received: int,
    packets_sent: int,
    packets_received: int,
    errors_in: int,
    errors_out: int,
    dropped_in: int,
    dropped_out: int,
)
```

### NetworkStats
Overall network statistics.
```python
NetworkStats(
    interfaces: list[str],
    total_bytes_sent: int,
    total_bytes_received: int,
    total_packets_sent: int,
    total_packets_received: int,
)
```

---

## System Result Types (10)

Located in `models.system_types`

### CPUInfo
CPU information.
```python
CPUInfo(
    processor: str,
    vendor_id: str,
    model_name: str,
    cores: int,
    threads: int,
    cpu_mhz: float,
    l1_cache: str,
    l2_cache: str,
    l3_cache: str,
    stepping: int | None,
    flags: list[str],
)
```

### MemoryInfo
Memory information.
```python
MemoryInfo(
    total: int,
    available: int,
    used: int,
    free: int,
    percent: float,
    buffers: int,
    cached: int,
    swap_total: int,
    swap_used: int,
    swap_free: int,
    swap_percent: float,
    human_total: str,
    human_available: str,
    human_used: str,
)
```

### DiskPartition
Disk partition information.
```python
DiskPartition(
    device: str,
    mount_point: str,
    fstype: str,
    total: int,
    used: int,
    free: int,
    percent: float,
    read_only: bool,
)
```

### LoadAverage
System load average.
```python
LoadAverage(
    one_minute: float,
    five_minutes: float,
    fifteen_minutes: float,
    running_processes: int,
    total_processes: int,
)
```

### UptimeInfo
System uptime information.
```python
UptimeInfo(
    uptime: timedelta,
    boot_time: datetime,
    seconds: float,
    days: int,
    hours: int,
    minutes: int,
)
```

### OSRelease
OS release information.
```python
OSRelease(
    name: str,
    version: str,
    version_id: str,
    pretty_name: str,
    id: str,
    id_like: str | None,
    home_url: str | None,
    bug_report_url: str | None,
    support_url: str | None,
)
```

### UnameInfo
Uname information.
```python
UnameInfo(
    sysname: str,
    nodename: str,
    release: str,
    version: str,
    machine: str,
)
```

### SystemInfo
Complete system information.
```python
SystemInfo(
    hostname: str,
    uptime: UptimeInfo,
    kernel_version: str,
    cpu_info: CPUInfo,
    memory_info: MemoryInfo,
    load_average: LoadAverage,
)
```

### UserInfo
Logged in user information.
```python
UserInfo(
    username: str,
    tty: str,
    hostname: str,
    login_time: datetime,
    idle_time: timedelta | None,
)
```

### LoginHistory
User login history entry.
```python
LoginHistory(
    username: str,
    tty: str,
    hostname: str,
    login_time: datetime,
    logout_time: datetime | None,
    duration: timedelta | None,
)
```

---

## Service Result Types (8)

Located in `models.service_types`

### ServiceStatus
Service status information.
```python
ServiceStatus(
    name: str,
    state: str,  # 'running', 'stopped', 'failed'
    enabled: bool,
    active: bool,
    loaded: bool,
    pid: int | None,
    memory: int | None,
    cpu_percent: float | None,
    uptime: int | None,  # seconds
)
```

### ServiceList
Collection of services.
```python
ServiceList(
    services: list[ServiceStatus],
    count: int,
)
```

### ServiceConfig
Service configuration.
```python
ServiceConfig(
    name: str,
    path: str,
    content: str,
    valid: bool,
)
```

### ServiceLog
Single service log entry.
```python
ServiceLog(
    timestamp: datetime,
    level: str,  # 'info', 'warn', 'error'
    message: str,
    unit: str | None,
)
```

### ServiceLogList
Collection of service log entries.
```python
ServiceLogList(
    service: str,
    logs: list[ServiceLog],
    count: int,
)
```

### ServiceDependency
Service dependency information.
```python
ServiceDependency(
    name: str,
    type: str,  # 'Requires', 'Wants', 'Before', 'After'
    is_satisfied: bool,
)
```

### ServiceDependencies
All service dependencies.
```python
ServiceDependencies(
    service: str,
    dependencies: list[ServiceDependency],
    dependents: list[str],
)
```

### ServiceInfo
Complete service information.
```python
ServiceInfo(
    name: str,
    status: ServiceStatus,
    config: ServiceConfig | None,
    dependencies: ServiceDependencies | None,
    active_since: datetime | None,
    restart_count: int,
    last_restart: datetime | None,
)
```

---

## Device Result Types (14)

Located in `models.device_types`

### DeviceInfo
Hardware device information.
```python
DeviceInfo(
    name: str,
    device_path: str,
    vendor: str,
    model: str,
    driver: str | None,
    enabled: bool,
    power_state: str,
)
```

### PCIDevice
PCI device information.
```python
PCIDevice(
    address: str,
    vendor_id: str,
    device_id: str,
    vendor_name: str,
    device_name: str,
    class_name: str,
    driver: str | None,
)
```

### USBDevice
USB device information.
```python
USBDevice(
    bus: str,
    device: str,
    vendor_id: str,
    product_id: str,
    vendor_name: str,
    product_name: str,
    speed: str,
)
```

### BlockDevice
Block device (disk) information.
```python
BlockDevice(
    name: str,
    path: str,
    size: int,
    ro: bool,
    fstype: str | None,
    uuid: str | None,
    label: str | None,
    model: str | None,
    serial: str | None,
)
```

### MountPoint
Mounted filesystem information.
```python
MountPoint(
    device: str,
    mount_point: str,
    fstype: str,
    total_size: int,
    used: int,
    available: int,
    percent: float,
    options: str,
)
```

### MountedList
Collection of mounted filesystems.
```python
MountedList(
    mount_points: list[MountPoint],
    count: int,
)
```

### FSCKResult
Filesystem check result.
```python
FSCKResult(
    device: str,
    status: str,  # 'clean', 'errors_fixed', etc.
    errors_found: int,
    errors_fixed: int,
    inodes_checked: int,
    blocks_checked: int,
    fragments: int,
)
```

### SMARTAttribute
Single S.M.A.R.T. attribute.
```python
SMARTAttribute(
    id: int,
    name: str,
    value: int,
    worst: int,
    threshold: int,
    status: str,  # 'ok', 'warning', 'critical'
)
```

### SMARTData
S.M.A.R.T. information.
```python
SMARTData(
    device: str,
    model: str,
    serial_number: str,
    firmware_version: str,
    overall_health: str,  # 'passed', 'failed'
    temperature_celsius: float,
    power_on_hours: int,
    power_cycle_count: int,
    attributes: list[SMARTAttribute],
)
```

### TemperatureInfo
Device temperature information.
```python
TemperatureInfo(
    device: str,
    celsius: float,
    fahrenheit: float,
    high_threshold: float | None,
    critical_threshold: float | None,
    status: str,  # 'ok', 'warning', 'critical'
)
```

### PowerStatus
Device power status.
```python
PowerStatus(
    device: str,
    status: str,  # 'on', 'off', 'sleep', 'standby'
    power_consumption: float | None,  # watts
    power_supply: str | None,
)
```

### FirmwareInfo
Device firmware information.
```python
FirmwareInfo(
    device: str,
    current_version: str,
    available_version: str | None,
    release_date: datetime | None,
    update_available: bool,
)
```

### GPIOPin
GPIO pin information.
```python
GPIOPin(
    pin: int,
    value: int,  # 0 or 1
    direction: str,  # 'in' or 'out'
    active_low: bool,
    available: bool,
)
```

### GPIOInfo
GPIO pins information.
```python
GPIOInfo(
    pins: list[GPIOPin],
    total: int,
    available: int,
)
```

---

## Usage Examples

### Filesystem Operations
```python
from remote_machine import RemoteMachine, models

with RemoteMachine("example.com", "user") as conn:
    # Returns FileInfo
    file_info: models.FileInfo = conn.fs.stat("/var/log/syslog")
    print(f"File size: {file_info.size}")
    print(f"Owner: {file_info.owner}")
    
    # Returns DirectoryListing
    listing: models.DirectoryListing = conn.fs.list("/var/log")
    for entry in listing.entries:
        print(f"{entry.name}: {entry.size} bytes")
```

### Process Management
```python
from remote_machine import RemoteMachine, models

with RemoteMachine("example.com", "user") as conn:
    # Returns ProcessList
    procs: models.ProcessList = conn.ps.list()
    for proc in procs.processes:
        print(f"PID {proc.pid}: {proc.name} ({proc.state})")
    
    # Returns MemoryUsage
    memory: models.MemoryUsage = conn.ps.memory_usage()
    print(f"Memory used: {memory.percent}%")
```

### Network Operations
```python
from remote_machine import RemoteMachine, models

with RemoteMachine("example.com", "user") as conn:
    # Returns InterfaceInfo
    ifaces = conn.net.interfaces()
    for iface_name in ifaces:
        info: models.InterfaceInfo = conn.net.interface_info(iface_name)
        print(f"{info.name}: {info.mac_address}")
    
    # Returns PingResult
    ping: models.PingResult = conn.net.ping("8.8.8.8")
    print(f"Packets lost: {ping.loss_percent}%")
    print(f"Avg time: {ping.avg_time}ms")
```

### System Information
```python
from remote_machine import RemoteMachine, models

with RemoteMachine("example.com", "user") as conn:
    # Returns SystemInfo
    sys: models.SystemInfo = conn.sys.info()
    print(f"Hostname: {sys.hostname}")
    print(f"Cores: {sys.cpu_info.cores}")
    print(f"Memory: {sys.memory_info.human_total}")
    
    # Returns LoadAverage
    load: models.LoadAverage = conn.sys.load_average()
    print(f"Load (1min): {load.one_minute}")
```

### Service Management
```python
from remote_machine import RemoteMachine, models

with RemoteMachine("example.com", "user") as conn:
    # Returns ServiceList
    services: models.ServiceList = conn.service.list()
    for svc in services.services:
        status = "running" if svc.active else "stopped"
        print(f"{svc.name}: {status}")
    
    # Returns ServiceInfo
    info: models.ServiceInfo = conn.service.get_info("nginx")
    print(f"Status: {info.status.state}")
```

### Device Management
```python
from remote_machine import RemoteMachine, models

with RemoteMachine("example.com", "user") as conn:
    # Returns list[SMARTData]
    smart: models.SMARTData = conn.device.smartctl("/dev/sda")
    print(f"Health: {smart.overall_health}")
    print(f"Temperature: {smart.temperature_celsius}°C")
    
    # Returns MountedList
    mounts: models.MountedList = conn.device.mounted()
    for mount in mounts.mount_points:
        print(f"{mount.device} -> {mount.mount_point}: {mount.percent}% used")
```

---

## Notes

- All types are **frozen dataclasses** (immutable and hashable)
- Uses **datetime** for timestamps
- Uses **timedelta** for durations
- Optional fields use `| None` (Python 3.10+ union syntax)
- All types can be imported from `remote_machine.models`
- Provides type safety and IDE autocomplete support
