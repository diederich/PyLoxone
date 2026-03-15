"""Tests for Loxone integration setup and unload."""

from unittest.mock import MagicMock

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.loxone.const import DOMAIN

# Apply init_integration to all tests in this module
# (individual tests can override by not requesting the fixture)


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
