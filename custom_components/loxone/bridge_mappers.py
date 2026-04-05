"""Concrete BridgeMapper implementations for each Loxone control type.

Each mapper knows how to translate between an HA entity's state/attributes
and the Loxone control's wire protocol (commands sent to ``uuidAction``,
state updates received from ``states`` UUIDs).
"""

from __future__ import annotations

import ast
import logging
from typing import Any

from homeassistant.const import STATE_ON
from homeassistant.core import HomeAssistant, State
import homeassistant.util.color as color_util

from .bridge_types import BridgeMapper, DeviceBridge
from .helpers import hass_to_lox, lox_to_hass

_LOGGER = logging.getLogger(__name__)

_BINARY_TRUE = frozenset({"on", "true", "1", "yes", "home", "open"})


def _loxone_to_bool(value: Any) -> bool:
    """Return loxone to bool."""
    try:
        return float(value) >= 1.0
    except (ValueError, TypeError):
        return str(value).lower() in _BINARY_TRUE


# ---------------------------------------------------------------------------
# ColorPickerV2 — bidirectional, supports HS color + color temp + brightness
# ---------------------------------------------------------------------------


class ColorPickerMapper(BridgeMapper):
    """Maps HA light <-> Loxone ColorPickerV2 sub-control.

    Handles all HA color modes (HS, RGB, RGBW, RGBWW, XY) by using the
    ``hs_color`` attribute that HA always derives, regardless of native mode.

    Wire protocol:
      - ``hsv(h, s, brightness_0_100)`` for any color mode
      - ``temp(brightness_0_100, kelvin)`` for color temperature mode
      - ``On`` / ``Off`` for simple on/off
    """

    @property
    def expose_supported(self) -> bool:
        """Return the expose supported."""
        return True

    @property
    def subscribe_supported(self) -> bool:
        """Return the subscribe supported."""
        return bool(self.bridge.loxone_states.get("color"))

    @property
    def subscribe_uuids(self) -> set[str]:
        """Return the subscribe uuids."""
        color_uuid = self.bridge.loxone_states.get("color")
        return {color_uuid} if color_uuid else set()

    def ha_state_to_command(self, state: State) -> tuple[str, Any] | None:
        """Ha state to command."""
        if state.state == "off":
            return (self.bridge.loxone_uuid, "Off")

        brightness = state.attributes.get("brightness")
        if brightness is None:
            return (self.bridge.loxone_uuid, "On")

        lox_br = hass_to_lox(brightness)
        color_mode = state.attributes.get("color_mode")

        if color_mode == "color_temp":
            kelvin = state.attributes.get("color_temp_kelvin", 3000)
            return (self.bridge.loxone_uuid, f"temp({lox_br:.1f},{kelvin})")

        # HA provides hs_color for all color modes (hs, rgb, rgbw, rgbww, xy)
        hs = state.attributes.get("hs_color")
        if hs is not None:
            r, g, b = color_util.color_hs_to_RGB(hs[0], hs[1])
            h, s, _v = color_util.color_RGB_to_hsv(r, g, b)
            return (self.bridge.loxone_uuid, f"hsv({h},{s},{lox_br:.1f})")

        return (self.bridge.loxone_uuid, f"temp({lox_br:.1f},3000)")

    async def loxone_value_to_ha(self, hass: HomeAssistant, uuid: str, value: Any) -> None:
        """Loxone value to ha."""
        entity_id = self.bridge.entity_id
        color = str(value)

        if color.startswith("hsv"):
            tup = ast.literal_eval(color.replace("hsv", ""))
            h, s, v = tup[0], tup[1], tup[2]
            brightness = round(lox_to_hass(v))
            if brightness <= 0:
                await hass.services.async_call("light", "turn_off", {"entity_id": entity_id})
            else:
                r, g, b = color_util.color_hsv_to_RGB(h, s, 100)
                hs = color_util.color_RGB_to_hs(r, g, b)
                await hass.services.async_call(
                    "light",
                    "turn_on",
                    {
                        "entity_id": entity_id,
                        "brightness": brightness,
                        "hs_color": list(hs),
                    },
                )
        elif color.startswith("temp"):
            tup = ast.literal_eval(color.replace("temp", ""))
            br_lox, kelvin = tup[0], tup[1]
            brightness = round(lox_to_hass(br_lox))
            if brightness <= 0:
                await hass.services.async_call("light", "turn_off", {"entity_id": entity_id})
            else:
                await hass.services.async_call(
                    "light",
                    "turn_on",
                    {
                        "entity_id": entity_id,
                        "brightness": brightness,
                        "color_temp_kelvin": kelvin,
                    },
                )
        else:
            on = _loxone_to_bool(value)
            svc = "turn_on" if on else "turn_off"
            await hass.services.async_call("light", svc, {"entity_id": entity_id})

    @property
    def description(self) -> str:
        """Return the description."""
        return "Color light bridge: brightness + color + color temp, bidirectional"


# ---------------------------------------------------------------------------
# Dimmer — bidirectional, brightness 0-255 <-> 0-100
# ---------------------------------------------------------------------------


class DimmerMapper(BridgeMapper):
    """Maps HA light <-> Loxone Dimmer sub-control.

    Brightness is scaled: HA 0-255 <-> Loxone 0-100.
    """

    @property
    def expose_supported(self) -> bool:
        """Return the expose supported."""
        return True

    @property
    def subscribe_supported(self) -> bool:
        """Return the subscribe supported."""
        return bool(self.bridge.loxone_states.get("position"))

    @property
    def subscribe_uuids(self) -> set[str]:
        """Return the subscribe uuids."""
        pos_uuid = self.bridge.loxone_states.get("position")
        return {pos_uuid} if pos_uuid else set()

    def ha_state_to_command(self, state: State) -> tuple[str, Any] | None:
        """Ha state to command."""
        if state.state == "off":
            return (self.bridge.loxone_uuid, "Off")

        brightness = state.attributes.get("brightness")
        if brightness is not None:
            return (self.bridge.loxone_uuid, round(hass_to_lox(brightness)))

        return (self.bridge.loxone_uuid, "On")

    async def loxone_value_to_ha(self, hass: HomeAssistant, uuid: str, value: Any) -> None:
        """Loxone value to ha."""
        entity_id = self.bridge.entity_id
        try:
            fval = float(value)
        except (ValueError, TypeError):
            on = _loxone_to_bool(value)
            svc = "turn_on" if on else "turn_off"
            await hass.services.async_call("light", svc, {"entity_id": entity_id})
            return

        if fval <= 0:
            await hass.services.async_call("light", "turn_off", {"entity_id": entity_id})
        else:
            brightness = min(255, max(1, round(lox_to_hass(fval))))
            await hass.services.async_call(
                "light",
                "turn_on",
                {"entity_id": entity_id, "brightness": brightness},
            )

    @property
    def description(self) -> str:
        """Return the description."""
        return "Dimmer bridge: brightness + on/off, bidirectional"


# ---------------------------------------------------------------------------
# Switch (light circuit) — bidirectional on/off
# ---------------------------------------------------------------------------


class LightSwitchMapper(BridgeMapper):
    """Maps HA light <-> Loxone Switch sub-control (on/off)."""

    @property
    def expose_supported(self) -> bool:
        """Return the expose supported."""
        return True

    @property
    def subscribe_supported(self) -> bool:
        """Return the subscribe supported."""
        return bool(self.bridge.loxone_states.get("active"))

    @property
    def subscribe_uuids(self) -> set[str]:
        """Return the subscribe uuids."""
        active_uuid = self.bridge.loxone_states.get("active")
        return {active_uuid} if active_uuid else set()

    def ha_state_to_command(self, state: State) -> tuple[str, Any] | None:
        """Ha state to command."""
        on = state.state == STATE_ON
        return (self.bridge.loxone_uuid, "on" if on else "off")

    async def loxone_value_to_ha(self, hass: HomeAssistant, uuid: str, value: Any) -> None:
        """Loxone value to ha."""
        entity_id = self.bridge.entity_id
        svc = "turn_on" if _loxone_to_bool(value) else "turn_off"
        await hass.services.async_call("light", svc, {"entity_id": entity_id})

    @property
    def description(self) -> str:
        """Return the description."""
        return "Switch bridge: on/off, bidirectional"


# ---------------------------------------------------------------------------
# Switch (generic, for HA switch domain) — bidirectional on/off
# ---------------------------------------------------------------------------


class SwitchMapper(BridgeMapper):
    """Maps HA switch <-> Loxone Switch control."""

    @property
    def expose_supported(self) -> bool:
        """Return the expose supported."""
        return True

    @property
    def subscribe_supported(self) -> bool:
        """Return the subscribe supported."""
        return bool(self.bridge.loxone_states.get("active"))

    @property
    def subscribe_uuids(self) -> set[str]:
        """Return the subscribe uuids."""
        active_uuid = self.bridge.loxone_states.get("active")
        return {active_uuid} if active_uuid else set()

    def ha_state_to_command(self, state: State) -> tuple[str, Any] | None:
        """Ha state to command."""
        on = state.state == STATE_ON
        return (self.bridge.loxone_uuid, 1 if on else 0)

    async def loxone_value_to_ha(self, hass: HomeAssistant, uuid: str, value: Any) -> None:
        """Loxone value to ha."""
        entity_id = self.bridge.entity_id
        svc = "turn_on" if _loxone_to_bool(value) else "turn_off"
        await hass.services.async_call("switch", svc, {"entity_id": entity_id})

    @property
    def description(self) -> str:
        """Return the description."""
        return "Switch bridge: on/off, bidirectional"


# ---------------------------------------------------------------------------
# Expose-only: binary_sensor -> Switch VI (sends 1/0)
# ---------------------------------------------------------------------------


class BinarySensorExposeMapper(BridgeMapper):
    """Maps HA binary_sensor -> Loxone Switch VI (expose only)."""

    @property
    def expose_supported(self) -> bool:
        """Return the expose supported."""
        return True

    @property
    def subscribe_supported(self) -> bool:
        """Return the subscribe supported."""
        return False

    def ha_state_to_command(self, state: State) -> tuple[str, Any] | None:
        """Ha state to command."""
        on = state.state == STATE_ON
        return (self.bridge.loxone_uuid, 1 if on else 0)

    @property
    def description(self) -> str:
        """Return the description."""
        return "Expose binary state to Loxone (on/off -> 1/0)"


# ---------------------------------------------------------------------------
# Expose-only: sensor -> Slider VI (sends float)
# ---------------------------------------------------------------------------


class AnalogExposeMapper(BridgeMapper):
    """Maps HA sensor -> Loxone Slider VI (expose only)."""

    @property
    def expose_supported(self) -> bool:
        """Return the expose supported."""
        return True

    @property
    def subscribe_supported(self) -> bool:
        """Return the subscribe supported."""
        return False

    def ha_state_to_command(self, state: State) -> tuple[str, Any] | None:
        """Ha state to command."""
        try:
            return (self.bridge.loxone_uuid, float(state.state))
        except (ValueError, TypeError):
            _LOGGER.warning("Cannot convert '%s' to float for analog bridge", state.state)
            return None

    @property
    def description(self) -> str:
        """Return the description."""
        return "Expose analog value to Loxone"


# ---------------------------------------------------------------------------
# Number / input_number -> Slider VI (bidirectional float)
# ---------------------------------------------------------------------------


class NumberMapper(BridgeMapper):
    """Maps HA number/input_number <-> Loxone Slider VI (bidirectional).

    Sends the raw float value both ways — no scaling. Both HA number and
    Loxone Slider operate in arbitrary ranges.
    """

    @property
    def expose_supported(self) -> bool:
        """Return the expose supported."""
        return True

    @property
    def subscribe_supported(self) -> bool:
        """Return the subscribe supported."""
        return bool(self.bridge.loxone_states.get("value"))

    @property
    def subscribe_uuids(self) -> set[str]:
        """Return the subscribe uuids."""
        value_uuid = self.bridge.loxone_states.get("value")
        return {value_uuid} if value_uuid else set()

    def ha_state_to_command(self, state: State) -> tuple[str, Any] | None:
        """Ha state to command."""
        try:
            return (self.bridge.loxone_uuid, float(state.state))
        except (ValueError, TypeError):
            _LOGGER.warning("Cannot convert '%s' to float for number bridge", state.state)
            return None

    async def loxone_value_to_ha(self, hass: HomeAssistant, uuid: str, value: Any) -> None:
        """Loxone value to ha."""
        entity_id = self.bridge.entity_id
        domain = entity_id.split(".")[0]
        try:
            fval = float(value)
        except (ValueError, TypeError):
            _LOGGER.warning(
                "Cannot convert Loxone value '%s' to float for number bridge",
                value,
            )
            return
        await hass.services.async_call(domain, "set_value", {"entity_id": entity_id, "value": fval})

    @property
    def description(self) -> str:
        """Return the description."""
        return "Number bridge: analog value, bidirectional"


# ---------------------------------------------------------------------------
# input_boolean -> Switch VI (bidirectional on/off)
# ---------------------------------------------------------------------------


class InputBooleanMapper(BridgeMapper):
    """Maps HA input_boolean <-> Loxone Switch VI (bidirectional)."""

    @property
    def expose_supported(self) -> bool:
        """Return the expose supported."""
        return True

    @property
    def subscribe_supported(self) -> bool:
        """Return the subscribe supported."""
        return bool(self.bridge.loxone_states.get("active"))

    @property
    def subscribe_uuids(self) -> set[str]:
        """Return the subscribe uuids."""
        active_uuid = self.bridge.loxone_states.get("active")
        return {active_uuid} if active_uuid else set()

    def ha_state_to_command(self, state: State) -> tuple[str, Any] | None:
        """Ha state to command."""
        on = state.state == STATE_ON
        return (self.bridge.loxone_uuid, 1 if on else 0)

    async def loxone_value_to_ha(self, hass: HomeAssistant, uuid: str, value: Any) -> None:
        """Loxone value to ha."""
        entity_id = self.bridge.entity_id
        svc = "turn_on" if _loxone_to_bool(value) else "turn_off"
        await hass.services.async_call("input_boolean", svc, {"entity_id": entity_id})

    @property
    def description(self) -> str:
        """Return the description."""
        return "Input boolean bridge: on/off, bidirectional"


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

_LIGHT_CIRCUIT_TYPES = {"Dimmer", "EIBDimmer", "Switch", "ColorPickerV2"}

_SUPPORTED_DOMAINS = frozenset(
    {
        "light",
        "switch",
        "binary_sensor",
        "sensor",
        "number",
        "input_number",
        "input_boolean",
    }
)


def get_mapper(bridge: DeviceBridge, entity_domain: str) -> BridgeMapper:
    """Select the right mapper for a bridge based on HA domain + Loxone type."""
    lox_type = bridge.loxone_type

    if entity_domain == "binary_sensor":
        return BinarySensorExposeMapper(bridge)

    if entity_domain == "sensor":
        return AnalogExposeMapper(bridge)

    if entity_domain == "light":
        if lox_type == "ColorPickerV2":
            return ColorPickerMapper(bridge)
        if lox_type in ("Dimmer", "EIBDimmer"):
            return DimmerMapper(bridge)
        if lox_type == "Switch":
            return LightSwitchMapper(bridge)

    if entity_domain == "switch":
        return SwitchMapper(bridge)

    if entity_domain in ("number", "input_number"):
        return NumberMapper(bridge)

    if entity_domain == "input_boolean":
        return InputBooleanMapper(bridge)

    raise ValueError(f"No mapper for entity domain '{entity_domain}' with Loxone type '{lox_type}'")
