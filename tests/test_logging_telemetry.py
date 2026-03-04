"""Test logging and telemetry integration."""

import pytest
from unittest.mock import Mock

from remote_machine.metrics.dummy import DummyTelemetry
from remote_machine.protocols.ssh import SSHProtocol
from remote_machine.models.remote_state import RemoteState


def test_ssh_protocol_telemetry():
    """Test that SSH protocol calls telemetry methods."""
    telemetry = DummyTelemetry()
    protocol = SSHProtocol("testhost", "testuser", telemetry=telemetry)

    # Mock the _client to avoid actual connection
    protocol._client = Mock()

    # Mock exec_command
    mock_stdout = Mock()
    mock_stdout.channel.recv_exit_status.return_value = 0
    mock_stdout.read.return_value = b"output"
    mock_stderr = Mock()
    mock_stderr.read.return_value = b""

    protocol._client.exec_command.return_value = (Mock(), mock_stdout, mock_stderr)

    state = RemoteState()
    result = protocol.exec("echo test", state)

    # Check that telemetry was called
    assert len(telemetry.calls) == 1
    call_type, host, duration, success = telemetry.calls[0]
    assert call_type == "command"
    assert host == "testhost"
    assert success is True
    assert isinstance(duration, float)


def test_ssh_protocol_no_telemetry():
    """Test that SSH protocol works without telemetry."""
    protocol = SSHProtocol("testhost", "testuser", telemetry=None)

    # Mock the _client to avoid actual connection
    protocol._client = Mock()

    # Mock exec_command
    mock_stdout = Mock()
    mock_stdout.channel.recv_exit_status.return_value = 0
    mock_stdout.read.return_value = b"output"
    mock_stderr = Mock()
    mock_stderr.read.return_value = b""

    protocol._client.exec_command.return_value = (Mock(), mock_stdout, mock_stderr)

    state = RemoteState()
    result = protocol.exec("echo test", state)

    # Should work without telemetry
    assert result.stdout == "output"
    assert result.exit_code == 0


def test_telemetry_failure_does_not_break_execution():
    """Test that telemetry failures don't break command execution."""
    telemetry = Mock()
    telemetry.record_command.side_effect = Exception("Telemetry failed")

    protocol = SSHProtocol("testhost", "testuser", telemetry=telemetry)

    # Mock the _client to avoid actual connection
    protocol._client = Mock()

    # Mock exec_command
    mock_stdout = Mock()
    mock_stdout.channel.recv_exit_status.return_value = 0
    mock_stdout.read.return_value = b"output"
    mock_stderr = Mock()
    mock_stderr.read.return_value = b""

    protocol._client.exec_command.return_value = (Mock(), mock_stdout, mock_stderr)

    state = RemoteState()
    result = protocol.exec("echo test", state)

    # Should still work despite telemetry failure
    assert result.stdout == "output"
    assert result.exit_code == 0