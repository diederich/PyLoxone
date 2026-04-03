"""Provide info to system health."""

from __future__ import annotations

from typing import Any

from homeassistant.components import system_health
from homeassistant.core import HomeAssistant, callback

from .const import DOMAIN


@callback
def async_register(
    hass: HomeAssistant, register: system_health.SystemHealthRegistration
) -> None:
    """Register system health callbacks."""
    register.async_register_info(system_health_info)


async def system_health_info(hass: HomeAssistant) -> dict[str, Any]:
    """Get info for the info page."""
    for entry in hass.config_entries.async_entries(DOMAIN):
        coordinator = getattr(entry, "runtime_data", None)
        if coordinator is None:
            continue
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
    return {}
