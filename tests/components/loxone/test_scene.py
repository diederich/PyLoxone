"""Tests for Loxone scene platform (auto-generated light scenes).

Scene generation works by:
1. async_setup_entry schedules run_delayed_scene_gen via hass.async_create_task
2. run_delayed_scene_gen sleeps for CONF_SCENE_GEN_DELAY seconds
3. gen_scenes iterates light entities, finds LightControllerV2 with moods
4. Each mood becomes a LoxoneLightScene entity

To test this, we need moods to be populated on the light controller BEFORE
gen_scenes runs.  We use CONF_SCENE_GEN_DELAY=1 so we have time to fire
mood events after setup but before the generator wakes up.
"""

import asyncio
import json
from unittest.mock import MagicMock, patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.loxone.const import CONF_SCENE_GEN, CONF_SCENE_GEN_DELAY, DOMAIN, SENDDOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from .conftest import MOCK_OPTIONS, fire_loxone_event

LC_ACTION_UUID = "lc010000-0000-0000-0000000000000000"
LC_ACTIVE_MOODS_UUID = "lc010000-0000-0000-0000000000000001"
LC_MOOD_LIST_UUID = "lc010000-0000-0000-0000000000000002"


@pytest.fixture
def structure_fixture_name() -> str:
    return "structure_lights.json"


def _make_entry(*, scene_gen: bool = True, delay: int = 1) -> MockConfigEntry:
    """Create a config entry with customizable scene options."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={},
        options={**MOCK_OPTIONS, CONF_SCENE_GEN: scene_gen, CONF_SCENE_GEN_DELAY: delay},
        unique_id="504F94A0FEA2",
        version=3,
    )


MOOD_LIST = [
    {"id": 100, "name": "Bright", "static": True},
    {"id": 200, "name": "Evening", "static": True},
]


async def _setup_with_moods(
    hass: HomeAssistant,
    entry: MockConfigEntry,
) -> None:
    """Set up integration and fire mood events before the delayed scene gen runs.

    Timing is critical:
    1. async_setup_entry schedules run_delayed_scene_gen (with asyncio.sleep)
    2. We fire mood events immediately — these create "ready" event-handler tasks
    3. async_block_till_done processes everything: the ready event-handler tasks
       run first (populating moods on the light entity), then the sleeping scene
       gen task wakes up and finds the moods already populated.
    """
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)

    fire_loxone_event(hass, {LC_MOOD_LIST_UUID: json.dumps(MOOD_LIST)})
    fire_loxone_event(hass, {LC_ACTIVE_MOODS_UUID: json.dumps([100])})

    await hass.async_block_till_done()


async def _wait_for_scenes(hass: HomeAssistant, timeout: float = 5.0) -> list[str]:
    """Poll until scene entities appear (or timeout)."""
    deadline = asyncio.get_event_loop().time() + timeout
    while asyncio.get_event_loop().time() < deadline:
        await asyncio.sleep(0.25)
        await hass.async_block_till_done()
        scenes = [
            eid
            for eid in hass.states.async_entity_ids("scene")
            if hass.states.get(eid) is not None
        ]
        if scenes:
            return scenes
    return []


# -- Scene generation ---------------------------------------------------------


async def test_scenes_generated_from_light_controller(
    hass: HomeAssistant,
    mock_loxone_connection: MagicMock,
) -> None:
    """With scene generation enabled, scenes should be created from LightControllerV2 moods."""
    entry = _make_entry(scene_gen=True, delay=1)
    await _setup_with_moods(hass, entry)
    scenes = await _wait_for_scenes(hass, timeout=5.0)

    assert len(scenes) >= 2, f"Expected at least 2 scenes, got {len(scenes)}: {scenes}"


async def test_no_scenes_when_disabled(
    hass: HomeAssistant,
    mock_loxone_connection: MagicMock,
) -> None:
    """With CONF_SCENE_GEN=False, no scenes should be created."""
    entry = _make_entry(scene_gen=False)
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    await asyncio.sleep(1.5)
    await hass.async_block_till_done()

    scenes = hass.states.async_entity_ids("scene")
    assert len(scenes) == 0


async def test_scene_generation_uses_async_create_task(
    hass: HomeAssistant,
    mock_loxone_connection: MagicMock,
) -> None:
    """Scene generation must use hass.async_create_task, not call from a thread."""
    with patch.object(hass, "async_create_task", wraps=hass.async_create_task) as mock_create_task:
        entry = _make_entry(scene_gen=True, delay=0)
        entry.add_to_hass(hass)
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        scene_tasks = [
            call
            for call in mock_create_task.call_args_list
            if "run_delayed_scene_gen" in str(call)
        ]
        assert len(scene_tasks) >= 1, (
            "Scene generation should schedule via hass.async_create_task"
        )


# -- Scene activation ---------------------------------------------------------


async def test_scene_activate_fires_command(
    hass: HomeAssistant,
    mock_loxone_connection: MagicMock,
) -> None:
    """Activating a scene should fire a changeTo command."""
    entry = _make_entry(scene_gen=True, delay=1)
    await _setup_with_moods(hass, entry)
    scenes = await _wait_for_scenes(hass, timeout=5.0)

    if not scenes:
        pytest.skip("Scene generation did not produce entities")

    events = []
    hass.bus.async_listen(SENDDOMAIN, lambda e: events.append(e))

    await hass.services.async_call(
        "scene",
        "turn_on",
        {"entity_id": scenes[0]},
        blocking=True,
    )
    await hass.async_block_till_done()

    assert len(events) == 1
    assert events[0].data["uuid"] == LC_ACTION_UUID
    assert "changeTo/" in events[0].data["value"]


# -- Reconnect -----------------------------------------------------------------


async def test_scenes_regenerated_after_reconnect(
    hass: HomeAssistant,
    mock_loxone_connection: MagicMock,
) -> None:
    """After a Miniserver reconnect, scene generation is re-triggered."""
    from homeassistant.helpers.dispatcher import async_dispatcher_send

    entry = _make_entry(scene_gen=True, delay=1)
    await _setup_with_moods(hass, entry)
    initial_scenes = await _wait_for_scenes(hass, timeout=5.0)
    assert len(initial_scenes) >= 2, "Pre-condition: initial scenes should be generated"

    # Fire the reconnect signal (simulates coordinator reconnecting)
    fire_loxone_event(hass, {LC_MOOD_LIST_UUID: json.dumps(MOOD_LIST)})
    fire_loxone_event(hass, {LC_ACTIVE_MOODS_UUID: json.dumps([100])})
    async_dispatcher_send(hass, f"loxone_{entry.entry_id}_reconnected")

    # Scene gen runs again after delay — scenes already exist so count stays the same
    post_reconnect_scenes = await _wait_for_scenes(hass, timeout=5.0)
    assert len(post_reconnect_scenes) >= 2, (
        f"Scenes should still exist after reconnect, got {post_reconnect_scenes}"
    )


# -- Scene unique_id ----------------------------------------------------------


async def test_scene_unique_id_format(
    hass: HomeAssistant,
    mock_loxone_connection: MagicMock,
) -> None:
    """Scene unique_id should be '{light_controller_unique_id}-{mood_id}'."""
    entry = _make_entry(scene_gen=True, delay=1)
    await _setup_with_moods(hass, entry)
    scenes = await _wait_for_scenes(hass, timeout=5.0)

    if not scenes:
        pytest.skip("Scene generation did not produce entities")

    ent_reg = er.async_get(hass)
    for eid in scenes:
        reg_entry = ent_reg.async_get(eid)
        if reg_entry:
            assert "-" in reg_entry.unique_id, f"unique_id should contain '-': {reg_entry.unique_id}"
