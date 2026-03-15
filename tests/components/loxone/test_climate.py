"""Tests for Loxone climate (AcControl) entities."""

import pytest
from homeassistant.components.climate import ATTR_TEMPERATURE
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.loxone.const import EVENT, SENDDOMAIN


@pytest.fixture
def structure_fixture_name() -> str:
    return "structure_climate.json"


AC_ENTITY_ID = "climate.living_room_ac"
AC_ACTION_UUID = "ac010000-0000-0000-0000000000000000"

AC_TEMP_UUID = "ac010000-0000-0000-0000000000000001"
AC_TARGET_UUID = "ac010000-0000-0000-0000000000000002"
AC_STATUS_UUID = "ac010000-0000-0000-0000000000000003"
AC_MODE_UUID = "ac010000-0000-0000-0000000000000004"


# -- Entity creation ----------------------------------------------------------


async def test_ac_entity_created(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """AcControl entity should be created from the fixture."""
    state = hass.states.get(AC_ENTITY_ID)
    assert state is not None


async def test_ac_attributes(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """AC should expose device_type in attributes."""
    state = hass.states.get(AC_ENTITY_ID)
    assert state.attributes["device_type"] == "AcControl"


# -- set_temperature sends correct command ------------------------------------


async def test_set_temperature_sends_command(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """set_temperature should fire SENDDOMAIN with setTarget/<temp>."""
    events = []
    hass.bus.async_listen(SENDDOMAIN, lambda e: events.append(e))

    await hass.services.async_call(
        "climate",
        "set_temperature",
        {"entity_id": AC_ENTITY_ID, ATTR_TEMPERATURE: 22.5},
        blocking=True,
    )
    await hass.async_block_till_done()

    assert len(events) == 1
    assert events[0].data["uuid"] == AC_ACTION_UUID
    assert events[0].data["value"] == "setTarget/22.5"


# -- Current / target temperature from events ---------------------------------


async def test_current_temperature_from_event(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """Temperature state update should reflect in current_temperature."""
    hass.bus.async_fire(EVENT, {AC_TEMP_UUID: 23.5})
    await hass.async_block_till_done()

    state = hass.states.get(AC_ENTITY_ID)
    assert state.attributes["current_temperature"] == pytest.approx(23.5)


async def test_target_temperature_from_event(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """Target temperature state update should reflect in target_temperature."""
    hass.bus.async_fire(EVENT, {AC_TARGET_UUID: 21.0})
    await hass.async_block_till_done()

    state = hass.states.get(AC_ENTITY_ID)
    assert state.attributes["temperature"] == pytest.approx(21.0)


# -- HVAC mode ----------------------------------------------------------------


async def test_hvac_mode_off_when_status_falsy(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """When status is 0/falsy, hvac_mode should be off."""
    hass.bus.async_fire(EVENT, {AC_STATUS_UUID: 0})
    await hass.async_block_till_done()

    state = hass.states.get(AC_ENTITY_ID)
    assert state.state == "off"


async def test_hvac_mode_heat(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """status=1 + mode=2 → heat."""
    hass.bus.async_fire(EVENT, {AC_STATUS_UUID: 1, AC_MODE_UUID: 2})
    await hass.async_block_till_done()

    state = hass.states.get(AC_ENTITY_ID)
    assert state.state == "heat"


async def test_hvac_mode_cool(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """status=1 + mode=3 → cool."""
    hass.bus.async_fire(EVENT, {AC_STATUS_UUID: 1, AC_MODE_UUID: 3})
    await hass.async_block_till_done()

    state = hass.states.get(AC_ENTITY_ID)
    assert state.state == "cool"
