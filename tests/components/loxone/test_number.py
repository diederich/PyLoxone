"""Tests for Loxone number (Slider) entities."""

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.loxone.const import SENDDOMAIN
from homeassistant.core import HomeAssistant

from .conftest import fire_loxone_event


@pytest.fixture
def structure_fixture_name() -> str:
    return "structure_numbers.json"


NUMBER_ENTITY_ID = "number.volume_dial"
NUMBER_ACTION_UUID = "sldr1000-0000-0000-0000000000000000"


# -- Entity creation ----------------------------------------------------------


async def test_number_entity_created(hass: HomeAssistant, init_integration: MockConfigEntry) -> None:
    """Slider control should create a number entity."""
    state = hass.states.get(NUMBER_ENTITY_ID)
    assert state is not None


async def test_number_min_max_step(hass: HomeAssistant, init_integration: MockConfigEntry) -> None:
    """Number entity should expose min, max, step from details."""
    state = hass.states.get(NUMBER_ENTITY_ID)
    assert state.attributes["min"] == 0
    assert state.attributes["max"] == 100
    assert state.attributes["step"] == 5


# -- Event handling -----------------------------------------------------------


async def test_number_state_from_event(hass: HomeAssistant, init_integration: MockConfigEntry) -> None:
    """Firing the uuidAction should update native_value."""
    fire_loxone_event(hass, {NUMBER_ACTION_UUID: 42.0})
    await hass.async_block_till_done()

    state = hass.states.get(NUMBER_ENTITY_ID)
    assert float(state.state) == pytest.approx(42.0)


async def test_number_ignores_unrelated_event(hass: HomeAssistant, init_integration: MockConfigEntry) -> None:
    """Unrelated UUID should not change state."""
    fire_loxone_event(hass, {NUMBER_ACTION_UUID: 10.0})
    await hass.async_block_till_done()

    fire_loxone_event(hass, {"unrelated-uuid": 99.0})
    await hass.async_block_till_done()

    state = hass.states.get(NUMBER_ENTITY_ID)
    assert float(state.state) == pytest.approx(10.0)


# -- Commands -----------------------------------------------------------------


async def test_set_native_value_sends_command(hass: HomeAssistant, init_integration: MockConfigEntry) -> None:
    """set_native_value should fire a SENDDOMAIN event with the value."""
    events = []
    hass.bus.async_listen(SENDDOMAIN, lambda e: events.append(e))

    await hass.services.async_call(
        "number",
        "set_value",
        {"entity_id": NUMBER_ENTITY_ID, "value": 75.0},
        blocking=True,
    )
    await hass.async_block_till_done()

    assert len(events) == 1
    assert events[0].data["uuid"] == NUMBER_ACTION_UUID
    assert events[0].data["value"] == "75.0"


async def test_set_native_value_zero(hass: HomeAssistant, init_integration: MockConfigEntry) -> None:
    """Setting zero should format and send correctly."""
    events = []
    hass.bus.async_listen(SENDDOMAIN, lambda e: events.append(e))

    await hass.services.async_call(
        "number",
        "set_value",
        {"entity_id": NUMBER_ENTITY_ID, "value": 0},
        blocking=True,
    )
    await hass.async_block_till_done()

    assert len(events) == 1
    assert float(events[0].data["value"]) == 0
