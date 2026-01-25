# RemoteMachine — Actions (short reference)

A compact list of commonly used action methods. See `examples/` and `remote_machine` modules for usage.

## Filesystem (conn.fs)
```python
conn.fs.list(path)
conn.fs.read(path)
conn.fs.write(path, content)
conn.fs.stat(path)
conn.fs.cd(path)
conn.fs.upload(local, remote)
conn.fs.download(remote, local)
conn.fs.rm(path)
```

## Processes (conn.ps)
```python
conn.ps.list()
conn.ps.find(name)
conn.ps.get_info(pid)
conn.ps.kill(pid)
conn.ps.memory_usage()
```

## Network (conn.net)
```python
conn.net.interfaces()
conn.net.interface_info(name)
conn.net.ip_list()
conn.net.ping(host)
conn.net.dns_lookup(hostname)
```

## System (conn.sys)
```python
conn.sys.info()
conn.sys.uptime()
conn.sys.cpu_info()
conn.sys.memory_info()
conn.sys.load_average()
```

## Services (conn.service)
```python
conn.service.list()
conn.service.status(name)
conn.service.start(name)
conn.service.stop(name)
conn.service.logs(name)
```

## Devices (conn.device)
```python
conn.device.list_block()
conn.device.mounted()
conn.device.smartctl(device)
conn.device.temperature(device)
conn.device.mount(device, path)
```

## Environment (conn.env)
```python
conn.env.set(key, value)
conn.env.get(key)
conn.env.list()
conn.env.update(dict)
```

For full method reference, inspect the `remote_machine.actions` modules.
