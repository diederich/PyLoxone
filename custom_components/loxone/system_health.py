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
        if coordinator is not None and coordinator.miniserver is not None:
            ms = coordinator.miniserver
            host = entry.options.get("host", "")
            port = entry.options.get("port", 8080)
            return {
                "Loxone Miniserver Serial": ms.serial,
                "Project Name": ms.project_name,
                "Local Url": f"http://{host}:{port}",
                "Loxone Software Version": ms.software_version,
            }
    return {}
