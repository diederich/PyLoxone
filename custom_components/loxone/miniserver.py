import logging
from dataclasses import dataclass
from typing import Any, Optional

from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.device_registry import format_mac

from .helpers import get_miniserver_type
from .pyloxone_api.structure import LoxoneStructure

_LOGGER = logging.getLogger(__name__)
DOMAIN = "loxone"
NEW_GROUP = "groups"
NEW_LIGHT = "lights"
NEW_SCENE = "scenes"
NEW_SENSOR = "sensors"
NEW_COVERS = "covers"


@callback
def get_miniserver_from_hass(hass):
    """Return the first available MiniServer, or None."""
    for entry in hass.config_entries.async_entries(DOMAIN):
        coordinator = getattr(entry, "runtime_data", None)
        if coordinator is not None and coordinator.miniserver is not None:
            return coordinator.miniserver
    return None


@callback
def get_miniserver_from_config(hass, config):
    """Return first Miniserver. Only one Miniserver is allowed"""
    if len(config) == 0:
        return None
    return config[next(iter(config))]


@dataclass
class ConfigDataClass:
    json: Optional[dict[str, Any]] = None

    def get(self, key, default=None):
        if self.json is not None:
            return self.json.get(key, default)
        return default

    def __contains__(self, key):
        if self.json is not None:
            return key in self.json
        return False

    def __getitem__(self, key):
        if self.json is not None:
            return self.json[key]
        raise KeyError(key)


class MiniServer:
    def __init__(self, hass, lox_config, config_entry):
        self.hass = hass
        self.lox_config: ConfigDataClass = ConfigDataClass(lox_config)
        self.config_entry = config_entry
        self.listeners = []

        self.structure: LoxoneStructure = LoxoneStructure.from_dict(
            lox_config if lox_config else {}
        )

    @property
    def serial(self):
        return self.structure.ms_info.serial_nr or None

    @property
    def miniserver_type(self):
        return self.structure.ms_info.miniserver_type

    @property
    def name(self):
        return self.structure.ms_info.ms_name or None

    @property
    def software_version(self):
        return self.structure.software_version_str

    @property
    def project_name(self):
        return self.structure.ms_info.project_name or None

    @property
    def location(self):
        return self.structure.ms_info.location or None

    @property
    def latitude(self):
        return self.structure.ms_info.latitude or None

    @property
    def longitude(self):
        return self.structure.ms_info.longitude or None

    @property
    def altitude(self):
        return self.structure.ms_info.altitude or None

    @property
    def current_user(self) -> dict | None:
        return self.structure.ms_info.current_user

    @property
    def miniserver_id(self) -> str:
        """Return the unique identifier of the Miniserver."""
        return self.config_entry.unique_id

    @callback
    def async_signal_new_device(self, device_type) -> str:
        """Gateway specific event to signal new device."""
        new_device = {
            NEW_GROUP: f"loxone_new_group_{self.miniserver_id}",
            NEW_LIGHT: f"loxone_new_light_{self.miniserver_id}",
            NEW_SCENE: f"loxone_new_scene_{self.miniserver_id}",
            NEW_SENSOR: f"loxone_new_sensor_{self.miniserver_id}",
            NEW_COVERS: f"loxone_new_cover_{self.miniserver_id}",
        }
        return new_device[device_type]

    async def async_update_device_registry(self) -> None:
        device_registry = dr.async_get(self.hass)
        connections: set[tuple[str, str]] = set()
        if self.serial:
            mac = format_mac(self.serial)
            if mac:
                connections.add((dr.CONNECTION_NETWORK_MAC, mac))

        device_registry.async_get_or_create(
            config_entry_id=self.config_entry.entry_id,
            connections=connections,
            name=self.name,
            model=get_miniserver_type(self.miniserver_type),
            identifiers={(DOMAIN, self.serial)},
            manufacturer="Loxone",
            sw_version=self.software_version,
            configuration_url="http://{host}:{port}".format(
                host=self.config_entry.options[CONF_HOST],
                port=self.config_entry.options[CONF_PORT],
            ),
        )
