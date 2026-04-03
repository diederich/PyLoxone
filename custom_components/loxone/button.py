"""
Loxone Buttons

For more details about this component, please refer to the documentation at
https://github.com/JoDehli/PyLoxone
"""

import logging
from functools import cached_property
from typing import final

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from . import LoxoneEntity
from .const import DOMAIN, SENDDOMAIN
from .helpers import add_room_and_cat_to_value_values, get_all
from .miniserver import get_miniserver_from_hass

_LOGGER = logging.getLogger(__name__)

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up entry."""
    miniserver = get_miniserver_from_hass(hass)
    loxconfig = miniserver.lox_config.json
    entities = []

    for button_entity in get_all(loxconfig, ["Pushbutton"]):
        button_entity = add_room_and_cat_to_value_values(loxconfig, button_entity)
        entities.append(LoxoneButton(**button_entity))

    async_add_entities(entities)


class LoxoneButton(LoxoneEntity, ButtonEntity):
    """Representation of a Loxone pushbutton."""

    __last_pressed_isoformat: str | None = None
    _attr_has_entity_name = True
    _attr_name = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._attr_name = None
        self._attr_unique_id = self.uuidAction

    # noinspection PyFinal
    @cached_property
    @final
    def state(self) -> str | None:
        """Return the entity state."""
        return self.__last_pressed_isoformat

    def __set_state(self, state: str | None) -> None:
        """Set the entity state."""
        # Invalidate the cache of the cached property
        self.__dict__.pop("state", None)
        self.__last_pressed_isoformat = state

    async def event_handler(self, event):
        request_update = False
        if "active" in self.states:
            if self.states["active"] in event:
                active = event[self.states["active"]]
                new_state = True if active == 1.0 else False
                if new_state != self._attr_state:
                    self.__set_state(dt_util.utcnow().isoformat())
                    request_update = True
        if request_update:
            self.async_schedule_update_ha_state()

    @cached_property
    def unique_id(self) -> str:
        """Return a unique ID."""
        return self._attr_unique_id

    def press(self, **kwargs):
        """Press the button."""
        self.hass.bus.fire(SENDDOMAIN, dict(uuid=self.uuidAction, value="pulse"))
        self.schedule_update_ha_state()

    @property
    def extra_state_attributes(self):
        """Return device specific state attributes."""
        return {
            **self._attr_extra_state_attributes,
            "state_uuid": self.states["active"],
            "device_type": self.type,
        }

