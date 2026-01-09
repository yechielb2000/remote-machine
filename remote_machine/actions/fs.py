"""Filesystem actions."""
from __future__ import annotations

from remote_machine.models.remote_state import RemoteState
from remote_machine.protocols.ssh import SSHProtocol
from remote_machine.utils.path_resolver import PathResolver


class FSAction:
    """Filesystem operations."""

    def __init__(self, protocol: SSHProtocol, state: RemoteState):
        """Initialize filesystem actions.

        Args:
            protocol: SSH protocol instance
            state: Remote execution state
        """
        self.protocol = protocol
        self.state = state
        self.resolver = PathResolver()

    def list(self, path: str = ".") -> dict:
        """Return directory listing for `path` resolved against cwd."""
        resolved_path = self.resolver.resolve(path, self.state.cwd)
        # Stub implementation - will be populated in Phase 2
        return {}

    def cd(self, path: str) -> None:
        """Change working directory to resolved `path`. Args: path"""
        resolved_path = self.resolver.resolve(path, self.state.cwd)
        self.state.cwd = resolved_path

    def read(self, path: str) -> str:
        """Return file contents for `path` resolved against cwd. Args: path"""
        resolved_path = self.resolver.resolve(path, self.state.cwd)
        # Stub implementation - will be populated in Phase 2
        return ""

    def write(self, path: str, content: str) -> None:
        """Write `content` to `path` resolved against cwd. Args: path, content"""
        resolved_path = self.resolver.resolve(path, self.state.cwd)
        # Stub implementation - will be populated in Phase 2
        pass

    def mkdir(self, path: str, parents: bool = False) -> None:
        """Create directory at `path`; `parents` creates ancestors. Args: path, parents"""
        resolved_path = self.resolver.resolve(path, self.state.cwd)
        # Stub implementation - will be populated in Phase 2
        pass

    def rm(self, path: str, recursive: bool = False, force: bool = False) -> None:
        """Remove `path`; use `recursive` and `force` as needed. Args: path, recursive, force"""
        resolved_path = self.resolver.resolve(path, self.state.cwd)
        # Stub implementation - will be populated in Phase 2
        pass

    def touch(self, path: str) -> None:
        """Create or update timestamp of `path`. Args: path"""
        resolved_path = self.resolver.resolve(path, self.state.cwd)
        # Stub implementation - will be populated in Phase 2
        pass

    def exists(self, path: str) -> bool:
        """Return True if `path` exists (resolved against cwd). Args: path"""
        resolved_path = self.resolver.resolve(path, self.state.cwd)
        # Stub implementation - will be populated in Phase 2
        return False

    def is_file(self, path: str) -> bool:
        """Return True if `path` is a file. Args: path"""
        resolved_path = self.resolver.resolve(path, self.state.cwd)
        # Stub implementation - will be populated in Phase 2
        return False

    def is_dir(self, path: str) -> bool:
        """Return True if `path` is a directory. Args: path"""
        resolved_path = self.resolver.resolve(path, self.state.cwd)
        # Stub implementation - will be populated in Phase 2
        return False

    def copy(self, src: str, dst: str) -> None:
        """Copy `src` to `dst` (both resolved against cwd). Args: src, dst"""
        src_path = self.resolver.resolve(src, self.state.cwd)
        dst_path = self.resolver.resolve(dst, self.state.cwd)
        # Stub implementation - will be populated in Phase 2
        pass

    def move(self, src: str, dst: str) -> None:
        """Move/rename `src` to `dst`. Args: src, dst"""
        src_path = self.resolver.resolve(src, self.state.cwd)
        dst_path = self.resolver.resolve(dst, self.state.cwd)
        # Stub implementation - will be populated in Phase 2
        pass

    def chmod(self, path: str, mode: str) -> None:
        """Set permissions `mode` on `path`. Args: path, mode"""
        resolved_path = self.resolver.resolve(path, self.state.cwd)
        # Stub implementation - will be populated in Phase 2
        pass

    def chown(self, path: str, user: str, group: str | None = None) -> None:
        """Set owner `user`[:`group`] on `path`. Args: path, user, group"""
        resolved_path = self.resolver.resolve(path, self.state.cwd)
        # Stub implementation - will be populated in Phase 2
        pass

    def stat(self, path: str) -> dict:
        """Return file stat dict for `path`. Args: path"""
        resolved_path = self.resolver.resolve(path, self.state.cwd)
        # Stub implementation - will be populated in Phase 2
        return {}

    def du(self, path: str = ".", human_readable: bool = True) -> dict:
        """Return disk usage for `path`; `human_readable` toggles format. Args: path, human_readable"""
        resolved_path = self.resolver.resolve(path, self.state.cwd)
        # Stub implementation - will be populated in Phase 2
        return {}

    def find(self, path: str = ".", name: str | None = None, type_: str | None = None) -> list[str]:
        """Find files under `path` matching `name` and `type_`. Args: path, name, type_"""
        resolved_path = self.resolver.resolve(path, self.state.cwd)
        # Stub implementation - will be populated in Phase 2
        return []

    def download(self, remote_path: str, local_path: str) -> None:
        """Download `remote_path` to local `local_path`. Args: remote_path, local_path"""
        resolved_path = self.resolver.resolve(remote_path, self.state.cwd)
        # Stub implementation - will be populated in Phase 2
        pass

    def upload(self, local_path: str, remote_path: str) -> None:
        """Upload `local_path` to `remote_path` (remote resolved). Args: local_path, remote_path"""
        resolved_path = self.resolver.resolve(remote_path, self.state.cwd)
        # Stub implementation - will be populated in Phase 2
        pass
