"""Tests for Loxone media player (AudioZoneV2) entities."""

import pytest
from homeassistant.components.media_player import (
    MediaPlayerEntityFeature,
    MediaPlayerState,
)
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.loxone.const import EVENT, SENDDOMAIN


@pytest.fixture
def structure_fixture_name() -> str:
    return "structure_media_player.json"


MP_ENTITY_ID = "media_player.living_room_speaker"
MP_ACTION_UUID = "audz1000-0000-0000-0000000000000000"

VOLUME_UUID = "audz1000-0000-0000-0000000000000010"
PLAY_STATE_UUID = "audz1000-0000-0000-0000000000000011"


# -- Entity creation ----------------------------------------------------------


async def test_media_player_entity_created(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """AudioZoneV2 should create a media_player entity."""
    state = hass.states.get(MP_ENTITY_ID)
    assert state is not None


async def test_media_player_supported_features(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """Should support play, pause, next, prev, volume set, volume step."""
    state = hass.states.get(MP_ENTITY_ID)
    features = state.attributes.get("supported_features")
    assert features & MediaPlayerEntityFeature.PLAY
    assert features & MediaPlayerEntityFeature.PAUSE
    assert features & MediaPlayerEntityFeature.NEXT_TRACK
    assert features & MediaPlayerEntityFeature.PREVIOUS_TRACK
    assert features & MediaPlayerEntityFeature.VOLUME_SET
    assert features & MediaPlayerEntityFeature.VOLUME_STEP


async def test_media_player_device_class(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """AudioZoneV2 should have SPEAKER device class."""
    state = hass.states.get(MP_ENTITY_ID)
    assert state.attributes.get("device_class") == "speaker"


# -- Event handling -----------------------------------------------------------


async def test_volume_from_event(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """Volume event should update volume_level when player is not OFF."""
    hass.bus.async_fire(EVENT, {PLAY_STATE_UUID: 2, VOLUME_UUID: 50})
    await hass.async_block_till_done()

    state = hass.states.get(MP_ENTITY_ID)
    assert state.state == MediaPlayerState.PLAYING
    assert state.attributes.get("volume_level") == pytest.approx(0.5)


async def test_play_state_playing(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """playState=2 should report playing."""
    hass.bus.async_fire(EVENT, {PLAY_STATE_UUID: 2})
    await hass.async_block_till_done()

    state = hass.states.get(MP_ENTITY_ID)
    assert state.state == MediaPlayerState.PLAYING


async def test_play_state_paused(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """playState=1 should report paused."""
    hass.bus.async_fire(EVENT, {PLAY_STATE_UUID: 1})
    await hass.async_block_till_done()

    state = hass.states.get(MP_ENTITY_ID)
    assert state.state == MediaPlayerState.PAUSED


async def test_play_state_idle(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """playState=0 should report idle."""
    hass.bus.async_fire(EVENT, {PLAY_STATE_UUID: 0})
    await hass.async_block_till_done()

    state = hass.states.get(MP_ENTITY_ID)
    assert state.state == MediaPlayerState.IDLE


# -- Commands -----------------------------------------------------------------


async def test_media_play_sends_command(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """media_play should fire 'play' command."""
    events = []
    hass.bus.async_listen(SENDDOMAIN, lambda e: events.append(e))

    await hass.services.async_call(
        "media_player", "media_play",
        {"entity_id": MP_ENTITY_ID},
        blocking=True,
    )
    await hass.async_block_till_done()

    assert len(events) == 1
    assert events[0].data["uuid"] == MP_ACTION_UUID
    assert events[0].data["value"] == "play"


async def test_media_pause_sends_command(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """media_pause should fire 'pause' command."""
    events = []
    hass.bus.async_listen(SENDDOMAIN, lambda e: events.append(e))

    await hass.services.async_call(
        "media_player", "media_pause",
        {"entity_id": MP_ENTITY_ID},
        blocking=True,
    )
    await hass.async_block_till_done()

    assert len(events) == 1
    assert events[0].data["value"] == "pause"


async def test_media_next_sends_command(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """media_next_track should fire 'next' command."""
    events = []
    hass.bus.async_listen(SENDDOMAIN, lambda e: events.append(e))

    await hass.services.async_call(
        "media_player", "media_next_track",
        {"entity_id": MP_ENTITY_ID},
        blocking=True,
    )
    await hass.async_block_till_done()

    assert len(events) == 1
    assert events[0].data["value"] == "next"


async def test_media_previous_sends_command(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """media_previous_track should fire 'prev' command."""
    events = []
    hass.bus.async_listen(SENDDOMAIN, lambda e: events.append(e))

    await hass.services.async_call(
        "media_player", "media_previous_track",
        {"entity_id": MP_ENTITY_ID},
        blocking=True,
    )
    await hass.async_block_till_done()

    assert len(events) == 1
    assert events[0].data["value"] == "prev"


async def test_set_volume_sends_command(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """set_volume_level(0.75) should fire 'volume/75'."""
    events = []
    hass.bus.async_listen(SENDDOMAIN, lambda e: events.append(e))

    await hass.services.async_call(
        "media_player", "volume_set",
        {"entity_id": MP_ENTITY_ID, "volume_level": 0.75},
        blocking=True,
    )
    await hass.async_block_till_done()

    assert len(events) == 1
    assert events[0].data["value"] == "volume/75"


async def test_volume_up_sends_command(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """volume_up should fire 'volUp'."""
    events = []
    hass.bus.async_listen(SENDDOMAIN, lambda e: events.append(e))

    await hass.services.async_call(
        "media_player", "volume_up",
        {"entity_id": MP_ENTITY_ID},
        blocking=True,
    )
    await hass.async_block_till_done()

    assert len(events) == 1
    assert events[0].data["value"] == "volUp"


async def test_volume_down_sends_command(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """volume_down should fire 'volDown'."""
    events = []
    hass.bus.async_listen(SENDDOMAIN, lambda e: events.append(e))

    await hass.services.async_call(
        "media_player", "volume_down",
        {"entity_id": MP_ENTITY_ID},
        blocking=True,
    )
    await hass.async_block_till_done()

    assert len(events) == 1
    assert events[0].data["value"] == "volDown"
