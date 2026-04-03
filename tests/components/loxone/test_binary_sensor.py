"""Tests for Loxone binary sensor entities."""

import pytest
from homeassistant.const import STATE_ON, STATE_OFF
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from tests.components.loxone.conftest import fire_loxone_event


@pytest.fixture
def structure_fixture_name() -> str:
    return "structure_binary_sensors.json"


DIGITAL_ENTITY_ID = "binary_sensor.door_contact"
DIGITAL_ACTION_UUID = "dig10000-0000-0000-0000000000000000"
DIGITAL_ACTIVE_UUID = "dig10000-0000-0000-0000000000000001"

PRESENCE_ENTITY_ID = "binary_sensor.hallway_motion"
PRESENCE_ACTIVE_UUID = "pres1000-0000-0000-0000000000000001"

SMOKE_ENTITY_ID = "binary_sensor.kitchen_smoke"
SMOKE_ALARM_OFF_UUID = "smok1000-0000-0000-0000000000000001"
SMOKE_ACTIVE_UUID = "smok1000-0000-0000-0000000000000002"
SMOKE_ACTION_UUID = "smok1000-0000-0000-0000000000000000"


# -- Entity creation ----------------------------------------------------------


async def test_digital_entity_created(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """InfoOnlyDigital should create a binary_sensor."""
    state = hass.states.get(DIGITAL_ENTITY_ID)
    assert state is not None


async def test_presence_entity_created(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """PresenceDetector should create a binary_sensor."""
    state = hass.states.get(PRESENCE_ENTITY_ID)
    assert state is not None


async def test_smoke_entity_created(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """SmokeAlarm should create a binary_sensor."""
    state = hass.states.get(SMOKE_ENTITY_ID)
    assert state is not None


# -- Digital sensor state updates ---------------------------------------------


async def test_digital_on_from_event(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """Digital sensor should turn on via states['active'] UUID."""
    fire_loxone_event(hass, {DIGITAL_ACTIVE_UUID: 1.0})
    await hass.async_block_till_done()

    state = hass.states.get(DIGITAL_ENTITY_ID)
    assert state.state == STATE_ON


async def test_digital_off_from_event(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """Digital sensor should turn off via states['active'] UUID."""
    fire_loxone_event(hass, {DIGITAL_ACTIVE_UUID: 1.0})
    await hass.async_block_till_done()

    fire_loxone_event(hass, {DIGITAL_ACTIVE_UUID: 0.0})
    await hass.async_block_till_done()

    state = hass.states.get(DIGITAL_ENTITY_ID)
    assert state.state == STATE_OFF


async def test_digital_ignores_unrelated_events(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """Unrelated UUID should not change state."""
    initial = hass.states.get(DIGITAL_ENTITY_ID).state

    fire_loxone_event(hass, {"unrelated-uuid": 1.0})
    await hass.async_block_till_done()

    assert hass.states.get(DIGITAL_ENTITY_ID).state == initial


# -- Presence sensor ----------------------------------------------------------


async def test_presence_listens_to_active_uuid(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """Presence type should listen on states['active'] UUID."""
    fire_loxone_event(hass, {PRESENCE_ACTIVE_UUID: 1.0})
    await hass.async_block_till_done()

    state = hass.states.get(PRESENCE_ENTITY_ID)
    assert state.state == STATE_ON


# -- Smoke sensor: listens on areAlarmSignalsOff ------------------------------


async def test_smoke_listens_on_alarm_signals_off(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """Smoke sensor should listen on states['areAlarmSignalsOff']."""
    fire_loxone_event(hass, {SMOKE_ALARM_OFF_UUID: 1.0})
    await hass.async_block_till_done()

    state = hass.states.get(SMOKE_ENTITY_ID)
    assert state.state == STATE_ON


async def test_smoke_ignores_action_uuid(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """Smoke sensor should not respond to uuidAction."""
    fire_loxone_event(hass, {SMOKE_ACTION_UUID: 1.0})
    await hass.async_block_till_done()

    state = hass.states.get(SMOKE_ENTITY_ID)
    assert state.state != STATE_ON