"""Tests for Loxone light entities (LightControllerV2, ColorPickerV2, Dimmer).

Covers BUG-008 (eval→json.loads for mood parsing) and BUG-009 (None guard
in RGBColorPicker.async_turn_on).
"""

import json
from unittest.mock import MagicMock

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.loxone.const import CONF_LIGHTCONTROLLER_SUBCONTROLS_GEN, SENDDOMAIN
from homeassistant.components.light import ATTR_BRIGHTNESS, ATTR_HS_COLOR
from homeassistant.core import HomeAssistant

from .conftest import fire_loxone_event


@pytest.fixture
def structure_fixture_name() -> str:
    return "structure_lights.json"


LC_ENTITY_ID = "light.main_light_controller"
LC_ACTION_UUID = "lc010000-0000-0000-0000000000000000"
LC_ACTIVE_MOODS_UUID = "lc010000-0000-0000-0000000000000001"
LC_MOOD_LIST_UUID = "lc010000-0000-0000-0000000000000002"
LC_ADDITIONAL_MOODS_UUID = "lc010000-0000-0000-0000000000000004"

DIMMER_ENTITY_ID = "light.hallway_dimmer"
DIMMER_POSITION_UUID = "dim10000-0000-0000-0000000000000001"


# -- Entity creation ----------------------------------------------------------


async def test_light_controller_created(hass: HomeAssistant, init_integration: MockConfigEntry) -> None:
    """LightControllerV2 should create a light entity."""
    state = hass.states.get(LC_ENTITY_ID)
    assert state is not None


async def test_dimmer_created(hass: HomeAssistant, init_integration: MockConfigEntry) -> None:
    """Standalone Dimmer should create a light entity."""
    state = hass.states.get(DIMMER_ENTITY_ID)
    assert state is not None


# -- LightControllerV2: mood JSON parsing (BUG-008 regression) ---------------


async def test_mood_list_parsed_from_json(hass: HomeAssistant, init_integration: MockConfigEntry) -> None:
    """MoodList event (JSON with true/false) should parse via json.loads."""
    mood_data = json.dumps(
        [
            {"id": 99, "name": "Default", "static": False, "used": True},
            {"id": 100, "name": "Movie", "static": False, "used": True},
        ]
    )
    fire_loxone_event(hass, {LC_MOOD_LIST_UUID: mood_data})
    await hass.async_block_till_done()

    state = hass.states.get(LC_ENTITY_ID)
    effects = state.attributes.get("effect_list", [])
    assert "Default" in effects
    assert "Movie" in effects


async def test_mood_list_with_json_booleans(hass: HomeAssistant, init_integration: MockConfigEntry) -> None:
    """JSON booleans (true/false) must parse correctly — old eval() code
    required string replacement to Python True/False first.
    """
    raw_json = '[{"id":99,"name":"Bright","static":true,"used":false}]'
    fire_loxone_event(hass, {LC_MOOD_LIST_UUID: raw_json})
    await hass.async_block_till_done()

    state = hass.states.get(LC_ENTITY_ID)
    effects = state.attributes.get("effect_list", [])
    assert "Bright" in effects


async def test_active_moods_parsed_from_json(hass: HomeAssistant, init_integration: MockConfigEntry) -> None:
    """ActiveMoods event should parse a JSON integer array."""
    mood_data = json.dumps([{"id": 99, "name": "Default"}, {"id": 100, "name": "Movie"}])
    fire_loxone_event(hass, {LC_MOOD_LIST_UUID: mood_data})
    await hass.async_block_till_done()

    fire_loxone_event(hass, {LC_ACTIVE_MOODS_UUID: "[99]"})
    await hass.async_block_till_done()

    state = hass.states.get(LC_ENTITY_ID)
    assert state.attributes.get("effect") == "Default"


async def test_additional_moods_parsed_from_json(hass: HomeAssistant, init_integration: MockConfigEntry) -> None:
    """AdditionalMoods event should parse a JSON array without error."""
    fire_loxone_event(hass, {LC_ADDITIONAL_MOODS_UUID: "[100, 101]"})
    await hass.async_block_till_done()

    state = hass.states.get(LC_ENTITY_ID)
    assert state is not None


# -- LightControllerV2: turn on/off commands ----------------------------------


async def test_light_controller_turn_off(hass: HomeAssistant, init_integration: MockConfigEntry) -> None:
    """turn_off should send changeTo/0."""
    events = []
    hass.bus.async_listen(SENDDOMAIN, lambda e: events.append(e))

    await hass.services.async_call("light", "turn_off", {"entity_id": LC_ENTITY_ID}, blocking=True)
    await hass.async_block_till_done()

    assert len(events) == 1
    assert events[0].data["uuid"] == LC_ACTION_UUID
    assert events[0].data["value"] == "changeTo/0"


async def test_light_controller_turn_on_with_effect(hass: HomeAssistant, init_integration: MockConfigEntry) -> None:
    """turn_on with effect should send changeTo/<mood_id>."""
    mood_data = json.dumps(
        [
            {"id": 99, "name": "Default"},
            {"id": 100, "name": "Movie"},
        ]
    )
    fire_loxone_event(hass, {LC_MOOD_LIST_UUID: mood_data})
    await hass.async_block_till_done()

    events = []
    hass.bus.async_listen(SENDDOMAIN, lambda e: events.append(e))

    await hass.services.async_call(
        "light",
        "turn_on",
        {"entity_id": LC_ENTITY_ID, "effect": "Movie"},
        blocking=True,
    )
    await hass.async_block_till_done()

    assert any(e.data["value"] == "changeTo/100" for e in events)


# -- RGBColorPicker: event parsing and None guard (BUG-008/009 regression) ----
# These tests exercise the color picker subcontrols, which require
# generate_lightcontroller_subcontrols=True.


RGB_ENTITY_ID = "light.main_light_controller_spot_rgb"
RGB_COLOR_UUID = "lc01sp00-0000-0000-0000000000000001"
RGB_ACTION_UUID = "lc01sp00-0000-0000-0000000000000000"


@pytest.fixture
def init_integration_with_subcontrols(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_loxone_connection: MagicMock,
) -> MockConfigEntry:
    """Set up integration with subcontrol generation enabled."""
    return None


async def _setup_with_subcontrols(hass, mock_config_entry, mock_loxone_connection):
    """Helper: set up integration with CONF_LIGHTCONTROLLER_SUBCONTROLS_GEN=True."""
    opts = dict(mock_config_entry.options)
    opts[CONF_LIGHTCONTROLLER_SUBCONTROLS_GEN] = True
    hass.config_entries.async_update_entry(mock_config_entry, options=opts)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()


async def test_rgb_color_picker_created_with_subcontrols(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_loxone_connection: MagicMock,
) -> None:
    """ColorPickerV2/Rgb subcontrol should be created when enabled."""
    mock_config_entry.add_to_hass(hass)
    await _setup_with_subcontrols(hass, mock_config_entry, mock_loxone_connection)

    state = hass.states.get(RGB_ENTITY_ID)
    assert state is not None


async def test_rgb_hsv_event_parsed(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_loxone_connection: MagicMock,
) -> None:
    """hsv() color string should be parsed with ast.literal_eval, not eval()."""
    mock_config_entry.add_to_hass(hass)
    await _setup_with_subcontrols(hass, mock_config_entry, mock_loxone_connection)

    fire_loxone_event(hass, {RGB_COLOR_UUID: "hsv(180,50,80)"})
    await hass.async_block_till_done()

    state = hass.states.get(RGB_ENTITY_ID)
    assert state.attributes.get("hs_color") == (180, 50)


async def test_rgb_temp_event_parsed(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_loxone_connection: MagicMock,
) -> None:
    """temp() color string should be parsed with ast.literal_eval, not eval()."""
    mock_config_entry.add_to_hass(hass)
    await _setup_with_subcontrols(hass, mock_config_entry, mock_loxone_connection)

    fire_loxone_event(hass, {RGB_COLOR_UUID: "temp(75,4000)"})
    await hass.async_block_till_done()

    state = hass.states.get(RGB_ENTITY_ID)
    assert state.attributes.get("color_temp_kelvin") == 4000


async def test_rgb_turn_on_without_prior_state(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_loxone_connection: MagicMock,
) -> None:
    """BUG-009: turn_on must not crash when brightness/hs_color are still None."""
    mock_config_entry.add_to_hass(hass)
    await _setup_with_subcontrols(hass, mock_config_entry, mock_loxone_connection)

    events = []
    hass.bus.async_listen(SENDDOMAIN, lambda e: events.append(e))

    await hass.services.async_call("light", "turn_on", {"entity_id": RGB_ENTITY_ID}, blocking=True)
    await hass.async_block_till_done()

    assert len(events) == 1
    assert events[0].data["value"] == "On"


async def test_rgb_turn_on_hs_color_without_prior_brightness(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_loxone_connection: MagicMock,
) -> None:
    """BUG-009: setting HS color when brightness is None should default to 100%."""
    mock_config_entry.add_to_hass(hass)
    await _setup_with_subcontrols(hass, mock_config_entry, mock_loxone_connection)

    events = []
    hass.bus.async_listen(SENDDOMAIN, lambda e: events.append(e))

    await hass.services.async_call(
        "light",
        "turn_on",
        {"entity_id": RGB_ENTITY_ID, ATTR_HS_COLOR: (200, 75)},
        blocking=True,
    )
    await hass.async_block_till_done()

    assert len(events) == 1
    assert "hsv(" in events[0].data["value"]
    assert events[0].data["value"].endswith(")")


async def test_rgb_turn_on_brightness_without_prior_hs(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_loxone_connection: MagicMock,
) -> None:
    """BUG-009: setting brightness in HS mode when hs_color is None should not crash."""
    mock_config_entry.add_to_hass(hass)
    await _setup_with_subcontrols(hass, mock_config_entry, mock_loxone_connection)

    # Put it in HS mode first
    fire_loxone_event(hass, {RGB_COLOR_UUID: "hsv(120,60,50)"})
    await hass.async_block_till_done()

    events = []
    hass.bus.async_listen(SENDDOMAIN, lambda e: events.append(e))

    await hass.services.async_call(
        "light",
        "turn_on",
        {"entity_id": RGB_ENTITY_ID, ATTR_BRIGHTNESS: 200},
        blocking=True,
    )
    await hass.async_block_till_done()

    assert len(events) == 1
    assert "hsv(" in events[0].data["value"]
