"""Tests for the Loxone PowerUnit binary sensors (fuse + CP1..CP7)."""

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.loxone.const import DOMAIN
from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.const import STATE_OFF, STATE_ON, EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er

from .conftest import fire_loxone_event


@pytest.fixture
def structure_fixture_name() -> str:
    return "structure_sensors.json"


PSU_UUID = "pwr10000-0000-0000-0000000000000000"
FUSE_STATE_UUID = "pwr10000-0000-0000-0000000000000005"
CP1_STATE_UUID = "pwr10000-0000-0000-0000000000000011"


async def _enable(hass: HomeAssistant, mock_config_entry: MockConfigEntry, unique_id: str) -> str:
    """Force-enable a disabled-by-default entity and return its entity_id."""
    mock_config_entry.add_to_hass(hass)
    ent_reg = er.async_get(hass)
    ent_reg.async_get_or_create(
        "binary_sensor",
        DOMAIN,
        unique_id,
        config_entry=mock_config_entry,
        disabled_by=None,
    )
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    entity_id = ent_reg.async_get_entity_id("binary_sensor", DOMAIN, unique_id)
    assert entity_id is not None
    return entity_id


async def test_fuse_binary_sensor_created_enabled(hass: HomeAssistant, init_integration: MockConfigEntry) -> None:
    """Fuse binary sensor should be created and enabled by default."""
    ent_reg = er.async_get(hass)
    entity_id = ent_reg.async_get_entity_id("binary_sensor", DOMAIN, f"{PSU_UUID}_fuse")
    assert entity_id is not None
    entry = ent_reg.async_get(entity_id)
    assert entry.disabled_by is None
    assert entry.entity_category == EntityCategory.DIAGNOSTIC
    assert entry.translation_key == "powerunit_fuse"


async def test_cp_binary_sensors_disabled_by_default(hass: HomeAssistant, init_integration: MockConfigEntry) -> None:
    """All 7 CP* binary sensors exist but are disabled by default."""
    ent_reg = er.async_get(hass)
    for n in range(1, 8):
        entity_id = ent_reg.async_get_entity_id("binary_sensor", DOMAIN, f"{PSU_UUID}_cp{n}")
        assert entity_id is not None, f"CP{n} binary sensor not registered"
        entry = ent_reg.async_get(entity_id)
        assert entry.disabled_by == er.RegistryEntryDisabler.INTEGRATION
        assert entry.entity_category == EntityCategory.DIAGNOSTIC


async def test_fuse_inverted_problem_semantics(hass: HomeAssistant, init_integration: MockConfigEntry) -> None:
    """fuse=1 (OK) -> off (no problem); fuse=0 (blown) -> on (problem)."""
    ent_reg = er.async_get(hass)
    entity_id = ent_reg.async_get_entity_id("binary_sensor", DOMAIN, f"{PSU_UUID}_fuse")

    fire_loxone_event(hass, {FUSE_STATE_UUID: 1.0})
    await hass.async_block_till_done()
    assert hass.states.get(entity_id).state == STATE_OFF

    fire_loxone_event(hass, {FUSE_STATE_UUID: 0.0})
    await hass.async_block_till_done()
    state = hass.states.get(entity_id)
    assert state.state == STATE_ON
    assert state.attributes.get("device_class") == BinarySensorDeviceClass.PROBLEM


async def test_cp1_state_event(hass: HomeAssistant, mock_config_entry: MockConfigEntry, mock_loxone_connection) -> None:
    """CP1 should reflect raw state via per-UUID event when enabled."""
    entity_id = await _enable(hass, mock_config_entry, f"{PSU_UUID}_cp1")

    fire_loxone_event(hass, {CP1_STATE_UUID: 0.0})
    await hass.async_block_till_done()
    assert hass.states.get(entity_id).state == STATE_ON  # 0 -> problem

    fire_loxone_event(hass, {CP1_STATE_UUID: 1.0})
    await hass.async_block_till_done()
    assert hass.states.get(entity_id).state == STATE_OFF


async def test_powerunit_binary_sensors_share_parent_device(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """Both fuse and CP1..CP7 binary sensors should live on the PowerUnit device."""
    ent_reg = er.async_get(hass)
    dev_reg = dr.async_get(hass)

    fuse_id = ent_reg.async_get_entity_id("binary_sensor", DOMAIN, f"{PSU_UUID}_fuse")
    cp3_id = ent_reg.async_get_entity_id("binary_sensor", DOMAIN, f"{PSU_UUID}_cp3")
    fuse_dev = dev_reg.async_get(ent_reg.async_get(fuse_id).device_id)
    cp3_dev = dev_reg.async_get(ent_reg.async_get(cp3_id).device_id)
    assert fuse_dev.id == cp3_dev.id
    assert (DOMAIN, PSU_UUID) in fuse_dev.identifiers
    assert fuse_dev.model == "Power Unit"
