"""Docker actions."""
from __future__ import annotations

import json
import shlex
from datetime import datetime
from typing import List, Optional

from remote_machine.models.remote_state import RemoteState
from remote_machine.protocols.ssh import SSHProtocol
from remote_machine.models.common_types import OperationResult
from remote_machine.models.docker_types import (
    Container,
    Image,
    ContainerStats,
    DockerInfo,
)


class DockerAction:
    """Docker operations."""

    def __init__(self, protocol: SSHProtocol, state: RemoteState):
        """Initialize Docker actions.

        Args:
            protocol: SSH protocol instance
            state: Remote execution state
        """
        self.protocol = protocol
        self.state = state

    def list_containers(self, all: bool = False) -> List[Container]:
        """List Docker containers.

        Args:
            all: If True, show all containers (including stopped), else only running

        Returns:
            List of Container objects
        """
        all_flag = "-a" if all else ""
        cmd = f"docker ps {all_flag} --format '{{{{json .}}}}'"
        output = self.protocol.run_command(cmd, self.state)

        containers = []
        for line in output.strip().split("\n"):
            if not line:
                continue
            try:
                data = json.loads(line)
                containers.append(
                    Container(
                        id=data.get("ID", ""),
                        name=data.get("Names", ""),
                        image=data.get("Image", ""),
                        status=data.get("Status", ""),
                        state=data.get("State", ""),
                        created=datetime.fromisoformat(data.get("CreatedAt", "").replace("Z", "+00:00")),
                        started=None,  # Not provided by ps command
                        ports=data.get("Ports", "").split(", ") if data.get("Ports") else [],
                        command=data.get("Command", ""),
                    )
                )
            except (json.JSONDecodeError, ValueError):
                continue

        return containers

    def list_images(self) -> List[Image]:
        """List Docker images.

        Returns:
            List of Image objects
        """
        cmd = "docker images --format '{{json .}}'"
        output = self.protocol.run_command(cmd, self.state)

        images = []
        for line in output.strip().split("\n"):
            if not line:
                continue
            try:
                data = json.loads(line)
                images.append(
                    Image(
                        id=data.get("ID", ""),
                        repository=data.get("Repository", ""),
                        tag=data.get("Tag", ""),
                        created=datetime.fromisoformat(data.get("CreatedAt", "").replace("Z", "+00:00")),
                        size=int(data.get("Size", "0").split()[0]) if data.get("Size") else 0,
                        virtual_size=0,  # Not provided by images command
                    )
                )
            except (json.JSONDecodeError, ValueError):
                continue

        return images

    def get_container(self, container_id: str) -> Optional[Container]:
        """Get information about a specific container.

        Args:
            container_id: Container ID or name

        Returns:
            Container object or None if not found
        """
        containers = self.list_containers(all=True)
        for container in containers:
            if container.id.startswith(container_id) or container.name == container_id:
                return container
        return None

    def start_container(self, container_id: str) -> OperationResult:
        """Start a stopped container.

        Args:
            container_id: Container ID or name

        Returns:
            OperationResult indicating success or failure
        """
        self.protocol.run_command(f"docker start {shlex.quote(container_id)}", self.state)
        return OperationResult(success=True, message=f"Container {container_id} started")

    def stop_container(self, container_id: str, timeout: int = 10) -> OperationResult:
        """Stop a running container.

        Args:
            container_id: Container ID or name
            timeout: Timeout in seconds before force killing

        Returns:
            OperationResult indicating success or failure
        """
        self.protocol.run_command(f"docker stop -t {timeout} {shlex.quote(container_id)}", self.state)
        return OperationResult(success=True, message=f"Container {container_id} stopped")

    def remove_container(self, container_id: str, force: bool = False) -> OperationResult:
        """Remove a container.

        Args:
            container_id: Container ID or name
            force: If True, force remove running container

        Returns:
            OperationResult indicating success or failure
        """
        force_flag = "-f" if force else ""
        self.protocol.run_command(f"docker rm {force_flag} {shlex.quote(container_id)}", self.state)
        return OperationResult(success=True, message=f"Container {container_id} removed")

    def run_container(
        self,
        image: str,
        name: Optional[str] = None,
        detach: bool = True,
        ports: Optional[List[str]] = None,
        env: Optional[dict] = None,
        volumes: Optional[List[str]] = None,
        command: Optional[str] = None,
    ) -> OperationResult:
        """Run a Docker container.

        Args:
            image: Image name or ID
            name: Container name
            detach: If True, run in background
            ports: List of port mappings (e.g., ["8080:80"])
            env: Dictionary of environment variables
            volumes: List of volume mounts
            command: Command to run in container

        Returns:
            OperationResult with container ID in message
        """
        cmd_parts = ["docker", "run"]

        if detach:
            cmd_parts.append("-d")

        if name:
            cmd_parts.extend(["--name", shlex.quote(name)])

        if ports:
            for port in ports:
                cmd_parts.extend(["-p", shlex.quote(port)])

        if env:
            for key, value in env.items():
                cmd_parts.extend(["-e", f"{key}={shlex.quote(str(value))}"])

        if volumes:
            for volume in volumes:
                cmd_parts.extend(["-v", shlex.quote(volume)])

        cmd_parts.append(shlex.quote(image))

        if command:
            cmd_parts.append(command)

        output = self.protocol.run_command(" ".join(cmd_parts), self.state)
        container_id = output.strip().split("\n")[0]
        return OperationResult(success=True, message=f"Container {container_id} started")

    def exec_container(self, container_id: str, command: str) -> str:
        """Execute a command in a running container.

        Args:
            container_id: Container ID or name
            command: Command to execute

        Returns:
            Command output
        """
        return self.protocol.run_command(f"docker exec {shlex.quote(container_id)} {command}", self.state)

    def get_logs(self, container_id: str, tail: int = 100) -> str:
        """Get container logs.

        Args:
            container_id: Container ID or name
            tail: Number of log lines to return

        Returns:
            Container logs
        """
        return self.protocol.run_command(f"docker logs --tail {tail} {shlex.quote(container_id)}", self.state)

    def stats_container(self, container_id: str) -> Optional[ContainerStats]:
        """Get resource statistics for a container.

        Args:
            container_id: Container ID or name

        Returns:
            ContainerStats object or None if not found
        """
        try:
            cmd = f"docker stats {shlex.quote(container_id)} --no-stream --format '{{{{json .}}}}'"
            output = self.protocol.run_command(cmd, self.state)
            data = json.loads(output.strip())

            def parse_size(size_str: str) -> int:
                """Parse size string like '123MiB' to bytes."""
                multipliers = {"B": 1, "KiB": 1024, "MiB": 1024**2, "GiB": 1024**3}
                for suffix, mult in multipliers.items():
                    if size_str.endswith(suffix):
                        return int(float(size_str[: -len(suffix)]) * mult)
                return 0

            return ContainerStats(
                container_id=data.get("Container", ""),
                cpu_percent=float(data.get("CPUPerc", "0").rstrip("%")) if data.get("CPUPerc") else 0.0,
                memory_usage=parse_size(data.get("MemUsage", "0B").split()[0]),
                memory_limit=parse_size(data.get("MemUsage", "").split()[-1]) if "/" in data.get("MemUsage", "") else 0,
                memory_percent=float(data.get("MemPerc", "0").rstrip("%")) if data.get("MemPerc") else 0.0,
                network_input=0,  # Not provided by stats command
                network_output=0,
                block_input=0,
                block_output=0,
            )
        except (json.JSONDecodeError, ValueError, IndexError):
            return None

    def info(self) -> Optional[DockerInfo]:
        """Get Docker system information.

        Returns:
            DockerInfo object or None on error
        """
        try:
            output = self.protocol.run_command("docker info --format json", self.state)
            data = json.loads(output)

            return DockerInfo(
                containers=data.get("Containers", 0),
                containers_running=data.get("ContainersRunning", 0),
                containers_paused=data.get("ContainersPaused", 0),
                containers_stopped=data.get("ContainersStopped", 0),
                images=data.get("Images", 0),
                driver=data.get("Driver", ""),
                memory_total=data.get("MemTotal", 0),
                memory_available=data.get("MemAvailable", 0),
                cpus=data.get("NCPU", 0),
                kernel_version=data.get("KernelVersion", ""),
                os=data.get("OperatingSystem", ""),
            )
        except (json.JSONDecodeError, ValueError):
            return None

    def pull_image(self, image: str) -> OperationResult:
        """Pull a Docker image from registry.

        Args:
            image: Image name with optional tag

        Returns:
            OperationResult indicating success or failure
        """
        self.protocol.run_command(f"docker pull {shlex.quote(image)}", self.state)
        return OperationResult(success=True, message=f"Image {image} pulled successfully")

    def push_image(self, image: str) -> OperationResult:
        """Push a Docker image to registry.

        Args:
            image: Image name with optional tag

        Returns:
            OperationResult indicating success or failure
        """
        self.protocol.run_command(f"docker push {shlex.quote(image)}", self.state)
        return OperationResult(success=True, message=f"Image {image} pushed successfully")
