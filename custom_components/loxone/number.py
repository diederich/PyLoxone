"""
Loxone Numbers

For more details about this component, please refer to the documentation at
https://github.com/JoDehli/PyLoxone
"""

import logging

from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_UNKNOWN
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import LoxoneEntity
from .const import SENDDOMAIN
from .coordinator import LoxoneCoordinator
from .helpers import add_room_and_cat_to_value_values, get_all

_LOGGER = logging.getLogger(__name__)

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up entry."""
    coordinator: LoxoneCoordinator = config_entry.runtime_data
    loxconfig = coordinator.api.structure_file
    entities = []

    for number_entity in get_all(loxconfig, ["Slider"]):
        number_entity = add_room_and_cat_to_value_values(loxconfig, number_entity)
        number_entity["coordinator"] = coordinator
        new_number = LoxoneNumber(**number_entity)
        entities.append(new_number)

    async_add_entities(entities)


class LoxoneNumber(LoxoneEntity, NumberEntity):
    """Representation of a Loxone number (Slider control)."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_assumed_state = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._attr_name = None
        self._state = STATE_UNKNOWN
        self._attr_native_max_value = kwargs["details"]["max"]
        self._attr_native_min_value = kwargs["details"]["min"]
        self._attr_native_step = kwargs["details"]["step"]
        self.type = "Slider"

    @property
    def native_value(self):
        return self._state

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
            "state_uuid": self.states["value"],
            "device_type": self.type,
            "platform": "loxone",
        }

    async def async_set_native_value(self, value: float):
        """Set new value."""
        self.hass.bus.async_fire(
            SENDDOMAIN, dict(uuid=self.uuidAction, value="{}".format(value))
        )
        self.schedule_update_ha_state()
