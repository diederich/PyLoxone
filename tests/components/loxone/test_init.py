"""Tests for Loxone integration setup, unload, and services."""

import pytest
from unittest.mock import MagicMock, patch

from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.loxone.const import DOMAIN
from custom_components.loxone.helpers import (
    device_registry as helpers_device_registry,
    get_or_create_device,
)


# -- Setup / unload -----------------------------------------------------------


async def test_setup_entry(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
) -> None:
    """Test that the integration sets up successfully."""
    entry = init_integration
    assert entry.state is ConfigEntryState.LOADED
    assert DOMAIN in hass.data
    assert entry.entry_id in hass.data[DOMAIN]


async def test_unload_entry(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
) -> None:
    """Test that the integration unloads successfully.

    BUG: async_unload_entry removes services quick_shade,
    enable_sun_automation, and disable_sun_automation that are never
    registered in async_setup_entry (they come from entity platforms
    only when matching controls exist). We register them as no-ops here
    so the unload path can be validated without changing production code.
    """
    # Register the phantom services so async_remove doesn't raise
    for svc in ("quick_shade", "enable_sun_automation", "disable_sun_automation"):
        hass.services.async_register(DOMAIN, svc, lambda _: None)

    entry = init_integration
    assert entry.state is ConfigEntryState.LOADED

    result = await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()

    assert result is True
    assert entry.state is ConfigEntryState.NOT_LOADED


async def test_unload_clears_helpers_device_registry(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
) -> None:
    """Unloading should clear the helpers device_registry cache."""
    get_or_create_device("test-uuid", "Test", "Switch", "Room")
    assert len(helpers_device_registry) > 0

    for svc in ("quick_shade", "enable_sun_automation", "disable_sun_automation"):
        hass.services.async_register(DOMAIN, svc, lambda _: None)

    await hass.config_entries.async_unload(init_integration.entry_id)
    await hass.async_block_till_done()

    assert len(helpers_device_registry) == 0


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
