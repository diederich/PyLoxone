"""WebSocket API commands and custom panel registration for PyLoxone.

Provides the backend for the Loxone custom panel — a sidebar app that shows
Loxone controls alongside their HA entities, manages device bridges, and
controls area/device sync.

Architecture follows the KNX integration pattern: a single ``register_panel``
coroutine registers both WS commands and the sidebar panel, called from
``async_setup_entry``.
"""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path
from typing import Any

import voluptuous as vol
from homeassistant.components import panel_custom, websocket_api
from homeassistant.components.http import StaticPathConfig
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import area_registry as ar
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

PANEL_FRONTEND_PATH = str(Path(__file__).parent / "frontend")
URL_BASE = "/loxone_static"


def _panel_js_hash() -> str:
    """Short hash of the bundled JS for cache-busting."""
    js_path = Path(PANEL_FRONTEND_PATH) / "loxone-panel.js"
    try:
        return hashlib.md5(js_path.read_bytes()).hexdigest()[:8]
    except OSError:
        return "0"


def _get_coordinator(hass: HomeAssistant):
    """Return the first available LoxoneCoordinator, or None."""
    for value in hass.data.get(DOMAIN, {}).values():
        if hasattr(value, "api"):
            return value
    return None


async def register_panel(hass: HomeAssistant) -> None:
    """Register the Loxone WebSocket API and custom panel.

    Follows the KNX pattern: both WS commands and the sidebar panel are
    registered from a single entry point called in ``async_setup_entry``.
    WS commands are idempotent (safe to call multiple times); the panel
    guard uses ``hass.data["frontend_panels"]`` to prevent double-registration.
    """
    websocket_api.async_register_command(hass, ws_get_devices)
    websocket_api.async_register_command(hass, ws_set_entity_enabled)
    websocket_api.async_register_command(hass, ws_get_areas)
    websocket_api.async_register_command(hass, ws_get_bridges)
    websocket_api.async_register_command(hass, ws_add_bridge)
    websocket_api.async_register_command(hass, ws_remove_bridge)
    websocket_api.async_register_command(hass, ws_get_status)

    if DOMAIN not in hass.data.get("frontend_panels", {}):
        from homeassistant.setup import async_setup_component

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


# -- loxone/get_devices -------------------------------------------------------


@websocket_api.require_admin
@websocket_api.websocket_command({vol.Required("type"): "loxone/get_devices"})
@callback
def ws_get_devices(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Return Loxone controls with their matched HA entities."""
    coordinator = _get_coordinator(hass)
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
        connection.send_error(
            msg["id"], "not_loxone", f"Entity {entity_id} is not a Loxone entity"
        )
        return

    if enabled:
        if entry.disabled_by == er.RegistryEntryDisabler.INTEGRATION:
            registry.async_update_entity(entity_id, disabled_by=None)
    else:
        registry.async_update_entity(
            entity_id, disabled_by=er.RegistryEntryDisabler.INTEGRATION
        )

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
@websocket_api.websocket_command({vol.Required("type"): "loxone/get_areas"})
@callback
def ws_get_areas(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Return Loxone rooms, HA areas, and device-to-area mappings."""
    coordinator = _get_coordinator(hass)
    if coordinator is None:
        connection.send_error(msg["id"], "not_connected", "Loxone Miniserver not connected")
        return

    structure = coordinator.api.structure_file or {}
    rooms = structure.get("rooms", {})

    area_reg = ar.async_get(hass)
    device_reg = dr.async_get(hass)

    ha_areas = {
        a.id: {"id": a.id, "name": a.name}
        for a in area_reg.async_list_areas()
    }

    ha_area_by_name: dict[str, str] = {
        a.name.lower(): a.id for a in area_reg.async_list_areas()
    }

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
@websocket_api.websocket_command({vol.Required("type"): "loxone/get_bridges"})
@callback
def ws_get_bridges(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Return the current list of device bridges."""
    coordinator = _get_coordinator(hass)
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
        for ab in bridge_runtime._active
    ]
    connection.send_result(msg["id"], {"bridges": bridges})


@websocket_api.require_admin
@websocket_api.websocket_command(
    {
        vol.Required("type"): "loxone/add_bridge",
        vol.Required("entity_id"): str,
        vol.Required("loxone_uuid"): str,
    }
)
@websocket_api.async_response
async def ws_add_bridge(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Add a new device bridge (HA entity <-> Loxone control)."""
    coordinator = _get_coordinator(hass)
    if coordinator is None:
        connection.send_error(msg["id"], "not_connected", "Loxone Miniserver not connected")
        return

    bridge_runtime = getattr(coordinator, "bridge_runtime", None)
    if bridge_runtime is None:
        connection.send_error(msg["id"], "no_bridge_runtime", "Bridge runtime not available")
        return

    entity_id: str = msg["entity_id"]
    loxone_uuid: str = msg["loxone_uuid"]

    for ab in bridge_runtime._active:
        if ab.bridge.entity_id == entity_id:
            connection.send_error(
                msg["id"], "already_bridged",
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

    from .bridge import DeviceBridge

    bridge = DeviceBridge(
        entity_id=entity_id,
        loxone_uuid=loxone_uuid,
        loxone_type=loxone_type,
        loxone_name=loxone_name,
        loxone_states=loxone_states,
    )

    try:
        bridge_runtime._activate(bridge)
        bridge_runtime._persist()
    except Exception as exc:
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
    }
)
@websocket_api.async_response
async def ws_remove_bridge(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Remove a device bridge by HA entity ID."""
    coordinator = _get_coordinator(hass)
    if coordinator is None:
        connection.send_error(msg["id"], "not_connected", "Loxone Miniserver not connected")
        return

    bridge_runtime = getattr(coordinator, "bridge_runtime", None)
    if bridge_runtime is None:
        connection.send_error(msg["id"], "no_bridge_runtime", "Bridge runtime not available")
        return

    entity_id: str = msg["entity_id"]
    found = None
    for ab in bridge_runtime._active:
        if ab.bridge.entity_id == entity_id:
            found = ab
            break

    if found is None:
        connection.send_error(
            msg["id"], "not_found",
            f"No bridge found for entity {entity_id}",
        )
        return

    removed_uuid = found.bridge.loxone_uuid
    bridge_runtime._deactivate(found)
    bridge_runtime._active.remove(found)
    bridge_runtime._reenable_entities({removed_uuid})
    bridge_runtime._persist()

    connection.send_result(msg["id"], {"removed": entity_id})


# -- loxone/get_status -------------------------------------------------------


@websocket_api.require_admin
@websocket_api.websocket_command({vol.Required("type"): "loxone/get_status"})
@callback
def ws_get_status(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Return Miniserver connection status and metadata."""
    coordinator = _get_coordinator(hass)
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
    entities_without_state = [
        e.entity_id for e in enabled_entities if hass.states.get(e.entity_id) is None
    ]

    bridge_runtime = getattr(coordinator, "bridge_runtime", None)
    bridge_count = len(bridge_runtime._active) if bridge_runtime else 0

    connection.send_result(
        msg["id"],
        {
            "connection_state": coordinator.connection_state.value,
            "host": f"{coordinator._host}:{coordinator._port}",
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
