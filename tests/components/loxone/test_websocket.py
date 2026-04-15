"""Tests for Loxone WebSocket API commands (custom panel backend)."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.loxone.const import DOMAIN
from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant


@pytest.fixture
def structure_fixture_name() -> str:
    return "structure_switches.json"


async def test_ws_get_devices_returns_controls(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    hass_ws_client,
) -> None:
    """loxone/get_devices should return controls from the structure file."""
    client = await hass_ws_client(hass)
    await client.send_json({"id": 1, "type": "loxone/get_devices"})
    resp = await client.receive_json()

    assert resp["success"] is True
    devices = resp["result"]["devices"]
    assert len(devices) >= 2

    names = {d["name"] for d in devices}
    assert "Wall Switch" in names
    assert "Bathroom Fan" in names


async def test_ws_get_devices_includes_room(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    hass_ws_client,
) -> None:
    """Each device should include the resolved room name."""
    client = await hass_ws_client(hass)
    await client.send_json({"id": 1, "type": "loxone/get_devices"})
    resp = await client.receive_json()

    devices = resp["result"]["devices"]
    wall_switch = next(d for d in devices if d["name"] == "Wall Switch")
    assert wall_switch["room"] == "Living Room"


async def test_ws_get_devices_includes_ha_entities(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    hass_ws_client,
) -> None:
    """Devices with HA entities should include entity_id in ha_entities."""
    client = await hass_ws_client(hass)
    await client.send_json({"id": 1, "type": "loxone/get_devices"})
    resp = await client.receive_json()

    devices = resp["result"]["devices"]
    for dev in devices:
        assert "ha_entities" in dev
        assert isinstance(dev["ha_entities"], list)


async def test_ws_get_devices_includes_subcontrols(
    hass: HomeAssistant,
    hass_ws_client,
    mock_loxone_connection: MagicMock,
) -> None:
    """Sub-controls should appear as separate entries with a parent field."""
    from .conftest import MOCK_OPTIONS

    entry = MockConfigEntry(
        domain=DOMAIN,
        data={},
        options={
            **MOCK_OPTIONS,
            "generate_lightcontroller_subcontrols": True,
        },
        unique_id="504F94A0FEA2_lights",
        version=3,
    )
    entry.add_to_hass(hass)

    import json
    from pathlib import Path

    lights_structure = json.loads((Path(__file__).parent / "fixtures" / "structure_lights.json").read_text())
    mock_loxone_connection.structure_file = lights_structure

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    client = await hass_ws_client(hass)
    await client.send_json({"id": 1, "type": "loxone/get_devices"})
    resp = await client.receive_json()

    devices = resp["result"]["devices"]
    sub_controls = [d for d in devices if "parent" in d]
    assert len(sub_controls) > 0, "Sub-controls should be included"
    for sc in sub_controls:
        assert sc["parent"], "Sub-control should reference parent UUID"


async def test_ws_get_devices_error_when_no_coordinator(
    hass: HomeAssistant,
    hass_ws_client,
) -> None:
    """loxone/get_devices should return an error when no coordinator exists."""
    from custom_components.loxone.websocket import ws_get_devices

    websocket_api.async_register_command(hass, ws_get_devices)
    await hass.async_block_till_done()

    client = await hass_ws_client(hass)
    await client.send_json({"id": 1, "type": "loxone/get_devices"})
    resp = await client.receive_json()

    assert resp["success"] is False
    assert resp["error"]["code"] == "not_connected"


# -- loxone/set_entity_enabled ------------------------------------------------


async def test_set_entity_enabled_disables_entity(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    hass_ws_client,
) -> None:
    """Disabling an entity should set disabled_by to 'integration'."""
    from homeassistant.helpers import entity_registry as er

    registry = er.async_get(hass)
    entry = registry.async_get("switch.wall_switch")
    assert entry is not None
    assert entry.disabled_by is None

    client = await hass_ws_client(hass)
    await client.send_json(
        {"id": 1, "type": "loxone/set_entity_enabled", "entity_id": "switch.wall_switch", "enabled": False}
    )
    resp = await client.receive_json()

    assert resp["success"] is True
    assert resp["result"]["disabled_by"] == er.RegistryEntryDisabler.INTEGRATION

    updated = registry.async_get("switch.wall_switch")
    assert updated.disabled_by == er.RegistryEntryDisabler.INTEGRATION


async def test_set_entity_enabled_reenables_entity(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    hass_ws_client,
) -> None:
    """Re-enabling a disabled entity should clear disabled_by."""
    from homeassistant.helpers import entity_registry as er

    registry = er.async_get(hass)
    registry.async_update_entity("switch.wall_switch", disabled_by=er.RegistryEntryDisabler.INTEGRATION)

    client = await hass_ws_client(hass)
    await client.send_json(
        {"id": 1, "type": "loxone/set_entity_enabled", "entity_id": "switch.wall_switch", "enabled": True}
    )
    resp = await client.receive_json()

    assert resp["success"] is True
    assert resp["result"]["disabled_by"] is None


async def test_set_entity_enabled_rejects_non_loxone(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    hass_ws_client,
) -> None:
    """Non-Loxone entities should be rejected."""
    from homeassistant.helpers import entity_registry as er

    registry = er.async_get(hass)
    registry.async_get_or_create("sensor", "other", "abc123")

    client = await hass_ws_client(hass)
    await client.send_json(
        {"id": 1, "type": "loxone/set_entity_enabled", "entity_id": "sensor.other_abc123", "enabled": False}
    )
    resp = await client.receive_json()

    assert resp["success"] is False
    assert resp["error"]["code"] == "not_loxone"


async def test_set_entity_enabled_rejects_unknown_entity(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    hass_ws_client,
) -> None:
    """Unknown entity IDs should return not_found."""
    client = await hass_ws_client(hass)
    await client.send_json(
        {"id": 1, "type": "loxone/set_entity_enabled", "entity_id": "switch.nonexistent", "enabled": False}
    )
    resp = await client.receive_json()

    assert resp["success"] is False
    assert resp["error"]["code"] == "not_found"


# -- loxone/get_areas ---------------------------------------------------------


async def test_ws_get_areas_returns_rooms(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    hass_ws_client,
) -> None:
    """loxone/get_areas should return Loxone rooms."""
    client = await hass_ws_client(hass)
    await client.send_json({"id": 1, "type": "loxone/get_areas"})
    resp = await client.receive_json()

    assert resp["success"] is True
    rooms = resp["result"]["rooms"]
    assert len(rooms) >= 1

    living = next(r for r in rooms if r["name"] == "Living Room")
    assert living["uuid"] == "room-1"


async def test_ws_get_areas_includes_ha_area_mapping(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    hass_ws_client,
) -> None:
    """Rooms with matching HA areas should include ha_area_id."""
    client = await hass_ws_client(hass)
    await client.send_json({"id": 1, "type": "loxone/get_areas"})
    resp = await client.receive_json()

    rooms = resp["result"]["rooms"]
    living = next(r for r in rooms if r["name"] == "Living Room")
    assert living["ha_area_id"] is not None
    assert living["ha_area_name"] == "Living Room"


async def test_ws_get_areas_returns_ha_areas_list(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    hass_ws_client,
) -> None:
    """Should include a list of all HA areas."""
    client = await hass_ws_client(hass)
    await client.send_json({"id": 1, "type": "loxone/get_areas"})
    resp = await client.receive_json()

    ha_areas = resp["result"]["ha_areas"]
    assert isinstance(ha_areas, list)
    assert len(ha_areas) >= 1
    names = {a["name"] for a in ha_areas}
    assert "Living Room" in names


# -- loxone/get_bridges, add_bridge, remove_bridge ----------------------------


async def test_ws_get_bridges_empty(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    hass_ws_client,
) -> None:
    """With no bridges configured, get_bridges returns an empty list."""
    client = await hass_ws_client(hass)
    await client.send_json({"id": 1, "type": "loxone/get_bridges"})
    resp = await client.receive_json()

    assert resp["success"] is True
    assert resp["result"]["bridges"] == []


async def test_ws_add_and_get_bridge(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    hass_ws_client,
) -> None:
    """Adding a bridge should make it appear in get_bridges."""
    from homeassistant.helpers import entity_registry as er

    registry = er.async_get(hass)
    registry.async_get_or_create("sensor", "other", "temp1")

    client = await hass_ws_client(hass)

    msg_id = 1
    await client.send_json(
        {
            "id": msg_id,
            "type": "loxone/add_bridge",
            "entity_id": "sensor.other_temp1",
            "loxone_uuid": "aaa10000-0000-0000-0000000000000000",
        }
    )
    resp = await client.receive_json()
    assert resp["success"] is True
    assert resp["result"]["loxone_uuid"] == "aaa10000-0000-0000-0000000000000000"

    msg_id += 1
    await client.send_json({"id": msg_id, "type": "loxone/get_bridges"})
    resp = await client.receive_json()
    assert resp["success"] is True
    bridges = resp["result"]["bridges"]
    assert len(bridges) == 1
    assert bridges[0]["entity_id"] == "sensor.other_temp1"


async def test_ws_remove_bridge(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    hass_ws_client,
) -> None:
    """Removing a bridge should make get_bridges return empty again."""
    from homeassistant.helpers import entity_registry as er

    registry = er.async_get(hass)
    registry.async_get_or_create("sensor", "other", "temp2")

    client = await hass_ws_client(hass)

    msg_id = 1
    await client.send_json(
        {
            "id": msg_id,
            "type": "loxone/add_bridge",
            "entity_id": "sensor.other_temp2",
            "loxone_uuid": "aaa10000-0000-0000-0000000000000000",
        }
    )
    resp = await client.receive_json()
    assert resp["success"] is True

    msg_id += 1
    await client.send_json({"id": msg_id, "type": "loxone/remove_bridge", "entity_id": "sensor.other_temp2"})
    resp = await client.receive_json()
    assert resp["success"] is True
    assert resp["result"]["removed"] == "sensor.other_temp2"

    msg_id += 1
    await client.send_json({"id": msg_id, "type": "loxone/get_bridges"})
    resp = await client.receive_json()
    assert resp["result"]["bridges"] == []


async def test_ws_add_bridge_rejects_duplicate(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    hass_ws_client,
) -> None:
    """Adding a bridge for an already-bridged entity should fail."""
    from homeassistant.helpers import entity_registry as er

    registry = er.async_get(hass)
    registry.async_get_or_create("sensor", "other", "temp3")

    client = await hass_ws_client(hass)

    msg_id = 1
    await client.send_json(
        {
            "id": msg_id,
            "type": "loxone/add_bridge",
            "entity_id": "sensor.other_temp3",
            "loxone_uuid": "aaa10000-0000-0000-0000000000000000",
        }
    )
    resp = await client.receive_json()
    assert resp["success"] is True

    msg_id += 1
    await client.send_json(
        {
            "id": msg_id,
            "type": "loxone/add_bridge",
            "entity_id": "sensor.other_temp3",
            "loxone_uuid": "bbb20000-0000-0000-0000000000000000",
        }
    )
    resp = await client.receive_json()
    assert resp["success"] is False
    assert resp["error"]["code"] == "already_bridged"


# -- Panel JS hash (blocking I/O safety) -------------------------------------


def test_panel_js_hash_sync_returns_string() -> None:
    """_panel_js_hash_sync should return a hex string."""
    from custom_components.loxone.websocket import _panel_js_hash_sync

    result = _panel_js_hash_sync()
    assert isinstance(result, str)
    assert len(result) <= 8


def test_panel_js_hash_sync_returns_zero_on_missing_file() -> None:
    """_panel_js_hash_sync should return '0' when the JS file doesn't exist."""
    from custom_components.loxone.websocket import _panel_js_hash_sync

    with patch("custom_components.loxone.websocket.PANEL_FRONTEND_PATH", "/nonexistent/path"):
        result = _panel_js_hash_sync()
        assert result == "0"


async def test_register_panel_calls_hash_in_executor(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
) -> None:
    """register_panel should call _panel_js_hash_sync via async_add_executor_job."""
    with patch.object(
        hass, "async_add_executor_job", new_callable=AsyncMock, return_value="abcd1234"
    ) as mock_executor:
        with patch("custom_components.loxone.websocket.panel_custom") as mock_panel:
            mock_panel.async_register_panel = AsyncMock()
            hass.data.pop("frontend_panels", None)

            with patch("custom_components.loxone.websocket.async_setup_component", return_value=True):
                with patch.object(hass.http, "async_register_static_paths", new_callable=AsyncMock):
                    from custom_components.loxone.websocket import register_panel

                    await register_panel(hass)

        executor_calls = [
            call
            for call in mock_executor.call_args_list
            if "_panel_js_hash_sync" in str(call)
        ]
        assert len(executor_calls) >= 1, (
            f"_panel_js_hash_sync should be called via async_add_executor_job, "
            f"got calls: {mock_executor.call_args_list}"
        )
