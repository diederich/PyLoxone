"""Tests for Loxone climate (AcControl, IRoomControllerV2) entities."""

import json

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.loxone.const import SENDDOMAIN
from homeassistant.components.climate import ATTR_TEMPERATURE
from homeassistant.core import HomeAssistant

from .conftest import fire_loxone_event


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


async def test_ac_entity_created(hass: HomeAssistant, init_integration: MockConfigEntry) -> None:
    """AcControl entity should be created from the fixture."""
    state = hass.states.get(AC_ENTITY_ID)
    assert state is not None


async def test_ac_attributes(hass: HomeAssistant, init_integration: MockConfigEntry) -> None:
    """AC should expose device_type in attributes."""
    state = hass.states.get(AC_ENTITY_ID)
    assert state.attributes["device_type"] == "AcControl"


# -- set_temperature sends correct command ------------------------------------


async def test_set_temperature_sends_command(hass: HomeAssistant, init_integration: MockConfigEntry) -> None:
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


async def test_current_temperature_from_event(hass: HomeAssistant, init_integration: MockConfigEntry) -> None:
    """Temperature state update should reflect in current_temperature."""
    fire_loxone_event(hass, {AC_TEMP_UUID: 23.5})
    await hass.async_block_till_done()

    state = hass.states.get(AC_ENTITY_ID)
    assert state.attributes["current_temperature"] == pytest.approx(23.5)


async def test_target_temperature_from_event(hass: HomeAssistant, init_integration: MockConfigEntry) -> None:
    """Target temperature state update should reflect in target_temperature."""
    fire_loxone_event(hass, {AC_TARGET_UUID: 21.0})
    await hass.async_block_till_done()

    state = hass.states.get(AC_ENTITY_ID)
    assert state.attributes["temperature"] == pytest.approx(21.0)


# -- HVAC mode ----------------------------------------------------------------


async def test_hvac_mode_off_when_status_falsy(hass: HomeAssistant, init_integration: MockConfigEntry) -> None:
    """When status is 0/falsy, hvac_mode should be off."""
    fire_loxone_event(hass, {AC_STATUS_UUID: 0})
    await hass.async_block_till_done()

    state = hass.states.get(AC_ENTITY_ID)
    assert state.state == "off"


async def test_hvac_mode_heat(hass: HomeAssistant, init_integration: MockConfigEntry) -> None:
    """status=1 + mode=2 → heat."""
    fire_loxone_event(hass, {AC_STATUS_UUID: 1, AC_MODE_UUID: 2})
    await hass.async_block_till_done()

    state = hass.states.get(AC_ENTITY_ID)
    assert state.state == "heat"


async def test_hvac_mode_cool(hass: HomeAssistant, init_integration: MockConfigEntry) -> None:
    """status=1 + mode=3 → cool."""
    fire_loxone_event(hass, {AC_STATUS_UUID: 1, AC_MODE_UUID: 3})
    await hass.async_block_till_done()

    state = hass.states.get(AC_ENTITY_ID)
    assert state.state == "cool"


# -- IRoomControllerV2 -------------------------------------------------------

RC_ENTITY_ID = "climate.bedroom_climate"
RC_OVERRIDE_UUID = "rc020000-0000-0000-0000000000000004"
RC_TEMP_ACTUAL_UUID = "rc020000-0000-0000-0000000000000001"


async def test_room_controller_v2_created(hass: HomeAssistant, init_integration: MockConfigEntry) -> None:
    """IRoomControllerV2 should create a climate entity."""
    state = hass.states.get(RC_ENTITY_ID)
    assert state is not None


async def test_room_controller_v2_current_temp(hass: HomeAssistant, init_integration: MockConfigEntry) -> None:
    """TempActual event should update current_temperature."""
    fire_loxone_event(hass, {RC_TEMP_ACTUAL_UUID: 21.5})
    await hass.async_block_till_done()

    state = hass.states.get(RC_ENTITY_ID)
    assert state.attributes["current_temperature"] == pytest.approx(21.5)


# -- is_overridden: json.loads regression (BUG-008) ---------------------------


async def test_is_overridden_false_when_empty(hass: HomeAssistant, init_integration: MockConfigEntry) -> None:
    """is_overridden should be False when overrideEntries is an empty list."""
    fire_loxone_event(hass, {RC_OVERRIDE_UUID: "[]"})
    await hass.async_block_till_done()

    state = hass.states.get(RC_ENTITY_ID)
    assert state.attributes["is_overridden"] is False


async def test_is_overridden_true_with_entries(hass: HomeAssistant, init_integration: MockConfigEntry) -> None:
    """is_overridden should be True when overrideEntries has items (JSON with true/false)."""
    entries = json.dumps([{"from": 1000, "to": 2000, "value": 22.0, "active": True}])
    fire_loxone_event(hass, {RC_OVERRIDE_UUID: entries})
    await hass.async_block_till_done()

    state = hass.states.get(RC_ENTITY_ID)
    assert state.attributes["is_overridden"] is True


async def test_is_overridden_false_when_no_event(hass: HomeAssistant, init_integration: MockConfigEntry) -> None:
    """is_overridden should be False before any overrideEntries event."""
    state = hass.states.get(RC_ENTITY_ID)
    assert state.attributes["is_overridden"] is False
