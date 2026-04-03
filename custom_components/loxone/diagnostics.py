"""Diagnostics support for Pyloxone."""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, config_entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator = getattr(config_entry, "runtime_data", None)
    if coordinator is not None and coordinator.miniserver is not None:
        return {
            "LoxAPP3.json": coordinator.miniserver.lox_config.json,
        }
    return {}
