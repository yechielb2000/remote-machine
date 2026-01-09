# RemoteMachine 🖥️

A **Pythonic, type-safe SSH library** for remote machine control and automation. Execute commands, manage processes, configure networks, and control system resources on Linux machines with clean, intuitive Python APIs.

![Python Version](https://img.shields.io/badge/python-3.10+-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Status](https://img.shields.io/badge/status-alpha-orange)

## Features

✨ **Type-Safe APIs** - Full type hints, frozen dataclasses, IDE autocomplete support
🔐 **SSH Protocol** - Secure connection using Paramiko with key-based authentication
📦 **Structured Results** - 54+ result types for consistent, predictable returns
⚡ **7 Action Modules** - Filesystem, Process, Network, Environment, System, Service, Device management
🎯 **Error Handling** - Typed exceptions with command results attached
🔄 **State Management** - Tracks working directory and environment variables across commands
📝 **Well Documented** - Comprehensive guides and API references

## Installation

### Requirements
- Python 3.10+
- SSH server on remote machine
- Private key or password authentication

### From Source

```bash
git clone https://github.com/yechielb2000/remote-machine.git
cd remote-machine
pip install -e .
```

### Dependencies

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
    for proc in procs.processes:
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

### Core Components

```
RemoteMachine
├── RemoteState (cwd, env)
├── Protocols
│   └── SSHProtocol (Paramiko wrapper)
├── Actions (7 modules)
│   ├── FSAction (Filesystem)
│   ├── PSAction (Process)
│   ├── NETAction (Network)
│   ├── ENVAction (Environment)
│   ├── SYSAction (System)
│   ├── ServiceAction (Service)
│   └── DeviceAction (Device)
└── Models (54 result types)
```

### Action Modules

| Module | Purpose | Methods |
|--------|---------|---------|
| **FSAction** | Filesystem operations | 18 methods |
| **PSAction** | Process management | 12 methods |
| **NETAction** | Network configuration | 16 methods |
| **ENVAction** | Environment variables | 10 methods |
| **SYSAction** | System information | 19 methods |
| **ServiceAction** | Service management | 18 methods |
| **DeviceAction** | Device management | 21 methods |

**Total: 114 methods** across all actions

### Result Types

All action methods return strongly-typed frozen dataclasses:

- **Filesystem** (5 types) - `FileInfo`, `DirectoryListing`, `DiskUsage`, etc.
- **Process** (4 types) - `ProcessInfo`, `MemoryUsage`, `CPUUsage`, etc.
- **Network** (13 types) - `InterfaceInfo`, `PingResult`, `RoutingTable`, etc.
- **System** (10 types) - `SystemInfo`, `CPUInfo`, `LoadAverage`, etc.
- **Service** (8 types) - `ServiceStatus`, `ServiceLog`, `ServiceDependencies`, etc.
- **Device** (14 types) - `DeviceInfo`, `SMARTData`, `MountPoint`, etc.

**Total: 54 result types** providing type-safe, predictable returns

## Error Handling

All errors are typed exceptions with command results attached:

```python
from remote_machine import RemoteMachine, PermissionDenied, NotFound

with RemoteMachine("example.com", "user") as conn:
    try:
        content = conn.fs.read("/root/secret")
    except PermissionDenied as e:
        print(f"Error: {e.message}")
        print(f"Command: {e.result.command}")
        print(f"Stderr: {e.result.stderr}")
    except NotFound as e:
        print(f"File not found")
    except Exception as e:
        print(f"Other error: {type(e).__name__}")
```

### Exception Hierarchy

```
RemoteError (base)
├── ConnectionError
└── CommandError
    ├── PermissionDenied
    ├── NotFound
    ├── AlreadyExists
    ├── InvalidArgument
    └── Timeout
```

## State Management

RemoteMachine tracks remote state locally:

```python
with RemoteMachine("example.com", "user") as conn:
    # Change directory (client-side)
    conn.fs.cd("/var/log")
    
    # Set environment variables (client-side)
    conn.env.set("DEBUG", "1")
    
    # State persists across commands
    print(conn.state.cwd)  # '/var/log'
    print(conn.state.env)  # {'DEBUG': '1'}
```

## Usage Examples

See [examples/](examples/) directory for comprehensive examples:

- [Basic Connection](examples/01_basic_connection.py)
- [File Operations](examples/02_file_operations.py)
- [Process Management](examples/03_process_management.py)
- [Network Configuration](examples/04_network_operations.py)
- [System Monitoring](examples/05_system_monitoring.py)
- [Service Management](examples/06_service_management.py)
- [Device Management](examples/07_device_management.py)

## API Documentation

### Filesystem Actions (`conn.fs`)

```python
conn.fs.list(path)              # List directory contents
conn.fs.cd(path)                # Change working directory
conn.fs.read(path)              # Read file
conn.fs.write(path, content)    # Write file
conn.fs.mkdir(path)             # Create directory
conn.fs.rm(path)                # Remove file/directory
conn.fs.copy(src, dst)          # Copy file
conn.fs.move(src, dst)          # Move file
conn.fs.stat(path)              # Get file info
conn.fs.du(path)                # Disk usage
conn.fs.find(path)              # Find files
conn.fs.chmod(path, mode)       # Change permissions
conn.fs.chown(path, user)       # Change owner
conn.fs.download(remote, local) # Download file
conn.fs.upload(local, remote)   # Upload file
```

### Process Actions (`conn.ps`)

```python
conn.ps.list()                  # List all processes
conn.ps.find(name)              # Find by name
conn.ps.kill(pid)               # Kill process
conn.ps.get_info(pid)           # Get process info
conn.ps.memory_usage()          # Memory stats
conn.ps.cpu_usage()             # CPU stats
conn.ps.count()                 # Count processes
conn.ps.nice(pid, priority)     # Set priority
```

### Network Actions (`conn.net`)

```python
conn.net.interfaces()           # List interfaces
conn.net.interface_info(iface)  # Interface details
conn.net.ip_list()              # List IPs
conn.net.ip_add(iface, addr)    # Add IP
conn.net.ping(host)             # Ping host
conn.net.dns_lookup(hostname)   # DNS lookup
conn.net.route_list()           # List routes
conn.net.listening_ports()      # Listening ports
conn.net.tcp_connections()      # TCP connections
```

### System Actions (`conn.sys`)

```python
conn.sys.info()                 # Complete system info
conn.sys.hostname()             # Hostname
conn.sys.uptime()               # Uptime info
conn.sys.cpu_info()             # CPU details
conn.sys.memory_info()          # Memory details
conn.sys.disk_usage(path)       # Disk usage
conn.sys.disk_partitions()      # Partitions
conn.sys.load_average()         # Load average
conn.sys.kernel_version()       # Kernel version
```

### Service Actions (`conn.service`)

```python
conn.service.list()             # List services
conn.service.status(name)       # Service status
conn.service.start(name)        # Start service
conn.service.stop(name)         # Stop service
conn.service.restart(name)      # Restart service
conn.service.enable(name)       # Enable on boot
conn.service.disable(name)      # Disable on boot
conn.service.logs(name)         # Get logs
```

### Device Actions (`conn.device`)

```python
conn.device.list()              # List all devices
conn.device.list_pci()          # PCI devices
conn.device.list_usb()          # USB devices
conn.device.list_block()        # Block devices
conn.device.mounted()           # Mounted filesystems
conn.device.smartctl(device)    # S.M.A.R.T. info
conn.device.temperature(device) # Temperature
conn.device.mount(device, path) # Mount device
conn.device.unmount(path)       # Unmount device
```

### Environment Actions (`conn.env`)

```python
conn.env.set(key, value)        # Set variable
conn.env.get(key)               # Get variable
conn.env.unset(key)             # Unset variable
conn.env.list()                 # List all variables
conn.env.update(dict)           # Update multiple
conn.env.append(key, value)     # Append to variable
conn.env.prepend(key, value)    # Prepend to variable
```

## Advanced Usage

### Custom Command Execution

Execute raw commands with automatic state management:

```python
with RemoteMachine("example.com", "user") as conn:
    conn.fs.cd("/var/log")
    conn.env.set("DEBUG", "1")
    
    # Commands automatically use current cwd and env
    result = conn.protocol.exec("ls -la", conn.state)
    print(result.stdout)
```

### Batch Operations

```python
with RemoteMachine("example.com", "user") as conn:
    # File operations
    for log_file in ["/var/log/syslog", "/var/log/auth.log"]:
        info = conn.fs.stat(log_file)
        print(f"{log_file}: {info.size} bytes")
    
    # Process monitoring
    for proc in conn.ps.list().processes:
        if proc.memory_percent > 50:
            print(f"High memory: {proc.name}")
```

### Error Recovery

```python
with RemoteMachine("example.com", "user") as conn:
    try:
        conn.service.start("nginx")
    except Exception as e:
        # Log error with command details
        print(f"Failed to start nginx: {e.result.stderr}")
        
        # Check service status
        status = conn.service.status("nginx")
        print(f"Status: {status.state}")
```

## Documentation

- [ACTIONS_API.md](ACTIONS_API.md) - Complete action method reference
- [RESULT_TYPES.md](RESULT_TYPES.md) - All result type documentation
- [examples/](examples/) - Usage examples for each action

## Architecture Details

See [DESIGN.md](DESIGN.md) for:
- Architectural overview
- Design principles
- Phase roadmap
- Future enhancements

## Development

### Setup Development Environment

```bash
pip install -e ".[dev]"
```

### Running Tests

```bash
pytest tests/
pytest --cov=remote_machine
```

### Code Style

```bash
black remote_machine/
isort remote_machine/
flake8 remote_machine/
```

### Type Checking

```bash
mypy remote_machine/
```

## Roadmap

### Phase 1: Core (Current)
✅ Architecture & project structure
✅ 7 action modules with 114 methods
✅ 54 result types with full type hints
✅ Error handling & typed exceptions
✅ SSH protocol wrapper
✅ State management

### Phase 2: Implementation
- [ ] Command execution with linux-parsers
- [ ] Parser integration for all actions
- [ ] Full test coverage
- [ ] Performance optimization

### Phase 3: Testing & Validation
- [ ] Integration tests
- [ ] Real system testing
- [ ] Performance benchmarks
- [ ] Documentation updates

### Phase 4: CLI & Async (Future)
- [ ] CLI adapter
- [ ] Async/await support
- [ ] Connection pooling
- [ ] Session persistence

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Update documentation
5. Submit a pull request

## License

MIT License - see [LICENSE](LICENSE) for details

## Support

For issues, questions, or suggestions:
- Open an [issue](https://github.com/yechielb2000/remote-machine/issues)
- Check [discussions](https://github.com/yechielb2000/remote-machine/discussions)
- Review [documentation](ACTIONS_API.md)

---

**Made with ❤️ for remote machine automation**
