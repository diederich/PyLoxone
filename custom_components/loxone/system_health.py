"""Provide info to system health."""

from __future__ import annotations

from typing import Any

from homeassistant.components import system_health
from homeassistant.core import HomeAssistant, callback

from .const import DOMAIN


@callback
def async_register(hass: HomeAssistant, register: system_health.SystemHealthRegistration) -> None:
    """Register system health callbacks."""
    register.async_register_info(system_health_info)


async def system_health_info(hass: HomeAssistant) -> dict[str, Any]:
    """Get info for the info page."""
    entries = hass.config_entries.async_entries(DOMAIN)
    coordinators = [(entry, getattr(entry, "runtime_data", None)) for entry in entries]
    coordinators = [(e, c) for e, c in coordinators if c is not None]

    if not coordinators:
        return {}

    if len(coordinators) == 1:
        entry, coordinator = coordinators[0]
        host = entry.options.get("host", "")
        port = entry.options.get("port", 8080)
        info: dict[str, Any] = {
            "Connection State": coordinator.connection_state.value,
            "Miniserver URL": f"http://{host}:{port}",
        }
        if coordinator.miniserver is not None:
            ms = coordinator.miniserver
            info["Serial"] = ms.serial
            info["Project Name"] = ms.project_name
            info["Software Version"] = ms.software_version
        return info

    info = {"Miniservers": len(coordinators)}
    for i, (entry, coordinator) in enumerate(coordinators, 1):
        label = entry.title or f"Miniserver {i}"
        host = entry.options.get("host", "")
        port = entry.options.get("port", 8080)
        info[f"{label} State"] = coordinator.connection_state.value
        info[f"{label} URL"] = f"http://{host}:{port}"
        if coordinator.miniserver is not None:
            info[f"{label} Serial"] = coordinator.miniserver.serial
    return info
