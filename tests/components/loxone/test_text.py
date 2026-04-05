"""Tests for Loxone text entities (TextInput controls)."""

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from homeassistant.core import HomeAssistant

from .conftest import fire_loxone_event

TEXT_ENTITY_ID = "text.status_display"
TEXT_STATE_UUID = "txt10000-0000-0000-0000000000000001"
TEXT_ACTION_UUID = "txt10000-0000-0000-0000000000000000"


@pytest.fixture
def structure_fixture_name() -> str:
    return "structure_sensors.json"


async def test_text_entity_created(hass: HomeAssistant, init_integration: MockConfigEntry) -> None:
    """TextInput should create a text entity."""
    state = hass.states.get(TEXT_ENTITY_ID)
    assert state is not None


async def test_text_state_from_event(hass: HomeAssistant, init_integration: MockConfigEntry) -> None:
    """Firing the text state UUID should update the entity."""
    fire_loxone_event(hass, {TEXT_STATE_UUID: "All systems normal"})
    await hass.async_block_till_done()

    state = hass.states.get(TEXT_ENTITY_ID)
    assert state.state == "All systems normal"


async def test_text_set_value(hass: HomeAssistant, init_integration: MockConfigEntry) -> None:
    """Calling set_value should fire a SENDDOMAIN event."""
    events = []
    hass.bus.async_listen("loxone_send", lambda e: events.append(e))

    await hass.services.async_call(
        "text",
        "set_value",
        {"entity_id": TEXT_ENTITY_ID, "value": "Hello Loxone"},
        blocking=True,
    )
    await hass.async_block_till_done()

    assert len(events) == 1
    assert events[0].data["uuid"] == TEXT_ACTION_UUID
    assert events[0].data["value"] == "Hello Loxone"
