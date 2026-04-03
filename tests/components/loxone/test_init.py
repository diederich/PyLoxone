"""Tests for Loxone integration setup, unload, and services."""

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import (
    area_registry as ar,
    device_registry as dr,
)
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.loxone.const import ATTR_AREA_CREATE, DOMAIN


# -- Setup / unload -----------------------------------------------------------


async def test_setup_entry(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
) -> None:
    """Test that the integration sets up successfully."""
    entry = init_integration
    assert entry.state is ConfigEntryState.LOADED
    assert entry.runtime_data is not None


async def test_unload_entry(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
) -> None:
    """Test that the integration unloads successfully."""
    entry = init_integration
    assert entry.state is ConfigEntryState.LOADED

    result = await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()

    assert result is True
    assert entry.state is ConfigEntryState.NOT_LOADED


# -- Services registered in async_setup (MED-012 fix) -------------------------


async def test_services_registered_before_entry_setup(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Services must exist after async_setup, even if no config entry has loaded."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    for service in (
        "event_websocket_command",
        "event_secured_websocket_command",
        "sync_areas",
        "sync_device_names",
        "reload",
    ):
        assert hass.services.has_service(DOMAIN, service), (
            f"Service {DOMAIN}.{service} should be registered"
        )


async def test_services_survive_entry_unload(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
) -> None:
    """Services must remain available after the config entry is unloaded."""
    entry = init_integration

    await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()

    for service in (
        "event_websocket_command",
        "event_secured_websocket_command",
        "sync_areas",
        "sync_device_names",
        "reload",
    ):
        assert hass.services.has_service(DOMAIN, service), (
            f"Service {DOMAIN}.{service} should survive entry unload"
        )


async def test_websocket_command_raises_when_no_coordinator(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
) -> None:
    """Calling event_websocket_command with no coordinator should raise."""
    entry = init_integration

    await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()

    with pytest.raises(HomeAssistantError, match="not connected"):
        await hass.services.async_call(
            DOMAIN,
            "event_websocket_command",
            {"uuid": "fake-uuid", "value": "pulse"},
            blocking=True,
        )


async def test_async_load_platform_only_for_yaml_platforms(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_loxone_connection: MagicMock,
) -> None:
    """async_load_platform should only be called for sensor and binary_sensor.

    These two platforms support YAML-based custom entities (the "Advanced usage"
    escape hatch documented in README.md). All other platforms use only
    async_forward_entry_setups via async_setup_entry.
    """
    with patch(
        "custom_components.loxone.async_load_platform",
        wraps=None,
    ) as mock_load:
        mock_config_entry.add_to_hass(hass)
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    called_platforms = {call.args[1] for call in mock_load.call_args_list}
    assert called_platforms == {Platform.SENSOR, Platform.BINARY_SENSOR}


# -- sync_device_names service ------------------------------------------------


@pytest.fixture
def structure_fixture_name() -> str:
    return "structure_switches.json"


async def test_sync_device_names_updates_device(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
) -> None:
    """sync_device_names should update a device whose name differs from the structure file."""
    dr_registry = dr.async_get(hass)

    # Manually create a device with a stale name for a known UUID
    device = dr_registry.async_get_or_create(
        config_entry_id=init_integration.entry_id,
        identifiers={(DOMAIN, "aaa10000-0000-0000-0000000000000000")},
        name="Old Stale Name",
    )
    assert device.name == "Old Stale Name"

    await hass.services.async_call(DOMAIN, "sync_device_names", blocking=True)

    updated = dr_registry.async_get(device.id)
    assert updated.name == "Wall Switch"


async def test_sync_device_names_skips_matching(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
) -> None:
    """sync_device_names should not touch devices whose name already matches."""
    dr_registry = dr.async_get(hass)

    device = dr_registry.async_get_or_create(
        config_entry_id=init_integration.entry_id,
        identifiers={(DOMAIN, "aaa10000-0000-0000-0000000000000000")},
        name="Wall Switch",
    )

    await hass.services.async_call(DOMAIN, "sync_device_names", blocking=True)

    updated = dr_registry.async_get(device.id)
    assert updated.name == "Wall Switch"


async def test_sync_device_names_ignores_non_loxone_devices(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
) -> None:
    """sync_device_names should ignore devices from other integrations."""
    dr_registry = dr.async_get(hass)

    device = dr_registry.async_get_or_create(
        config_entry_id=init_integration.entry_id,
        identifiers={("other_integration", "some-uuid")},
        name="Foreign Device",
    )

    await hass.services.async_call(DOMAIN, "sync_device_names", blocking=True)

    unchanged = dr_registry.async_get(device.id)
    assert unchanged.name == "Foreign Device"


# -- Auto-sync on setup -------------------------------------------------------


async def test_auto_sync_creates_areas_on_first_setup(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
) -> None:
    """First setup with create_areas=True should auto-create HA areas."""
    ar_registry = ar.async_get(hass)
    area = ar_registry.async_get_area_by_name("Living Room")
    assert area is not None, "Living Room area should be auto-created on first setup"


async def test_auto_sync_assigns_devices_to_areas_on_setup(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
) -> None:
    """First setup should auto-assign devices to areas based on Loxone rooms."""
    ar_registry = ar.async_get(hass)
    dr_registry = dr.async_get(hass)

    area = ar_registry.async_get_area_by_name("Living Room")
    assert area is not None

    for device in dr_registry.devices.values():
        if device.via_device_id is None:
            continue
        for domain, _uuid in device.identifiers:
            if domain == DOMAIN:
                assert device.area_id == area.id, (
                    f"Device {device.name} should be in Living Room area"
                )


async def test_auto_sync_sets_initial_sync_done_flag(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
) -> None:
    """After first setup, initial_sync_done flag should be stored in entry data."""
    assert init_integration.data.get("initial_sync_done") is True


async def test_auto_sync_does_not_create_areas_when_opted_out(
    hass: HomeAssistant,
) -> None:
    """When create_areas_on_setup=False, sync_areas should not create new HA areas.

    Uses a fixture with rooms/controls but create_areas=False. HA will still
    create areas from suggested_area in device_info, but sync_areas itself
    should not add any *extra* areas beyond what HA creates automatically.
    """
    from custom_components.loxone.const import CONF_CREATE_AREAS
    from tests.components.loxone.conftest import MOCK_OPTIONS

    with patch(
        "custom_components.loxone._async_sync_areas",
    ) as mock_sync_areas, patch(
        "custom_components.loxone.coordinator.LoxoneConnection",
    ) as mock_cls:
        api = MagicMock()
        api.open = AsyncMock()
        api.close = AsyncMock()
        api.start_listening = AsyncMock()
        api.send_websocket_command = AsyncMock()
        api.send_secured__websocket_command = AsyncMock()
        api.get_token_dict = MagicMock(
            return_value={"token": "fake", "hash_alg": "SHA256", "valid_until": "9999"}
        )
        structure = json.loads(
            (Path(__file__).parent / "fixtures" / "structure_switches.json").read_text()
        )
        api.structure_file = structure
        api.connection = MagicMock()
        mock_cls.return_value = api

        entry = MockConfigEntry(
            domain=DOMAIN,
            data={},
            options={**MOCK_OPTIONS, CONF_CREATE_AREAS: False},
            unique_id="504F94A0FEA2_no_areas",
            version=3,
        )
        entry.add_to_hass(hass)
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    mock_sync_areas.assert_awaited_once()
    call_data = mock_sync_areas.call_args[0][1]
    assert call_data[ATTR_AREA_CREATE] is False, (
        "sync_areas should be called with create_areas=False when user opted out"
    )


async def test_auto_sync_does_not_recreate_deleted_areas_on_restart(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    mock_loxone_connection: MagicMock,
) -> None:
    """On restart (initial_sync_done=True), deleted areas should not be recreated."""
    ar_registry = ar.async_get(hass)

    area = ar_registry.async_get_area_by_name("Living Room")
    assert area is not None
    ar_registry.async_delete(area.id)
    assert ar_registry.async_get_area_by_name("Living Room") is None

    assert init_integration.data.get("initial_sync_done") is True

    # Simulate restart by unloading and reloading
    await hass.config_entries.async_unload(init_integration.entry_id)
    await hass.async_block_till_done()
    await hass.config_entries.async_setup(init_integration.entry_id)
    await hass.async_block_till_done()

    area = ar_registry.async_get_area_by_name("Living Room")
    assert area is None, "Deleted area should not be recreated on restart"
