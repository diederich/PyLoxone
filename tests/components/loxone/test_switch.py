"""Tests for Loxone switch entities."""

import pytest
from homeassistant.const import STATE_ON, STATE_OFF
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from tests.components.loxone.conftest import fire_loxone_event

from custom_components.loxone.const import SENDDOMAIN


@pytest.fixture
def structure_fixture_name() -> str:
    return "structure_switches.json"


SWITCH_ENTITY_ID = "switch.wall_switch"
SWITCH_ACTIVE_UUID = "aaa10000-0000-0000-0000000000000001"
SWITCH_ACTION_UUID = "aaa10000-0000-0000-0000000000000000"

TIMED_ENTITY_ID = "switch.bathroom_fan"
TIMED_DELAY_UUID = "bbb20000-0000-0000-0000000000000010"
TIMED_DELAY_TOTAL_UUID = "bbb20000-0000-0000-0000000000000011"


# -- Entity creation ----------------------------------------------------------


async def test_switch_entities_created(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """Both switch types should be created from the fixture."""
    state = hass.states.get(SWITCH_ENTITY_ID)
    assert state is not None

    state = hass.states.get(TIMED_ENTITY_ID)
    assert state is not None


async def test_switch_attributes(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """Switch should expose room, category, and device_type."""
    state = hass.states.get(SWITCH_ENTITY_ID)
    assert state.attributes["device_type"] == "Switch"
    assert state.attributes["room"] == "Living Room"
    assert state.attributes["category"] == "Lighting"
    assert state.attributes["platform"] == "loxone"


# -- State updates via events ------------------------------------------------


async def test_switch_turns_on_from_event(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """Receiving active=1.0 from the Miniserver should set state to on."""
    fire_loxone_event(hass, {SWITCH_ACTIVE_UUID: 1.0})
    await hass.async_block_till_done()

    state = hass.states.get(SWITCH_ENTITY_ID)
    assert state.state == STATE_ON


async def test_switch_turns_off_from_event(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """Receiving active=0.0 should set state to off."""
    # First turn on
    fire_loxone_event(hass, {SWITCH_ACTIVE_UUID: 1.0})
    await hass.async_block_till_done()

    # Then off
    fire_loxone_event(hass, {SWITCH_ACTIVE_UUID: 0.0})
    await hass.async_block_till_done()

    state = hass.states.get(SWITCH_ENTITY_ID)
    assert state.state == STATE_OFF


async def test_switch_ignores_unrelated_events(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """Events with an unrelated UUID should not change state."""
    initial_state = hass.states.get(SWITCH_ENTITY_ID).state

    fire_loxone_event(hass, {"unrelated-uuid": 1.0})
    await hass.async_block_till_done()

    assert hass.states.get(SWITCH_ENTITY_ID).state == initial_state


# -- Actions (turn_on / turn_off) --------------------------------------------


async def test_switch_turn_on_sends_command(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """turn_on should fire a SENDDOMAIN event with value 'On'."""
    # First give the switch a known off state
    fire_loxone_event(hass, {SWITCH_ACTIVE_UUID: 0.0})
    await hass.async_block_till_done()

    events = []
    hass.bus.async_listen(SENDDOMAIN, lambda e: events.append(e))

    await hass.services.async_call(
        "switch", "turn_on",
        {"entity_id": SWITCH_ENTITY_ID},
        blocking=True,
    )
    await hass.async_block_till_done()

    assert len(events) == 1
    assert events[0].data["uuid"] == SWITCH_ACTION_UUID
    assert events[0].data["value"] == "On"


async def test_switch_turn_off_sends_command(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """turn_off should fire a SENDDOMAIN event with value 'Off'."""
    # Give it an on state first so turn_off actually fires
    fire_loxone_event(hass, {SWITCH_ACTIVE_UUID: 1.0})
    await hass.async_block_till_done()

    events = []
    hass.bus.async_listen(SENDDOMAIN, lambda e: events.append(e))

    await hass.services.async_call(
        "switch", "turn_off",
        {"entity_id": SWITCH_ENTITY_ID},
        blocking=True,
    )
    await hass.async_block_till_done()

    assert len(events) == 1
    assert events[0].data["uuid"] == SWITCH_ACTION_UUID
    assert events[0].data["value"] == "Off"


async def test_switch_turn_on_noop_when_already_on(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """Calling turn_on when already on should not fire a command."""
    fire_loxone_event(hass, {SWITCH_ACTIVE_UUID: 1.0})
    await hass.async_block_till_done()

    events = []
    hass.bus.async_listen(SENDDOMAIN, lambda e: events.append(e))

    await hass.services.async_call(
        "switch", "turn_on",
        {"entity_id": SWITCH_ENTITY_ID},
        blocking=True,
    )
    await hass.async_block_till_done()

    assert len(events) == 0


# -- TimedSwitch specifics ----------------------------------------------------


async def test_timed_switch_delay_attributes(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """TimedSwitch should expose delay remaining and total in attributes."""
    fire_loxone_event(hass, {
        TIMED_DELAY_UUID: 45.0,
        TIMED_DELAY_TOTAL_UUID: 120.0,
    })
    await hass.async_block_till_done()

    state = hass.states.get(TIMED_ENTITY_ID)
    assert state.state == STATE_ON
    assert state.attributes["delay"] == "45"
    assert state.attributes["delay_time_total"] == "120"


async def test_timed_switch_delay_zero_means_off(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """TimedSwitch with deactivationDelay=0 should be off."""
    fire_loxone_event(hass, {TIMED_DELAY_UUID: 0.0})
    await hass.async_block_till_done()

    state = hass.states.get(TIMED_ENTITY_ID)
    assert state.state == STATE_OFF
