"""
Loxone Sensors

For more details about this component, please refer to the documentation at
https://github.com/JoDehli/PyLoxone
"""

import logging
import re
from collections.abc import Callable
from dataclasses import dataclass
from functools import cached_property
from typing import Any

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.components.sensor import (CONF_STATE_CLASS, PLATFORM_SCHEMA,
                                             SensorDeviceClass, SensorEntity,
                                             SensorEntityDescription,
                                             SensorStateClass)
from homeassistant.const import (CONF_DEVICE_CLASS, CONF_NAME,
                                 CONF_UNIT_OF_MEASUREMENT, CONF_VALUE_TEMPLATE,
                                 EntityCategory, LIGHT_LUX, PERCENTAGE,
                                 STATE_UNKNOWN, UnitOfEnergy, UnitOfPower,
                                 UnitOfSpeed, UnitOfTemperature,
                                 UnitOfVolume)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
import homeassistant.helpers.issue_registry as ir
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.util import dt as dt_util

from . import LoxoneConfigEntry, LoxoneEntity
from .const import CONF_ACTIONID, DOMAIN, SENDDOMAIN, THROTTLE_KEEP_ALIVE_TIME
from .coordinator import LoxoneCoordinator
from .helpers import add_room_and_cat_to_value_values, get_all
from .miniserver import MiniServer

NEW_SENSOR = "sensors"

_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = "Loxone Sensor"

PARALLEL_UPDATES = 0

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_ACTIONID): cv.string,
        vol.Optional(CONF_NAME): cv.string,
        vol.Optional(CONF_UNIT_OF_MEASUREMENT): cv.string,
        vol.Optional(CONF_DEVICE_CLASS): cv.string,
        vol.Optional(CONF_STATE_CLASS): cv.string,
    }
)


@dataclass(frozen=True)
class LoxoneRequiredKeysMixin:
    """Mixin for required keys."""

    loxone_format_string: str


@dataclass(frozen=True)
class LoxoneEntityDescription(SensorEntityDescription, LoxoneRequiredKeysMixin):
    """Describes Loxone sensor entity."""


SENSOR_TYPES: tuple[LoxoneEntityDescription, ...] = (
    LoxoneEntityDescription(
        key="temperature",
        name="Temperature",
        suggested_display_precision=1,
        loxone_format_string=UnitOfTemperature.CELSIUS,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.TEMPERATURE,
    ),
    LoxoneEntityDescription(
        key="temperature_fahrenheit",
        name="Temperature",
        suggested_display_precision=1,
        loxone_format_string=UnitOfTemperature.FAHRENHEIT,
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.TEMPERATURE,
    ),
    LoxoneEntityDescription(
        key="windstrength",
        name="Wind Strength",
        suggested_display_precision=1,
        loxone_format_string=UnitOfSpeed.KILOMETERS_PER_HOUR,
        native_unit_of_measurement=UnitOfSpeed.KILOMETERS_PER_HOUR,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.WIND_SPEED,
    ),
    LoxoneEntityDescription(
        key="kwh",
        name="Kilowatt per hour",
        suggested_display_precision=1,
        loxone_format_string=UnitOfEnergy.KILO_WATT_HOUR,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        device_class=SensorDeviceClass.ENERGY,
    ),
    LoxoneEntityDescription(
        key="wh",
        name="Watt per hour",
        suggested_display_precision=1,
        loxone_format_string=UnitOfEnergy.WATT_HOUR,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        device_class=SensorDeviceClass.ENERGY,
    ),
    LoxoneEntityDescription(
        key="power",
        name="Watt",
        suggested_display_precision=1,
        loxone_format_string=UnitOfPower.WATT,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.POWER,
    ),
    LoxoneEntityDescription(
        key="power",
        name="Kilowatt",
        suggested_display_precision=3,
        loxone_format_string=UnitOfPower.KILO_WATT,
        native_unit_of_measurement=UnitOfPower.KILO_WATT,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.POWER,
    ),
    LoxoneEntityDescription(
        key="light_level",
        name="Light Level",
        loxone_format_string=LIGHT_LUX,
        native_unit_of_measurement=LIGHT_LUX,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.ILLUMINANCE,
    ),
    LoxoneEntityDescription(
        key="humidity_or_battery",
        name="Humidity or Battery",
        suggested_display_precision=1,
        loxone_format_string=PERCENTAGE,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
)

SENSOR_FORMATS = [desc.loxone_format_string for desc in SENSOR_TYPES]


# Meter type → (state_key → (device_class, state_class, fallback_unit))
# Used when the format string doesn't match a known SENSOR_FORMAT, so the
# meter subsensor still gets the right classification for HA energy dashboard.
_METER_CLASSIFICATION: dict[
    str, dict[str, tuple[SensorDeviceClass, SensorStateClass, str]]
] = {
    "energy": {
        "actual": (SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT, UnitOfPower.WATT),
        "total": (SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING, UnitOfEnergy.KILO_WATT_HOUR),
        "totalNeg": (SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING, UnitOfEnergy.KILO_WATT_HOUR),
        "storage": (SensorDeviceClass.ENERGY, SensorStateClass.MEASUREMENT, UnitOfEnergy.KILO_WATT_HOUR),
    },
    "water": {
        "actual": (SensorDeviceClass.VOLUME_FLOW_RATE, SensorStateClass.MEASUREMENT, "L/min"),
        "total": (SensorDeviceClass.WATER, SensorStateClass.TOTAL_INCREASING, UnitOfVolume.LITERS),
        "totalNeg": (SensorDeviceClass.WATER, SensorStateClass.TOTAL_INCREASING, UnitOfVolume.LITERS),
    },
    "gas": {
        "actual": (SensorDeviceClass.GAS, SensorStateClass.MEASUREMENT, UnitOfVolume.CUBIC_METERS),
        "total": (SensorDeviceClass.GAS, SensorStateClass.TOTAL_INCREASING, UnitOfVolume.CUBIC_METERS),
        "totalNeg": (SensorDeviceClass.GAS, SensorStateClass.TOTAL_INCREASING, UnitOfVolume.CUBIC_METERS),
    },
}

# Expected device classes per meter type — used to detect format/type mismatches.
_METER_EXPECTED_CLASSES: dict[str, set[SensorDeviceClass]] = {
    "energy": {SensorDeviceClass.ENERGY, SensorDeviceClass.POWER},
    "water": {SensorDeviceClass.WATER, SensorDeviceClass.VOLUME_FLOW_RATE},
    "gas": {SensorDeviceClass.GAS},
}


# ---------------------------------------------------------------------------
# Miniserver diagnostic sensor descriptions
# ---------------------------------------------------------------------------


def _no_extra_attrs(_ms: MiniServer) -> dict[str, Any]:
    return {}


@dataclass(frozen=True)
class MiniserverSensorDescription:
    """Describes a static diagnostic sensor on the miniserver device."""

    key: str
    name: str
    icon: str
    value_fn: Callable[[MiniServer], str | None]
    extra_attrs_fn: Callable[[MiniServer], dict[str, Any]] = _no_extra_attrs


def _location_attrs(ms: MiniServer) -> dict[str, Any]:
    attrs: dict[str, Any] = {}
    if ms.latitude is not None:
        attrs["latitude"] = ms.latitude
    if ms.longitude is not None:
        attrs["longitude"] = ms.longitude
    if ms.altitude is not None:
        attrs["altitude"] = ms.altitude
    return attrs


def _current_user_attrs(ms: MiniServer) -> dict[str, Any]:
    user = ms.current_user
    if user and "isAdmin" in user:
        return {"is_admin": user["isAdmin"]}
    return {}


MINISERVER_SENSOR_DESCRIPTIONS: tuple[MiniserverSensorDescription, ...] = (
    MiniserverSensorDescription(
        key="project_name",
        name="Project name",
        icon="mdi:file-cog-outline",
        value_fn=lambda ms: ms.project_name,
    ),
    MiniserverSensorDescription(
        key="location",
        name="Location",
        icon="mdi:map-marker",
        value_fn=lambda ms: ms.location,
        extra_attrs_fn=_location_attrs,
    ),
    MiniserverSensorDescription(
        key="connected_user",
        name="Connected user",
        icon="mdi:account",
        value_fn=lambda ms: ms.current_user.get("name") if ms.current_user else None,
        extra_attrs_fn=_current_user_attrs,
    ),
)


class LoxoneMiniserverInfoSensor(LoxoneEntity, SensorEntity):
    """Static diagnostic sensor attached to the miniserver device."""

    _attr_has_entity_name = True
    _attr_should_poll = False
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self, description: MiniserverSensorDescription, miniserver: MiniServer
    ) -> None:
        super().__init__()
        self._serial = miniserver.serial
        self._attr_name = description.name
        self._attr_icon = description.icon
        self._attr_unique_id = f"{miniserver.serial}_{description.key}"
        self._attr_native_value = description.value_fn(miniserver)
        self._attr_extra_state_attributes.update(
            {k: v for k, v in description.extra_attrs_fn(miniserver).items()}
        )

    @cached_property
    def unique_id(self) -> str:
        return self._attr_unique_id

    @property
    def device_info(self) -> DeviceInfo | None:
        if self._serial:
            return DeviceInfo(identifiers={(DOMAIN, self._serial)})
        return None

    async def async_added_to_hass(self) -> None:
        """Static sensor — no event bus subscription, but still track availability."""
        self._register_coordinator_listener()


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_devices: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up Loxone Sensor from yaml"""
    value_template = config.get(CONF_VALUE_TEMPLATE)
    if value_template is not None:
        value_template.hass = hass

    # Devices from yaml
    if config:
        # Setup all Sensors in Yaml-File
        new_sensor = LoxoneCustomSensor(**config)
        async_add_devices([new_sensor], update_before_add=True)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: LoxoneConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up entry."""
    coordinator: LoxoneCoordinator = config_entry.runtime_data
    miniserver = coordinator.miniserver
    loxconfig = coordinator.api.structure_file
    serial = miniserver.serial if miniserver else None

    entities: list[Any] = [LoxoneKeepAliveSensor(serial=serial, coordinator=coordinator)]

    if "softwareVersion" in loxconfig:
        entities.append(LoxoneVersionSensor(loxconfig["softwareVersion"], serial=serial, coordinator=coordinator))

    if miniserver:
        for desc in MINISERVER_SENSOR_DESCRIPTIONS:
            if desc.value_fn(miniserver) is not None:
                entities.append(LoxoneMiniserverInfoSensor(desc, miniserver))

    for sensor in get_all(loxconfig, "InfoOnlyAnalog"):
        sensor = add_room_and_cat_to_value_values(loxconfig, sensor)
        sensor.update({"type": "analog", "coordinator": coordinator})
        entities.append(LoxoneSensor(**sensor))

    for sensor in get_all(loxconfig, "Meter"):
        _LOGGER.info("Found Meter: %s", sensor)
        sensor = add_room_and_cat_to_value_values(loxconfig, sensor)
        device_info = LoxoneMeterSensor.create_DeviceInfo_from_sensor(sensor)
        meter_type = sensor.get("details", {}).get("type", "").lower()

        for state_key, suffix, format_key in [
            ("actual", "Actual", "actualFormat"),
            ("total", "Total", "totalFormat"),
            ("totalNeg", "Total Returned", "totalFormat"),
            ("storage", "Level", "storageFormat"),
        ]:
            if state_key in sensor["states"]:
                subsensor = {
                    "device_info": device_info,
                    "parent_id": sensor["uuidAction"],
                    "uuidAction": sensor["states"][state_key],
                    "type": "analog",
                    "room": sensor.get("room", ""),
                    "cat": sensor.get("cat", ""),
                    "name": sensor["name"],
                    "name_suffix": suffix,
                    "details": {"format": sensor["details"][format_key]},
                    "meter_type": meter_type,
                    "meter_state_key": state_key,
                    "async_add_devices": async_add_entities,
                    "config_entry": config_entry,
                    "coordinator": coordinator,
                }
                meter_entity = LoxoneMeterSensor(**subsensor)
                entities.append(meter_entity)

                # Warn if the unit resolved from the format string contradicts
                # the meter's declared type (e.g. "energy" meter formatted as "L").
                if meter_type in _METER_EXPECTED_CLASSES:
                    resolved_cls = meter_entity.device_class
                    expected = _METER_EXPECTED_CLASSES[meter_type]
                    if resolved_cls and resolved_cls not in expected:
                        _LOGGER.warning(
                            "Meter %s (%s/%s): device_class %s from format "
                            "string conflicts with meter type '%s' "
                            "(expected %s). Check Loxone Config.",
                            sensor["name"],
                            state_key,
                            sensor["uuidAction"],
                            resolved_cls,
                            meter_type,
                            expected,
                        )
                        ir.async_create_issue(
                            hass,
                            DOMAIN,
                            f"meter_unit_mismatch_{sensor['uuidAction']}_{state_key}",
                            is_fixable=False,
                            severity=ir.IssueSeverity.WARNING,
                            translation_key="meter_unit_mismatch",
                            translation_placeholders={
                                "name": sensor["name"],
                                "state_key": suffix,
                                "meter_type": meter_type,
                                "detected_class": str(resolved_cls),
                            },
                        )

    if miniserver:
        @callback
        def async_add_sensors(_):
            async_add_entities(_, True)

        miniserver.listeners.append(
            async_dispatcher_connect(
                hass, miniserver.async_signal_new_device(NEW_SENSOR), async_add_sensors
            )
        )

    async_add_entities(entities, update_before_add=True)


class LoxoneCustomSensor(LoxoneEntity, SensorEntity):
    def __init__(self, **kwargs):
        self._attr_name = kwargs.pop("name", None)
        self._attr_state_class = kwargs.pop("state_class", None)
        self._attr_device_class = kwargs.pop("device_class", None)
        self._attr_native_unit_of_measurement = kwargs.pop("unit_of_measurement", None)
        self._attr_native_value = None  # Initialize state
        # Must be after the kwargs.pop functions!
        super().__init__(**kwargs)

    @cached_property
    def unique_id(self) -> str:
        """Return a unique ID."""
        return self.uuidAction + self._attr_name

    async def event_handler(self, e):
        if self.uuidAction in e:
            data = e[self.uuidAction]
            if isinstance(data, (list, dict)):
                data = str(data)
                if len(data) >= 255:
                    self._attr_native_value = data[:255]
                else:
                    self._attr_native_value = data
            else:
                self._attr_native_value = data

            self.async_schedule_update_ha_state()

    @property
    def native_unit_of_measurement(self):
        """Return the unit of measurement of this entity, if any."""
        if self._attr_native_unit_of_measurement in ["None", "none", "-"]:
            return None
        return self._attr_native_unit_of_measurement

    @property
    def extra_state_attributes(self):
        """Return device specific state attributes."""
        return {**self._attr_extra_state_attributes}


class LoxoneKeepAliveSensor(LoxoneEntity, SensorEntity):
    _attr_has_entity_name = True
    _attr_name = "Keep alive"
    _attr_icon = "mdi:heart-pulse"
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, serial: str | None = None, **kwargs):
        super().__init__(**kwargs)
        self._serial = serial
        self._attr_native_value = None
        self._attr_unique_id = (
            f"{serial}_keep_alive" if serial else "loxone_keep_alive_sensor_uuid"
        )

    @cached_property
    def unique_id(self) -> str:
        """Return a unique ID."""
        return self._attr_unique_id

    @property
    def device_info(self) -> DeviceInfo | None:
        if self._serial:
            return DeviceInfo(identifiers={(DOMAIN, self._serial)})
        return None

    async def event_handler(self, e):
        if "keep_alive" in e and e["keep_alive"] == "received":
            now = dt_util.utcnow()
            if self._attr_native_value is not None:
                time_since_last = (now - self._attr_native_value).total_seconds()
                if time_since_last < THROTTLE_KEEP_ALIVE_TIME:
                    return

            self._attr_native_value = now
            self.async_schedule_update_ha_state()


class LoxoneVersionSensor(LoxoneEntity, SensorEntity):
    _attr_has_entity_name = True
    _attr_should_poll = False
    _attr_name = "Software version"
    _attr_icon = "mdi:package-up"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_entity_registry_enabled_default = False

    def __init__(self, version_list, serial: str | None = None, **kwargs):
        super().__init__(**kwargs)
        self._serial = serial
        self._attr_unique_id = (
            f"{serial}_software_version" if serial else "loxone_software_version"
        )
        try:
            self._attr_native_value = ".".join([str(x) for x in version_list])
        except Exception:
            self._attr_native_value = STATE_UNKNOWN

    @cached_property
    def unique_id(self) -> str:
        """Return a unique ID."""
        return self._attr_unique_id

    @property
    def device_info(self) -> DeviceInfo | None:
        if self._serial:
            return DeviceInfo(identifiers={(DOMAIN, self._serial)})
        return None


class LoxoneSensor(LoxoneEntity, SensorEntity):
    """Representation of a Loxone Sensor."""

    _attr_has_entity_name = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._attr_name = None
        self._format = self._get_format(self.details["format"])
        self._attr_should_poll = False
        self._attr_native_unit_of_measurement = self._clean_unit(self.details["format"])
        self._parent_id = kwargs.get("parent_id", None)

        if entity_description := self._get_entity_description():
            self.entity_description = entity_description

        else:
            precision = self._parse_digits_after_decimal(self.details["format"])
            if precision:
                self._attr_suggested_display_precision = precision

        self.type = "Sensor analog"

    def _parse_digits_after_decimal(self, format_string):
        """Parse digits after the decimal point from the format string."""
        pattern = r"\.(\d+)"
        match = re.search(pattern, format_string)
        if match:
            digits = int(match.group(1))
            return digits
        return None

    def _get_entity_description(self) -> SensorEntityDescription | None:
        """Return the sensor entity description."""
        if self._attr_native_unit_of_measurement in SENSOR_FORMATS:
            return SENSOR_TYPES[
                SENSOR_FORMATS.index(self._attr_native_unit_of_measurement)
            ]
        return None

    @property
    def available(self) -> bool:
        """Return entity availability."""
        return self.state is not None

    def _get_lox_rounded_value(self, value):
        try:
            return float(self._format % float(value))
        except ValueError:
            return value

    async def event_handler(self, e):
        if self.uuidAction in e:
            self._attr_native_value = e[self.uuidAction]
            self.async_schedule_update_ha_state()

    @property
    def extra_state_attributes(self):
        """Return device specific state attributes."""
        return {
            **self._attr_extra_state_attributes,
            "device_type": self.type + "_sensor",
        }


class LoxoneMeterSensor(LoxoneSensor, SensorEntity):
    def __init__(self, **kwargs):
        name_suffix = kwargs.pop("name_suffix", None)
        meter_type = kwargs.pop("meter_type", "")
        meter_state_key = kwargs.pop("meter_state_key", "")
        super().__init__(**kwargs)
        device_info = kwargs.get("device_info", None)
        if device_info:
            self._attr_device_info = device_info
        if name_suffix:
            self._attr_name = name_suffix

        # If the format-based detection in LoxoneSensor didn't assign a
        # device_class, fall back to the meter type classification so the
        # entity is compatible with HA's energy/water/gas dashboards.
        if not hasattr(self, "entity_description") and meter_type in _METER_CLASSIFICATION:
            cls_map = _METER_CLASSIFICATION[meter_type]
            if meter_state_key in cls_map:
                dev_cls, state_cls, fallback_unit = cls_map[meter_state_key]
                self._attr_device_class = dev_cls
                self._attr_state_class = state_cls
                if not self._attr_native_unit_of_measurement:
                    self._attr_native_unit_of_measurement = fallback_unit

    @staticmethod
    def create_DeviceInfo_from_sensor(sensor) -> DeviceInfo:
        try:
            # For legacy Meter
            model = sensor["details"]["type"].capitalize() + " Meter"
        except (KeyError, TypeError):
            model = "Meter"
        return DeviceInfo(
            identifiers={(DOMAIN, sensor["uuidAction"])},
            name=sensor["name"],
            manufacturer="Loxone",
            model=model,
        )
