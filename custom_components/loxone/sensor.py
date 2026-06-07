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
    UnitOfTime,
    UnitOfVolume,
    UnitOfVolumeFlowRate,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er
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
from .helpers import add_room_and_cat_to_value_values, clean_unit, get_all, get_all_including_subcontrols
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
#
# Note on `storage` meters (Loxone Battery, e.g. BYD HVB):
#   - `actual` is signed power: +W = discharging, -W = charging
#   - `total` accumulates DISCHARGE energy (Loxone Mrd)
#   - `totalNeg` accumulates CHARGE energy (Loxone Mrc)
#   - `storage` is the battery state-of-charge in %
# The labels exposed to HA (see `_meter_state_layout`) reflect this so users
# don't swap them in the Energy Dashboard config.
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
    "storage": {
        "actual": (SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT, UnitOfPower.WATT),
        "total": (SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING, UnitOfEnergy.KILO_WATT_HOUR),
        "totalNeg": (SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING, UnitOfEnergy.KILO_WATT_HOUR),
        "storage": (SensorDeviceClass.BATTERY, SensorStateClass.MEASUREMENT, PERCENTAGE),
    },
}

# Expected device classes per meter type — used to detect format/type mismatches.
_METER_EXPECTED_CLASSES: dict[str, set[SensorDeviceClass]] = {
    "energy": {SensorDeviceClass.ENERGY, SensorDeviceClass.POWER},
    "water": {SensorDeviceClass.WATER, SensorDeviceClass.VOLUME_FLOW_RATE},
    "gas": {SensorDeviceClass.GAS},
    "storage": {SensorDeviceClass.ENERGY, SensorDeviceClass.POWER, SensorDeviceClass.BATTERY},
}


# Meter type → sub-sensor layout. Each tuple is
# ``(state_key, name_suffix, translation_key, format_key)``. The name suffix is
# the English fallback used when the translation_key resolves to nothing.
#
# Storage meters get discharge/charge labels because Loxone's convention
# (``total`` = discharge / Mrd, ``totalNeg`` = charge / Mrc) is the opposite of
# how an English reader interprets "Total" / "Total Returned"; mislabeling
# silently flips the HA Energy Dashboard battery storage source.
_METER_LAYOUT_DEFAULT: tuple[tuple[str, str, str, str], ...] = (
    ("actual", "Actual", "meter_actual", "actualFormat"),
    ("total", "Total", "meter_total", "totalFormat"),
    ("totalNeg", "Total Returned", "meter_total_returned", "totalFormat"),
    ("storage", "Level", "meter_storage", "storageFormat"),
)

_METER_LAYOUT_STORAGE: tuple[tuple[str, str, str, str], ...] = (
    ("actual", "Actual", "meter_actual", "actualFormat"),
    ("total", "Discharge energy", "meter_storage_discharge", "totalFormat"),
    ("totalNeg", "Charge energy", "meter_storage_charge", "totalFormat"),
    ("storage", "Battery level", "meter_storage_level", "storageFormat"),
)


def _meter_state_layout(meter_type: str) -> tuple[tuple[str, str, str, str], ...]:
    """Return the sub-sensor layout for a given Loxone meter type."""
    if meter_type == "storage":
        return _METER_LAYOUT_STORAGE
    return _METER_LAYOUT_DEFAULT


# Legacy entity-id suffixes generated from the pre-fix labels "Total" /
# "Total Returned". Used to detect users who installed the integration BEFORE
# storage meters got discharge/charge labels, so we can prompt them to verify
# their HA Energy Dashboard mapping.
_LEGACY_STORAGE_TOTAL_SUFFIXES: tuple[str, ...] = ("_total", "_total_returned")


def _maybe_create_storage_legacy_repair(
    hass: HomeAssistant,
    *,
    meter: dict,
) -> None:
    """Create a one-shot repair issue if this storage meter has legacy entity slugs.

    Only fires for users who installed the integration before the storage
    relabel: their `total` / `totalNeg` entities are still registered with the
    old `..._total` / `..._total_returned` slugs (HA never auto-renames slugs).
    Fresh installs land directly on the new `..._discharge_energy` /
    `..._charge_energy` slugs and never see this warning.
    """
    states = meter.get("states") or {}
    total_uuid = states.get("total")
    total_neg_uuid = states.get("totalNeg")
    if not total_uuid and not total_neg_uuid:
        return

    ent_reg = er.async_get(hass)
    discharge_entity = ent_reg.async_get_entity_id("sensor", DOMAIN, total_uuid) if total_uuid else None
    charge_entity = ent_reg.async_get_entity_id("sensor", DOMAIN, total_neg_uuid) if total_neg_uuid else None

    def _is_legacy(entity_id: str | None) -> bool:
        return bool(entity_id) and entity_id.endswith(_LEGACY_STORAGE_TOTAL_SUFFIXES)

    if not (_is_legacy(discharge_entity) or _is_legacy(charge_entity)):
        return

    ir.async_create_issue(
        hass,
        DOMAIN,
        f"meter_storage_legacy_labels_{meter['uuidAction']}",
        is_fixable=False,
        severity=ir.IssueSeverity.WARNING,
        translation_key="meter_storage_legacy_labels",
        translation_placeholders={
            "name": meter.get("name", ""),
            "discharge_entity": discharge_entity or "-",
            "charge_entity": charge_entity or "-",
        },
    )


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

    # Pre-register PowerUnit parent devices so that via_device links on Meter
    # subcontrol entities (registered below) resolve immediately. Without this
    # step HA silently drops via_device when the parent isn't yet in the device
    # registry, and the visual nesting in the UI is lost.
    device_registry = dr.async_get(hass)
    for power_unit in get_all(loxconfig, "PowerUnit"):
        device_registry.async_get_or_create(
            config_entry_id=config_entry.entry_id,
            **create_power_unit_device_info(power_unit),
        )

    for sensor, parent in get_all_including_subcontrols(loxconfig, "Meter", with_parent=True):
        _LOGGER.info("Found Meter: %s (parent=%s)", sensor.get("name"), parent.get("name") if parent else None)
        sensor = add_room_and_cat_to_value_values(loxconfig, sensor)
        device_info = LoxoneMeterSensor.create_device_info_from_sensor(sensor, parent=parent)
        meter_type = sensor.get("details", {}).get("type", "").lower()

        if meter_type == "storage":
            _maybe_create_storage_legacy_repair(hass, meter=sensor)

        for state_key, suffix, translation_key, format_key in _meter_state_layout(meter_type):
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

    # Headline + diagnostic sensors for each PowerUnit (Energy Flow Monitor).
    # The PowerUnit itself is not a Meter; its child Meter subControls have already
    # been linked to it via via_device in the loop above. Here we surface its own
    # states (output power, battery SoC, time on battery, deviceInfo).
    for power_unit in get_all(loxconfig, "PowerUnit"):
        states = power_unit.get("states") or {}
        entities.extend(
            LoxonePowerUnitSensor(
                power_unit=power_unit,
                description=desc,
                coordinator=coordinator,
            )
            for desc in POWER_UNIT_SENSOR_DESCRIPTIONS
            if desc.state_key in states
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
    def create_device_info_from_sensor(sensor, parent: dict | None = None) -> DeviceInfo:
        """Create device info from sensor.

        When ``parent`` is provided (the meter is a subControl of e.g. a
        ``PowerUnit``), link the sub-meter device to the parent device via
        HA's ``via_device`` so they render as a nested device hierarchy.
        """
        try:
            # For legacy Meter
            model = sensor["details"]["type"].capitalize() + " Meter"
        except (KeyError, TypeError):
            model = "Meter"
        info = DeviceInfo(
            identifiers={(DOMAIN, sensor["uuidAction"])},
            name=sensor["name"],
            manufacturer="Loxone",
            model=model,
        )
        if parent and parent.get("uuidAction"):
            info["via_device"] = (DOMAIN, parent["uuidAction"])
        return info


@dataclass(frozen=True, kw_only=True)
class PowerUnitSensorDescription(SensorEntityDescription):
    """Describes a sensor entity that lives on a Loxone PowerUnit device.

    ``state_key`` is the key under PowerUnit ``states`` whose UUID this
    sensor subscribes to. ``value_fn`` (optional) maps the raw Loxone
    value to the entity's native value; defaults to identity.
    """

    state_key: str
    value_fn: Callable[[Any], Any] | None = None


POWER_UNIT_SENSOR_DESCRIPTIONS: tuple[PowerUnitSensorDescription, ...] = (
    PowerUnitSensorDescription(
        key="output_power",
        state_key="outputPower",
        translation_key="powerunit_output_power",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        suggested_display_precision=1,
    ),
    PowerUnitSensorDescription(
        key="battery_state_of_charge",
        state_key="batteryStateOfCharge",
        translation_key="powerunit_battery_soc",
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        suggested_display_precision=0,
    ),
    PowerUnitSensorDescription(
        key="supply_time_remaining",
        state_key="supplyTimeRemaining",
        translation_key="powerunit_supply_time_remaining",
        device_class=SensorDeviceClass.DURATION,
        # Loxone reports the value in seconds; HA's DURATION sensor
        # auto-formats to human-readable in the UI.
        native_unit_of_measurement=UnitOfTime.SECONDS,
        suggested_display_precision=0,
        icon="mdi:battery-clock",
    ),
    PowerUnitSensorDescription(
        key="device_info",
        state_key="deviceInfo",
        translation_key="powerunit_device_info",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        icon="mdi:information-outline",
    ),
)


def create_power_unit_device_info(power_unit: dict) -> DeviceInfo:
    """Build the DeviceInfo for a Loxone PowerUnit parent device.

    Shared by both the sensor and binary_sensor platforms so all child
    entities land on a single device entry keyed by the PowerUnit UUID.
    """
    return DeviceInfo(
        identifiers={(DOMAIN, power_unit["uuidAction"])},
        name=power_unit.get("name") or "Power Supply & Backup",
        manufacturer="Loxone",
        model="Power Unit",
    )


class LoxonePowerUnitSensor(LoxoneEntity, SensorEntity):
    """A sensor exposing one Loxone PowerUnit state on the parent device."""

    _attr_has_entity_name = True
    _attr_should_poll = False
    entity_description: PowerUnitSensorDescription

    def __init__(
        self,
        *,
        power_unit: dict,
        description: PowerUnitSensorDescription,
        coordinator: LoxoneCoordinator,
    ) -> None:
        """Initialize the LoxonePowerUnitSensor."""
        super().__init__(coordinator=coordinator)
        self.entity_description = description
        self.uuidAction = power_unit["states"][description.state_key]
        self._power_unit_uuid = power_unit["uuidAction"]
        self._attr_unique_id = f"{self._power_unit_uuid}_{description.key}"
        self._attr_device_info = create_power_unit_device_info(power_unit)
        self._attr_native_value = None

    @cached_property
    def unique_id(self) -> str:
        """Return a unique ID."""
        return self._attr_unique_id

    async def event_handler(self, e):
        """Handle a state update message from Loxone."""
        if self.uuidAction in e:
            value = e[self.uuidAction]
            if self.entity_description.value_fn is not None:
                value = self.entity_description.value_fn(value)
            self._attr_native_value = value
            self.async_schedule_update_ha_state()


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
