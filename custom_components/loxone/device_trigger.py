"""Device triggers for Loxone controls.

Exposes Loxone state changes as device triggers so users can build
automations from the HA device UI ("When this device does X…").
"""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.components.device_automation import DEVICE_TRIGGER_BASE_SCHEMA
from homeassistant.components.homeassistant.triggers import event as event_trigger
from homeassistant.const import CONF_DEVICE_ID, CONF_DOMAIN, CONF_PLATFORM, CONF_TYPE
from homeassistant.core import CALLBACK_TYPE, HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.trigger import TriggerActionType, TriggerInfo
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN

CONF_SUBTYPE = "subtype"
EVENT_LOXONE_STATE_CHANGE = "loxone_state_change"

TRIGGER_TYPES = {"state_change"}

TRIGGER_SCHEMA = DEVICE_TRIGGER_BASE_SCHEMA.extend(
    {
        vol.Required(CONF_TYPE): vol.In(TRIGGER_TYPES),
        vol.Optional(CONF_SUBTYPE): str,
    }
)


async def async_get_triggers(
    hass: HomeAssistant, device_id: str
) -> list[dict[str, Any]]:
    """Return a list of triggers for a Loxone device."""
    device_registry = dr.async_get(hass)
    device = device_registry.async_get(device_id)
    if device is None:
        return []

    is_loxone = any(domain == DOMAIN for domain, _ in device.identifiers)
    if not is_loxone:
        return []

    # Don't expose triggers on the Miniserver hub device itself
    if device.via_device_id is None and device.model and "Miniserver" in device.model:
        return []

    return [
        {
            CONF_PLATFORM: "device",
            CONF_DEVICE_ID: device_id,
            CONF_DOMAIN: DOMAIN,
            CONF_TYPE: "state_change",
        }
    ]


async def async_attach_trigger(
    hass: HomeAssistant,
    config: ConfigType,
    action: TriggerActionType,
    trigger_info: TriggerInfo,
) -> CALLBACK_TYPE:
    """Attach a trigger to fire on loxone_state_change events for this device."""
    device_registry = dr.async_get(hass)
    device = device_registry.async_get(config[CONF_DEVICE_ID])
    if device is None:
        raise ValueError(f"Device {config[CONF_DEVICE_ID]} not found")

    uuid = None
    for domain, identifier in device.identifiers:
        if domain == DOMAIN:
            uuid = identifier
            break

    event_data: dict[str, Any] = {"device_id": config[CONF_DEVICE_ID]}
    if uuid:
        event_data["uuid"] = uuid

    event_config = event_trigger.TRIGGER_SCHEMA(
        {
            event_trigger.CONF_PLATFORM: "event",
            event_trigger.CONF_EVENT_TYPE: EVENT_LOXONE_STATE_CHANGE,
            event_trigger.CONF_EVENT_DATA: event_data,
        }
    )
    return await event_trigger.async_attach_trigger(
        hass, event_config, action, trigger_info, platform_type="device"
    )
