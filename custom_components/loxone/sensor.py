"""Loxone Sensors.

For more details about this component, please refer to the documentation at
https://github.com/JoDehli/PyLoxone
"""

from collections.abc import Callable
from dataclasses import dataclass
from functools import cached_property
import logging
import re
from typing import Any

import voluptuous as vol

from homeassistant.components.sensor import (
    CONF_STATE_CLASS,
    PLATFORM_SCHEMA as SENSOR_PLATFORM_SCHEMA,
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    CONCENTRATION_PARTS_PER_MILLION,
    CONF_DEVICE_CLASS,
    CONF_NAME,
    CONF_UNIT_OF_MEASUREMENT,
    CONF_VALUE_TEMPLATE,
    LIGHT_LUX,
    PERCENTAGE,
    STATE_UNKNOWN,
    EntityCategory,
    UnitOfEnergy,
    UnitOfPower,
    UnitOfSpeed,
    UnitOfTemperature,
    UnitOfVolume,
    UnitOfVolumeFlowRate,
)
from homeassistant.core import HomeAssistant
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
import homeassistant.helpers.issue_registry as ir
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.util import dt as dt_util

from . import LoxoneConfigEntry, LoxoneEntity
from .const import CONF_ACTIONID, DOMAIN, THROTTLE_KEEP_ALIVE_TIME
from .coordinator import LoxoneCoordinator
from .helpers import add_room_and_cat_to_value_values, clean_unit, get_all
from .miniserver import MiniServer

NEW_SENSOR = "sensors"

_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = "Loxone Sensor"

PARALLEL_UPDATES = 0

SENSOR_PLATFORM_SCHEMA = SENSOR_PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_ACTIONID): cv.string,
        vol.Optional(CONF_NAME): cv.string,
        vol.Optional(CONF_UNIT_OF_MEASUREMENT): cv.string,
        vol.Optional(CONF_DEVICE_CLASS): cv.string,
        vol.Optional(CONF_STATE_CLASS): cv.string,
    }
)


class LoxoneEntityDescription(SensorEntityDescription, frozen_or_thawed=True):
    """Describes a Loxone sensor entity.

    Acts as a classification object: carries matching criteria (which Loxone
    units/keywords trigger this description) and the resulting classification
    (device_class, state_class). Presentation details (actual unit, precision)
    come from the Loxone format string via _attr_* in __init__.
    """

    loxone_format_strings: tuple[str, ...]
    category_keywords: tuple[str, ...] = ()
    name_keywords: tuple[str, ...] = ()


SENSOR_TYPES: tuple[LoxoneEntityDescription, ...] = (
    LoxoneEntityDescription(
        key="temperature",
        loxone_format_strings=(UnitOfTemperature.CELSIUS, UnitOfTemperature.FAHRENHEIT),
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.TEMPERATURE,
    ),
    LoxoneEntityDescription(
        key="wind_speed",
        loxone_format_strings=(UnitOfSpeed.KILOMETERS_PER_HOUR,),
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.WIND_SPEED,
    ),
    LoxoneEntityDescription(
        key="energy",
        loxone_format_strings=(
            UnitOfEnergy.KILO_WATT_HOUR,
            UnitOfEnergy.WATT_HOUR,
            UnitOfEnergy.MEGA_WATT_HOUR,
        ),
        state_class=SensorStateClass.TOTAL_INCREASING,
        device_class=SensorDeviceClass.ENERGY,
    ),
    LoxoneEntityDescription(
        key="power",
        loxone_format_strings=(UnitOfPower.WATT, UnitOfPower.KILO_WATT),
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.POWER,
    ),
    LoxoneEntityDescription(
        key="volume_flow_rate",
        loxone_format_strings=(
            UnitOfVolumeFlowRate.LITERS_PER_HOUR,
            UnitOfVolumeFlowRate.LITERS_PER_MINUTE,
        ),
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.VOLUME_FLOW_RATE,
    ),
    LoxoneEntityDescription(
        key="water",
        loxone_format_strings=(UnitOfVolume.LITERS,),
        state_class=SensorStateClass.TOTAL_INCREASING,
        device_class=SensorDeviceClass.WATER,
    ),
    LoxoneEntityDescription(
        key="illuminance",
        loxone_format_strings=(LIGHT_LUX, "Lx", "lux"),
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.ILLUMINANCE,
    ),
    LoxoneEntityDescription(
        key="carbon_dioxide",
        loxone_format_strings=(CONCENTRATION_PARTS_PER_MILLION,),
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.CO2,
    ),
    LoxoneEntityDescription(
        key="humidity",
        loxone_format_strings=(PERCENTAGE,),
        category_keywords=("vlhkost", "humidity", "feucht", "humidité"),
        name_keywords=("vlhkost", "humidity", "feucht", "humidité"),
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.HUMIDITY,
    ),
    LoxoneEntityDescription(
        key="battery",
        loxone_format_strings=(PERCENTAGE,),
        name_keywords=("batt", "akku", "battery"),
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.BATTERY,
    ),
)

UNAMBIGUOUS_UNITS: frozenset[str] = frozenset(
    u
    for desc in SENSOR_TYPES
    if not desc.category_keywords and not desc.name_keywords
    for u in desc.loxone_format_strings
)
"""Units that map to exactly one device class without needing keyword disambiguation."""


def match_sensor_description(
    unit: str,
    name: str = "",
    category: str = "",
) -> LoxoneEntityDescription | None:
    """Find the first matching sensor description for a Loxone sensor.

    Unambiguous units (°C, kWh, ppm, …) match immediately.
    Ambiguous units (%) require a keyword hit in name or category.
    Returns None if no description matches.
    """
    name_lower = name.lower()
    cat_lower = category.lower()
    for desc in SENSOR_TYPES:
        if unit not in desc.loxone_format_strings:
            continue
        if not desc.category_keywords and not desc.name_keywords:
            return desc
        cat_match = any(kw in cat_lower for kw in desc.category_keywords)
        name_match = any(kw in name_lower for kw in desc.name_keywords)
        if cat_match or name_match:
            return desc
    return None


# Meter type → (state_key → (device_class, state_class, fallback_unit))
# Used when the format string doesn't match a known SENSOR_FORMAT, so the
# meter subsensor still gets the right classification for HA energy dashboard.
_METER_CLASSIFICATION: dict[str, dict[str, tuple[SensorDeviceClass, SensorStateClass, str]]] = {
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
    """Return no extra attrs."""
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
    """Return location attrs."""
    attrs: dict[str, Any] = {}
    if ms.latitude is not None:
        attrs["latitude"] = ms.latitude
    if ms.longitude is not None:
        attrs["longitude"] = ms.longitude
    if ms.altitude is not None:
        attrs["altitude"] = ms.altitude
    return attrs


def _current_user_attrs(ms: MiniServer) -> dict[str, Any]:
    """Return current user attrs."""
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

    def __init__(self, description: MiniserverSensorDescription, miniserver: MiniServer) -> None:
        """Initialize the LoxoneMiniserverInfoSensor."""
        super().__init__()
        self._serial = miniserver.serial
        self._attr_translation_key = description.key
        self._attr_icon = description.icon
        self._attr_unique_id = f"{miniserver.serial}_{description.key}"
        self._attr_native_value = description.value_fn(miniserver)
        self._attr_extra_state_attributes.update(description.extra_attrs_fn(miniserver))

    @cached_property
    def unique_id(self) -> str:
        """Return a unique ID for this entity."""
        return self._attr_unique_id

    @property
    def device_info(self) -> DeviceInfo | None:
        """Return device information."""
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
    """Set up Loxone Sensor from yaml."""
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
        entities.extend(
            LoxoneMiniserverInfoSensor(desc, miniserver)
            for desc in MINISERVER_SENSOR_DESCRIPTIONS
            if desc.value_fn(miniserver) is not None
        )

    for sensor in get_all(loxconfig, "InfoOnlyAnalog"):
        sensor = add_room_and_cat_to_value_values(loxconfig, sensor)
        sensor.update({"type": "analog", "coordinator": coordinator})
        entities.append(LoxoneSensor(**sensor))

    for sensor in get_all(loxconfig, "Meter"):
        _LOGGER.info("Found Meter: %s", sensor)
        sensor = add_room_and_cat_to_value_values(loxconfig, sensor)
        device_info = LoxoneMeterSensor.create_device_info_from_sensor(sensor)
        meter_type = sensor.get("details", {}).get("type", "").lower()

        for state_key, suffix, translation_key, format_key in [
            ("actual", "Actual", "meter_actual", "actualFormat"),
            ("total", "Total", "meter_total", "totalFormat"),
            ("totalNeg", "Total Returned", "meter_total_returned", "totalFormat"),
            ("storage", "Level", "meter_storage", "storageFormat"),
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
                    "translation_key": translation_key,
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

    if miniserver and miniserver.serial:
        entities.append(LoxoneConnectionStateSensor(serial=miniserver.serial, coordinator=coordinator))
        entities.append(LoxoneReconnectCountSensor(serial=miniserver.serial, coordinator=coordinator))

    if miniserver:
        miniserver.listeners.append(
            async_dispatcher_connect(hass, miniserver.async_signal_new_device(NEW_SENSOR), async_add_entities)
        )

    async_add_entities(entities, update_before_add=True)


class LoxoneCustomSensor(LoxoneEntity, SensorEntity):
    """Represent loxone custom sensor."""

    def __init__(self, **kwargs):
        """Initialize the LoxoneCustomSensor."""
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
        """Handle a state update message from Loxone."""
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
    """Represent loxone keep alive sensor."""

    _attr_has_entity_name = True
    _attr_name = "Keep alive"
    _attr_icon = "mdi:heart-pulse"
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, serial: str | None = None, **kwargs):
        """Initialize the LoxoneKeepAliveSensor."""
        super().__init__(**kwargs)
        self._serial = serial
        self._attr_native_value = None
        self._attr_unique_id = f"{serial}_keep_alive" if serial else "loxone_keep_alive_sensor_uuid"

    @cached_property
    def unique_id(self) -> str:
        """Return a unique ID."""
        return self._attr_unique_id

    @property
    def device_info(self) -> DeviceInfo | None:
        """Return device information."""
        if self._serial:
            return DeviceInfo(identifiers={(DOMAIN, self._serial)})
        return None

    async def event_handler(self, e):
        """Handle a state update message from Loxone."""
        if "keep_alive" in e and e["keep_alive"] == "received":
            now = dt_util.utcnow()
            if self._attr_native_value is not None:
                time_since_last = (now - self._attr_native_value).total_seconds()
                if time_since_last < THROTTLE_KEEP_ALIVE_TIME:
                    return

            self._attr_native_value = now
            self.async_schedule_update_ha_state()


class LoxoneVersionSensor(LoxoneEntity, SensorEntity):
    """Represent loxone version sensor."""

    _attr_has_entity_name = True
    _attr_should_poll = False
    _attr_name = "Software version"
    _attr_icon = "mdi:package-up"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_entity_registry_enabled_default = False

    def __init__(self, version_list, serial: str | None = None, **kwargs):
        """Initialize the LoxoneVersionSensor."""
        super().__init__(**kwargs)
        self._serial = serial
        self._attr_unique_id = f"{serial}_software_version" if serial else "loxone_software_version"
        try:
            self._attr_native_value = ".".join([str(x) for x in version_list])
        except TypeError:
            self._attr_native_value = STATE_UNKNOWN

    @cached_property
    def unique_id(self) -> str:
        """Return a unique ID."""
        return self._attr_unique_id

    @property
    def device_info(self) -> DeviceInfo | None:
        """Return device information."""
        if self._serial:
            return DeviceInfo(identifiers={(DOMAIN, self._serial)})
        return None


class LoxoneSensor(LoxoneEntity, SensorEntity):
    """Representation of a Loxone Sensor."""

    _attr_has_entity_name = True

    def __init__(self, **kwargs):
        """Initialize the LoxoneSensor."""
        super().__init__(**kwargs)
        self._attr_name = None
        self._format = self._get_format(self.details["format"])
        self._attr_should_poll = False
        self._attr_native_unit_of_measurement = clean_unit(self.details["format"])
        self._parent_id = kwargs.get("parent_id")

        precision = self._parse_digits_after_decimal(self.details["format"])
        if precision:
            self._attr_suggested_display_precision = precision

        # Device class is auto-detected from unit + name + Loxone category.
        # Users can override via HA's customize/customize_glob in configuration.yaml.
        if desc := match_sensor_description(
            unit=self._attr_native_unit_of_measurement or "",
            name=kwargs.get("name", "") or "",
            category=kwargs.get("cat", "") or "",
        ):
            self.entity_description = desc

        self.type = "Sensor analog"

    def _parse_digits_after_decimal(self, format_string):
        """Parse digits after the decimal point from the format string."""
        pattern = r"\.(\d+)"
        match = re.search(pattern, format_string)
        if match:
            return int(match.group(1))
        return None

    @property
    def available(self) -> bool:
        """Return entity availability."""
        return self.state is not None

    def _get_lox_rounded_value(self, value):
        """Return get lox rounded value."""
        try:
            return float(self._format % float(value))
        except ValueError:
            return value

    async def event_handler(self, e):
        """Handle a state update message from Loxone."""
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
    """Represent loxone meter sensor."""

    def __init__(self, **kwargs):
        """Initialize the LoxoneMeterSensor."""
        name_suffix = kwargs.pop("name_suffix", None)
        tkey = kwargs.pop("translation_key", None)
        meter_type = kwargs.pop("meter_type", "")
        meter_state_key = kwargs.pop("meter_state_key", "")
        super().__init__(**kwargs)
        device_info = kwargs.get("device_info")
        if device_info:
            self._attr_device_info = device_info
        if tkey:
            self._attr_translation_key = tkey
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
    def create_device_info_from_sensor(sensor) -> DeviceInfo:
        """Create device info from sensor."""
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


class LoxoneConnectionStateSensor(LoxoneEntity, SensorEntity):
    """Diagnostic sensor showing the coordinator's connection state."""

    _attr_has_entity_name = True
    _attr_should_poll = False
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_entity_registry_enabled_default = False
    _attr_translation_key = "connection_state"

    def __init__(self, *, serial: str, coordinator: LoxoneCoordinator) -> None:
        """Initialize the LoxoneConnectionStateSensor."""
        super().__init__()
        self._serial = serial
        self._coordinator = coordinator
        self._attr_unique_id = f"{serial}_connection_state"

    @cached_property
    def unique_id(self) -> str:
        """Return a unique ID."""
        return self._attr_unique_id

    @property
    def native_value(self) -> str:
        """Return the native value."""
        return self._coordinator.connection_state.value

    @property
    def available(self) -> bool:
        """Always available — this sensor reports state even when disconnected."""
        return True

    @property
    def device_info(self) -> DeviceInfo | None:
        """Return device information."""
        return DeviceInfo(identifiers={(DOMAIN, self._serial)})

    async def async_added_to_hass(self) -> None:
        """Run when this entity is added to Home Assistant."""
        self._register_coordinator_listener()


class LoxoneReconnectCountSensor(LoxoneEntity, SensorEntity):
    """Diagnostic sensor counting successful reconnections."""

    _attr_has_entity_name = True
    _attr_should_poll = False
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_entity_registry_enabled_default = False
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_translation_key = "reconnect_count"

    def __init__(self, *, serial: str, coordinator: LoxoneCoordinator) -> None:
        """Initialize the LoxoneReconnectCountSensor."""
        super().__init__()
        self._serial = serial
        self._coordinator = coordinator
        self._attr_unique_id = f"{serial}_reconnect_count"

    @cached_property
    def unique_id(self) -> str:
        """Return a unique ID."""
        return self._attr_unique_id

    @property
    def native_value(self) -> int:
        """Return the native value."""
        return self._coordinator.reconnect_count

    @property
    def available(self) -> bool:
        """Always available — this sensor reports state even when disconnected."""
        return True

    @property
    def device_info(self) -> DeviceInfo | None:
        """Return device information."""
        return DeviceInfo(identifiers={(DOMAIN, self._serial)})

    async def async_added_to_hass(self) -> None:
        """Run when this entity is added to Home Assistant."""
        self._register_coordinator_listener()
