"""Tests for Docker actions."""

import pytest
from unittest.mock import Mock
from datetime import datetime

from remote_machine.actions.docker import DockerAction
from remote_machine.models.remote_state import RemoteState
from remote_machine.models.command_result import CommandResult


class FakeProtocol:
    """Fake SSH protocol for testing."""

    def __init__(self):
        self.commands = []

    def exec(self, command: str, state: RemoteState) -> CommandResult:
        self.commands.append(command)

        # Mock docker ps
        if "docker ps" in command and "--format" in command:
            if "-a" in command:
                return CommandResult(
                    exit_code=0,
                    stdout='{"ID":"abc123","Names":"my-container","Image":"ubuntu:20.04","Status":"Up 2 hours","State":"running","CreatedAt":"2024-01-20T10:00:00Z","Ports":"","Command":"bash"}\n'
                    '{"ID":"def456","Names":"stopped-container","Image":"nginx:latest","Status":"Exited (0) 1 hour ago","State":"exited","CreatedAt":"2024-01-20T09:00:00Z","Ports":"80/tcp","Command":"nginx"}',
                    stderr="",
                )
            else:
                return CommandResult(
                    exit_code=0,
                    stdout='{"ID":"abc123","Names":"my-container","Image":"ubuntu:20.04","Status":"Up 2 hours","State":"running","CreatedAt":"2024-01-20T10:00:00Z","Ports":"","Command":"bash"}',
                    stderr="",
                )

        # Mock docker images
        if "docker images" in command and "--format" in command:
            return CommandResult(
                exit_code=0,
                stdout='{"ID":"sha256:abc123","Repository":"ubuntu","Tag":"20.04","CreatedAt":"2024-01-15T10:00:00Z","Size":"77.8MB"}\n'
                '{"ID":"sha256:def456","Repository":"nginx","Tag":"latest","CreatedAt":"2024-01-10T10:00:00Z","Size":"142MB"}',
                stderr="",
            )

        # Mock docker run
        if "docker run" in command:
            return CommandResult(
                exit_code=0,
                stdout="container_id_12345",
                stderr="",
            )

        # Mock docker start/stop
        if "docker start" in command or "docker stop" in command:
            return CommandResult(exit_code=0, stdout="container_name", stderr="")

        # Mock docker rm
        if "docker rm" in command:
            return CommandResult(exit_code=0, stdout="container_id", stderr="")

        # Mock docker exec
        if "docker exec" in command:
            return CommandResult(
                exit_code=0,
                stdout="command output",
                stderr="",
            )

        # Mock docker logs
        if "docker logs" in command:
            return CommandResult(
                exit_code=0,
                stdout="2024-01-20 10:00:00 - Application started\n2024-01-20 10:00:01 - Ready to accept requests",
                stderr="",
            )

        # Mock docker stats
        if "docker stats" in command and "--no-stream" in command:
            return CommandResult(
                exit_code=0,
                stdout='{"Container":"abc123","CPUPerc":"0.05%","MemUsage":"120.5MiB / 16GiB","MemPerc":"0.73%","NetInput":"1.2kB","NetOutput":"2.5kB","BlockInput":"0B","BlockOutput":"0B"}',
                stderr="",
            )

        # Mock docker info
        if "docker info" in command and "--format" in command:
            return CommandResult(
                exit_code=0,
                stdout='{"Containers":5,"ContainersRunning":2,"ContainersPaused":0,"ContainersStopped":3,"Images":10,"Driver":"overlay2","MemTotal":17179869184,"MemAvailable":8589934592,"NCPU":8,"KernelVersion":"5.10.0","OperatingSystem":"Docker Desktop"}',
                stderr="",
            )

        # Mock docker pull/push
        if "docker pull" in command or "docker push" in command:
            return CommandResult(exit_code=0, stdout="Digest: sha256:abc123", stderr="")

        # Default
        return CommandResult(exit_code=0, stdout="", stderr="")


def test_docker_list_containers():
    """Test listing running containers."""
    protocol = FakeProtocol()
    state = RemoteState()
    action = DockerAction(protocol, state)

    containers = action.list_containers(all=False)

    assert len(containers) == 1
    assert containers[0].name == "my-container"
    assert containers[0].image == "ubuntu:20.04"
    assert containers[0].state == "running"


def test_docker_list_all_containers():
    """Test listing all containers."""
    protocol = FakeProtocol()
    state = RemoteState()
    action = DockerAction(protocol, state)

    containers = action.list_containers(all=True)

    assert len(containers) == 2
    assert containers[0].name == "my-container"
    assert containers[1].name == "stopped-container"
    assert containers[1].state == "exited"


def test_docker_list_images():
    """Test listing Docker images."""
    protocol = FakeProtocol()
    state = RemoteState()
    action = DockerAction(protocol, state)

    images = action.list_images()

    assert len(images) == 2
    assert images[0].repository == "ubuntu"
    assert images[0].tag == "20.04"
    assert images[1].repository == "nginx"


def test_docker_get_container():
    """Test getting a specific container."""
    protocol = FakeProtocol()
    state = RemoteState()
    action = DockerAction(protocol, state)

    container = action.get_container("my-container")

    assert container is not None
    assert container.name == "my-container"


def test_docker_start_container():
    """Test starting a container."""
    protocol = FakeProtocol()
    state = RemoteState()
    action = DockerAction(protocol, state)

    result = action.start_container("my-container")

    assert result.success is True
    assert "started" in result.message.lower()


def test_docker_stop_container():
    """Test stopping a container."""
    protocol = FakeProtocol()
    state = RemoteState()
    action = DockerAction(protocol, state)

    result = action.stop_container("my-container", timeout=15)

    assert result.success is True
    assert "stopped" in result.message.lower()


def test_docker_remove_container():
    """Test removing a container."""
    protocol = FakeProtocol()
    state = RemoteState()
    action = DockerAction(protocol, state)

    result = action.remove_container("my-container", force=True)

    assert result.success is True
    assert "removed" in result.message.lower()


def test_docker_run_container():
    """Test running a container."""
    protocol = FakeProtocol()
    state = RemoteState()
    action = DockerAction(protocol, state)

    result = action.run_container(
        image="ubuntu:20.04",
        name="test-container",
        detach=True,
        ports=["8080:80"],
        env={"KEY": "value"},
    )

    assert result.success is True
    assert "container_id_12345" in result.message


def test_docker_exec_container():
    """Test executing command in container."""
    protocol = FakeProtocol()
    state = RemoteState()
    action = DockerAction(protocol, state)

    output = action.exec_container("my-container", "ls -la")

    assert "command output" in output


def test_docker_get_logs():
    """Test getting container logs."""
    protocol = FakeProtocol()
    state = RemoteState()
    action = DockerAction(protocol, state)

    logs = action.get_logs("my-container", tail=50)

    assert "Application started" in logs
    assert "Ready to accept requests" in logs


def test_docker_stats_container():
    """Test getting container stats."""
    protocol = FakeProtocol()
    state = RemoteState()
    action = DockerAction(protocol, state)

    stats = action.stats_container("my-container")

    assert stats is not None
    assert stats.container_id == "abc123"
    assert stats.cpu_percent == 0.05
    assert stats.memory_percent == 0.73


def test_docker_info():
    """Test getting Docker info."""
    protocol = FakeProtocol()
    state = RemoteState()
    action = DockerAction(protocol, state)

    info = action.info()

    assert info is not None
    assert info.containers == 5
    assert info.containers_running == 2
    assert info.containers_stopped == 3
    assert info.images == 10


def test_docker_pull_image():
    """Test pulling Docker image."""
    protocol = FakeProtocol()
    state = RemoteState()
    action = DockerAction(protocol, state)

    result = action.pull_image("ubuntu:22.04")

    assert result.success is True
    assert "pulled" in result.message.lower()


def test_docker_push_image():
    """Test pushing Docker image."""
    protocol = FakeProtocol()
    state = RemoteState()
    action = DockerAction(protocol, state)

    result = action.push_image("myregistry.azurecr.io/myimage:latest")

    assert result.success is True
    assert "pushed" in result.message.lower()
