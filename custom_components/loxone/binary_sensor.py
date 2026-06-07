"""Loxone binary sensor platform."""

from __future__ import annotations

from dataclasses import dataclass
from functools import cached_property
import logging
from typing import Literal, final

import voluptuous as vol

from homeassistant.components.binary_sensor import (
    PLATFORM_SCHEMA as BINARY_SENSOR_PLATFORM_SCHEMA,
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.const import (
    CONF_DEVICE_CLASS,
    CONF_NAME,
    CONF_VALUE_TEMPLATE,
    STATE_OFF,
    STATE_ON,
    STATE_UNKNOWN,
    EntityCategory,
)
from homeassistant.core import HomeAssistant
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import LoxoneConfigEntry, LoxoneEntity
from .const import CONF_ACTIONID, DOMAIN
from .coordinator import LoxoneCoordinator
from .helpers import add_room_and_cat_to_value_values, get_all
from .sensor import create_power_unit_device_info

_LOGGER = logging.getLogger(__name__)
NEW_SENSOR = "sensors"
DEFAULT_NAME = "Loxone Binary Sensor"

PARALLEL_UPDATES = 0

BINARY_SENSOR_PLATFORM_SCHEMA = BINARY_SENSOR_PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_ACTIONID): cv.string,
        vol.Required(CONF_NAME): cv.string,
        vol.Optional(CONF_DEVICE_CLASS): cv.string,
    }
)


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_devices: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up Loxone Sensor from yaml."""
    value_template = config.get(CONF_VALUE_TEMPLATE)
    if value_template is not None:
        value_template.hass = hass

    # Devices from yaml
    if config != {}:
        # Here setup all Sensors in Yaml-File
        new_sensor = LoxoneCustomBinarySensor(**config)
        async_add_devices([new_sensor])
        return True
    return True


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: LoxoneConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up entry."""
    coordinator: LoxoneCoordinator = config_entry.runtime_data
    miniserver = coordinator.miniserver
    loxconfig = coordinator.api.structure_file
    entities = []

    for sensor in get_all(loxconfig, "InfoOnlyDigital"):
        sensor = add_room_and_cat_to_value_values(loxconfig, sensor)
        sensor.update({"type": "digital", "coordinator": coordinator})
        entities.append(LoxoneDigitalSensor(**sensor))

    for sensor in get_all(loxconfig, "PresenceDetector"):
        sensor = add_room_and_cat_to_value_values(loxconfig, sensor)
        sensor.update({"type": "presence", "coordinator": coordinator})
        entities.append(LoxoneDigitalSensor(**sensor))

    for sensor in get_all(loxconfig, "SmokeAlarm"):
        sensor = add_room_and_cat_to_value_values(loxconfig, sensor)
        sensor.update({"type": "smoke", "coordinator": coordinator})
        entities.append(LoxoneDigitalSensor(**sensor))

    # Fuse + CP1..CP7 diagnostic binary sensors on each PowerUnit.
    # CP* are disabled by default (cryptic per-circuit protection state,
    # noisy in the UI); fuse is enabled because a blown main fuse is
    # actionable for the user.
    for power_unit in get_all(loxconfig, "PowerUnit"):
        states = power_unit.get("states") or {}
        entities.extend(
            LoxonePowerUnitBinarySensor(
                power_unit=power_unit,
                description=desc,
                coordinator=coordinator,
            )
            for desc in POWER_UNIT_BINARY_DESCRIPTIONS
            if desc.state_key in states
        )

    if miniserver and miniserver.serial:
        entities.append(LoxoneConnectivitySensor(coordinator, miniserver.serial))

    if miniserver:
        miniserver.listeners.append(
            async_dispatcher_connect(
                hass,
                miniserver.async_signal_new_device("sensors"),
                async_add_entities,
            )
        )
    async_add_entities(entities)


class LoxoneDigitalSensor(LoxoneEntity, BinarySensorEntity):
    """Representation of a binary Loxone device."""

    _attr_has_entity_name = True

    def __init__(self, **kwargs):
        """Initialize the LoxoneDigitalSensor."""
        super().__init__(**kwargs)
        self._attr_name = None
        self._from_loxone_config = False

        if "type" in kwargs and "room" in kwargs and "cat" in kwargs and hasattr(self, "states"):
            self._from_loxone_config = True
            if self.type == "smoke":
                self._state_uuid = self.states["areAlarmSignalsOff"]
            elif self.type == "presence" or "active" in self.states:
                self._state_uuid = self.states["active"]
        else:
            self._state_uuid = self.uuidAction

        self._state = STATE_UNKNOWN
        self._format = self._get_format(kwargs.get("details", {}).get("format", ""))
        self._parent_id = kwargs.get("parent_id")
        self._on_state = STATE_ON
        self._off_state = STATE_OFF
        self._attr_available = True

        if self._from_loxone_config:
            self._attr_extra_state_attributes.update(
                {
                    "state_uuid": self._state_uuid,
                    "device_type": self.type,
                }
            )
        else:
            self._attr_extra_state_attributes.update(
                {
                    "device_type": self.device_class,
                }
            )

    @property
    def icon(self):
        """Return the icon."""
        if self._from_loxone_config:
            if self.type == "presence":
                """Return the sensor icon."""
                return "mdi:motion-sensor"
            if self.type == "smoke":
                """Return the sensor icon."""
                return "mdi:smoke-detector"
            if self.type == "digital":
                """Return the sensor icon."""
                return "mdi:checkbox-blank-circle-outline"
        elif self.device_class:
            if self.device_class == "presence":
                """Return the sensor icon."""
                return "mdi:motion-sensor"
            if self.device_class == "smoke":
                """Return the sensor icon."""
                return "mdi:smoke-detector"
            if self.device_class == "digital":
                """Return the sensor icon."""
                return "mdi:checkbox-blank-circle-outline"
            """Return the sensor icon."""
        else:
            return "mdi:checkbox-blank-circle-outline"
        return None

    async def event_handler(self, e):
        """Handle a state update message from Loxone."""
        if self._state_uuid in e:
            self._state = e[self._state_uuid]
            if self._state == 1.0:
                self._state = self._on_state
            else:
                self._state = self._off_state
            self.async_schedule_update_ha_state()

    @final
    @property
    def state(self) -> Literal["on", "off"] | None:
        """Return the state of the binary sensor."""
        if (is_on := self.is_on) is None:
            return None
        return STATE_ON if is_on else STATE_OFF

    @property
    def is_on(self) -> bool | None:
        """Return true if sensor is on."""
        return self._state == self._on_state


class LoxoneCustomBinarySensor(LoxoneEntity, BinarySensorEntity):
    """Represent loxone custom binary sensor."""

    def __init__(self, **kwargs):
        """Initialize the LoxoneCustomBinarySensor."""
        super().__init__(**kwargs)
        self._state = STATE_UNKNOWN
        self._on_state = STATE_ON
        self._off_state = STATE_OFF

        self.uuidAction = kwargs.get("uuidAction", "")

        if "device_class" in kwargs:
            self._attr_device_class = kwargs["device_class"]

    @property
    def is_on(self) -> bool | None:
        """Return true if sensor is on."""
        return self._state == self._on_state

    @property
    def state(self) -> Literal["on", "off"] | None:
        """Return the state of the binary sensor."""
        if (is_on := self.is_on) is None:
            return None
        return STATE_ON if is_on else STATE_OFF

    async def event_handler(self, e):
        """Handle a state update message from Loxone."""
        if self.uuidAction in e:
            data = e[self.uuidAction]
            if data == 1.0:
                self._state = self._on_state
            else:
                self._state = self._off_state
            self.async_schedule_update_ha_state()


@dataclass(frozen=True, kw_only=True)
class PowerUnitBinarySensorDescription(BinarySensorEntityDescription):
    """Describes a binary sensor on a Loxone PowerUnit device.

    ``state_key`` is the key under PowerUnit ``states`` whose UUID this
    binary sensor subscribes to. ``on_when`` is the raw Loxone value that
    represents ``is_on=True`` — for fuse/CP* a value of 0 means "tripped"
    (problem), so on_when=0.0 lets the entity expose this as a HA problem.
    """

    state_key: str
    on_when: float = 0.0


# fuse = main fuse: 1=OK, 0=blown.  CP1..CP7 = per-circuit protection: same convention.
# Both map to BinarySensorDeviceClass.PROBLEM, where is_on=True == "there's a problem".
POWER_UNIT_BINARY_DESCRIPTIONS: tuple[PowerUnitBinarySensorDescription, ...] = (
    PowerUnitBinarySensorDescription(
        key="fuse",
        state_key="fuse",
        translation_key="powerunit_fuse",
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    *(
        PowerUnitBinarySensorDescription(
            key=f"cp{n}",
            state_key=f"CP{n}",
            translation_key=f"powerunit_cp{n}",
            device_class=BinarySensorDeviceClass.PROBLEM,
            entity_category=EntityCategory.DIAGNOSTIC,
            entity_registry_enabled_default=False,
        )
        for n in range(1, 8)
    ),
)


class LoxonePowerUnitBinarySensor(LoxoneEntity, BinarySensorEntity):
    """A binary sensor exposing one PowerUnit state on the parent device."""

    _attr_has_entity_name = True
    _attr_should_poll = False
    entity_description: PowerUnitBinarySensorDescription

    def __init__(
        self,
        *,
        power_unit: dict,
        description: PowerUnitBinarySensorDescription,
        coordinator: LoxoneCoordinator,
    ) -> None:
        """Initialize the LoxonePowerUnitBinarySensor."""
        super().__init__(coordinator=coordinator)
        self.entity_description = description
        self.uuidAction = power_unit["states"][description.state_key]
        self._power_unit_uuid = power_unit["uuidAction"]
        self._attr_unique_id = f"{self._power_unit_uuid}_{description.key}"
        self._attr_device_info = create_power_unit_device_info(power_unit)
        self._attr_is_on: bool | None = None

    @cached_property
    def unique_id(self) -> str:
        """Return a unique ID."""
        return self._attr_unique_id

    @property
    def is_on(self) -> bool | None:
        """Return true if the binary sensor is on (problem state)."""
        return self._attr_is_on

    async def event_handler(self, e):
        """Handle a state update message from Loxone."""
        if self.uuidAction in e:
            try:
                value = float(e[self.uuidAction])
            except (TypeError, ValueError):
                return
            self._attr_is_on = value == self.entity_description.on_when
            self.async_schedule_update_ha_state()


class LoxoneConnectivitySensor(CoordinatorEntity[LoxoneCoordinator], BinarySensorEntity):
    """Reports whether the Loxone Miniserver WebSocket is connected."""

    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_has_entity_name = True
    _attr_name = "Connection"

    def __init__(self, coordinator: LoxoneCoordinator, serial: str) -> None:
        """Initialize the LoxoneConnectivitySensor."""
        super().__init__(coordinator)
        self._serial = serial
        self._attr_unique_id = f"{serial}_connectivity"

    @property
    def is_on(self) -> bool:
        """Return whether is on."""
        return self.coordinator.last_update_success

    @property
    def available(self) -> bool:
        """Return whether the entity is available."""
        return True

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return DeviceInfo(identifiers={(DOMAIN, self._serial)})
