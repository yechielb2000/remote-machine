# RemoteMachine — Result types (short)

Result types are frozen dataclasses under `remote_machine.models`. They are returned by action methods and are convenient to inspect in code or tests.

Common types (examples):

- Filesystem: `FileInfo`, `DirectoryListing`, `DiskUsage` — file and disk info
- Process: `ProcessInfo`, `ProcessList`, `MemoryUsage` — process and memory data
- Network: `InterfaceInfo`, `IPAddress`, `PingResult` — interfaces, IPs, ping
- System: `SystemInfo`, `CPUInfo`, `LoadAverage` — system metrics
- Service: `ServiceStatus`, `ServiceList` — service state and logs
- Device: `BlockDevice`, `MountPoint`, `SMARTData` — block devices and S.M.A.R.T.

Example usage:

```python
from remote_machine import RemoteMachine, models

with RemoteMachine("host", "user") as conn:
    info: models.FileInfo = conn.fs.stat("/etc/hostname")
    print(info.size, info.owner)
```

For full definitions, inspect the dataclasses in `remote_machine/models/`.

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
