"""Diagnostics support for PyLoxone."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant

from . import LoxoneConfigEntry

TO_REDACT_CONFIG = {CONF_USERNAME, CONF_PASSWORD, CONF_HOST, "token", "hash_alg"}
TO_REDACT_STRUCTURE = {"msInfo", "users", "autopilot", "caller"}


def _redact_structure(structure: dict) -> dict:
    """Redact sensitive fields from LoxAPP3.json while preserving useful debug info."""
    result = {}
    for key, value in structure.items():
        if key in TO_REDACT_STRUCTURE:
            result[key] = "**REDACTED**"
        elif key == "controls":
            result[key] = _summarise_controls(value)
        elif key == "rooms":
            result[key] = {
                uid: {"name": r.get("name", ""), "type": r.get("type", "")} for uid, r in (value or {}).items()
            }
        elif key == "cats":
            result[key] = {
                uid: {"name": c.get("name", ""), "type": c.get("type", "")} for uid, c in (value or {}).items()
            }
        else:
            result[key] = value
    return result


def _summarise_controls(controls: dict | None) -> dict:
    """Summarise controls: keep type/room/states/subControls, drop raw details."""
    if not controls:
        return {}
    summary = {}
    for uuid, ctrl in controls.items():
        entry: dict[str, Any] = {
            "name": ctrl.get("name", ""),
            "type": ctrl.get("type", ""),
            "room": ctrl.get("room", ""),
            "cat": ctrl.get("cat", ""),
            "states": ctrl.get("states", {}),
        }
        sub = ctrl.get("subControls")
        if sub:
            entry["subControls"] = {
                sc_uuid: {
                    "name": sc.get("name", ""),
                    "type": sc.get("type", ""),
                    "states": sc.get("states", {}),
                }
                for sc_uuid, sc in sub.items()
            }
        summary[uuid] = entry
    return summary


async def async_get_config_entry_diagnostics(hass: HomeAssistant, config_entry: LoxoneConfigEntry) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    diag: dict[str, Any] = {
        "config_entry": async_redact_data(
            {
                "options": dict(config_entry.options),
                "data": dict(config_entry.data),
            },
            TO_REDACT_CONFIG,
        ),
    }

    coordinator = getattr(config_entry, "runtime_data", None)
    if coordinator is not None:
        diag["connection_state"] = coordinator.connection_state.value

        if coordinator.miniserver is not None:
            ms = coordinator.miniserver
            diag["miniserver"] = {
                "serial": ms.serial,
                "software_version": ms.software_version,
                "miniserver_type": ms.miniserver_type,
                "project_name": ms.project_name,
            }

        if coordinator.api and coordinator.api.structure_file:
            diag["structure"] = _redact_structure(coordinator.api.structure_file)
        else:
            diag["structure"] = None

    return diag
