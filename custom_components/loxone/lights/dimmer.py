"""Loxone integration — dimmer."""

from functools import cached_property

from homeassistant.components.light import ATTR_BRIGHTNESS, ColorMode, LightEntity
from homeassistant.const import STATE_UNKNOWN
from homeassistant.helpers.entity import DeviceInfo

from .. import LoxoneEntity
from ..const import DOMAIN, SENDDOMAIN
from ..helpers import hass_to_lox, lox2hass_mapped, lox_to_hass
from ..miniserver import get_miniserver_from_hass


class LoxoneDimmer(LoxoneEntity, LightEntity):
    """Representation of a Loxone Dimmer."""

    _attr_has_entity_name = True
    _attr_color_mode = ColorMode.BRIGHTNESS
    _attr_supported_color_modes = {ColorMode.BRIGHTNESS}

    def __init__(self, **kwargs):
        """Initialize the LoxoneDimmer."""
        super().__init__(**kwargs)
        self._attr_is_on = STATE_UNKNOWN
        self._attr_unique_id = self.uuidAction
        self._position = 0.0
        self._step = 1
        self._min_uuid = kwargs.get("states", {}).get("min", None)
        self._max_uuid = kwargs.get("states", {}).get("max", None)
        self._position_uuid = kwargs.get("states", {}).get("position", None)
        self._step_uuid = kwargs.get("states", {}).get("step", None)
        self._min = STATE_UNKNOWN
        self._max = STATE_UNKNOWN
        self._async_add_devices = kwargs["async_add_devices"]
        self._light_controller_id = kwargs.get("lightcontroller_id")
        self._light_controller_name = kwargs.get("lightcontroller_name")

        if self._light_controller_id:
            self.type = "LightControllerV2"
            self._attr_name = self._loxone_name
        else:
            self.type = "Dimmer"
            self._attr_name = None

        state_attributes = {
            "device_type": self.type,
        }
        if self._light_controller_name:
            state_attributes.update({"light_controller": self._light_controller_name})

        self._attr_extra_state_attributes.update(state_attributes)

    @property
    def device_info(self) -> DeviceInfo | None:
        """Return device information."""
        if self._light_controller_id:
            info = DeviceInfo(
                identifiers={(DOMAIN, self._light_controller_id)},
                name=self._light_controller_name,
                manufacturer="Loxone",
                model=self.type,
                suggested_area=getattr(self, "room", None),
            )
            try:
                serial = get_miniserver_from_hass(self.hass).serial
                if serial:
                    info["via_device"] = (DOMAIN, serial)
            except (KeyError, AttributeError):
                pass
            return info
        return super().device_info

    @cached_property
    def unique_id(self) -> str:
        """Return a unique ID."""
        return self._attr_unique_id

    async def async_turn_on(self, **kwargs) -> None:
        """Turn on asynchronously."""
        if ATTR_BRIGHTNESS in kwargs:
            self.hass.bus.async_fire(
                SENDDOMAIN,
                {
                    "uuid": self.uuidAction,
                    "value": round(hass_to_lox(kwargs[ATTR_BRIGHTNESS])),
                },
            )
        else:
            self.hass.bus.async_fire(SENDDOMAIN, {"uuid": self.uuidAction, "value": "on"})
        self.async_schedule_update_ha_state()

    async def async_turn_off(self, **kwargs) -> None:
        """Turn off asynchronously."""
        self.hass.bus.async_fire(SENDDOMAIN, {"uuid": self.uuidAction, "value": "off"})
        self.async_schedule_update_ha_state()

    async def event_handler(self, e):
        """Handle a state update message from Loxone."""
        request_update = False
        if self._min_uuid in e:
            self._min = e[self._min_uuid]
            request_update = True

        if self._max_uuid in e:
            self._max = e[self._max_uuid]
            request_update = True

        if self._step_uuid in e:
            self._step = e[self._step_uuid]
            request_update = True

        if self._position_uuid in e:
            if self._min is not None and self._max is not None and self._min != "unknown" and self._max != "unknown":
                self._attr_brightness = lox2hass_mapped(e[self._position_uuid], self._min, self._max)
            else:
                self._attr_brightness = lox_to_hass(e[self._position_uuid])
            request_update = True

        self._attr_is_on = bool(self._attr_brightness and self._attr_brightness > 0)

        if request_update:
            self.async_schedule_update_ha_state()

    @cached_property
    def icon(self):
        """Return the sensor icon."""
        return "mdi:brightness-6"


class EIBDimmer(LoxoneDimmer):
    """Represent eib dimmer."""

    def __init__(self, **kwargs):
        """Initialize the EIBDimmer."""
        super().__init__(**kwargs)
        if self._light_controller_id:
            self.type = "LightControllerV2"
        else:
            self.type = "EIBDimmer"

    @cached_property
    def icon(self):
        """Return the sensor icon."""
        return "mdi:brightness-4"
