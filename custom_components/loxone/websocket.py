"""WebSocket API commands and custom panel registration for PyLoxone.

Provides the backend for the Loxone custom panel — a sidebar app that shows
Loxone controls alongside their HA entities, manages device bridges, and
controls area/device sync.

Architecture follows the KNX integration pattern: a single ``register_panel``
coroutine registers both WS commands and the sidebar panel, called from
``async_setup_entry``.
"""

from __future__ import annotations

import contextlib
import hashlib
import logging
from pathlib import Path
from typing import Any

import voluptuous as vol

from homeassistant.components import panel_custom, websocket_api
from homeassistant.components.http import StaticPathConfig
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import area_registry as ar, device_registry as dr, entity_registry as er
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.setup import async_setup_component
from homeassistant.util import dt as dt_util

from .bridge_mappers import get_mapper
from .bridge_types import DeviceBridge
from .const import DOMAIN
from .coordinator import STRUCTURE_DIFF_KEY

_LOGGER = logging.getLogger(__name__)

PANEL_FRONTEND_PATH = str(Path(__file__).parent / "frontend")
URL_BASE = "/loxone_static"


def _panel_js_hash() -> str:
    """Short hash of the bundled JS for cache-busting."""
    js_path = Path(PANEL_FRONTEND_PATH) / "loxone-panel.js"
    try:
        return hashlib.md5(js_path.read_bytes(), usedforsecurity=False).hexdigest()[:8]
    except OSError:
        return "0"


def _get_coordinator(hass: HomeAssistant, miniserver: str | None = None):
    """Return the LoxoneCoordinator for the given Miniserver, or the first available.

    *miniserver* can be an HA entry_id or a Miniserver serial number.
    """
    for entry in hass.config_entries.async_entries(DOMAIN):
        if miniserver is not None and entry.entry_id != miniserver:
            coord = getattr(entry, "runtime_data", None)
            ms = getattr(coord, "miniserver", None) if coord else None
            if not ms or ms.serial != miniserver:
                continue
        coordinator = getattr(entry, "runtime_data", None)
        if coordinator is not None:
            return coordinator
    return None


async def register_panel(hass: HomeAssistant) -> None:
    """Register the Loxone WebSocket API and custom panel.

    Follows the KNX pattern: both WS commands and the sidebar panel are
    registered from a single entry point called in ``async_setup_entry``.
    WS commands are idempotent (safe to call multiple times); the panel
    guard uses ``hass.data["frontend_panels"]`` to prevent double-registration.
    """
    websocket_api.async_register_command(hass, ws_list_entries)
    websocket_api.async_register_command(hass, ws_get_devices)
    websocket_api.async_register_command(hass, ws_set_entity_enabled)
    websocket_api.async_register_command(hass, ws_get_areas)
    websocket_api.async_register_command(hass, ws_get_bridges)
    websocket_api.async_register_command(hass, ws_add_bridge)
    websocket_api.async_register_command(hass, ws_remove_bridge)
    websocket_api.async_register_command(hass, ws_get_status)
    websocket_api.async_register_command(hass, ws_subscribe_events)
    websocket_api.async_register_command(hass, ws_send_command)
    websocket_api.async_register_command(hass, ws_get_structure_diff)
    websocket_api.async_register_command(hass, ws_get_control_detail)
    websocket_api.async_register_command(hass, ws_get_structure)
    websocket_api.async_register_command(hass, ws_subscribe_logs)

    if DOMAIN not in hass.data.get("frontend_panels", {}):
        if not await async_setup_component(hass, "panel_custom", {}):
            _LOGGER.warning("panel_custom not available — Loxone sidebar panel disabled")
            return

        await hass.http.async_register_static_paths(
            [StaticPathConfig(URL_BASE, PANEL_FRONTEND_PATH, cache_headers=False)]
        )
        await panel_custom.async_register_panel(
            hass=hass,
            frontend_url_path=DOMAIN,
            webcomponent_name="loxone-panel",
            module_url=f"{URL_BASE}/loxone-panel.js?v={_panel_js_hash()}",
            sidebar_title="Loxone",
            sidebar_icon="mdi:home-automation",
            embed_iframe=False,
            require_admin=True,
        )
        _LOGGER.info("Loxone custom panel registered")


# -- loxone/list_entries ------------------------------------------------------


@websocket_api.require_admin
@websocket_api.websocket_command({vol.Required("type"): "loxone/list_entries"})
@callback
def ws_list_entries(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Return available Loxone config entries (one per Miniserver)."""
    entries: list[dict[str, Any]] = []
    for entry in hass.config_entries.async_entries(DOMAIN):
        coordinator = getattr(entry, "runtime_data", None)
        if coordinator is None:
            continue
        ms = coordinator.miniserver
        entries.append(
            {
                "miniserver": entry.entry_id,
                "title": entry.title,
                "host": entry.options.get("host", ""),
                "serial": ms.serial if ms else None,
                "name": ms.name if ms else None,
            }
        )
    connection.send_result(msg["id"], {"entries": entries})


# -- loxone/get_devices -------------------------------------------------------


@websocket_api.require_admin
@websocket_api.websocket_command(
    {
        vol.Required("type"): "loxone/get_devices",
        vol.Optional("miniserver"): str,
    }
)
@callback
def ws_get_devices(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Return Loxone controls with their matched HA entities."""
    coordinator = _get_coordinator(hass, msg.get("miniserver"))
    if coordinator is None:
        connection.send_error(msg["id"], "not_connected", "Loxone Miniserver not connected")
        return

    structure = coordinator.api.structure_file or {}
    controls = structure.get("controls", {})
    rooms = structure.get("rooms", {})

    registry = er.async_get(hass)

    lox_entities_by_uid: dict[str, list[dict]] = {}
    for ent in registry.entities.values():
        if ent.platform == DOMAIN:
            lox_entities_by_uid.setdefault(ent.unique_id, []).append(ent)

    devices: list[dict[str, Any]] = []

    for _uuid, ctrl in controls.items():
        uuid_action = ctrl.get("uuidAction", _uuid)
        room_ref = ctrl.get("room", "")
        room_name = rooms.get(room_ref, {}).get("name", "") if room_ref in rooms else room_ref

        matched = lox_entities_by_uid.get(uuid_action, [])
        ha_entities = [
            {
                "entity_id": ent.entity_id,
                "disabled_by": ent.disabled_by,
                "area_id": ent.area_id,
            }
            for ent in matched
        ]

        devices.append(
            {
                "uuid": uuid_action,
                "name": ctrl.get("name", ""),
                "type": ctrl.get("type", ""),
                "room": room_name,
                "ha_entities": ha_entities,
            }
        )

        for sc_key, sc in ctrl.get("subControls", {}).items():
            sc_uuid = sc.get("uuidAction", sc_key)
            sc_matched = lox_entities_by_uid.get(sc_uuid, [])
            sc_ha = [
                {
                    "entity_id": ent.entity_id,
                    "disabled_by": ent.disabled_by,
                    "area_id": ent.area_id,
                }
                for ent in sc_matched
            ]
            devices.append(
                {
                    "uuid": sc_uuid,
                    "name": sc.get("name", ""),
                    "type": sc.get("type", ""),
                    "room": room_name,
                    "parent": uuid_action,
                    "ha_entities": sc_ha,
                }
            )

    connection.send_result(msg["id"], {"devices": devices})


# -- loxone/set_entity_enabled ------------------------------------------------


@websocket_api.require_admin
@websocket_api.websocket_command(
    {
        vol.Required("type"): "loxone/set_entity_enabled",
        vol.Required("entity_id"): str,
        vol.Required("enabled"): bool,
    }
)
@callback
def ws_set_entity_enabled(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Enable or disable a Loxone entity in the entity registry."""
    registry = er.async_get(hass)
    entity_id: str = msg["entity_id"]
    enabled: bool = msg["enabled"]

    entry = registry.async_get(entity_id)
    if entry is None:
        connection.send_error(msg["id"], "not_found", f"Entity {entity_id} not found")
        return

    if entry.platform != DOMAIN:
        connection.send_error(msg["id"], "not_loxone", f"Entity {entity_id} is not a Loxone entity")
        return

    if enabled:
        if entry.disabled_by == er.RegistryEntryDisabler.INTEGRATION:
            registry.async_update_entity(entity_id, disabled_by=None)
    else:
        registry.async_update_entity(entity_id, disabled_by=er.RegistryEntryDisabler.INTEGRATION)

    updated = registry.async_get(entity_id)
    connection.send_result(
        msg["id"],
        {
            "entity_id": entity_id,
            "disabled_by": updated.disabled_by if updated else None,
        },
    )


# -- loxone/get_areas ---------------------------------------------------------


@websocket_api.require_admin
@websocket_api.websocket_command(
    {
        vol.Required("type"): "loxone/get_areas",
        vol.Optional("miniserver"): str,
    }
)
@callback
def ws_get_areas(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Return Loxone rooms, HA areas, and device-to-area mappings."""
    coordinator = _get_coordinator(hass, msg.get("miniserver"))
    if coordinator is None:
        connection.send_error(msg["id"], "not_connected", "Loxone Miniserver not connected")
        return

    structure = coordinator.api.structure_file or {}
    rooms = structure.get("rooms", {})

    area_reg = ar.async_get(hass)
    device_reg = dr.async_get(hass)

    ha_areas = {a.id: {"id": a.id, "name": a.name} for a in area_reg.async_list_areas()}

    ha_area_by_name: dict[str, str] = {a.name.lower(): a.id for a in area_reg.async_list_areas()}

    loxone_rooms: list[dict[str, Any]] = []
    for room_uuid, room in rooms.items():
        room_name = room.get("name", "")
        matched_area_id = ha_area_by_name.get(room_name.lower())

        device_count = 0
        for dev in device_reg.devices.values():
            if any(id_pair[0] == DOMAIN for id_pair in dev.identifiers):
                if dev.area_id == matched_area_id and matched_area_id is not None:
                    device_count += 1

        loxone_rooms.append(
            {
                "uuid": room_uuid,
                "name": room_name,
                "ha_area_id": matched_area_id,
                "ha_area_name": ha_areas[matched_area_id]["name"] if matched_area_id else None,
                "device_count": device_count,
            }
        )

    connection.send_result(
        msg["id"],
        {
            "rooms": loxone_rooms,
            "ha_areas": list(ha_areas.values()),
        },
    )


# -- Bridge management --------------------------------------------------------


@websocket_api.require_admin
@websocket_api.websocket_command(
    {
        vol.Required("type"): "loxone/get_bridges",
        vol.Optional("miniserver"): str,
    }
)
@callback
def ws_get_bridges(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Return the current list of device bridges."""
    coordinator = _get_coordinator(hass, msg.get("miniserver"))
    if coordinator is None:
        connection.send_error(msg["id"], "not_connected", "Loxone Miniserver not connected")
        return

    bridge_runtime = getattr(coordinator, "bridge_runtime", None)
    if bridge_runtime is None:
        connection.send_result(msg["id"], {"bridges": []})
        return

    bridges = [
        {
            "entity_id": ab.bridge.entity_id,
            "loxone_uuid": ab.bridge.loxone_uuid,
            "loxone_name": ab.bridge.loxone_name,
            "loxone_type": ab.bridge.loxone_type,
        }
        for ab in bridge_runtime.active_bridges
    ]
    connection.send_result(msg["id"], {"bridges": bridges})


@websocket_api.require_admin
@websocket_api.websocket_command(
    {
        vol.Required("type"): "loxone/add_bridge",
        vol.Required("entity_id"): str,
        vol.Required("loxone_uuid"): str,
        vol.Optional("miniserver"): str,
        vol.Optional("details"): {str: str},
    }
)
@websocket_api.async_response
async def ws_add_bridge(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Add a new device bridge (HA entity <-> Loxone control)."""
    coordinator = _get_coordinator(hass, msg.get("miniserver"))
    if coordinator is None:
        connection.send_error(msg["id"], "not_connected", "Loxone Miniserver not connected")
        return

    bridge_runtime = getattr(coordinator, "bridge_runtime", None)
    if bridge_runtime is None:
        connection.send_error(msg["id"], "no_bridge_runtime", "Bridge runtime not available")
        return

    entity_id: str = msg["entity_id"]
    loxone_uuid: str = msg["loxone_uuid"]
    extra_details: dict[str, str] = msg.get("details", {})

    for ab in bridge_runtime.active_bridges:
        if ab.bridge.entity_id == entity_id:
            connection.send_error(
                msg["id"],
                "already_bridged",
                f"Entity {entity_id} already has a bridge",
            )
            return

    structure = coordinator.api.structure_file or {}
    controls = structure.get("controls", {})
    loxone_type = ""
    loxone_name = ""
    loxone_states: dict[str, str] = {}

    for ctrl in controls.values():
        if ctrl.get("uuidAction") == loxone_uuid:
            loxone_type = ctrl.get("type", "")
            loxone_name = ctrl.get("name", "")
            loxone_states = ctrl.get("states", {})
            break
        for sc in ctrl.get("subControls", {}).values():
            if sc.get("uuidAction") == loxone_uuid:
                loxone_type = sc.get("type", "")
                loxone_name = sc.get("name", "")
                loxone_states = sc.get("states", {})
                break

    entity_domain = entity_id.split(".", maxsplit=1)[0]

    # For cover entities the loxone_type sentinel is "cover"; the actual
    # control types (Slider VIs, VOs) are carried in details.
    if entity_domain == "cover" and not loxone_type:
        loxone_type = "cover"

    bridge = DeviceBridge(
        entity_id=entity_id,
        loxone_uuid=loxone_uuid,
        loxone_type=loxone_type,
        loxone_name=loxone_name,
        loxone_states=loxone_states,
        details=extra_details,
    )

    try:
        get_mapper(bridge, entity_domain)
    except ValueError as exc:
        connection.send_error(msg["id"], "unsupported_bridge", str(exc))
        return

    try:
        bridge_runtime.register_bridge(bridge)
        bridge_runtime.persist_bridge_options()
    except Exception as exc:  # noqa: BLE001 — must catch-all to send WS error response
        connection.send_error(msg["id"], "bridge_error", str(exc))
        return

    connection.send_result(
        msg["id"],
        {
            "entity_id": entity_id,
            "loxone_uuid": loxone_uuid,
            "loxone_name": loxone_name,
            "loxone_type": loxone_type,
        },
    )


@websocket_api.require_admin
@websocket_api.websocket_command(
    {
        vol.Required("type"): "loxone/remove_bridge",
        vol.Required("entity_id"): str,
        vol.Optional("miniserver"): str,
    }
)
@websocket_api.async_response
async def ws_remove_bridge(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Remove a device bridge by HA entity ID."""
    coordinator = _get_coordinator(hass, msg.get("miniserver"))
    if coordinator is None:
        connection.send_error(msg["id"], "not_connected", "Loxone Miniserver not connected")
        return

    bridge_runtime = getattr(coordinator, "bridge_runtime", None)
    if bridge_runtime is None:
        connection.send_error(msg["id"], "no_bridge_runtime", "Bridge runtime not available")
        return

    entity_id: str = msg["entity_id"]
    found = None
    for ab in bridge_runtime.active_bridges:
        if ab.bridge.entity_id == entity_id:
            found = ab
            break

    if found is None:
        connection.send_error(
            msg["id"],
            "not_found",
            f"No bridge found for entity {entity_id}",
        )
        return

    bridge_runtime.unregister_bridge(found)

    connection.send_result(msg["id"], {"removed": entity_id})


# -- loxone/get_status -------------------------------------------------------


@websocket_api.require_admin
@websocket_api.websocket_command(
    {
        vol.Required("type"): "loxone/get_status",
        vol.Optional("miniserver"): str,
    }
)
@callback
def ws_get_status(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Return Miniserver connection status and metadata."""
    coordinator = _get_coordinator(hass, msg.get("miniserver"))
    if coordinator is None:
        connection.send_error(msg["id"], "not_connected", "Loxone Miniserver not connected")
        return

    structure = coordinator.api.structure_file or {}
    ms_info = structure.get("msInfo", {})
    sw_version = structure.get("softwareVersion", [])
    if isinstance(sw_version, list):
        sw_version = ".".join(str(x) for x in sw_version)

    controls = structure.get("controls", {})
    rooms = structure.get("rooms", {})

    entity_reg = er.async_get(hass)
    loxone_entities = [e for e in entity_reg.entities.values() if e.platform == DOMAIN]
    enabled_entities = [e for e in loxone_entities if e.disabled_by is None]
    disabled_entities = [e for e in loxone_entities if e.disabled_by is not None]
    entities_without_state = [e.entity_id for e in enabled_entities if hass.states.get(e.entity_id) is None]

    bridge_runtime = getattr(coordinator, "bridge_runtime", None)
    bridge_count = len(bridge_runtime.active_bridges) if bridge_runtime else 0

    connection.send_result(
        msg["id"],
        {
            "connection_state": coordinator.connection_state.value,
            "host": coordinator.miniserver_addr,
            "miniserver_name": ms_info.get("msName", ""),
            "project_name": ms_info.get("projectName", ""),
            "location": ms_info.get("location", ""),
            "serial_number": ms_info.get("serialNr", ""),
            "miniserver_type": ms_info.get("miniserverType", ""),
            "software_version": sw_version,
            "controls_count": len(controls),
            "rooms_count": len(rooms),
            "entities_total": len(loxone_entities),
            "entities_enabled": len(enabled_entities),
            "entities_disabled": len(disabled_entities),
            "entities_without_state": entities_without_state,
            "bridge_count": bridge_count,
        },
    )


# -- loxone/subscribe_events -------------------------------------------------


@websocket_api.require_admin
@websocket_api.websocket_command(
    {
        vol.Required("type"): "loxone/subscribe_events",
        vol.Optional("miniserver"): str,
    }
)
@callback
def ws_subscribe_events(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Subscribe to real-time Loxone state-change events.

    Streams every UUID value update as it arrives from the Miniserver.
    Each event includes the control name and room resolved from the
    structure file.
    """
    coordinator = _get_coordinator(hass, msg.get("miniserver"))
    if coordinator is None:
        connection.send_error(msg["id"], "not_connected", "Loxone Miniserver not connected")
        return

    structure = coordinator.api.structure_file or {}
    controls = structure.get("controls", {})
    rooms = structure.get("rooms", {})

    uuid_to_info: dict[str, tuple[str, str]] = {}
    for ctrl in controls.values():
        ctrl_name = ctrl.get("name", "")
        room_uuid = ctrl.get("room", "")
        room_name = rooms.get(room_uuid, {}).get("name", "") if room_uuid else ""
        ctrl_uuid = ctrl.get("uuidAction", "")
        uuid_to_info[ctrl_uuid] = (ctrl_name, room_name)
        for state_uuid in ctrl.get("states", {}).values():
            uuid_to_info[state_uuid] = (ctrl_name, room_name)
        for sc in ctrl.get("subControls", {}).values():
            sc_name = sc.get("name", ctrl_name)
            sc_uuid = sc.get("uuidAction", "")
            uuid_to_info[sc_uuid] = (sc_name, room_name)
            for state_uuid in sc.get("states", {}).values():
                uuid_to_info[state_uuid] = (sc_name, room_name)

    @callback
    def _forward_event(message: dict) -> None:
        ts = dt_util.utcnow().isoformat()
        events = []
        for uuid, value in message.items():
            name, room = uuid_to_info.get(uuid, ("", ""))
            events.append({"uuid": uuid, "name": name, "room": room, "value": value, "timestamp": ts})
        connection.send_message(websocket_api.event_message(msg["id"], {"events": events}))

    unsub = async_dispatcher_connect(hass, coordinator.monitor_signal, _forward_event)
    connection.subscriptions[msg["id"]] = unsub
    connection.send_result(msg["id"])


# -- loxone/send_command -----------------------------------------------------


@websocket_api.require_admin
@websocket_api.websocket_command(
    {
        vol.Required("type"): "loxone/send_command",
        vol.Required("uuid"): str,
        vol.Required("command"): str,
        vol.Optional("miniserver"): str,
    }
)
@websocket_api.async_response
async def ws_send_command(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Send a raw command to a Loxone control by UUID."""
    coordinator = _get_coordinator(hass, msg.get("miniserver"))
    if coordinator is None:
        connection.send_error(msg["id"], "not_connected", "Loxone Miniserver not connected")
        return

    try:
        await coordinator.api.send_websocket_command(msg["uuid"], msg["command"])
        connection.send_result(msg["id"], {"sent": True, "uuid": msg["uuid"], "command": msg["command"]})
    except Exception as exc:  # noqa: BLE001 — must catch-all to send WS error response
        connection.send_error(msg["id"], "command_failed", str(exc))


# -- loxone/get_structure_diff -----------------------------------------------


@websocket_api.require_admin
@websocket_api.websocket_command(
    {
        vol.Required("type"): "loxone/get_structure_diff",
        vol.Optional("miniserver"): str,
    }
)
@callback
def ws_get_structure_diff(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Return the last structure diff for the given Miniserver."""
    coordinator = _get_coordinator(hass, msg.get("miniserver"))
    if coordinator is None:
        connection.send_error(msg["id"], "not_connected", "Loxone Miniserver not connected")
        return

    diffs = hass.data.get(STRUCTURE_DIFF_KEY, {})
    diff = diffs.get(coordinator.config_entry.entry_id)

    if diff is None or diff.get("timestamp") is None:
        connection.send_result(
            msg["id"],
            {
                "has_diff": False,
                "timestamp": None,
                "added": [],
                "removed": [],
                "changed": [],
            },
        )
        return

    def _to_list(d: dict) -> list:
        return [{"uuid": k, **v} for k, v in d.items()]

    def _changed_to_list(d: dict) -> list:
        return [{"uuid": k, "old": v["old"], "new": v["new"]} for k, v in d.items()]

    connection.send_result(
        msg["id"],
        {
            "has_diff": True,
            "timestamp": diff["timestamp"],
            "added": _to_list(diff.get("added", {})),
            "removed": _to_list(diff.get("removed", {})),
            "changed": _changed_to_list(diff.get("changed", {})),
        },
    )


# ---------------------------------------------------------------------------
# Control detail
# ---------------------------------------------------------------------------


@websocket_api.require_admin
@websocket_api.websocket_command(
    {
        vol.Required("type"): "loxone/get_control_detail",
        vol.Required("uuid"): str,
        vol.Optional("miniserver"): str,
    }
)
@callback
def ws_get_control_detail(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Return detailed info for a single Loxone control."""
    coordinator = _get_coordinator(hass, msg.get("miniserver"))
    if coordinator is None:
        connection.send_error(msg["id"], "not_connected", "Loxone Miniserver not connected")
        return

    structure = coordinator.api.structure_file or {}
    controls_raw = structure.get("controls", {})
    rooms = structure.get("rooms", {})
    cats = structure.get("cats", {})

    uuid = msg["uuid"]

    # Build a flat lookup keyed by uuidAction (the UUID exposed to the frontend),
    # including sub-controls.  ws_get_devices uses uuidAction as the device UUID,
    # so we must resolve the same way here.
    ctrl: dict | None = None
    parent_ctrl: dict | None = None

    for raw_uuid, top_ctrl in controls_raw.items():
        top_action = top_ctrl.get("uuidAction", raw_uuid)
        if top_action == uuid or raw_uuid == uuid:
            ctrl = top_ctrl
            break
        for sc_key, sc in top_ctrl.get("subControls", {}).items():
            sc_action = sc.get("uuidAction", sc_key)
            if sc_action == uuid or sc_key == uuid:
                ctrl = sc
                parent_ctrl = top_ctrl
                break
        if ctrl is not None:
            break

    if ctrl is None:
        connection.send_error(msg["id"], "not_found", f"Control {uuid} not found")
        return

    room_uuid = ctrl.get("room", "")
    cat_uuid = ctrl.get("cat", "")
    room_name = rooms.get(room_uuid, {}).get("name", "") if room_uuid else ""
    cat_name = cats.get(cat_uuid, {}).get("name", "") if cat_uuid else ""

    # Determine parent info (sub-controls carry a "parentUuid" key in the raw structure;
    # we also track it via parent_ctrl found above).
    parent_name = None
    is_sub = False
    if parent_ctrl is not None:
        parent_name = parent_ctrl.get("name", "")
        is_sub = True
    elif ctrl.get("parentUuid"):
        parent_uuid = ctrl["parentUuid"]
        for top_ctrl in controls_raw.values():
            if (
                top_ctrl.get("uuidAction", "") == parent_uuid
                or top_ctrl.get("uuidAction", top_ctrl.get("name")) == parent_uuid
            ):
                parent_name = top_ctrl.get("name", parent_uuid)
                is_sub = True
                break

    states_raw = ctrl.get("states", {})
    state_map: dict[str, dict] = {}
    for sname, suuid in states_raw.items():
        state_map[sname] = {
            "uuid": suuid,
            "value": None,
            "last_changed": None,
        }

    ent_reg = er.async_get(hass)
    entry_id = coordinator.config_entry.entry_id
    entity_entries = er.async_entries_for_config_entry(ent_reg, entry_id)
    ha_entities = []
    for e in entity_entries:
        if e.unique_id and uuid in e.unique_id:
            st = hass.states.get(e.entity_id)
            ha_entities.append(
                {
                    "entity_id": e.entity_id,
                    "domain": e.domain,
                    "disabled_by": e.disabled_by,
                    "state": st.state if st else None,
                    "last_changed": st.last_changed.isoformat() if st and st.last_changed else None,
                }
            )

    safe_keys = {"name", "type", "room", "cat", "states", "parentUuid", "uuidAction", "subControls"}
    details = {k: v for k, v in ctrl.items() if k not in safe_keys and not k.startswith("_")}

    connection.send_result(
        msg["id"],
        {
            "uuid": uuid,
            "name": ctrl.get("name", uuid),
            "type": ctrl.get("type", ""),
            "room": room_name,
            "category": cat_name,
            "is_sub_control": is_sub,
            "parent_name": parent_name,
            "states": state_map,
            "ha_entities": ha_entities,
            "details": details,
        },
    )


# ---------------------------------------------------------------------------
# Structure tree
# ---------------------------------------------------------------------------


@websocket_api.require_admin
@websocket_api.websocket_command(
    {
        vol.Required("type"): "loxone/get_structure",
        vol.Optional("miniserver"): str,
    }
)
@callback
def ws_get_structure(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Return the full structure tree from the Miniserver."""
    coordinator = _get_coordinator(hass, msg.get("miniserver"))
    if coordinator is None:
        connection.send_error(msg["id"], "not_connected", "Loxone Miniserver not connected")
        return

    structure = coordinator.api.structure_file or {}
    controls = structure.get("controls", {})
    rooms = structure.get("rooms", {})
    cats = structure.get("cats", {})

    room_list = [{"uuid": k, "name": v.get("name", k)} for k, v in rooms.items()]
    cat_list = [{"uuid": k, "name": v.get("name", k)} for k, v in cats.items()]

    ctrl_list = []
    for raw_uuid, c in controls.items():
        if c.get("parentUuid"):
            continue
        uuid_action = c.get("uuidAction", raw_uuid)
        state_names = list((c.get("states") or {}).keys())
        subs = []
        for sc_key, sc in c.get("subControls", {}).items():
            sc_uuid_action = sc.get("uuidAction", sc_key)
            subs.append(
                {
                    "uuid": sc_uuid_action,
                    "name": sc.get("name", sc_key),
                    "type": sc.get("type", ""),
                    "states": list((sc.get("states") or {}).keys()),
                }
            )
        room_uuid = c.get("room", "")
        cat_uuid = c.get("cat", "")
        ctrl_list.append(
            {
                "uuid": uuid_action,
                "name": c.get("name", uuid_action),
                "type": c.get("type", ""),
                "room": rooms.get(room_uuid, {}).get("name", "") if room_uuid else "",
                "category": cats.get(cat_uuid, {}).get("name", "") if cat_uuid else "",
                "states": state_names,
                "sub_controls": subs,
            }
        )

    ctrl_list.sort(key=lambda x: (x["room"], x["name"]))

    connection.send_result(
        msg["id"],
        {
            "rooms": room_list,
            "categories": cat_list,
            "controls": ctrl_list,
        },
    )


# ---------------------------------------------------------------------------
# Log viewer subscription
# ---------------------------------------------------------------------------


class _PanelLogHandler(logging.Handler):
    """Streams log records to a WS subscription."""

    def __init__(self, send_fn):
        """Initialize the _PanelLogHandler."""
        super().__init__(logging.DEBUG)
        self._send = send_fn

    def emit(self, record: logging.LogRecord) -> None:
        """Emit."""
        with contextlib.suppress(Exception):
            self._send(
                {
                    "name": record.name,
                    "level": record.levelname,
                    "message": self.format(record),
                    "timestamp": record.created,
                }
            )


@websocket_api.require_admin
@websocket_api.websocket_command({vol.Required("type"): "loxone/subscribe_logs"})
@callback
def ws_subscribe_logs(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Subscribe to live log output for the loxone integration."""
    logger = logging.getLogger("custom_components.loxone")

    handler = _PanelLogHandler(lambda event: connection.send_message(websocket_api.event_message(msg["id"], event)))
    logger.addHandler(handler)

    def _unsubscribe() -> None:
        logger.removeHandler(handler)

    connection.subscriptions[msg["id"]] = _unsubscribe
    connection.send_result(msg["id"])
