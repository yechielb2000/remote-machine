# RemoteMachine

A lightweight, type-safe Python library for managing Linux machines over SSH.

![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue) ![License: MIT](https://img.shields.io/badge/license-MIT-green)

## Install

```bash
git clone https://github.com/yechielb2000/remote-machine.git
cd remote-machine
pip install -e .
```

Install runtime dependencies:

```bash
pip install paramiko>=3.0.0
```

## Quick Start

### Basic Connection

```python
from remote_machine import RemoteMachine

# Create connection
conn = RemoteMachine("example.com", "user", key_path="~/.ssh/id_rsa")

# Use context manager for automatic cleanup
with conn:
    # Execute commands, manage systems, etc.
    pass
```

### File Operations

```python
with RemoteMachine("example.com", "user") as conn:
    # Read file
    content = conn.fs.read("/etc/hostname")
    
    # List directory
    listing = conn.fs.list("/var/log")
    for entry in listing.entries:
        print(f"{entry.name}: {entry.size} bytes")
    
    # Get file info
    info = conn.fs.stat("/var/log/syslog")
    print(f"Owner: {info.owner}, Permissions: {info.mode}")
```

### Process Management

```python
with RemoteMachine("example.com", "user") as conn:
    # List processes
    procs = conn.ps.list()
    for proc in procs:
        print(f"{proc.pid}: {proc.name} ({proc.cpu_percent}% CPU)")
    
    # Find specific process
    nginx = conn.ps.find("nginx")
    
    # Kill process
    conn.ps.kill(1234, signal=15)
```

### Network Operations

```python
with RemoteMachine("example.com", "user") as conn:
    # Get interface info
    interfaces = conn.net.interfaces()
    for iface in interfaces:
        info = conn.net.interface_info(iface)
        print(f"{iface}: {info.mac_address}")
    
    # Ping host
    result = conn.net.ping("8.8.8.8")
    print(f"Packets lost: {result.loss_percent}%")
    
    # DNS lookup
    dns = conn.net.dns_lookup("example.com")
    print(f"IPs: {dns.ipv4_addresses}")
```

### System Information

```python
with RemoteMachine("example.com", "user") as conn:
    # Get system info
    sys_info = conn.sys.info()
    print(f"Hostname: {sys_info.hostname}")
    print(f"Cores: {sys_info.cpu_info.cores}")
    print(f"Memory: {sys_info.memory_info.human_total}")
    
    # Get load average
    load = conn.sys.load_average()
    print(f"Load: {load.one_minute} (1min), {load.five_minutes} (5min)")
```

### Service Management

```python
with RemoteMachine("example.com", "user") as conn:
    # List services
    services = conn.service.list()
    for svc in services.services:
        status = "running" if svc.active else "stopped"
        print(f"{svc.name}: {status}")
    
    # Control service
    if not conn.service.is_running("nginx"):
        conn.service.start("nginx")
    
    # Get service logs
    logs = conn.service.logs("nginx", lines=50)
    print(logs)
```

### Device Management

```python
with RemoteMachine("example.com", "user") as conn:
    # Get disk info
    disks = conn.device.list_block()
    for disk in disks:
        print(f"{disk.name}: {disk.size} bytes")
    
    # Check S.M.A.R.T. status
    smart = conn.device.smartctl("/dev/sda")
    print(f"Health: {smart.overall_health}")
    print(f"Temperature: {smart.temperature_celsius}°C")
    
    # List mounted filesystems
    mounts = conn.device.mounted()
    for mp in mounts.mount_points:
        print(f"{mp.device} -> {mp.mount_point}: {mp.percent}% used")
```

### Environment Variables

```python
with RemoteMachine("example.com", "user") as conn:
    # Set variables
    conn.env.set("DEBUG", "1")
    conn.env.set("LOG_LEVEL", "INFO")
    
    # Get variable
    debug_mode = conn.env.get("DEBUG")
    
    # Update multiple
    conn.env.update({
        "DB_HOST": "localhost",
        "DB_PORT": "5432"
    })
    
    # List all
    all_vars = conn.env.list()
```

## Architecture

RemoteMachine composes an SSH protocol, a client-side state (cwd, env), and action modules (filesystem, processes, network, system, services, devices, env).

## Key points

- Action methods return frozen dataclasses in `remote_machine.models`.
- Errors are typed exceptions in `remote_machine.errors` and include command outputs.
- State (cwd, env) is stored in `conn.state` and applied to commands.

## Contributing

```bash
pip install -e "[dev]"
pytest
```

License: MIT

For examples and usage samples, see the `examples/` directory.
