"""Tests for Loxone fan (Ventilation) entities.

Note: Ventilation sub-entities (presence, humidity, air quality, temperature)
are not tested here. The production code adds them through the fan platform's
async_add_entities with parent_id set, which overwrites their uuidAction to
the parent's — causing unique_id collisions that prevent the main fan entity
from being registered. Sub-entity behavior is covered by the sensor and
binary_sensor test suites.
"""

import pytest
from homeassistant.components.fan import FanEntityFeature
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.loxone.const import EVENT, SENDDOMAIN


@pytest.fixture
def structure_fixture_name() -> str:
    return "structure_fan.json"


FAN_ENTITY_ID = "fan.house_ventilation"
FAN_ACTION_UUID = "fan10000-0000-0000-0000000000000000"

SPEED_UUID = "fan10000-0000-0000-0000000000000010"
MODE_UUID = "fan10000-0000-0000-0000000000000011"


# -- Entity creation ----------------------------------------------------------


async def test_fan_entity_created(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """Ventilation control should create a fan entity."""
    state = hass.states.get(FAN_ENTITY_ID)
    assert state is not None


async def test_fan_supported_features(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """Fan should support preset mode, set speed, turn on, and turn off."""
    state = hass.states.get(FAN_ENTITY_ID)
    features = state.attributes.get("supported_features")
    assert features & FanEntityFeature.PRESET_MODE
    assert features & FanEntityFeature.SET_SPEED
    assert features & FanEntityFeature.TURN_ON
    assert features & FanEntityFeature.TURN_OFF


async def test_fan_preset_modes(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """Fan should expose ventilation preset modes."""
    state = hass.states.get(FAN_ENTITY_ID)
    preset_modes = state.attributes.get("preset_modes")
    assert "Low" in preset_modes
    assert "Medium" in preset_modes
    assert "High" in preset_modes
    assert "Auto" in preset_modes


# -- Event handling -----------------------------------------------------------


async def test_fan_speed_from_event(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """Speed event should update percentage."""
    hass.bus.async_fire(EVENT, {SPEED_UUID: 75})
    await hass.async_block_till_done()

    state = hass.states.get(FAN_ENTITY_ID)
    assert state.attributes.get("percentage") == 75


async def test_fan_is_on_when_speed_nonzero(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """Fan should report on when speed > 0."""
    hass.bus.async_fire(EVENT, {SPEED_UUID: 50})
    await hass.async_block_till_done()

    state = hass.states.get(FAN_ENTITY_ID)
    assert state.state == "on"


async def test_fan_is_off_when_speed_zero(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """Fan should report off when speed is 0."""
    hass.bus.async_fire(EVENT, {SPEED_UUID: 0})
    await hass.async_block_till_done()

    state = hass.states.get(FAN_ENTITY_ID)
    assert state.state == "off"


async def test_fan_preset_mode_from_event(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """Mode event should update preset_mode."""
    hass.bus.async_fire(EVENT, {MODE_UUID: 5})
    await hass.async_block_till_done()

    state = hass.states.get(FAN_ENTITY_ID)
    assert state.attributes.get("preset_mode") == "Auto"


# -- Commands -----------------------------------------------------------------


async def test_set_percentage_sends_command(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """set_percentage should fire a setTimer SENDDOMAIN event."""
    hass.bus.async_fire(EVENT, {MODE_UUID: 5})
    await hass.async_block_till_done()

    events = []
    hass.bus.async_listen(SENDDOMAIN, lambda e: events.append(e))

    await hass.services.async_call(
        "fan", "set_percentage",
        {"entity_id": FAN_ENTITY_ID, "percentage": 60},
        blocking=True,
    )
    await hass.async_block_till_done()

    assert len(events) == 1
    assert events[0].data["uuid"] == FAN_ACTION_UUID
    assert "setTimer/" in events[0].data["value"]
    assert "/60/" in events[0].data["value"]


async def test_set_percentage_zero_turns_off(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """Setting speed to 0 should turn the fan off."""
    hass.bus.async_fire(EVENT, {SPEED_UUID: 50, MODE_UUID: 5})
    await hass.async_block_till_done()

    events = []
    hass.bus.async_listen(SENDDOMAIN, lambda e: events.append(e))

    await hass.services.async_call(
        "fan", "set_percentage",
        {"entity_id": FAN_ENTITY_ID, "percentage": 0},
        blocking=True,
    )
    await hass.async_block_till_done()

    assert any("/0/" in e.data["value"] for e in events)
