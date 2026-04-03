"""
Loxone Switches

For more details about this component, please refer to the documentation at
https://github.com/JoDehli/PyLoxone
"""

import logging

from homeassistant.components.switch import SwitchEntity
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

    for switch_entity in get_all(loxconfig, ["Switch", "TimedSwitch", "Intercom"]):
        switch_entity = add_room_and_cat_to_value_values(loxconfig, switch_entity)
        switch_entity["coordinator"] = coordinator

        if switch_entity["type"] in ["Switch"]:
            new_switch = LoxoneSwitch(**switch_entity)
            entities.append(new_switch)

        elif switch_entity["type"] == "TimedSwitch":
            new_switch = LoxoneTimedSwitch(**switch_entity)
            entities.append(new_switch)

        elif switch_entity["type"] == "Intercom":
            if "subControls" in switch_entity:
                for sub_name in switch_entity["subControls"]:
                    subcontrol = switch_entity["subControls"][sub_name]

                    _ = subcontrol
                    _ = add_room_and_cat_to_value_values(loxconfig, _)
                    _.update(
                        {
                            "name": "{} - {}".format(
                                switch_entity["name"], subcontrol["name"]
                            ),
                            "coordinator": coordinator,
                        }
                    )

                    new_switch = LoxoneIntercomSubControl(**_)
                    entities.append(new_switch)

    async_add_entities(entities)


class LoxoneTimedSwitch(LoxoneEntity, SwitchEntity):
    """Representation of a Loxone timed switch."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_assumed_state = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._attr_name = None
        self._state = STATE_UNKNOWN
        self._delay_remain = 0.0
        self._delay_time_total = 0.0

        self._deactivation_delay = self.states.get("deactivationDelay", "")
        self._deactivation_delay_total = self.states.get("deactivationDelayTotal", "")
        self.type = "TimeSwitch"

    @property
    def is_on(self):
        """Return true if switch is on."""
        return self._state

    def turn_on(self, **kwargs):
        """Turn the switch on."""
        self.hass.bus.fire(SENDDOMAIN, dict(uuid=self.uuidAction, value="pulse"))
        self._state = True
        self.schedule_update_ha_state()

    def turn_off(self, **kwargs):
        """Turn the device off."""
        self.hass.bus.fire(SENDDOMAIN, dict(uuid=self.uuidAction, value="off"))
        self._state = False
        self.schedule_update_ha_state()

    async def event_handler(self, e):
        should_update = False
        if self._deactivation_delay in e:
            if e[self._deactivation_delay] == 0.0:
                self._state = False
            else:
                self._state = True

            self._delay_remain = int(e[self._deactivation_delay])
            should_update = True

        if self._deactivation_delay_total in e:
            self._delay_time_total = int(e[self._deactivation_delay_total])
            should_update = True

        if should_update:
            self.schedule_update_ha_state()

    @property
    def extra_state_attributes(self):
        """Return device specific state attributes.

        Implemented by platform classes.
        """
        state_dict = {
            **self._attr_extra_state_attributes,
            "device_type": self.type,
        }

        if self._state == 0.0:
            state_dict.update({"delay_time_total": str(self._delay_time_total)})

        else:
            state_dict.update(
                {
                    "delay": str(self._delay_remain),
                    "delay_time_total": str(self._delay_time_total),
                }
            )
        return state_dict


class LoxoneSwitch(LoxoneEntity, SwitchEntity):
    """Representation of a Loxone switch."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_assumed_state = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._attr_name = None
        self._state = STATE_UNKNOWN
        self.type = "Switch"

    @property
    def is_on(self):
        """Return true if switch is on."""
        return self._state

    def turn_on(self, **kwargs):
        """Turn the switch on."""
        if not self._state:
            self.hass.bus.fire(SENDDOMAIN, dict(uuid=self.uuidAction, value="On"))
            self._state = True
            self.schedule_update_ha_state()

    def turn_off(self, **kwargs):
        """Turn the device off."""
        if self._state:
            self.hass.bus.fire(SENDDOMAIN, dict(uuid=self.uuidAction, value="Off"))
            self._state = False
            self.schedule_update_ha_state()

    async def event_handler(self, event):
        if self.uuidAction in event or self.states["active"] in event:
            if self.states["active"] in event:
                self._state = event[self.states["active"]]
            self.schedule_update_ha_state()

    @property
    def extra_state_attributes(self):
        """Return device specific state attributes.

        Implemented by platform classes.
        """
        return {
            "uuid": self.uuidAction,
            "state_uuid": self.states["active"],
            "room": self.room,
            "category": self.cat,
            "device_type": self.type,
            "platform": "loxone",
        }


class LoxoneIntercomSubControl(LoxoneSwitch):
    def __init__(self, **kwargs):
        LoxoneSwitch.__init__(self, **kwargs)

        self.type = "IntercomSubControl"

    def turn_on(self, **kwargs):
        """Turn the switch on."""
        self.hass.bus.fire(SENDDOMAIN, dict(uuid=self.uuidAction, value="on"))
        self._state = True
        self.schedule_update_ha_state()

    @property
    def extra_state_attributes(self):
        """Return device specific state attributes.

        Implemented by platform classes.
        """
        return {
            "uuid": self.uuidAction,
            "state_uuid": self.states["active"],
            "room": self.room,
            "category": self.cat,
            "device_type": self.type,
            "platform": "loxone",
        }
