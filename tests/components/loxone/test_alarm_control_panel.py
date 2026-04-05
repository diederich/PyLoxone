"""Tests for Loxone alarm control panel."""

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.loxone.const import SENDDOMAIN
from homeassistant.components.alarm_control_panel import AlarmControlPanelState
from homeassistant.core import HomeAssistant

from .conftest import fire_loxone_event


@pytest.fixture
def structure_fixture_name() -> str:
    return "structure_alarm.json"


ALARM_ENTITY_ID = "alarm_control_panel.house_alarm"
ALARM_ACTION_UUID = "alm10000-0000-0000-0000000000000000"

ARMED_UUID = "alm10000-0000-0000-0000000000000001"
DISABLED_MOVE_UUID = "alm10000-0000-0000-0000000000000002"
ARMED_DELAY_UUID = "alm10000-0000-0000-0000000000000003"
ARMED_DELAY_TOTAL_UUID = "alm10000-0000-0000-0000000000000004"
LEVEL_UUID = "alm10000-0000-0000-0000000000000005"
ARMED_AT_UUID = "alm10000-0000-0000-0000000000000006"


# -- Entity creation ----------------------------------------------------------


async def test_alarm_entity_created(hass: HomeAssistant, init_integration: MockConfigEntry) -> None:
    """Alarm control should create an alarm_control_panel entity."""
    state = hass.states.get(ALARM_ENTITY_ID)
    assert state is not None


# -- alarm_state branching (the core logic) -----------------------------------


async def test_alarm_state_disarmed(hass: HomeAssistant, init_integration: MockConfigEntry) -> None:
    """Default state (all zeros) should be disarmed."""
    state = hass.states.get(ALARM_ENTITY_ID)
    assert state.state == AlarmControlPanelState.DISARMED


async def test_alarm_state_armed_away(hass: HomeAssistant, init_integration: MockConfigEntry) -> None:
    """armed=1.0 without disabledMove should be armed_away."""
    fire_loxone_event(hass, {ARMED_UUID: 1.0})
    await hass.async_block_till_done()

    state = hass.states.get(ALARM_ENTITY_ID)
    assert state.state == AlarmControlPanelState.ARMED_AWAY


async def test_alarm_state_armed_home(hass: HomeAssistant, init_integration: MockConfigEntry) -> None:
    """armed=1.0 + disabledMove=1.0 should be armed_home."""
    fire_loxone_event(hass, {ARMED_UUID: 1.0, DISABLED_MOVE_UUID: 1.0})
    await hass.async_block_till_done()

    state = hass.states.get(ALARM_ENTITY_ID)
    assert state.state == AlarmControlPanelState.ARMED_HOME


async def test_alarm_state_arming_via_delay(hass: HomeAssistant, init_integration: MockConfigEntry) -> None:
    """Non-zero armedDelay should report arming."""
    fire_loxone_event(hass, {ARMED_DELAY_UUID: 10.0})
    await hass.async_block_till_done()

    state = hass.states.get(ALARM_ENTITY_ID)
    assert state.state == AlarmControlPanelState.ARMING


async def test_alarm_state_arming_via_armed_at(hass: HomeAssistant, init_integration: MockConfigEntry) -> None:
    """Non-zero armedAt should also report arming."""
    fire_loxone_event(hass, {ARMED_AT_UUID: 1234567890})
    await hass.async_block_till_done()

    state = hass.states.get(ALARM_ENTITY_ID)
    assert state.state == AlarmControlPanelState.ARMING


async def test_alarm_state_triggered(hass: HomeAssistant, init_integration: MockConfigEntry) -> None:
    """Level >= 1.0 should be triggered (highest priority)."""
    fire_loxone_event(hass, {LEVEL_UUID: 1.0})
    await hass.async_block_till_done()

    state = hass.states.get(ALARM_ENTITY_ID)
    assert state.state == AlarmControlPanelState.TRIGGERED


async def test_triggered_takes_priority_over_armed(hass: HomeAssistant, init_integration: MockConfigEntry) -> None:
    """Even when armed, level >= 1 should show triggered."""
    fire_loxone_event(hass, {ARMED_UUID: 1.0, LEVEL_UUID: 2.0})
    await hass.async_block_till_done()

    state = hass.states.get(ALARM_ENTITY_ID)
    assert state.state == AlarmControlPanelState.TRIGGERED


# -- Arm / disarm commands ----------------------------------------------------


async def test_alarm_arm_away_sends_command(hass: HomeAssistant, init_integration: MockConfigEntry) -> None:
    """alarm_arm_away should fire delayedon/1."""
    events = []
    hass.bus.async_listen(SENDDOMAIN, lambda e: events.append(e))

    await hass.services.async_call(
        "alarm_control_panel",
        "alarm_arm_away",
        {"entity_id": ALARM_ENTITY_ID},
        blocking=True,
    )
    await hass.async_block_till_done()

    assert len(events) == 1
    assert events[0].data["uuid"] == ALARM_ACTION_UUID
    assert events[0].data["value"] == "delayedon/1"


async def test_alarm_arm_home_sends_command(hass: HomeAssistant, init_integration: MockConfigEntry) -> None:
    """alarm_arm_home should fire delayedon/0."""
    events = []
    hass.bus.async_listen(SENDDOMAIN, lambda e: events.append(e))

    await hass.services.async_call(
        "alarm_control_panel",
        "alarm_arm_home",
        {"entity_id": ALARM_ENTITY_ID},
        blocking=True,
    )
    await hass.async_block_till_done()

    assert len(events) == 1
    assert events[0].data["uuid"] == ALARM_ACTION_UUID
    assert events[0].data["value"] == "delayedon/0"


async def test_alarm_disarm_sends_command(hass: HomeAssistant, init_integration: MockConfigEntry) -> None:
    """alarm_disarm should fire 'off'."""
    events = []
    hass.bus.async_listen(SENDDOMAIN, lambda e: events.append(e))

    await hass.services.async_call(
        "alarm_control_panel",
        "alarm_disarm",
        {"entity_id": ALARM_ENTITY_ID},
        blocking=True,
    )
    await hass.async_block_till_done()

    assert len(events) == 1
    assert events[0].data["uuid"] == ALARM_ACTION_UUID
    assert events[0].data["value"] == "off"


# -- Extra state attributes --------------------------------------------------


async def test_alarm_extra_attributes(hass: HomeAssistant, init_integration: MockConfigEntry) -> None:
    """Alarm should expose level, armed_at, and delay attributes."""
    fire_loxone_event(
        hass,
        {
            LEVEL_UUID: 0.5,
            ARMED_AT_UUID: 1000,
            ARMED_DELAY_UUID: 5.0,
            ARMED_DELAY_TOTAL_UUID: 30.0,
        },
    )
    await hass.async_block_till_done()

    state = hass.states.get(ALARM_ENTITY_ID)
    assert state.attributes["level"] == 0.5
    assert state.attributes["armed_at"] == 1000
    assert state.attributes["armed_delay"] == 5.0
    assert state.attributes["armed_delay_total_delay"] == 30.0
