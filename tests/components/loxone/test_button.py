"""Tests for Loxone button (Pushbutton) entities."""

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.loxone.const import SENDDOMAIN
from homeassistant.core import HomeAssistant

from .conftest import fire_loxone_event


@pytest.fixture
def structure_fixture_name() -> str:
    return "structure_buttons.json"


BUTTON_ENTITY_ID = "button.doorbell"
BUTTON_ACTION_UUID = "btn10000-0000-0000-0000000000000000"
BUTTON_ACTIVE_UUID = "btn10000-0000-0000-0000000000000001"


# -- Entity creation ----------------------------------------------------------


async def test_button_entity_created(hass: HomeAssistant, init_integration: MockConfigEntry) -> None:
    """Pushbutton control should create a button entity."""
    state = hass.states.get(BUTTON_ENTITY_ID)
    assert state is not None


async def test_button_extra_attributes(hass: HomeAssistant, init_integration: MockConfigEntry) -> None:
    """Button should expose state_uuid and device_type."""
    state = hass.states.get(BUTTON_ENTITY_ID)
    assert state.attributes["state_uuid"] == BUTTON_ACTIVE_UUID
    assert state.attributes["device_type"] == "Pushbutton"


# -- Press command ------------------------------------------------------------


async def test_press_sends_pulse(hass: HomeAssistant, init_integration: MockConfigEntry) -> None:
    """Pressing the button should fire a 'pulse' command."""
    events = []
    hass.bus.async_listen(SENDDOMAIN, lambda e: events.append(e))

    await hass.services.async_call(
        "button",
        "press",
        {"entity_id": BUTTON_ENTITY_ID},
        blocking=True,
    )
    await hass.async_block_till_done()

    assert len(events) == 1
    assert events[0].data["uuid"] == BUTTON_ACTION_UUID
    assert events[0].data["value"] == "pulse"


# -- Event handling -----------------------------------------------------------


async def test_button_event_updates_state(hass: HomeAssistant, init_integration: MockConfigEntry) -> None:
    """Active=1.0 event should update button's last pressed timestamp."""
    state_before = hass.states.get(BUTTON_ENTITY_ID).state

    fire_loxone_event(hass, {BUTTON_ACTIVE_UUID: 1.0})
    await hass.async_block_till_done()

    state_after = hass.states.get(BUTTON_ENTITY_ID).state
    assert state_after != state_before


async def test_button_ignores_unrelated_event(hass: HomeAssistant, init_integration: MockConfigEntry) -> None:
    """Unrelated UUID should not change button state."""
    state_before = hass.states.get(BUTTON_ENTITY_ID).state

    fire_loxone_event(hass, {"unrelated-uuid": 1.0})
    await hass.async_block_till_done()

    assert hass.states.get(BUTTON_ENTITY_ID).state == state_before
