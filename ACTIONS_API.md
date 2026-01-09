# RemoteMachine Actions API Reference

This document describes all available actions and their methods in the RemoteMachine library.

## Actions Overview

The RemoteMachine library provides 7 main action modules:

1. **FSAction** - Filesystem operations
2. **PSAction** - Process management
3. **NETAction** - Network operations
4. **ENVAction** - Environment variable management
5. **SYSAction** - System information and control
6. **ServiceAction** - Service management (systemd)
7. **DeviceAction** - Hardware device management

---

## 1. FSAction - Filesystem Operations

```python
conn.fs.list(path)              # List directory contents
conn.fs.cd(path)                # Change working directory
conn.fs.read(path)              # Read file contents
conn.fs.write(path, content)    # Write to file
conn.fs.mkdir(path)             # Create directory
conn.fs.rm(path)                # Remove file/directory
conn.fs.touch(path)             # Create empty file or update timestamp
conn.fs.exists(path)            # Check if path exists
conn.fs.is_file(path)           # Check if path is a file
conn.fs.is_dir(path)            # Check if path is a directory
conn.fs.copy(src, dst)          # Copy file or directory
conn.fs.move(src, dst)          # Move or rename file/directory
conn.fs.chmod(path, mode)       # Change file permissions
conn.fs.chown(path, user)       # Change file owner
conn.fs.stat(path)              # Get file statistics
conn.fs.du(path)                # Get disk usage of path
conn.fs.find(path)              # Find files matching criteria
conn.fs.download(remote, local) # Download file from remote
conn.fs.upload(local, remote)   # Upload file to remote
```

---

## 2. PSAction - Process Management

```python
conn.ps.list()                  # List all processes
conn.ps.list_by_user(user)     # List processes for specific user
conn.ps.kill(pid)               # Kill a process
conn.ps.find(name)              # Find processes by name
conn.ps.get_info(pid)           # Get detailed process information
conn.ps.is_running(pid)         # Check if process is running
conn.ps.wait(pid)               # Wait for process to finish
conn.ps.count()                 # Count running processes
conn.ps.memory_usage()          # Get memory usage information
conn.ps.cpu_usage()             # Get CPU usage information
conn.ps.get_children(pid)       # Get child processes of a process
conn.ps.get_parent(pid)         # Get parent process ID
conn.ps.nice(pid, priority)     # Set process priority
```

---

## 3. NETAction - Network Operations

```python
conn.net.stat()                 # Get network statistics
conn.net.interfaces()           # Get list of network interfaces
conn.net.interface_info(iface)  # Get interface information
conn.net.ip_add(iface, addr)    # Add IP address to interface
conn.net.ip_delete(iface, addr) # Delete IP address from interface
conn.net.ip_list()              # List IP addresses
conn.net.up(iface)              # Bring interface up
conn.net.down(iface)            # Bring interface down
conn.net.ping(host)             # Ping a host
conn.net.dns_lookup(hostname)   # Perform DNS lookup
conn.net.route_list()           # List routing table
conn.net.route_add(dest, gw)    # Add route to routing table
conn.net.route_delete(dest)     # Delete route from routing table
conn.net.tcp_connections()      # Get list of TCP connections
conn.net.listening_ports()      # Get list of listening ports
conn.net.firewall_status()      # Get firewall status
conn.net.bandwidth()            # Get bandwidth usage
```

---

## 4. ENVAction - Environment Variable Management

```python
conn.env.set(key, value)        # Set environment variable
conn.env.get(key)               # Get environment variable
conn.env.unset(key)             # Unset environment variable
conn.env.list()                 # List all environment variables
conn.env.clear()                # Clear all environment variables
conn.env.update(variables)      # Update multiple variables
conn.env.exists(key)            # Check if variable exists
conn.env.append(key, value)     # Append to variable
conn.env.prepend(key, value)    # Prepend to variable
conn.env.remove_from_path(key, value)  # Remove from path-like variable
```

---

## 5. SYSAction - System Information & Control

```python
conn.sys.info()                 # Get system information
conn.sys.uname()                # Get system name and information
conn.sys.uptime()               # Get system uptime
conn.sys.hostname()             # Get system hostname
conn.sys.set_hostname(name)     # Set system hostname
conn.sys.disk_usage(path)       # Get disk usage information
conn.sys.disk_partitions()      # Get list of disk partitions
conn.sys.memory_info()          # Get memory information
conn.sys.cpu_info()             # Get CPU information
conn.sys.cpu_count()            # Get number of CPU cores
conn.sys.load_average()         # Get load average
conn.sys.timezone()             # Get system timezone
conn.sys.set_timezone(tz)       # Set system timezone
conn.sys.reboot(delay)          # Reboot the system
conn.sys.shutdown(delay)        # Shutdown the system
conn.sys.dmesg(lines)           # Get kernel messages
conn.sys.kernel_version()       # Get kernel version
conn.sys.os_release()           # Get OS release information
conn.sys.logged_in_users()      # Get list of logged in users
conn.sys.last_login(user)       # Get last login information
```

---

## 6. ServiceAction - Service Management

```python
conn.service.list()             # List all services
conn.service.status(service)    # Get service status
conn.service.is_running(service)      # Check if service is running
conn.service.is_enabled(service)      # Check if service is enabled at boot
conn.service.start(service)     # Start a service
conn.service.stop(service)      # Stop a service
conn.service.restart(service)   # Restart a service
conn.service.reload(service)    # Reload service configuration
conn.service.enable(service)    # Enable service at boot
conn.service.disable(service)   # Disable service at boot
conn.service.logs(service)      # Get service logs
conn.service.get_config(service)      # Get service configuration
conn.service.edit_config(service, content)    # Edit configuration
conn.service.validate_config(service) # Validate configuration
conn.service.get_pid(service)   # Get service process ID
conn.service.get_port(service)  # Get service listening port
conn.service.mask(service)      # Mask service (prevent from starting)
conn.service.unmask(service)    # Unmask service
conn.service.dependencies(service)    # Get service dependencies
```

---

## 7. DeviceAction - Hardware Device Management

```python
conn.device.list()              # List all devices
conn.device.list_pci()          # List PCI devices
conn.device.list_usb()          # List USB devices
conn.device.list_block()        # List block devices (disks)
conn.device.get_device_info(device)   # Get detailed device information
conn.device.mount(device, path) # Mount a device
conn.device.unmount(path)       # Unmount a device
conn.device.mounted()           # List mounted filesystems
conn.device.mount_options(path) # Get mount options
conn.device.fsck(device)        # Check filesystem
conn.device.mkfs(device, fstype)      # Create filesystem
conn.device.smartctl(device)    # Get S.M.A.R.T. information
conn.device.temperature(device) # Get device temperature
conn.device.power_status(device)      # Get device power status
conn.device.enable_device(device)     # Enable a device
conn.device.disable_device(device)    # Disable a device
conn.device.rescan_bus(bus)     # Rescan device bus
conn.device.get_firmware(device)      # Get device firmware version
conn.device.update_firmware(device, path)    # Update firmware
conn.device.gpio_list()         # List GPIO pins
conn.device.gpio_read(pin)      # Read GPIO pin value
conn.device.gpio_write(pin, value)    # Write GPIO pin value
```

---

## Usage Examples

### Example 1: Basic Connection and File Operations

```python
from remote_machine import RemoteMachine

# Create connection
conn = RemoteMachine("example.com", "user", key_path="~/.ssh/id_rsa")

# Use context manager for automatic connection handling
with conn:
    # List directory
    files = conn.fs.list("/var/log")
    
    # Read file
    content = conn.fs.read("/etc/hostname")
    print(f"Hostname: {content}")
    
    # Get disk usage
    usage = conn.sys.disk_usage("/")
    print(f"Disk usage: {usage}")
```

### Example 2: Process Management

```python
with RemoteMachine("example.com", "user") as conn:
    # Find processes
    procs = conn.ps.find("nginx")
    for proc in procs:
        print(f"PID: {proc['pid']}, Memory: {proc['memory']}")
    
    # Get system load
    load = conn.sys.load_average()
    print(f"Load: {load}")
```

### Example 3: Service Management

```python
with RemoteMachine("example.com", "user") as conn:
    # Check if service is running
    if not conn.service.is_running("nginx"):
        print("Starting nginx...")
        conn.service.start("nginx")
    
    # Get service logs
    logs = conn.service.logs("nginx", lines=50)
    print(logs)
```

### Example 4: Network Configuration

```python
with RemoteMachine("example.com", "user") as conn:
    # Get network interfaces
    interfaces = conn.net.interfaces()
    for iface in interfaces:
        info = conn.net.interface_info(iface)
        print(f"{iface}: {info}")
    
    # Ping a host
    result = conn.net.ping("8.8.8.8")
    print(f"Ping result: {result}")
```

### Example 5: Environment Variables

```python
with RemoteMachine("example.com", "user") as conn:
    # Set environment variables
    conn.env.set("DEBUG", "1")
    conn.env.set("LOG_LEVEL", "INFO")
    
    # Append to PATH
    conn.env.append("PATH", "/custom/bin")
    
    # Get all variables
    all_vars = conn.env.list()
    print(f"All environment variables: {all_vars}")
```

---

## Notes

- All paths are resolved against the current working directory (managed by `conn.state.cwd`)
- Use `conn.env` to manage environment variables that persist across commands
- Error handling uses typed exceptions from `remote_machine.errors`
- All methods support stub implementations that will be fully implemented in Phase 2
- The library maintains state locally, so commands are efficient and predictable
