"""Tests for low-level Loxone WebSocket connection behavior."""

import logging
from types import SimpleNamespace

import pytest

from custom_components.loxone.pyloxone_api.connection import LoxoneConnection


def _connected_transport():
    """Return a minimal transport object that satisfies is_connected."""
    return SimpleNamespace(protocol=SimpleNamespace(state=SimpleNamespace(name="OPEN")))


@pytest.fixture
def loxone_connection() -> LoxoneConnection:
    """Return a LoxoneConnection without opening a real network connection."""
    return LoxoneConnection("192.168.1.100", "admin", "password")


async def test_send_websocket_command_queues_when_connected(
    loxone_connection: LoxoneConnection,
) -> None:
    """Connected commands should still be enqueued for the send loop."""
    loxone_connection.connection = _connected_transport()

    await loxone_connection.send_websocket_command("test-uuid", "on")

    queued = loxone_connection._message_queue.get_nowait()
    assert queued.command == "jdev/sps/io/test-uuid/on"
    assert queued.flag is True


async def test_send_websocket_command_drops_when_disconnected(
    loxone_connection: LoxoneConnection,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Disconnected commands should not pile up in the queue."""
    caplog.set_level(logging.WARNING)

    await loxone_connection.send_websocket_command("test-uuid", "on")

    assert loxone_connection._message_queue.empty()
    assert "Dropping websocket command for test-uuid because connection is not open" in caplog.text


async def test_send_websocket_command_validates_uuid_before_connection_state(
    loxone_connection: LoxoneConnection,
) -> None:
    """Input validation should still reject invalid UUID values."""
    with pytest.raises(ValueError, match="device_uuid must be a non-empty string"):
        await loxone_connection.send_websocket_command("", "on")


async def test_send_text_command_returns_when_disconnected(
    loxone_connection: LoxoneConnection,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """The send loop should stop cleanly if the connection closes before send."""
    caplog.set_level(logging.WARNING)

    await loxone_connection._send_text_command("jdev/sps/io/test-uuid/on")

    assert "Cannot send command" in caplog.text
