"""Filesystem actions."""
from datetime import datetime
import shlex

from typing import List
from remote_machine.models.remote_state import RemoteState
from remote_machine.protocols.ssh import SSHProtocol
from remote_machine.protocols.scp import SCPProtocol
from remote_machine.utils.decorators import requires_protocols
from remote_machine.utils.fs_utils import parse_permissions
from remote_machine.utils.path_resolver import PathResolver
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

    def list(self, path: str = ".") -> DirectoryListing:
        """Return directory listing for `path` resolved against cwd."""
        resolved_path = self.resolver.resolve(path, self.state.cwd)
        output = self.protocol.run_command(f"ls -la {shlex.quote(resolved_path)}", self.state)
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
        self.protocol.run_command(f"test -d {shlex.quote(resolved_path)}", self.state)
        self.state.cwd = resolved_path
        return OperationResult(success=True, message=None)

    def read(self, path: str) -> FileContent:
        """Return file contents for `path` resolved against cwd as FileContent dataclass. Args: path"""
        resolved_path = self.resolver.resolve(path, self.state.cwd)
        content = self.protocol.run_command(f"cat {shlex.quote(resolved_path)}", self.state)
        return FileContent(path=resolved_path, content=content)

    def read(self, path: str) -> str:
        """Return file contents for `path` resolved against cwd. Args: path"""
        resolved_path = self.resolver.resolve(path, self.state.cwd)
        return self.protocol.run_command(f"cat {shlex.quote(resolved_path)}", self.state)

    def write(self, path: str, content: str) -> OperationResult:
        """Write `content` to `path` resolved against cwd and return OperationResult."""
        resolved_path = self.resolver.resolve(path, self.state.cwd)
        # Use printf instead of echo for better handling of special characters
        escaped_content = content.replace("'", "'\"'\"'")
        self.protocol.run_command(f"printf '%s' '{escaped_content}' > {shlex.quote(resolved_path)}", self.state)
        return OperationResult(success=True, message=None)

    def mkdir(self, path: str, parents: bool = False) -> None:
        """Create directory at `path`; `parents` creates ancestors. Args: path, parents"""
        resolved_path = self.resolver.resolve(path, self.state.cwd)
        cmd = f"mkdir {'-p ' if parents else ''}{shlex.quote(resolved_path)}"
        self.protocol.run_command(cmd, self.state)

    def rm(self, path: str, recursive: bool = False, force: bool = False) -> None:
        """Remove `path`; use `recursive` and `force` as needed. Args: path, recursive, force"""
        resolved_path = self.resolver.resolve(path, self.state.cwd)
        flags = ""
        if recursive:
            flags += "r"
        if force:
            flags += "f"
        cmd = f"rm {'-' + flags + ' ' if flags else ''}{shlex.quote(resolved_path)}"
        self.protocol.run_command(cmd, self.state)

    def touch(self, path: str) -> None:
        """Create or update timestamp of `path`. Args: path"""
        resolved_path = self.resolver.resolve(path, self.state.cwd)
        self.protocol.run_command(f"touch {shlex.quote(resolved_path)}", self.state)

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
        self.protocol.run_command(f"cp -r {shlex.quote(src_path)} {shlex.quote(dst_path)}", self.state)

    def move(self, src: str, dst: str) -> None:
        """Move/rename `src` to `dst`. Args: src, dst"""
        src_path = self.resolver.resolve(src, self.state.cwd)
        dst_path = self.resolver.resolve(dst, self.state.cwd)
        self.protocol.run_command(f"mv {shlex.quote(src_path)} {shlex.quote(dst_path)}", self.state)

    def chmod(self, path: str, mode: str) -> None:
        """Set permissions `mode` on `path`. Args: path, mode"""
        resolved_path = self.resolver.resolve(path, self.state.cwd)
        self.protocol.run_command(f"chmod {mode} {shlex.quote(resolved_path)}", self.state)

    def chown(self, path: str, user: str, group: str | None = None) -> None:
        """Set owner `user`[:`group`] on `path`. Args: path, user, group"""
        resolved_path = self.resolver.resolve(path, self.state.cwd)
        owner = f"{user}:{group}" if group else user
        self.protocol.run_command(f"chown {owner} {shlex.quote(resolved_path)}", self.state)

    def stat(self, path: str) -> FileInfo:
        """Return file stat info for `path`. Args: path"""
        resolved_path = self.resolver.resolve(path, self.state.cwd)
        cmd = f"stat {shlex.quote(resolved_path)}"
        parsed = parse_stat(self.protocol.run_command(cmd), self.state)
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
        disks = parse_df(self.protocol.run_command(f"df {shlex.quote(resolved_path)}"), self.state)
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
        output = self.protocol.run_command(cmd, self.state)

        matches = [line.strip() for line in output.splitlines() if line.strip()]
        pattern = name or "*"

        return FileFindResult(
            pattern=pattern,
            root_path=resolved_path,
            matches=matches,
            count=len(matches)
        )

    @requires_protocols("scp")
    def download(self, remote_path: str, local_path: str):
        scp: SCPProtocol = self._rm.protocol("scp")
        return scp.download(remote_path, local_path)

    @requires_protocols("scp")
    def upload(self, local_path: str, remote_path: str) -> None:
        scp: SCPProtocol = self._rm.protocol("scp")
        return scp.upload(local_path, remote_path)

    # Archive operations
    def create_tar(self, source_path: str, archive_path: str, compress: str = "gz") -> OperationResult:
        """Create a tar archive.

        Args:
            source_path: Source directory or file to archive
            archive_path: Path for the output archive file
            compress: Compression type: 'gz' (gzip), 'bz2' (bzip2), 'xz', or None (uncompressed)

        Returns:
            OperationResult indicating success or failure
        """
        compress_flags = {
            "gz": "z",
            "bz2": "j",
            "xz": "J",
            None: ""
        }
        flag = compress_flags.get(compress, "z")
        cmd = f"tar -c{flag}f {shlex.quote(archive_path)} -C {shlex.quote(self.resolver.resolve('.'))} {shlex.quote(self.resolver.resolve(source_path))}"
        self.protocol.run_command(cmd, self.state)
        return OperationResult(success=True, message=f"Archive created: {archive_path}")

    def extract_tar(self, archive_path: str, extract_to: str = ".") -> OperationResult:
        """Extract a tar archive.

        Args:
            archive_path: Path to tar archive
            extract_to: Directory to extract to (default: current directory)

        Returns:
            OperationResult indicating success or failure
        """
        resolved_extract = self.resolver.resolve(extract_to, self.state.cwd)
        cmd = f"tar -xf {shlex.quote(archive_path)} -C {shlex.quote(resolved_extract)}"
        self.protocol.run_command(cmd, self.state)
        return OperationResult(success=True, message=f"Archive extracted to: {resolved_extract}")

    def list_tar(self, archive_path: str) -> List[str]:
        """List contents of a tar archive.

        Args:
            archive_path: Path to tar archive

        Returns:
            List of file paths in archive
        """
        cmd = f"tar -tf {shlex.quote(archive_path)}"
        output = self.protocol.run_command(cmd, self.state)
        return [line.strip() for line in output.strip().split("\n") if line.strip()]

    def create_zip(self, source_path: str, archive_path: str, recursive: bool = True) -> OperationResult:
        """Create a zip archive.

        Args:
            source_path: Source directory or file to archive
            archive_path: Path for the output zip file
            recursive: If True, recursively include directories

        Returns:
            OperationResult indicating success or failure
        """
        recursive_flag = "-r" if recursive else ""
        cmd = f"zip {recursive_flag} {shlex.quote(archive_path)} {shlex.quote(source_path)}"
        self.protocol.run_command(cmd, self.state)
        return OperationResult(success=True, message=f"Zip archive created: {archive_path}")

    def extract_zip(self, archive_path: str, extract_to: str = ".") -> OperationResult:
        """Extract a zip archive.

        Args:
            archive_path: Path to zip archive
            extract_to: Directory to extract to (default: current directory)

        Returns:
            OperationResult indicating success or failure
        """
        resolved_extract = self.resolver.resolve(extract_to, self.state.cwd)
        cmd = f"unzip {shlex.quote(archive_path)} -d {shlex.quote(resolved_extract)}"
        self.protocol.run_command(cmd, self.state)
        return OperationResult(success=True, message=f"Zip archive extracted to: {resolved_extract}")

    def list_zip(self, archive_path: str) -> List[str]:
        """List contents of a zip archive.

        Args:
            archive_path: Path to zip archive

        Returns:
            List of file paths in archive
        """
        cmd = f"unzip -l {shlex.quote(archive_path)}"
        output = self.protocol.run_command(cmd, self.state)
        # Skip header and footer lines
        lines = output.strip().split("\n")[3:-2]
        return [line.split()[-1] for line in lines if line.strip()]

    def compress_gzip(self, source_path: str, archive_path: str = None) -> OperationResult:
        """Compress a file with gzip.

        Args:
            source_path: Path to file to compress
            archive_path: Path for the compressed file (default: source_path.gz)

        Returns:
            OperationResult indicating success or failure
        """
        resolved_source = self.resolver.resolve(source_path, self.state.cwd)
        if not archive_path:
            archive_path = f"{resolved_source}.gz"
        cmd = f"gzip -k {shlex.quote(resolved_source)} -c > {shlex.quote(archive_path)}"
        self.protocol.run_command(cmd, self.state)
        return OperationResult(success=True, message=f"File compressed: {archive_path}")

    def decompress_gzip(self, archive_path: str, output_path: str = None) -> OperationResult:
        """Decompress a gzip file.

        Args:
            archive_path: Path to gzip file
            output_path: Path for the decompressed file

        Returns:
            OperationResult indicating success or failure
        """
        if not output_path:
            # Remove .gz extension
            output_path = archive_path.rstrip(".gz") if archive_path.endswith(".gz") else f"{archive_path}.out"
        cmd = f"gunzip -k {shlex.quote(archive_path)} -c > {shlex.quote(output_path)}"
        self.protocol.run_command(cmd, self.state)
        return OperationResult(success=True, message=f"File decompressed: {output_path}")

    def test_archive(self, archive_path: str) -> OperationResult:
        """Test archive integrity.

        Args:
            archive_path: Path to archive file

        Returns:
            OperationResult indicating if archive is valid
        """
        # Determine archive type by extension
        if archive_path.endswith(".tar.gz") or archive_path.endswith(".tgz"):
            cmd = f"tar -tzf {shlex.quote(archive_path)} > /dev/null"
        elif archive_path.endswith(".tar.bz2") or archive_path.endswith(".tbz2"):
            cmd = f"tar -tjf {shlex.quote(archive_path)} > /dev/null"
        elif archive_path.endswith(".tar"):
            cmd = f"tar -tf {shlex.quote(archive_path)} > /dev/null"
        elif archive_path.endswith(".zip"):
            cmd = f"unzip -t {shlex.quote(archive_path)} > /dev/null"
        else:
            return OperationResult(success=False, message="Unknown archive format")

        self.protocol.run_command(cmd, self.state)
        return OperationResult(success=True, message="Archive is valid")
