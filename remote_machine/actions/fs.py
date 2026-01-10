"""Filesystem actions."""
from datetime import datetime
import shlex

from typing import List
from remote_machine.models.remote_state import RemoteState
from remote_machine.protocols.ssh import SSHProtocol
from remote_machine.utils.fs_utils import parse_permissions
from remote_machine.utils.path_resolver import PathResolver
from remote_machine.errors.error_mapper import ErrorMapper

from linux_parsers.parsers.filesystem.ls import parse_ls
from linux_parsers.parsers.filesystem.stat import parse_stat
from linux_parsers.parsers.filesystem.df import parse_df

from remote_machine.models.common_types import OperationResult
from remote_machine.models.filesystem_types import (
    FileContent, FileInfo, DirectoryEntry, DirectoryListing, DiskUsage, FileFindResult
)


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

    def _run(self, cmd: str) -> str:
        """Run a command and raise mapped errors."""
        result = self.protocol.exec(cmd, self.state)
        ErrorMapper.raise_if_error(result)
        return result.stdout

    def list(self, path: str = ".") -> DirectoryListing:
        """Return directory listing for `path` resolved against cwd."""
        resolved_path = self.resolver.resolve(path, self.state.cwd)
        output = self._run(f"ls -la {shlex.quote(resolved_path)}")
        dirlist = parse_ls(output)
        entries = []
        for entry in dirlist:
            try:
                perms = parse_permissions(entry["Permissions"])
            except ValueError:
                perms = ''

            entries.append(DirectoryEntry(
                name=entry["File"],
                path=entry["File"],
                type=perms.entry_type if perms else None,
                size=int(entry["Size"]),
                modified=datetime.strptime(entry["LastModified"], "%b %d %H:%M"),
                owner=entry["Owner"],
                group=entry["Group"],
                permissions=perms
            ))
        return DirectoryListing(entries=entries, count=len(entries), path=resolved_path)

    def cd(self, path: str) -> OperationResult:
        """Change working directory to resolved `path` and return OperationResult."""
        resolved_path = self.resolver.resolve(path, self.state.cwd)
        # Verify the directory exists and is accessible
        self._run(f"test -d {shlex.quote(resolved_path)}")
        self.state.cwd = resolved_path
        return OperationResult(success=True, message=None)

    def read(self, path: str) -> FileContent:
        """Return file contents for `path` resolved against cwd as FileContent dataclass. Args: path"""
        resolved_path = self.resolver.resolve(path, self.state.cwd)
        content = self._run(f"cat {shlex.quote(resolved_path)}")
        return FileContent(path=resolved_path, content=content)

    def read(self, path: str) -> str:
        """Return file contents for `path` resolved against cwd. Args: path"""
        resolved_path = self.resolver.resolve(path, self.state.cwd)
        return self._run(f"cat {shlex.quote(resolved_path)}")

    def write(self, path: str, content: str) -> OperationResult:
        """Write `content` to `path` resolved against cwd and return OperationResult."""
        resolved_path = self.resolver.resolve(path, self.state.cwd)
        # Use printf instead of echo for better handling of special characters
        escaped_content = content.replace("'", "'\"'\"'")
        self._run(f"printf '%s' '{escaped_content}' > {shlex.quote(resolved_path)}")
        return OperationResult(success=True, message=None)

    def mkdir(self, path: str, parents: bool = False) -> None:
        """Create directory at `path`; `parents` creates ancestors. Args: path, parents"""
        resolved_path = self.resolver.resolve(path, self.state.cwd)
        cmd = f"mkdir {'-p ' if parents else ''}{shlex.quote(resolved_path)}"
        self._run(cmd)

    def rm(self, path: str, recursive: bool = False, force: bool = False) -> None:
        """Remove `path`; use `recursive` and `force` as needed. Args: path, recursive, force"""
        resolved_path = self.resolver.resolve(path, self.state.cwd)
        flags = ""
        if recursive:
            flags += "r"
        if force:
            flags += "f"
        cmd = f"rm {'-' + flags + ' ' if flags else ''}{shlex.quote(resolved_path)}"
        self._run(cmd)

    def touch(self, path: str) -> None:
        """Create or update timestamp of `path`. Args: path"""
        resolved_path = self.resolver.resolve(path, self.state.cwd)
        self._run(f"touch {shlex.quote(resolved_path)}")

    def exists(self, path: str) -> bool:
        """Return True if `path` exists (resolved against cwd). Args: path"""
        resolved_path = self.resolver.resolve(path, self.state.cwd)
        result = self.protocol.exec(f"test -e {shlex.quote(resolved_path)}", self.state)
        return result.exit_code == 0

    def is_file(self, path: str) -> bool:
        """Return True if `path` is a file. Args: path"""
        resolved_path = self.resolver.resolve(path, self.state.cwd)
        result = self.protocol.exec(f"test -f {shlex.quote(resolved_path)}", self.state)
        return result.exit_code == 0

    def is_dir(self, path: str) -> bool:
        """Return True if `path` is a directory. Args: path"""
        resolved_path = self.resolver.resolve(path, self.state.cwd)
        result = self.protocol.exec(f"test -d {shlex.quote(resolved_path)}", self.state)
        return result.exit_code == 0

    def copy(self, src: str, dst: str) -> None:
        """Copy `src` to `dst` (both resolved against cwd). Args: src, dst"""
        src_path = self.resolver.resolve(src, self.state.cwd)
        dst_path = self.resolver.resolve(dst, self.state.cwd)
        self._run(f"cp -r {shlex.quote(src_path)} {shlex.quote(dst_path)}")

    def move(self, src: str, dst: str) -> None:
        """Move/rename `src` to `dst`. Args: src, dst"""
        src_path = self.resolver.resolve(src, self.state.cwd)
        dst_path = self.resolver.resolve(dst, self.state.cwd)
        self._run(f"mv {shlex.quote(src_path)} {shlex.quote(dst_path)}")

    def chmod(self, path: str, mode: str) -> None:
        """Set permissions `mode` on `path`. Args: path, mode"""
        resolved_path = self.resolver.resolve(path, self.state.cwd)
        self._run(f"chmod {mode} {shlex.quote(resolved_path)}")

    def chown(self, path: str, user: str, group: str | None = None) -> None:
        """Set owner `user`[:`group`] on `path`. Args: path, user, group"""
        resolved_path = self.resolver.resolve(path, self.state.cwd)
        owner = f"{user}:{group}" if group else user
        self._run(f"chown {owner} {shlex.quote(resolved_path)}")

    def stat(self, path: str) -> FileInfo:
        """Return file stat info for `path`. Args: path"""
        resolved_path = self.resolver.resolve(path, self.state.cwd)
        cmd = f"stat {shlex.quote(resolved_path)}"
        parsed = parse_stat(self._run(cmd))
        return FileInfo(
            path=parsed.get("file", resolved_path),
            size=parsed.get("size", 0),
            mode=parsed.get("mode", ""),
            owner=parsed.get("owner", parsed.get("user", "")),
            group=parsed.get("group", ""),
            modified=datetime.fromtimestamp(parsed.get("mtime", 0)),
            accessed=datetime.fromtimestamp(parsed.get("atime", 0)),
            created=datetime.fromtimestamp(parsed.get("ctime", 0)),
            is_symlink=parsed.get("type", "").lower().startswith("symbolic"),
            is_file=parsed.get("type", "").lower().startswith("regular"),
            is_dir=parsed.get("type", "").lower().startswith("directory")
        )

    def df(self, path: str = ".") -> List[DiskUsage]:
        resolved_path = self.resolver.resolve(path, self.state.cwd)
        disks = parse_df(self._run(f"df {shlex.quote(resolved_path)}"))
        disks_usage = []
        for disk in disks:
            disks_usage.append(DiskUsage(
            path=resolved_path,
            filesystem=disk['Filesystem'],
            blocks=disk['Blocks'],
            used=int(disk['Used']),
            available=int(disk['Available']),
            percent=disk['UsePercent'],
            mounted=disk['Mounted']
        ))
        return disks_usage

    def find(self, path: str = ".", name: str | None = None, type_: str | None = None) -> FileFindResult:
        """Find files under `path` matching `name` and `type_`. Args: path, name, type_"""
        resolved_path = self.resolver.resolve(path, self.state.cwd)

        cmd_parts = ["find", shlex.quote(resolved_path)]

        if name:
            cmd_parts.extend(["-name", shlex.quote(name)])

        if type_:
            cmd_parts.extend(["-type", type_])

        cmd = " ".join(cmd_parts)
        output = self._run(cmd)

        matches = [line.strip() for line in output.splitlines() if line.strip()]
        pattern = name or "*"

        return FileFindResult(
            pattern=pattern,
            root_path=resolved_path,
            matches=matches,
            count=len(matches)
        )

    def download(self, remote_path: str, local_path: str) -> None:
        """Download `remote_path` to local `local_path`. Args: remote_path, local_path"""
        resolved_path = self.resolver.resolve(remote_path, self.state.cwd)
        # This would require SFTP implementation in the protocol
        # For now, raise NotImplementedError
        raise NotImplementedError("Download functionality requires SFTP implementation")

    def upload(self, local_path: str, remote_path: str) -> None:
        """Upload `local_path` to `remote_path` (remote resolved). Args: local_path, remote_path"""
        resolved_path = self.resolver.resolve(remote_path, self.state.cwd)
        # This would require SFTP implementation in the protocol
        # For now, raise NotImplementedError
        raise NotImplementedError("Upload functionality requires SFTP implementation")
