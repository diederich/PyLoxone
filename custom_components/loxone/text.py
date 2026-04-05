"""Loxone TextInput platform.

Exposes Loxone TextInput controls as HA TextEntity (read/write).
"""

import logging

from homeassistant.components.text import TextEntity
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
    """Set up Loxone TextInput entities."""
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
        entities.append(LoxoneText(**text_entity))

    async_add_entities(entities)


class LoxoneText(LoxoneEntity, TextEntity):
    """Representation of a Loxone TextInput control."""

    _attr_has_entity_name = True
    _attr_name = None

    def __init__(self, **kwargs):
        """Initialize the LoxoneText."""
        super().__init__(**kwargs)
        self._attr_name = None
        self._attr_native_value = ""
        self.type = "TextInput"

    async def event_handler(self, e):
        """Handle a state update message from Loxone."""
        if self.states["text"] in e:
            self._attr_native_value = str(e[self.states["text"]])
            self.async_schedule_update_ha_state()

    async def async_set_value(self, value: str) -> None:
        """Set new value."""
        self.hass.bus.async_fire(SENDDOMAIN, {"uuid": self.uuidAction, "value": value})
        self.async_schedule_update_ha_state()

    @property
    def extra_state_attributes(self):
        """Return extra state attributes for this entity."""
        return {
            **self._attr_extra_state_attributes,
            "state_uuid": self.states["text"],
            "device_type": self.type,
        }
