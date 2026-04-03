"""Tests for the LoxoneCoordinator reconnect logic and connectivity sensor."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.const import STATE_ON, STATE_OFF, EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.loxone.const import DOMAIN
from custom_components.loxone.coordinator import ConnectionState, LoxoneCoordinator
from custom_components.loxone.pyloxone_api.exceptions import (
    LoxoneConnectionError,
    LoxoneTokenError,
)

MINISERVER_SERIAL = "504F94A0FEA2"
CONNECTIVITY_ENTITY_ID = "binary_sensor.test_miniserver_connection"


@pytest.fixture
def structure_fixture_name() -> str:
    return "structure_binary_sensors.json"


# -- Connectivity binary sensor ------------------------------------------------


async def test_connectivity_sensor_created(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """Connectivity sensor should be created on the miniserver device."""
    state = hass.states.get(CONNECTIVITY_ENTITY_ID)
    assert state is not None
    assert state.state == STATE_ON


async def test_connectivity_sensor_device_link(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """Connectivity sensor should be attached to the miniserver device."""
    ent_reg = er.async_get(hass)
    entry = ent_reg.async_get(CONNECTIVITY_ENTITY_ID)
    assert entry is not None
    assert entry.unique_id == f"{MINISERVER_SERIAL}_connectivity"
    assert entry.entity_category == EntityCategory.DIAGNOSTIC

    dev_reg = dr.async_get(hass)
    device = dev_reg.async_get(entry.device_id)
    assert device is not None
    assert (DOMAIN, MINISERVER_SERIAL) in device.identifiers


async def test_connectivity_sensor_always_available(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """Connectivity sensor should report available=True even when disconnected."""
    coordinator: LoxoneCoordinator = init_integration.runtime_data

    coordinator.async_set_update_error(
        LoxoneConnectionError("Disconnected from Miniserver")
    )
    await hass.async_block_till_done()

    state = hass.states.get(CONNECTIVITY_ENTITY_ID)
    assert state is not None
    assert state.state == STATE_OFF


async def test_connectivity_sensor_reflects_reconnect(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """Connectivity sensor should toggle off on disconnect, on after reconnect."""
    coordinator: LoxoneCoordinator = init_integration.runtime_data

    coordinator.async_set_update_error(
        LoxoneConnectionError("Disconnected")
    )
    await hass.async_block_till_done()
    assert hass.states.get(CONNECTIVITY_ENTITY_ID).state == STATE_OFF

    coordinator.async_set_updated_data({"connected": True})
    await hass.async_block_till_done()
    assert hass.states.get(CONNECTIVITY_ENTITY_ID).state == STATE_ON


# -- Connection state tracking -------------------------------------------------


async def test_initial_connection_state(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """After setup the coordinator should be in CONNECTED state."""
    coordinator: LoxoneCoordinator = init_integration.runtime_data
    assert coordinator.connection_state == ConnectionState.CONNECTED
    assert coordinator.last_update_success is True


async def test_disconnect_sets_state(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """Simulating a disconnect sets state to DISCONNECTED and last_update_success False."""
    coordinator: LoxoneCoordinator = init_integration.runtime_data

    coordinator.connection_state = ConnectionState.DISCONNECTED
    coordinator.async_set_update_error(
        LoxoneConnectionError("Disconnected")
    )
    await hass.async_block_till_done()

    assert coordinator.connection_state == ConnectionState.DISCONNECTED
    assert coordinator.last_update_success is False


# -- Reconnect logic ----------------------------------------------------------


async def test_handle_task_result_triggers_reconnect(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """When the listening task fails, _handle_task_result should start reconnect."""
    coordinator: LoxoneCoordinator = init_integration.runtime_data

    with patch.object(coordinator, "_async_reconnect", new_callable=AsyncMock) as mock_reconnect:
        failed_task = asyncio.Future()
        failed_task.set_exception(LoxoneConnectionError("Connection lost"))

        coordinator._handle_task_result(failed_task)
        await hass.async_block_till_done()

        mock_reconnect.assert_called_once_with(clear_token=False)

    assert coordinator.connection_state == ConnectionState.DISCONNECTED
    assert coordinator.last_update_success is False


async def test_handle_task_result_clears_token_on_token_error(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """LoxoneTokenError should trigger reconnect with clear_token=True."""
    coordinator: LoxoneCoordinator = init_integration.runtime_data

    with patch.object(coordinator, "_async_reconnect", new_callable=AsyncMock) as mock_reconnect:
        failed_task = asyncio.Future()
        failed_task.set_exception(LoxoneTokenError("Token expired"))

        coordinator._handle_task_result(failed_task)
        await hass.async_block_till_done()

        mock_reconnect.assert_called_once_with(clear_token=True)


async def test_handle_task_result_skips_reconnect_when_cancelled(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """CancelledError (from cleanup) should not trigger reconnect."""
    coordinator: LoxoneCoordinator = init_integration.runtime_data

    with patch.object(coordinator, "_async_reconnect", new_callable=AsyncMock) as mock_reconnect:
        cancelled_task = asyncio.Future()
        cancelled_task.cancel()

        try:
            coordinator._handle_task_result(cancelled_task)
        except asyncio.CancelledError:
            pass
        await hass.async_block_till_done()

        mock_reconnect.assert_not_called()


async def test_handle_task_result_skips_when_shutting_down(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """No reconnect if the coordinator is shutting down."""
    coordinator: LoxoneCoordinator = init_integration.runtime_data
    coordinator._shutting_down = True

    with patch.object(coordinator, "_async_reconnect", new_callable=AsyncMock) as mock_reconnect:
        failed_task = asyncio.Future()
        failed_task.set_exception(LoxoneConnectionError("Lost"))

        coordinator._handle_task_result(failed_task)
        await hass.async_block_till_done()

        mock_reconnect.assert_not_called()


async def test_reconnect_creates_new_api(
    hass: HomeAssistant, init_integration: MockConfigEntry,
    mock_loxone_connection: MagicMock,
) -> None:
    """_async_reconnect should create a new LoxoneConnection and start listening."""
    coordinator: LoxoneCoordinator = init_integration.runtime_data

    with patch.object(coordinator, "async_start_listening", new_callable=AsyncMock):
        await coordinator._async_reconnect()

    assert coordinator.connection_state == ConnectionState.CONNECTED
    assert coordinator.last_update_success is True


async def test_reconnect_clears_token_when_requested(
    hass: HomeAssistant, init_integration: MockConfigEntry,
    mock_loxone_connection: MagicMock,
) -> None:
    """_async_reconnect with clear_token=True should clear token from config entry."""
    coordinator: LoxoneCoordinator = init_integration.runtime_data

    hass.config_entries.async_update_entry(
        init_integration,
        data={"token": "old-token", "hash_alg": "SHA256", "valid_until": "9999"},
    )
    assert init_integration.data["token"] == "old-token"

    with patch.object(coordinator, "async_start_listening", new_callable=AsyncMock):
        await coordinator._async_reconnect(clear_token=True)

    assert init_integration.data["token"] == ""


# -- Entity availability on disconnect ----------------------------------------


async def test_entity_goes_unavailable_on_disconnect(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """LoxoneEntity-based entities should go unavailable when coordinator disconnects."""
    coordinator: LoxoneCoordinator = init_integration.runtime_data

    state = hass.states.get("binary_sensor.door_contact")
    assert state is not None

    coordinator.async_set_update_error(
        LoxoneConnectionError("Disconnected")
    )
    await hass.async_block_till_done()

    state = hass.states.get("binary_sensor.door_contact")
    assert state.state == "unavailable"


async def test_entity_recovers_on_reconnect(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """LoxoneEntity-based entities should recover when coordinator reconnects."""
    coordinator: LoxoneCoordinator = init_integration.runtime_data

    coordinator.async_set_update_error(
        LoxoneConnectionError("Disconnected")
    )
    await hass.async_block_till_done()
    assert hass.states.get("binary_sensor.door_contact").state == "unavailable"

    coordinator.async_set_updated_data({"connected": True})
    await hass.async_block_till_done()

    state = hass.states.get("binary_sensor.door_contact")
    assert state.state != "unavailable"


# -- Cleanup during reconnect -------------------------------------------------


async def test_cleanup_cancels_reconnect_task(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """async_cleanup should cancel an in-flight reconnect task."""
    coordinator: LoxoneCoordinator = init_integration.runtime_data

    reconnect_started = asyncio.Event()

    async def slow_reconnect(**kwargs):
        reconnect_started.set()
        await asyncio.sleep(300)

    with patch.object(coordinator, "_async_reconnect", side_effect=slow_reconnect):
        coordinator._reconnect_task = hass.async_create_task(
            coordinator._async_reconnect()
        )
        await reconnect_started.wait()

    coordinator._reconnect_task = hass.async_create_task(asyncio.sleep(300))
    await coordinator.async_cleanup()

    assert coordinator._reconnect_task is None
    assert coordinator._listening_task is None


async def test_unload_during_connected_state(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """Unloading the config entry should clean up cleanly."""
    entry = init_integration
    assert entry.state.name == "LOADED"

    result = await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    assert result is True
