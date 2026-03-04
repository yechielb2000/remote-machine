"""Unit tests for parallel execution."""

import pytest
pytestmark = [pytest.mark.parallel]

import os
import sys
import time

# Make the package importable in tests run in this environment
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from remote_machine.parallel import ParallelExecutor, ParallelResult
from remote_machine.models.command_result import CommandResult
from remote_machine.models.remote_state import RemoteState


class FakeRemoteMachine:
    def __init__(self, host: str, responses: dict[str, str] = None, should_fail: bool = False):
        self.host = host
        self.responses = responses or {}
        self.should_fail = should_fail

    def run(self, command: str) -> str:
        if self.should_fail:
            raise Exception("Simulated failure")
        return self.responses.get(command, f"executed {command} on {self.host}")


def test_parallel_executor_success():
    """Test successful parallel execution."""
    clients = [
        FakeRemoteMachine("host1"),
        FakeRemoteMachine("host2"),
        FakeRemoteMachine("host3"),
    ]

    executor = ParallelExecutor(max_workers=2)
    results = executor.run(clients, "uptime")

    assert len(results) == 3
    for result in results:
        assert result.success
        assert result.error is None
        assert result.duration_ms >= 0
        assert "uptime" in result.output
        assert result.host in ["host1", "host2", "host3"]


def test_parallel_executor_failure():
    """Test parallel execution with failures."""
    clients = [
        FakeRemoteMachine("host1"),
        FakeRemoteMachine("host2", should_fail=True),
        FakeRemoteMachine("host3"),
    ]

    executor = ParallelExecutor(max_workers=2)
    results = executor.run(clients, "uptime")

    assert len(results) == 3

    success_results = [r for r in results if r.success]
    failure_results = [r for r in results if not r.success]

    assert len(success_results) == 2
    assert len(failure_results) == 1

    failure = failure_results[0]
    assert failure.host == "host2"
    assert failure.output is None
    assert isinstance(failure.error, Exception)
    assert str(failure.error) == "Simulated failure"


def test_parallel_executor_max_workers():
    """Test that max_workers limits concurrency."""
    # This is hard to test directly, but we can check the parameter validation
    with pytest.raises(ValueError):
        ParallelExecutor(max_workers=0)

    with pytest.raises(ValueError):
        ParallelExecutor(max_workers=-1)

    # Valid
    executor = ParallelExecutor(max_workers=5)
    assert executor.max_workers == 5


def test_parallel_result_structure():
    """Test ParallelResult dataclass structure."""
    result = ParallelResult(
        host="testhost",
        success=True,
        output="output",
        error=None,
        duration_ms=123.45
    )

    assert result.host == "testhost"
    assert result.success is True
    assert result.output == "output"
    assert result.error is None
    assert result.duration_ms == 123.45