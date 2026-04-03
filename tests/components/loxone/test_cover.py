"""Tests for Loxone cover entities."""

import pytest
from homeassistant.components.cover import CoverDeviceClass
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from tests.components.loxone.conftest import fire_loxone_event

from custom_components.loxone.const import SENDDOMAIN


@pytest.fixture
def structure_fixture_name() -> str:
    return "structure_covers.json"


BLIND_ENTITY_ID = "cover.bedroom_blind"        # Jalousie, animation=0
CURTAIN_ENTITY_ID = "cover.kitchen_curtain"     # Jalousie, animation=2
GATE_ENTITY_ID = "cover.garage_door"            # Gate, animation=0
WINDOW_ENTITY_ID = "cover.skylight"             # Window

# State UUIDs from fixture
BLIND_POS_UUID = "cov10000-0000-0000-0000000000000001"
BLIND_SHADE_UUID = "cov10000-0000-0000-0000000000000002"
BLIND_UP_UUID = "cov10000-0000-0000-0000000000000003"
BLIND_DOWN_UUID = "cov10000-0000-0000-0000000000000004"
BLIND_AUTO_STATE_UUID = "cov10000-0000-0000-0000000000000006"
BLIND_ACTION_UUID = "cov10000-0000-0000-0000000000000000"

GATE_POS_UUID = "cov30000-0000-0000-0000000000000001"
GATE_ACTIVE_UUID = "cov30000-0000-0000-0000000000000002"

WINDOW_POS_UUID = "cov40000-0000-0000-0000000000000001"
WINDOW_DIR_UUID = "cov40000-0000-0000-0000000000000002"


# -- Entity creation ----------------------------------------------------------


async def test_all_cover_entities_created(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """All four cover entities should exist after setup."""
    for entity_id in (BLIND_ENTITY_ID, CURTAIN_ENTITY_ID, GATE_ENTITY_ID, WINDOW_ENTITY_ID):
        assert hass.states.get(entity_id) is not None, f"{entity_id} missing"


# -- Device class mapping -----------------------------------------------------


async def test_jalousie_animation_0_is_blind(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """Jalousie with animation=0 should be device_class BLIND."""
    state = hass.states.get(BLIND_ENTITY_ID)
    assert state.attributes["device_class"] == CoverDeviceClass.BLIND


async def test_jalousie_animation_2_is_curtain(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """Jalousie with animation=2 should be device_class CURTAIN."""
    state = hass.states.get(CURTAIN_ENTITY_ID)
    assert state.attributes["device_class"] == CoverDeviceClass.CURTAIN


async def test_gate_animation_0_is_garage(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """Gate with animation=0 should be device_class GARAGE."""
    state = hass.states.get(GATE_ENTITY_ID)
    assert state.attributes["device_class"] == CoverDeviceClass.GARAGE


async def test_window_is_window(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """Window should be device_class WINDOW."""
    state = hass.states.get(WINDOW_ENTITY_ID)
    assert state.attributes["device_class"] == CoverDeviceClass.WINDOW


# -- Jalousie position inversion (Loxone 100%=closed, HA 100%=open) -----------


async def test_jalousie_position_fully_open(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """Loxone position 0.0 (fully open) should map to HA 100 (fully open)."""
    fire_loxone_event(hass, {BLIND_POS_UUID: 0.0})
    await hass.async_block_till_done()

    state = hass.states.get(BLIND_ENTITY_ID)
    assert state.attributes["current_position"] == pytest.approx(100)


async def test_jalousie_position_fully_closed(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """Loxone position 1.0 (fully closed) should map to HA 0 (closed)."""
    fire_loxone_event(hass, {BLIND_POS_UUID: 1.0})
    await hass.async_block_till_done()

    state = hass.states.get(BLIND_ENTITY_ID)
    assert state.attributes["current_position"] == pytest.approx(0)
    assert state.state == "closed"


async def test_jalousie_position_halfway(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """Loxone 0.5 (50% closed) should map to HA 50."""
    fire_loxone_event(hass, {BLIND_POS_UUID: 0.5})
    await hass.async_block_till_done()

    state = hass.states.get(BLIND_ENTITY_ID)
    assert state.attributes["current_position"] == pytest.approx(50)


# -- Tilt position ------------------------------------------------------------


async def test_blind_tilt_position(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """Shade position should be inverted like the main position."""
    fire_loxone_event(hass, {BLIND_SHADE_UUID: 0.0})
    await hass.async_block_till_done()

    state = hass.states.get(BLIND_ENTITY_ID)
    assert state.attributes["current_tilt_position"] == pytest.approx(100)


# -- Opening / closing state --------------------------------------------------


async def test_jalousie_opening_state(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """up=True should report is_opening."""
    fire_loxone_event(hass, {BLIND_UP_UUID: True})
    await hass.async_block_till_done()

    state = hass.states.get(BLIND_ENTITY_ID)
    assert state.state == "opening"


async def test_jalousie_closing_state(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """down=True should report is_closing."""
    fire_loxone_event(hass, {BLIND_DOWN_UUID: True})
    await hass.async_block_till_done()

    state = hass.states.get(BLIND_ENTITY_ID)
    assert state.state == "closing"


# -- Gate position and direction ----------------------------------------------


async def test_gate_position_scales(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """Gate position is Loxone 0-1 scaled to HA 0-100 (no inversion)."""
    fire_loxone_event(hass, {GATE_POS_UUID: 0.75})
    await hass.async_block_till_done()

    state = hass.states.get(GATE_ENTITY_ID)
    assert state.attributes["current_position"] == pytest.approx(75)


async def test_gate_direction_opening(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """Gate active=1 means opening."""
    fire_loxone_event(hass, {GATE_ACTIVE_UUID: 1})
    await hass.async_block_till_done()

    state = hass.states.get(GATE_ENTITY_ID)
    assert state.state == "opening"


async def test_gate_direction_closing(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """Gate active=-1 means closing."""
    fire_loxone_event(hass, {GATE_ACTIVE_UUID: -1})
    await hass.async_block_till_done()

    state = hass.states.get(GATE_ENTITY_ID)
    assert state.state == "closing"


# -- Window -------------------------------------------------------------------


async def test_window_position(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """Window position: Loxone 0.5 → HA 50."""
    fire_loxone_event(hass, {WINDOW_POS_UUID: 0.5})
    await hass.async_block_till_done()

    state = hass.states.get(WINDOW_ENTITY_ID)
    assert state.attributes["current_position"] == pytest.approx(50)


async def test_window_direction_opening(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """Window direction=1 means opening."""
    fire_loxone_event(hass, {WINDOW_DIR_UUID: 1})
    await hass.async_block_till_done()

    state = hass.states.get(WINDOW_ENTITY_ID)
    assert state.state == "opening"


# -- Cover actions send correct commands --------------------------------------


async def test_jalousie_open_sends_fullup(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """Opening a jalousie should send 'FullUp'."""
    events = []
    hass.bus.async_listen(SENDDOMAIN, lambda e: events.append(e))

    await hass.services.async_call(
        "cover", "open_cover",
        {"entity_id": BLIND_ENTITY_ID},
        blocking=True,
    )
    await hass.async_block_till_done()

    assert any(e.data["value"] == "FullUp" for e in events)


async def test_jalousie_close_sends_fulldown(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """Closing a jalousie should send 'FullDown'."""
    # Give it a non-zero position so close isn't a no-op
    fire_loxone_event(hass, {BLIND_POS_UUID: 0.5})
    await hass.async_block_till_done()

    events = []
    hass.bus.async_listen(SENDDOMAIN, lambda e: events.append(e))

    await hass.services.async_call(
        "cover", "close_cover",
        {"entity_id": BLIND_ENTITY_ID},
        blocking=True,
    )
    await hass.async_block_till_done()

    assert any(e.data["value"] == "FullDown" for e in events)


async def test_jalousie_set_position_inverts(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """set_cover_position(75) should send manualPosition/25 (inverted)."""
    events = []
    hass.bus.async_listen(SENDDOMAIN, lambda e: events.append(e))

    await hass.services.async_call(
        "cover", "set_cover_position",
        {"entity_id": BLIND_ENTITY_ID, "position": 75},
        blocking=True,
    )
    await hass.async_block_till_done()

    assert len(events) == 1
    assert events[0].data["value"] == "manualPosition/25.0"


async def test_jalousie_stop_sends_stop(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """Stopping a jalousie sends 'stop'."""
    events = []
    hass.bus.async_listen(SENDDOMAIN, lambda e: events.append(e))

    await hass.services.async_call(
        "cover", "stop_cover",
        {"entity_id": BLIND_ENTITY_ID},
        blocking=True,
    )
    await hass.async_block_till_done()

    assert any(e.data["value"] == "stop" for e in events)
