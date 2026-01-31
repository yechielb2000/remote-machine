# Remote Machine Future Actions Ideas

This document outlines potential actions that could be added to the remote-machine library to enhance automation capabilities.

## Package Management Actions


3. **NodePackageManager Action** - NPM/Yarn management
   - Install/uninstall npm packages
   - Manage package.json dependencies
   - List packages
   - Run npm scripts
   - Install node versions (nvm)

4. **RubyPackageManager Action** - Ruby gems and Bundler
   - Install/uninstall gems
   - Manage Gemfile
   - RVM environment management
   - Run bundler commands

## Infrastructure & Cloud Actions

5. **Kubernetes Action** - kubectl wrapper
   - List pods, services, deployments
   - Get pod logs
   - Exec into pods
   - Apply/delete manifests
   - Scale deployments
   - Check cluster status

6. **Terraform Action** - Infrastructure as Code
   - Plan infrastructure changes
   - Apply/destroy resources
   - Validate configurations
   - Format Terraform code
   - Show state

7. **CloudCLI Action** - AWS/Azure/GCP unified interface
   - AWS CLI (S3, EC2, Lambda, etc.)
   - Azure CLI (az commands)
   - Google Cloud (gcloud)

9. **Ansible Action** - Configuration management
   - Run playbooks
   - List inventories
   - Run ad-hoc commands
   - Validate playbooks

## Development & Build Actions

10. **Build Action** - Make/Maven/Gradle wrapper
    - Run builds
    - Clean builds
    - Run tests
    - List targets
    - Install artifacts

11. **VersionManager Action** - nvm/rbenv/pyenv/jenv
    - List installed versions
    - Switch versions
    - Install versions
    - Check current version

12. **Cargo Action** - Rust package manager
    - Build/test projects
    - Run programs
    - Check code
    - Generate documentation

## Database Actions

13. **DatabaseClient Action** - PostgreSQL/MySQL/MongoDB
    - Execute queries
    - Backup/restore databases
    - List databases/tables
    - Manage users/permissions
    - Monitor connections

14. **RedisClient Action** - Redis operations
    - Set/get keys
    - List keys
    - Monitor performance
    - Flush databases
    - Manage connections

15. **SQLiteAction** - SQLite management
    - Execute queries
    - Backup database
    - Analyze schema

## File & Archive Actions

17. **Rsync Action** - File synchronization
    - Sync directories
    - Backup files
    - Exclude patterns
    - Monitor bandwidth
    - Resume transfers

## Network & Monitoring Actions

19. **HTTP Action** - curl/wget/httpie wrapper
    - Make HTTP requests
    - Download files
    - Test endpoints
    - Check response codes
    - Monitor uptime

21. **MonitoringAction** - htop/top/systemd monitoring
    - Real-time process monitoring
    - Memory/CPU metrics
    - System resource usage
    - Performance profiling

## Security & Encryption Actions

22. **OpenSSLAction** - SSL/TLS management
    - Generate certificates
    - Check certificate validity
    - Encrypt/decrypt data
    - Generate keys
    - Manage keystores

23. **GPGAction** - Encryption and signing
    - Encrypt files
    - Decrypt files
    - Sign/verify files
    - List keys
    - Import/export keys

24. **VaultAction** - HashiCorp Vault integration
    - Store secrets
    - Retrieve secrets
    - Manage policies
    - Seal/unseal vault
    - List secrets

## System Administration Actions

25. **CronAction** - Job scheduling *(Implemented)*
    - List cron jobs
    - Add/remove jobs
    - Enable/disable jobs
    - View logs
    - Test schedule

26. **LogManagementAction** - Log viewing and analysis
    - Tail logs
    - Filter logs
    - Rotate logs
    - Archive logs
    - Search logs with patterns

27. **UserManagementAction** - User and group operations
    - Create/delete users
    - Manage groups
    - Set permissions
    - View login history
    - Manage sudo access

28. **JournalctlAction** - systemd journal
    - Query logs
    - Filter by service/priority
    - Follow logs
    - Export logs
    - Manage journal storage

## Container & Virtualization Actions

29. **PodmanAction** - Podman (Docker alternative)
    - Same operations as Docker
    - Manage pods
    - Rootless containers

30. **LXCAction** - LXC containers
    - List containers
    - Start/stop containers
    - Execute commands
    - Manage networks

## Media & Processing Actions

31. **FFmpegAction** - Video/audio processing
    - Convert formats
    - Extract audio/video
    - Get media info
    - Transcode files
    - Create thumbnails

32. **ImageMagickAction** - Image processing
    - Resize images
    - Convert formats
    - Add watermarks
    - Get image info
    - Batch processing

33. **JQAction** - JSON processing
    - Parse JSON
    - Filter JSON
    - Transform JSON
    - Pretty-print JSON

## Configuration Management Actions

34. **ConfigParserAction** - INI/YAML/TOML files
    - Read configurations
    - Write configurations
    - Validate syntax
    - Merge configs
    - Template rendering

35. **EnvironmentAction** - Environment variable management
    - Set/get environment variables
    - Load from .env files
    - Validate environment
    - Export environment

## Service Discovery & Messaging Actions

36. **ConsulAction** - Service discovery
    - Register services
    - Deregister services
    - Query services
    - Health checks
    - KV store operations

37. **EtcdAction** - Distributed configuration
    - Set/get keys
    - Watch keys
    - List keys
    - Manage leases

## Implementation Status

### ✅ Completed
- Docker Action
- Git Action
- Archive functions (FSAction)
- Firewall Action (iptables)
- Cron Action

### 🔄 In Progress
- None currently

### 📋 Planned
- PackageManager (High Priority)
- Kubernetes (High Priority)
- Database Client (High Priority)
- HTTP (High Priority)
- Terraform (Medium Priority)
- Rsync (Medium Priority)
- Docker Compose (Medium Priority)
- Build Action (Medium Priority)
- OpenSSL (Medium Priority)

## Recommended Implementation Order

**Tier 1 (High Value - Broad Applicability)**
1. PackageManager - universal system package management
2. Kubernetes - widely used in DevOps
3. Database Client - essential for web applications
4. HTTP - testing and file downloads
5. Archive - *(DONE)* common administrative task

**Tier 2 (Medium Value - Specialized Use Cases)**
6. Terraform - infrastructure automation
7. Rsync - backup and sync operations
8. Docker Compose - complement to Docker action
9. Cron - *(DONE)* scheduled tasks
10. Firewall - *(DONE)* security operations

**Tier 3 (Lower Priority - Niche Use Cases)**
11. Cloud CLI - AWS/Azure/GCP specific
12. Build tools - project-specific
13. FFmpeg/ImageMagick - media-specific
14. Vault - secrets management
15. OpenSSL - SSL/TLS operations

## Design Patterns for New Actions

All new actions should follow the established patterns:

1. **Module Structure**
   - `remote_machine/actions/<action_name>.py` - Main action class
   - `remote_machine/models/<action_name>_types.py` - Return type dataclasses
   - Update `remote_machine/models/__init__.py` to export types
   - Update `remote_machine/actions/__init__.py` to export action

2. **Action Class Pattern**
   ```python
   class MyAction:
       def __init__(self, protocol: SSHProtocol, state: RemoteState):
           self.protocol = protocol
           self.state = state
       
       def _run(self, cmd: str) -> str:
           """Run command and raise mapped errors."""
           result = self.protocol.exec(cmd, self.state)
           ErrorMapper.raise_if_error(result)
           return result.stdout
       
       def my_method(self, arg: str) -> ReturnType:
           """Docstring with clear description."""
           output = self._run(f"command {shlex.quote(arg)}")
           # Parse and return structured data
   ```

3. **Testing Pattern**
   - Use `FakeProtocol` that returns `CommandResult` objects
   - Test both success paths and error conditions
   - Mock command outputs with realistic data

4. **Core Integration**
   - Add action import to `core.py`
   - Add action instantiation in `RemoteMachine.__init__`
   - Update `capabilities()` method

5. **Documentation**
   - Create comprehensive `.md` file with examples
   - Document all methods with parameters and returns
   - Provide practical usage examples
   - Include error handling examples

## Notes

- All actions should follow SSH-safe patterns (use `shlex.quote()` for arguments)
- Return typed dataclasses for structured data
- Use `ErrorMapper` for consistent error handling
- Provide comprehensive docstrings and examples
- Include unit tests with `FakeProtocol` mocks
