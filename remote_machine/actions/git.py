"""Git actions."""
from __future__ import annotations

import shlex
from datetime import datetime
from typing import List, Optional

from remote_machine.models.remote_state import RemoteState
from remote_machine.protocols.ssh import SSHProtocol
from remote_machine.errors.error_mapper import ErrorMapper
from remote_machine.models.common_types import OperationResult
from remote_machine.models.git_types import (
    Commit,
    Branch,
    RepositoryStatus,
    RemoteInfo,
    DiffStat,
)


class GitAction:
    """Git operations."""

    def __init__(self, protocol: SSHProtocol, state: RemoteState):
        """Initialize Git actions.

        Args:
            protocol: SSH protocol instance
            state: Remote execution state
        """
        self.protocol = protocol
        self.state = state

    def _run(self, cmd: str) -> str:
        """Run a command and raise mapped errors."""
        result = self.protocol.exec(cmd, self.state)
        ErrorMapper.raise_if_error(result)
        return result.stdout

    def status(self, repo_path: str = ".") -> RepositoryStatus:
        """Get Git repository status.

        Args:
            repo_path: Path to repository (default: current directory)

        Returns:
            RepositoryStatus object
        """
        # Get current branch
        branch_output = self._run(
            f"git -C {shlex.quote(repo_path)} rev-parse --abbrev-ref HEAD"
        )
        branch = branch_output.strip()

        # Get current commit hash
        commit_output = self._run(
            f"git -C {shlex.quote(repo_path)} rev-parse HEAD"
        )
        commit_hash = commit_output.strip()

        # Get modified files count
        modified_output = self._run(
            f"git -C {shlex.quote(repo_path)} diff --name-only"
        )
        modified_count = len([f for f in modified_output.strip().split("\n") if f])

        # Get untracked files count
        untracked_output = self._run(
            f"git -C {shlex.quote(repo_path)} ls-files --others --exclude-standard"
        )
        untracked_count = len([f for f in untracked_output.strip().split("\n") if f])

        # Get staged files count
        staged_output = self._run(
            f"git -C {shlex.quote(repo_path)} diff --cached --name-only"
        )
        staged_count = len([f for f in staged_output.strip().split("\n") if f])

        # Get ahead/behind info
        try:
            ahead_behind = self._run(
                f"git -C {shlex.quote(repo_path)} rev-list --left-right --count @{{u}}...HEAD"
            )
            parts = ahead_behind.strip().split()
            behind = int(parts[0]) if len(parts) > 0 else 0
            ahead = int(parts[1]) if len(parts) > 1 else 0
        except:
            ahead = 0
            behind = 0

        is_dirty = modified_count > 0 or untracked_count > 0 or staged_count > 0

        return RepositoryStatus(
            branch=branch,
            commit_hash=commit_hash,
            modified_files=modified_count,
            untracked_files=untracked_count,
            staged_files=staged_count,
            ahead=ahead,
            behind=behind,
            is_dirty=is_dirty,
        )

    def log(self, repo_path: str = ".", limit: int = 10) -> List[Commit]:
        """Get Git commit log.

        Args:
            repo_path: Path to repository (default: current directory)
            limit: Number of commits to return

        Returns:
            List of Commit objects
        """
        format_str = "%H%n%h%n%an%n%ae%n%ai%n%s%n---"
        cmd = f"git -C {shlex.quote(repo_path)} log -n {limit} --format='{format_str}'"
        output = self._run(cmd)

        commits = []
        entries = output.strip().split("---")

        for entry in entries:
            if not entry.strip():
                continue
            lines = entry.strip().split("\n")
            if len(lines) < 6:
                continue

            try:
                commit = Commit(
                    hash=lines[0],
                    short_hash=lines[1],
                    author=lines[2],
                    email=lines[3],
                    date=datetime.fromisoformat(lines[4].replace("Z", "+00:00")),
                    message=lines[5],
                )
                commits.append(commit)
            except (IndexError, ValueError):
                continue

        return commits

    def list_branches(self, repo_path: str = ".") -> List[Branch]:
        """List Git branches.

        Args:
            repo_path: Path to repository (default: current directory)

        Returns:
            List of Branch objects
        """
        # Get current branch
        current_branch_output = self._run(
            f"git -C {shlex.quote(repo_path)} rev-parse --abbrev-ref HEAD"
        )
        current_branch = current_branch_output.strip()

        # Get all branches
        output = self._run(f"git -C {shlex.quote(repo_path)} branch -a")

        branches = []
        for line in output.strip().split("\n"):
            if not line.strip():
                continue

            is_current = line.startswith("*")
            name = line.replace("*", "").strip()

            # Remove remote prefix if present
            if name.startswith("remotes/"):
                continue

            branches.append(
                Branch(
                    name=name,
                    is_current=is_current,
                    tracking=None,  # Could be enhanced to parse tracking info
                    last_commit=None,
                )
            )

        return branches

    def list_remotes(self, repo_path: str = ".") -> List[RemoteInfo]:
        """List Git remotes.

        Args:
            repo_path: Path to repository (default: current directory)

        Returns:
            List of RemoteInfo objects
        """
        output = self._run(f"git -C {shlex.quote(repo_path)} remote -v")

        remotes = {}
        for line in output.strip().split("\n"):
            if not line.strip():
                continue

            parts = line.split()
            if len(parts) < 3:
                continue

            name = parts[0]
            url = parts[1]
            operation = parts[2].strip("()")

            if name not in remotes:
                remotes[name] = RemoteInfo(name=name, url=url, fetch_url="", push_url="")

            if operation == "fetch":
                remotes[name] = RemoteInfo(
                    name=remotes[name].name,
                    url=remotes[name].url,
                    fetch_url=url,
                    push_url=remotes[name].push_url,
                )
            elif operation == "push":
                remotes[name] = RemoteInfo(
                    name=remotes[name].name,
                    url=remotes[name].url,
                    fetch_url=remotes[name].fetch_url,
                    push_url=url,
                )

        return list(remotes.values())

    def clone(
        self,
        repository_url: str,
        target_path: str,
        branch: Optional[str] = None,
        depth: Optional[int] = None,
    ) -> OperationResult:
        """Clone a Git repository.

        Args:
            repository_url: URL of repository to clone
            target_path: Target directory path
            branch: Specific branch to clone (optional)
            depth: Shallow clone depth (optional)

        Returns:
            OperationResult indicating success or failure
        """
        cmd_parts = ["git", "clone"]

        if branch:
            cmd_parts.extend(["-b", shlex.quote(branch)])

        if depth:
            cmd_parts.extend(["--depth", str(depth)])

        cmd_parts.extend([shlex.quote(repository_url), shlex.quote(target_path)])

        self._run(" ".join(cmd_parts))
        return OperationResult(success=True, message=f"Repository cloned to {target_path}")

    def commit(
        self, repo_path: str = ".", message: str = "", all: bool = False
    ) -> OperationResult:
        """Create a Git commit.

        Args:
            repo_path: Path to repository
            message: Commit message
            all: If True, stage all changes before committing

        Returns:
            OperationResult indicating success or failure
        """
        cmd_parts = ["git", "-C", shlex.quote(repo_path), "commit"]

        if all:
            cmd_parts.append("-a")

        cmd_parts.extend(["-m", shlex.quote(message)])

        output = self._run(" ".join(cmd_parts))
        return OperationResult(success=True, message=output.strip())

    def add(self, repo_path: str = ".", paths: Optional[List[str]] = None) -> OperationResult:
        """Stage changes for commit.

        Args:
            repo_path: Path to repository
            paths: List of file paths to stage (default: all)

        Returns:
            OperationResult indicating success or failure
        """
        cmd_parts = ["git", "-C", shlex.quote(repo_path), "add"]

        if paths:
            for path in paths:
                cmd_parts.append(shlex.quote(path))
        else:
            cmd_parts.append(".")

        self._run(" ".join(cmd_parts))
        return OperationResult(success=True, message="Changes staged")

    def push(
        self,
        repo_path: str = ".",
        remote: str = "origin",
        branch: Optional[str] = None,
        force: bool = False,
    ) -> OperationResult:
        """Push commits to remote repository.

        Args:
            repo_path: Path to repository
            remote: Remote name (default: origin)
            branch: Branch to push (default: current branch)
            force: If True, force push

        Returns:
            OperationResult indicating success or failure
        """
        cmd_parts = ["git", "-C", shlex.quote(repo_path), "push"]

        if force:
            cmd_parts.append("-f")

        cmd_parts.append(remote)

        if branch:
            cmd_parts.append(branch)

        output = self._run(" ".join(cmd_parts))
        return OperationResult(success=True, message=output.strip())

    def pull(
        self, repo_path: str = ".", remote: str = "origin", branch: Optional[str] = None
    ) -> OperationResult:
        """Pull changes from remote repository.

        Args:
            repo_path: Path to repository
            remote: Remote name (default: origin)
            branch: Branch to pull (default: current branch)

        Returns:
            OperationResult indicating success or failure
        """
        cmd_parts = ["git", "-C", shlex.quote(repo_path), "pull", remote]

        if branch:
            cmd_parts.append(branch)

        output = self._run(" ".join(cmd_parts))
        return OperationResult(success=True, message=output.strip())

    def checkout(self, repo_path: str = ".", ref: str = "") -> OperationResult:
        """Checkout a branch or commit.

        Args:
            repo_path: Path to repository
            ref: Branch name or commit hash

        Returns:
            OperationResult indicating success or failure
        """
        self._run(f"git -C {shlex.quote(repo_path)} checkout {shlex.quote(ref)}")
        return OperationResult(success=True, message=f"Checked out {ref}")

    def create_branch(self, repo_path: str = ".", branch_name: str = "") -> OperationResult:
        """Create a new branch.

        Args:
            repo_path: Path to repository
            branch_name: Name of new branch

        Returns:
            OperationResult indicating success or failure
        """
        self._run(f"git -C {shlex.quote(repo_path)} branch {shlex.quote(branch_name)}")
        return OperationResult(success=True, message=f"Branch {branch_name} created")

    def delete_branch(self, repo_path: str = ".", branch_name: str = "", force: bool = False) -> OperationResult:
        """Delete a branch.

        Args:
            repo_path: Path to repository
            branch_name: Name of branch to delete
            force: If True, force delete

        Returns:
            OperationResult indicating success or failure
        """
        force_flag = "-D" if force else "-d"
        self._run(f"git -C {shlex.quote(repo_path)} branch {force_flag} {shlex.quote(branch_name)}")
        return OperationResult(success=True, message=f"Branch {branch_name} deleted")

    def diff(self, repo_path: str = ".", file_path: Optional[str] = None) -> str:
        """Get diff of changes.

        Args:
            repo_path: Path to repository
            file_path: Optional specific file to diff

        Returns:
            Diff output
        """
        cmd = f"git -C {shlex.quote(repo_path)} diff"
        if file_path:
            cmd += f" {shlex.quote(file_path)}"
        return self._run(cmd)

    def diff_stat(self, repo_path: str = ".", ref1: str = "", ref2: str = "HEAD") -> List[DiffStat]:
        """Get diff statistics between two refs.

        Args:
            repo_path: Path to repository
            ref1: First reference (default: HEAD~1)
            ref2: Second reference (default: HEAD)

        Returns:
            List of DiffStat objects
        """
        if not ref1:
            ref1 = "HEAD~1"

        cmd = f"git -C {shlex.quote(repo_path)} diff --stat {shlex.quote(ref1)}...{shlex.quote(ref2)}"
        output = self._run(cmd)

        diff_stats = []
        for line in output.strip().split("\n"):
            if not line.strip() or line.startswith(" "):
                continue

            # Parse format: " filename | insertions insertions, deletions deletions"
            parts = line.split("|")
            if len(parts) != 2:
                continue

            file_path = parts[0].strip()
            changes = parts[1].strip().split()

            insertions = 0
            deletions = 0

            for part in changes:
                if "+" in part:
                    insertions = int(part.replace("+", ""))
                elif "-" in part:
                    deletions = int(part.replace("-", ""))

            diff_stats.append(
                DiffStat(
                    file=file_path,
                    insertions=insertions,
                    deletions=deletions,
                    changes=insertions + deletions,
                )
            )

        return diff_stats
