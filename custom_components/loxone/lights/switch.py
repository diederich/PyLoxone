from functools import cached_property
from typing import Any

from homeassistant.components.light import ColorMode, LightEntity
from homeassistant.const import STATE_UNKNOWN
from homeassistant.helpers.entity import DeviceInfo

from .. import LoxoneEntity
from ..const import DOMAIN, SENDDOMAIN


class LoxoneLightSwitch(LoxoneEntity, LightEntity):
    """Representation of a light switch."""

    _attr_has_entity_name = True
    _attr_color_mode = ColorMode.ONOFF
    _attr_supported_color_modes = {ColorMode.ONOFF}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._attr_is_on = STATE_UNKNOWN
        self._attr_unique_id = self.uuidAction
        self._async_add_devices = kwargs["async_add_devices"]
        self._light_controller_id = kwargs.get("lightcontroller_id", None)
        self._light_controller_name = kwargs.get("lightcontroller_name", None)

        if self._light_controller_id:
            self.type = "LightControllerV2"
            self._attr_name = self._loxone_name
        else:
            self.type = "Light"
            self._attr_name = None

        state_attributes = {
            "device_type": self.type,
        }
        if self._light_controller_name:
            state_attributes.update({"light_controller": self._light_controller_name})

        self._attr_extra_state_attributes.update(state_attributes)

    @property
    def device_info(self) -> DeviceInfo | None:
        if self._light_controller_id:
            info = DeviceInfo(
                identifiers={(DOMAIN, self._light_controller_id)},
                name=self._light_controller_name,
                manufacturer="Loxone",
                model=self.type,
                suggested_area=getattr(self, "room", None),
            )
            try:
                from ..miniserver import get_miniserver_from_hass

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

    async def async_turn_on(self, **kwargs: Any) -> None:
        self.hass.bus.async_fire(SENDDOMAIN, dict(uuid=self.uuidAction, value="on"))
        self.async_schedule_update_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        self.hass.bus.async_fire(SENDDOMAIN, dict(uuid=self.uuidAction, value="off"))
        self.async_schedule_update_ha_state()

    async def event_handler(self, event):
        request_update = False
        if "active" in self.states:
            if self.states["active"] in event:
                active = event[self.states["active"]]
                new_state = True if active == 1.0 else False
                if new_state != self._attr_is_on:
                    self._attr_is_on = new_state
                    request_update = True

        if request_update:
            self.async_schedule_update_ha_state()
