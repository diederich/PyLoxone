"""Loxone integration — colorpickers."""

import ast
from functools import cached_property
import logging

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_COLOR_TEMP_KELVIN,
    ATTR_HS_COLOR,
    ColorMode,
    LightEntity,
)
from homeassistant.helpers.entity import DeviceInfo
import homeassistant.util.color as color_util

from .. import LoxoneEntity
from ..const import DOMAIN, SENDDOMAIN
from ..helpers import hass_to_lox, lox_to_hass
from ..miniserver import get_miniserver_from_hass

_LOGGER = logging.getLogger(__name__)


class TunableWhiteLight(LoxoneEntity, LightEntity):
    """Represent tunable white light."""

    _attr_has_entity_name = True
    _attr_max_color_temp_kelvin = 6500
    _attr_min_color_temp_kelvin = 2000

    _attr_supported_color_modes: set[ColorMode] = {ColorMode.COLOR_TEMP}

    def __init__(self, **kwargs):
        """Initialize the TunableWhiteLight."""
        super().__init__(**kwargs)
        self._attr_unique_id = self.uuidAction
        self._attr_color_mode = ColorMode.UNKNOWN
        self._color_uuid = kwargs.get("states", {}).get("color", None)

        self._async_add_devices = kwargs["async_add_devices"]
        self._light_controller_id = kwargs.get("lightcontroller_id")
        self._light_controller_name = kwargs.get("lightcontroller_name")

        if self._light_controller_id:
            self.type = "LightControllerV2"
            self._attr_name = self._loxone_name
        else:
            self.type = "ColorPickerV2"
            self._attr_name = None

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

    @property
    def is_on(self) -> bool:
        """Return whether is on."""
        return bool(self._attr_brightness and self._attr_brightness > 0)

    async def async_turn_off(self) -> None:
        """Turn off asynchronously."""
        self.hass.bus.async_fire(SENDDOMAIN, {"uuid": self.uuidAction, "value": "setBrightness/0"})
        self.async_schedule_update_ha_state()

    async def async_turn_on(self, **kwargs) -> None:
        """Turn on asynchronously."""
        if ATTR_COLOR_TEMP_KELVIN in kwargs:
            self._attr_color_temp_kelvin = kwargs[ATTR_COLOR_TEMP_KELVIN]
            self.hass.bus.async_fire(
                SENDDOMAIN,
                {
                    "uuid": self.uuidAction,
                    "value": f"temp({hass_to_lox(self._attr_brightness)},{self._attr_color_temp_kelvin})",
                },
            )
        elif ATTR_BRIGHTNESS in kwargs:
            self._attr_brightness = kwargs[ATTR_BRIGHTNESS]
            self.hass.bus.async_fire(
                SENDDOMAIN,
                {
                    "uuid": self.uuidAction,
                    "value": f"temp({hass_to_lox(self._attr_brightness)},{self._attr_color_temp_kelvin})",
                },
            )
        else:
            self.hass.bus.async_fire(SENDDOMAIN, {"uuid": self.uuidAction, "value": "On"})

    async def event_handler(self, e):
        """Handle a state update message from Loxone."""
        request_update = False
        if self._color_uuid in e:
            _color = e[self._color_uuid]

            if _color.startswith("temp"):
                _color = _color.replace("temp", "")
                _color = ast.literal_eval(_color)
                self._attr_color_mode = ColorMode.COLOR_TEMP
                self._attr_color_temp_kelvin = _color[1]
                self._attr_brightness = round(255 * _color[0] / 100)
                request_update = True
            else:
                _LOGGER.error("Not handled command -> %s", _color)

        if request_update:
            self.async_schedule_update_ha_state()

    @cached_property
    def icon(self):
        """Return the sensor icon."""
        return "mdi:lightbulb"


class RGBColorPicker(LoxoneEntity, LightEntity):
    """Represent rgb color picker."""

    _attr_max_color_temp_kelvin = 6500
    _attr_min_color_temp_kelvin = 2000

    _attr_supported_color_modes: set[ColorMode] = {
        ColorMode.COLOR_TEMP,
        ColorMode.HS,
    }

    _attr_has_entity_name = True

    def __init__(self, **kwargs):
        """Initialize the RGBColorPicker."""
        super().__init__(**kwargs)
        self._attr_unique_id = self.uuidAction
        self._attr_color_mode = ColorMode.UNKNOWN
        self._color_uuid = kwargs.get("states", {}).get("color", None)

        self._async_add_devices = kwargs["async_add_devices"]
        self._light_controller_id = kwargs.get("lightcontroller_id")
        self._light_controller_name = kwargs.get("lightcontroller_name")

        if self._light_controller_id:
            self.type = "LightControllerV2"
            self._attr_name = self._loxone_name
        else:
            self.type = "ColorPickerV2"
            self._attr_name = None

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

    @property
    def is_on(self) -> bool:
        """Return whether is on."""
        return bool(self._attr_brightness and self._attr_brightness > 0)

    async def async_turn_off(self) -> None:
        """Turn off asynchronously."""
        self.hass.bus.async_fire(SENDDOMAIN, {"uuid": self.uuidAction, "value": "setBrightness/0"})
        self.async_schedule_update_ha_state()

    async def async_turn_on(self, **kwargs) -> None:
        """Turn on asynchronously."""
        brightness = kwargs.get(ATTR_BRIGHTNESS, self._attr_brightness) or 255
        hs = self._attr_hs_color or (0, 0)

        if ATTR_HS_COLOR in kwargs:
            r, g, b = color_util.color_hs_to_RGB(kwargs[ATTR_HS_COLOR][0], kwargs[ATTR_HS_COLOR][1])
            h, s, _v = color_util.color_RGB_to_hsv(r, g, b)
            self.hass.bus.async_fire(
                SENDDOMAIN,
                {
                    "uuid": self.uuidAction,
                    "value": f"hsv({h},{s},{hass_to_lox(brightness)})",
                },
            )
        elif ATTR_COLOR_TEMP_KELVIN in kwargs:
            self._attr_color_temp_kelvin = kwargs[ATTR_COLOR_TEMP_KELVIN]
            self.hass.bus.async_fire(
                SENDDOMAIN,
                {
                    "uuid": self.uuidAction,
                    "value": f"temp({hass_to_lox(brightness)},{self._attr_color_temp_kelvin})",
                },
            )

        elif ATTR_BRIGHTNESS in kwargs:
            self._attr_brightness = kwargs[ATTR_BRIGHTNESS]
            if self._attr_color_mode == ColorMode.HS:
                self.hass.bus.async_fire(
                    SENDDOMAIN,
                    {
                        "uuid": self.uuidAction,
                        "value": f"hsv({hs[0]},{hs[1]},{hass_to_lox(self._attr_brightness)})",
                    },
                )
            elif self._attr_color_mode == ColorMode.COLOR_TEMP:
                self.hass.bus.async_fire(
                    SENDDOMAIN,
                    {
                        "uuid": self.uuidAction,
                        "value": f"temp({hass_to_lox(self._attr_brightness)},{self._attr_color_temp_kelvin})",
                    },
                )
        else:
            self.hass.bus.async_fire(SENDDOMAIN, {"uuid": self.uuidAction, "value": "On"})

    async def event_handler(self, e):
        """Handle a state update message from Loxone."""
        request_update = False
        if self._color_uuid in e:
            _color = e[self._color_uuid]

            if _color.startswith("hsv"):
                _color = _color.replace("hsv", "")
                _color = ast.literal_eval(_color)
                self._attr_color_mode = ColorMode.HS
                self._attr_hs_color = (_color[0], _color[1])
                self._attr_brightness = lox_to_hass(_color[2])
                request_update = True
            elif _color.startswith("temp"):
                _color = _color.replace("temp", "")
                _color = ast.literal_eval(_color)
                self._attr_color_mode = ColorMode.COLOR_TEMP
                self._attr_color_temp_kelvin = _color[1]
                self._attr_hs_color = None
                self._attr_brightness = round(255 * _color[0] / 100)
                request_update = True
            else:
                _LOGGER.error("Not handled command -> %s", _color)

        if request_update:
            self.async_schedule_update_ha_state()

    @cached_property
    def icon(self):
        """Return the sensor icon."""
        return "mdi:eyedropper-variant"


class LumiTech(RGBColorPicker):
    """Representation of a Loxone LumiTech Dimmer."""

    def __init__(self, **kwargs):
        """Initialize the LumiTech."""
        super().__init__(**kwargs)
        """Initialize the LumiTech."""
        if self._light_controller_id:
            self.type = "LightControllerV2"
        else:
            self.type = "LumiTech"
