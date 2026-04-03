"""
Loxone Texts

For more details about this component, please refer to the documentation at
https://github.com/JoDehli/PyLoxone
"""

import logging

from homeassistant.components.text import TextEntity
from homeassistant.const import STATE_UNKNOWN
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import LoxoneConfigEntry, LoxoneEntity
from .const import SENDDOMAIN
from .coordinator import LoxoneCoordinator
from .helpers import add_room_and_cat_to_value_values, get_all

_LOGGER = logging.getLogger(__name__)

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: LoxoneConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up entry."""
    coordinator: LoxoneCoordinator = config_entry.runtime_data
    loxconfig = coordinator.api.structure_file
    entities = []

    for text_entity in get_all(loxconfig, ["TextInput"]):

        text_entity = add_room_and_cat_to_value_values(loxconfig, text_entity)
        text_entity.update(
            {
                "config_entry": config_entry,
                "coordinator": coordinator,
            }
        )
        new_text = LoxoneText(**text_entity)
        entities.append(new_text)

    async_add_entities(entities)


class LoxoneText(LoxoneEntity, TextEntity):
    """Representation of a Loxone text (TextInput control)."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_assumed_state = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._attr_name = None
        self._state = STATE_UNKNOWN
        self._native_value = ""
        self.type = "TextInput"

    @property
    def native_value(self):
        return self._native_value

    async def event_handler(self, e):
        if self.uuidAction in e:
            data = e[self.uuidAction]
            if isinstance(data, (list, dict)):
                data = str(data)
                if len(data) >= 255:
                    self._state = data[:255]
                else:
                    self._state = data
            else:
                self._state = data

            self.schedule_update_ha_state()

    @property
    def extra_state_attributes(self):
        """Return device specific state attributes.

        Implemented by platform classes.
        """
        return {
            **self._attr_extra_state_attributes,
            "state_uuid": self.states["text"],
            "device_type": self.type,
        }

    async def async_set_value(self, value: str):
        """Set new value."""
        self.hass.bus.async_fire(
            SENDDOMAIN, dict(uuid=self.uuidAction, value="{}".format(value))
        )
        self.schedule_update_ha_state()
