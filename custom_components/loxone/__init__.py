"""
Component to create an interface to the Loxone Miniserver.

For more details about this component, please refer to the documentation at
https://github.com/JoDehli/PyLoxone
"""

import asyncio
import logging
import re
from functools import cached_property

import homeassistant.components.group as group
import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (CONF_HOST, CONF_PASSWORD, CONF_PORT,
                                 CONF_USERNAME, EVENT_COMPONENT_LOADED,
                                 Platform)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady, HomeAssistantError
from homeassistant.helpers import area_registry as ar
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.device_registry import DeviceEntry
from homeassistant.helpers.discovery import async_load_platform
from homeassistant.helpers.entity import DeviceInfo, Entity

from .bridge import BridgeRuntime
from homeassistant.setup import async_setup_component

from .const import (ATTR_AREA_CREATE, ATTR_CODE, ATTR_DEVICE,
                    ATTR_UUID, ATTR_VALUE, CONF_CREATE_AREAS,
                    CONF_LIGHTCONTROLLER_SUBCONTROLS_GEN, CONF_SCENE_GEN,
                    CONF_SCENE_GEN_DELAY, DEFAULT, DEFAULT_DELAY_SCENE,
                    DEFAULT_PORT, DOMAIN, EVENT,
                    LOXONE_PLATFORMS, SECUREDSENDDOMAIN, SENDDOMAIN, cfmt)
from .coordinator import ConnectionState, LoxoneCoordinator
from .miniserver import get_miniserver_from_hass
from .pyloxone_api.exceptions import (LoxoneConnectionClosedOk,
                                      LoxoneConnectionError,
                                      LoxoneServiceUnAvailableError,
                                      LoxoneUnauthorisedError)

REQUIREMENTS = ["websockets", "pycryptodome", "numpy"]

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_USERNAME): cv.string,
                vol.Required(CONF_PASSWORD): cv.string,
                vol.Required(CONF_HOST): cv.string,
                vol.Optional(CONF_PORT, default=DEFAULT_PORT): cv.port,
                vol.Optional(CONF_SCENE_GEN, default=True): cv.boolean,
                vol.Optional(
                    CONF_SCENE_GEN_DELAY, default=DEFAULT_DELAY_SCENE
                ): cv.positive_int,
                vol.Required(CONF_LIGHTCONTROLLER_SUBCONTROLS_GEN, default=False): bool,
            }
        ),
    },
    extra=vol.ALLOW_EXTRA,
)

_UNDEF: dict = {}

# TODO: get version and check for updates https://update.loxone.com/updatecheck.xml?serial=xxxxxxxxx


def _get_coordinator(hass: HomeAssistant):
    """Return the first available LoxoneCoordinator, or None."""
    for value in hass.data.get(DOMAIN, {}).values():
        if hasattr(value, "api"):
            return value
    return None


async def _async_sync_areas(hass: HomeAssistant, data=None):
    """Sync HA areas with Loxone room attributes on devices."""
    data = data or {}
    create_areas = data.get(ATTR_AREA_CREATE, False)
    er_registry = er.async_get(hass)
    ar_registry = ar.async_get(hass)
    dr_registry = dr.async_get(hass)

    loxone_entities = [e for e in er_registry.entities.values() if e.platform == DOMAIN]
    _LOGGER.debug("sync_areas: found %d loxone entities (create_areas=%s)",
                   len(loxone_entities), create_areas)

    no_state = []
    no_room = []
    no_area = []

    device_rooms: dict[str, str] = {}
    device_entities: dict[str, list] = {}
    orphan_entities = []

    for entry in loxone_entities:
        state = hass.states.get(entry.entity_id)
        if not state:
            no_state.append(entry.entity_id)
            continue
        if "room" not in state.attributes:
            no_room.append(entry.entity_id)
            continue
        room_name = state.attributes["room"]

        if entry.device_id:
            device_rooms.setdefault(entry.device_id, room_name)
            device_entities.setdefault(entry.device_id, []).append(entry)
        else:
            orphan_entities.append((entry, room_name))

    devices_updated = 0
    devices_ok = 0
    overrides_cleared = 0

    for device_id, room_name in device_rooms.items():
        area = ar_registry.async_get_area_by_name(room_name)
        if area is None and create_areas:
            area = ar_registry.async_get_or_create(room_name)
            _LOGGER.debug("sync_areas: created area '%s'", room_name)
        if area is None:
            no_area.append((device_id, room_name))
            continue

        device = dr_registry.async_get(device_id)
        if device and device.area_id != area.id:
            dr_registry.async_update_device(device_id, area_id=area.id)
            _LOGGER.debug("sync_areas: device %s → area '%s' (was %s)",
                          device.name or device_id, room_name, device.area_id)
            devices_updated += 1
        else:
            devices_ok += 1

        for entry in device_entities.get(device_id, []):
            if entry.area_id is not None:
                er_registry.async_update_entity(entry.entity_id, area_id=None)
                overrides_cleared += 1

    orphans_updated = 0
    for entry, room_name in orphan_entities:
        area = ar_registry.async_get_area_by_name(room_name)
        if area is None and create_areas:
            area = ar_registry.async_get_or_create(room_name)
        if area is None:
            no_area.append((entry.entity_id, room_name))
            continue
        if entry.area_id != area.id:
            er_registry.async_update_entity(entry.entity_id, area_id=area.id)
            orphans_updated += 1

    _LOGGER.info(
        "sync_areas: %d device(s) updated, %d already correct, "
        "%d entity override(s) cleared, %d orphan(s) updated, "
        "%d no state, %d no room attr, %d room not found",
        devices_updated, devices_ok, overrides_cleared, orphans_updated,
        len(no_state), len(no_room), len(no_area),
    )
    if no_state:
        _LOGGER.debug("sync_areas: entities with no state: %s", no_state)
    if no_room:
        _LOGGER.debug("sync_areas: entities missing 'room' attribute: %s", no_room)
    if no_area:
        _LOGGER.debug("sync_areas: room not found in HA areas (create_areas=%s): %s",
                      create_areas, no_area)


async def _async_sync_device_names(hass: HomeAssistant):
    """Sync HA device names from the current Loxone structure file."""
    miniserver = get_miniserver_from_hass(hass)
    structure = miniserver.lox_config.json
    controls = structure.get("controls", {})

    uuid_to_name = {
        ctrl["uuidAction"]: ctrl["name"]
        for ctrl in controls.values()
        if "uuidAction" in ctrl and "name" in ctrl
    }

    dr_registry = dr.async_get(hass)
    updated = 0
    for device in dr_registry.devices.values():
        for domain, uuid in device.identifiers:
            if domain != DOMAIN:
                continue
            lox_name = uuid_to_name.get(uuid)
            if lox_name and device.name != lox_name:
                dr_registry.async_update_device(device.id, name=lox_name)
                updated += 1
    _LOGGER.info("sync_device_names: updated %d device(s)", updated)


def _async_register_services(hass: HomeAssistant):
    """Register domain-level Loxone services.

    Called from async_setup so services exist even if no config entry has
    loaded yet (e.g. Miniserver temporarily unreachable at boot).  Handlers
    look up the coordinator lazily — if none is available they raise.
    """

    async def handle_websocket_command(call):
        """Handle websocket command services."""
        coordinator = _get_coordinator(hass)
        if coordinator is None:
            raise HomeAssistantError(
                "Loxone Miniserver is not connected — cannot send command"
            )
        if coordinator.connection_state != ConnectionState.CONNECTED:
            raise HomeAssistantError(
                f"Loxone Miniserver is {coordinator.connection_state.value}"
                " — cannot send command"
            )
        value = call.data.get(ATTR_VALUE, DEFAULT)
        if call.data.get(ATTR_DEVICE) is None:
            entity_uuid = call.data.get(ATTR_UUID, DEFAULT)
        else:
            entity_registry = er.async_get(hass)
            entity_id = call.data.get(ATTR_DEVICE)
            entity = entity_registry.async_get(entity_id)
            entity_uuid = entity.unique_id
        await coordinator.api.send_websocket_command(entity_uuid, value)

    async def handle_secured_websocket_command(call):
        """Handle secured websocket command services."""
        coordinator = _get_coordinator(hass)
        if coordinator is None:
            raise HomeAssistantError(
                "Loxone Miniserver is not connected — cannot send secured command"
            )
        if coordinator.connection_state != ConnectionState.CONNECTED:
            raise HomeAssistantError(
                f"Loxone Miniserver is {coordinator.connection_state.value}"
                " — cannot send secured command"
            )
        value = call.data.get(ATTR_VALUE, DEFAULT)
        code = call.data.get(ATTR_CODE, DEFAULT)
        if call.data.get(ATTR_DEVICE) is None:
            entity_uuid = call.data.get(ATTR_UUID, DEFAULT)
        else:
            entity_registry = er.async_get(hass)
            entity_id = call.data.get(ATTR_DEVICE)
            entity = entity_registry.async_get(entity_id)
            entity_uuid = entity.unique_id
        await coordinator.api.send_secured__websocket_command(
            entity_uuid, value, code
        )

    async def handle_sync_areas(call):
        await _async_sync_areas(hass, call.data)

    async def handle_sync_device_names(call):
        await _async_sync_device_names(hass)

    async def handle_reload(call):
        """Handle the service call to reload the integration."""
        _LOGGER.info("Reloading Loxone integration via service call")
        entries = hass.config_entries.async_entries(DOMAIN)
        unloads = [
            hass.config_entries.async_unload(entry.entry_id) for entry in entries
        ]
        await asyncio.gather(*unloads)
        loads = [hass.config_entries.async_reload(entry.entry_id) for entry in entries]
        await asyncio.gather(*loads)
        _LOGGER.info("Loxone integration reload complete")

    hass.services.async_register(
        DOMAIN, "event_websocket_command", handle_websocket_command
    )
    hass.services.async_register(
        DOMAIN, "event_secured_websocket_command", handle_secured_websocket_command
    )
    hass.services.async_register(DOMAIN, "sync_areas", handle_sync_areas)
    hass.services.async_register(DOMAIN, "sync_device_names", handle_sync_device_names)
    hass.services.async_register(DOMAIN, "reload", handle_reload)


async def async_unload_entry(hass, config_entry):
    """Completely unloads the Loxone integration and closes all connections."""
    coordinator = hass.data.get(DOMAIN, {}).get(config_entry.entry_id)

    if coordinator is not None:
        try:
            await coordinator.async_cleanup()
        except Exception as e:
            _LOGGER.warning("Error during cleanup: %s", e)

        if hasattr(coordinator, "bridge_runtime") and coordinator.bridge_runtime:
            await coordinator.bridge_runtime.async_teardown()

        hass.data[DOMAIN].pop(config_entry.entry_id, None)

    unload_ok = await hass.config_entries.async_unload_platforms(
        config_entry, LOXONE_PLATFORMS
    )
    return unload_ok


async def async_setup(hass, config):
    """Set up the Loxone integration."""
    hass.data.setdefault(DOMAIN, {})

    if DOMAIN in config:
        hass.async_create_task(
            hass.config_entries.flow.async_init(
                DOMAIN, context={"source": "import"}, data=config[DOMAIN]
            )
        )

    _async_register_services(hass)
    return True


async def async_migrate_entry(hass, config_entry):
    # _LOGGER.debug("Migrating from version %s", config_entry.version)
    if config_entry.version == 1:
        new = {**config_entry.options, CONF_LIGHTCONTROLLER_SUBCONTROLS_GEN: True}
        config_entry.options = {**new}
        config_entry.version = 2
        _LOGGER.info("Migration to version %s successful", 2)

    if config_entry.version == 2:
        new = {**config_entry.options, CONF_SCENE_GEN_DELAY: DEFAULT_DELAY_SCENE}
        config_entry.options = {**new}
        config_entry.version = 3
        _LOGGER.info("Migration to version %s successful", 3)
    return True


async def async_set_options(hass, config_entry):
    options_in = {**config_entry.options}
    options = {
        CONF_HOST: options_in.pop(CONF_HOST, ""),
        CONF_PORT: options_in.pop(CONF_PORT, DEFAULT_PORT),
        CONF_USERNAME: options_in.pop(CONF_USERNAME, ""),
        CONF_PASSWORD: options_in.pop(CONF_PASSWORD, ""),
        CONF_SCENE_GEN: options_in.pop(CONF_SCENE_GEN, ""),
        CONF_SCENE_GEN_DELAY: options_in.pop(CONF_SCENE_GEN_DELAY, DEFAULT_DELAY_SCENE),
        CONF_LIGHTCONTROLLER_SUBCONTROLS_GEN: options_in.pop(
            CONF_LIGHTCONTROLLER_SUBCONTROLS_GEN, ""
        ),
    }
    hass.config_entries.async_update_entry(
        config_entry, data=config_entry.data, options=options
    )


async def async_config_entry_updated(hass, entry) -> None:
    """Handle signals of config entry being updated.

    This is a static method because a class method (bound method), can not be used with weak references.
    Causes for this is either discovery updating host address or config entry options changing.
    """
    pass


async def create_group_for_loxone_entities(hass, entities, name, object_id):
    try:
        await group.Group.async_create_group(
            hass,
            name,
            created_by_service=False,
            entity_ids=entities,
            icon=None,
            mode=None,
            object_id=object_id,
            order=None,
        )
    except HomeAssistantError as err:
        await group.Group.async_create_group(
            hass,
            name,
            created_by_service=True,
            entity_ids=entities,
            icon=None,
            mode=None,
            object_id=object_id,
            order=None,
        )
        _LOGGER.error("Can't create group '%s' with error: %s", name, err)
    except Exception as e:
        _LOGGER.error(
            "Can't create group '%s'. Try to make at least one group manually. ("
            "https://www.home-assistant.io/integrations/group/)",
            e,
        )


async def async_setup_entry(hass, config_entry):
    if not config_entry.options:
        await async_set_options(hass, config_entry)

    coordinator = LoxoneCoordinator(hass, config_entry)
    host = config_entry.options.get(CONF_HOST)

    _LOGGER.info(
        "Setting up Loxone integration for Miniserver at %s:%s",
        host,
        config_entry.options.get(CONF_PORT),
    )

    try:
        await coordinator.async_config_entry_first_refresh()
    except LoxoneServiceUnAvailableError as err:
        _LOGGER.warning(
            "Loxone Miniserver at %s is unavailable (service restarting?). Will retry automatically",
            host,
        )
        raise ConfigEntryNotReady from err
    except LoxoneUnauthorisedError:
        _LOGGER.error(
            "Could not connect to Loxone Miniserver. Unauthorised. Please check username and password."
        )
        return False
    except OSError as err:
        await coordinator.api.close()
        _LOGGER.warning(
            "Network error connecting to Loxone Miniserver at %s: %s. Will retry automatically",
            host,
            err,
        )
        raise ConfigEntryNotReady from err
    except (LoxoneConnectionError, LoxoneConnectionClosedOk, TimeoutError, ConnectionError) as err:
        await coordinator.api.close()
        _LOGGER.warning(
            "Could not connect to Loxone Miniserver at %s: %s. Will retry automatically",
            host,
            err,
        )
        raise ConfigEntryNotReady from err
    except Exception as err:
        await coordinator.api.close()
        _LOGGER.warning(
            "Unexpected error connecting to Loxone Miniserver at %s: %s. Will retry automatically",
            host,
            err,
        )
        raise ConfigEntryNotReady from err

    _LOGGER.info(
        "Successfully connected to Loxone Miniserver at %s",
        host,
    )

    hass.data.setdefault(DOMAIN, {})[config_entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(config_entry, LOXONE_PLATFORMS)

    # YAML-based custom sensors/binary_sensors (documented "Advanced usage" escape hatch)
    yaml_platforms = [Platform.SENSOR, Platform.BINARY_SENSOR]
    yaml_tasks = [
        hass.async_create_task(
            async_load_platform(hass, platform, DOMAIN, {}, config_entry)
        )
        for platform in yaml_platforms
    ]
    if yaml_tasks:
        await asyncio.wait(yaml_tasks)

    async def loxone_discovered(event):
        miniserver = get_miniserver_from_hass(hass)
        if miniserver.miniserver_type < 2 and "component" in event.data:
            if event.data["component"] == DOMAIN:
                try:
                    _LOGGER.info("loxone discovered")
                    await asyncio.sleep(0.1)
                    # await sync_areas_with_loxone()
                    entity_ids = hass.states.async_all()
                    sensors_analog = []
                    sensors_digital = []
                    switches = []
                    covers = []
                    lights = []
                    dimmers = []
                    climates = []
                    fans = []
                    accontrols = []
                    numbers = []
                    texts = []
                    buttons = []

                    for s in entity_ids:
                        s_dict = s.as_dict()
                        attr = s_dict["attributes"]
                        if "platform" in attr and attr["platform"] == DOMAIN:
                            device_type = attr.get("device_type", "")
                            if device_type in ["analog_sensor", "Meter"]:
                                sensors_analog.append(s_dict["entity_id"])
                            elif device_type == "digital_sensor":
                                sensors_digital.append(s_dict["entity_id"])
                            elif device_type in ["Jalousie", "Gate", "Window"]:
                                covers.append(s_dict["entity_id"])
                            elif device_type in ["Switch", "TimedSwitch"]:
                                switches.append(s_dict["entity_id"])
                            elif device_type == "Pushbutton":
                                buttons.append(s_dict["entity_id"])
                            elif device_type in ["LightControllerV2"]:
                                lights.append(s_dict["entity_id"])
                            elif device_type == "Dimmer":
                                dimmers.append(s_dict["entity_id"])
                            elif device_type == "IRoomControllerV2":
                                climates.append(s_dict["entity_id"])
                            elif device_type == "Ventilation":
                                fans.append(s_dict["entity_id"])
                            elif device_type == "AcControl":
                                accontrols.append(s_dict["entity_id"])
                            elif device_type == "Slider":
                                numbers.append(s_dict["entity_id"])
                            elif device_type == "TextInput":
                                texts.append(s_dict["entity_id"])

                    sensors_analog.sort()
                    sensors_digital.sort()
                    covers.sort()
                    switches.sort()
                    buttons.sort()
                    lights.sort()
                    climates.sort()
                    dimmers.sort()
                    fans.sort()
                    accontrols.sort()
                    numbers.sort()
                    texts.sort()
                    await async_setup_component(hass, "group", {})
                    await create_group_for_loxone_entities(
                        hass, sensors_analog, "Loxone Analog Sensors", "loxone_analog"
                    )
                    await create_group_for_loxone_entities(
                        hass,
                        sensors_digital,
                        "Loxone Digital Sensors",
                        "loxone_digital",
                    )
                    await create_group_for_loxone_entities(
                        hass, switches, "Loxone Switches", "loxone_switches"
                    )
                    await create_group_for_loxone_entities(
                        hass, buttons, "Loxone Buttons", "loxone_buttons"
                    )
                    await create_group_for_loxone_entities(
                        hass, covers, "Loxone Covers", "loxone_covers"
                    )
                    await create_group_for_loxone_entities(
                        hass, lights, "Loxone LightControllers", "loxone_lights"
                    )
                    await create_group_for_loxone_entities(
                        hass, lights, "Loxone Dimmer", "loxone_dimmers"
                    )
                    await create_group_for_loxone_entities(
                        hass, climates, "Loxone Room Controllers", "loxone_climates"
                    )
                    await create_group_for_loxone_entities(
                        hass,
                        fans,
                        "Loxone Ventilation Controllers",
                        "loxone_ventilations",
                    )
                    await create_group_for_loxone_entities(
                        hass,
                        accontrols,
                        "Loxone AC Controllers",
                        "loxone_accontrollers",
                    )
                    await create_group_for_loxone_entities(
                        hass, numbers, "Loxone Numbers", "loxone_numbers"
                    )
                    await create_group_for_loxone_entities(
                        hass, texts, "Loxone Texts", "loxone_texts"
                    )
                    await hass.async_block_till_done()
                    await create_group_for_loxone_entities(
                        hass,
                        [
                            "group.loxone_analog",
                            "group.loxone_digital",
                            "group.loxone_switches",
                            "group.loxone_buttons",
                            "group.loxone_covers",
                            "group.loxone_lights",
                            "group.loxone_ventilations",
                            "group.loxone_numbers",
                            "group.loxone_texts",
                        ],
                        "Loxone Group",
                        "loxone_group",
                    )
                except Exception as err:
                    _LOGGER.error(
                        "Can't create group '%s'. Try to make at least one group manually. ("
                        "https://www.home-assistant.io/integrations/group/)",
                        err,
                    )

    async def loxone_send(event):
        """Listen for change Events from Loxone Components"""
        try:
            if event.event_type == SENDDOMAIN and isinstance(event.data, dict):
                value = event.data.get(ATTR_VALUE, DEFAULT)
                device_uuid = event.data.get(ATTR_UUID, DEFAULT)
                if value is None:
                    value = DEFAULT
                if device_uuid is None:
                    device_uuid = DEFAULT

                asyncio.create_task(
                    coordinator.async_send_command(device_uuid, value)
                )

            elif event.event_type == SECUREDSENDDOMAIN and isinstance(event.data, dict):
                value = event.data.get(ATTR_VALUE, DEFAULT)
                device_uuid = event.data.get(ATTR_UUID, DEFAULT)
                code = event.data.get(ATTR_CODE, DEFAULT)
                if code is None:
                    code = DEFAULT
                if value is None:
                    value = DEFAULT
                if device_uuid is None:
                    device_uuid = DEFAULT
                asyncio.create_task(
                    coordinator.async_send_secured_command(
                        device_uuid, value, code
                    )
                )

        except Exception as e:
            _LOGGER.error(e)

    # -- Device Bridges (HA entity <-> Loxone control) ------------------------

    bridge_runtime = BridgeRuntime(hass, coordinator, config_entry)
    await bridge_runtime.async_setup()
    coordinator.bridge_runtime = bridge_runtime

    # Auto-sync: align HA device names and areas with Loxone structure.
    # On first setup, honour the user's "create areas" preference from the
    # config flow.  On subsequent restarts only assign to existing areas.
    initial_sync_done = config_entry.data.get("initial_sync_done", False)
    if initial_sync_done:
        create_areas = False
    else:
        create_areas = config_entry.options.get(CONF_CREATE_AREAS, True)

    try:
        await _async_sync_device_names(hass)
        await _async_sync_areas(hass, {ATTR_AREA_CREATE: create_areas})
        if not initial_sync_done:
            hass.config_entries.async_update_entry(
                config_entry,
                data={**config_entry.data, "initial_sync_done": True},
            )
    except Exception:
        _LOGGER.warning(
            "Auto-sync failed during setup; you can retry via "
            "loxone.sync_areas / loxone.sync_device_names services",
            exc_info=True,
        )

    async def _async_options_updated(hass_ref, entry):
        coord = hass_ref.data.get(DOMAIN, {}).get(entry.entry_id)
        if coord and hasattr(coord, "bridge_runtime") and coord.bridge_runtime:
            await coord.bridge_runtime.async_options_updated()

    config_entry.async_on_unload(
        config_entry.add_update_listener(_async_options_updated)
    )

    hass.bus.async_listen_once(EVENT_COMPONENT_LOADED, loxone_discovered)

    # Store listeners for cleanup
    coordinator.listeners = [
        hass.bus.async_listen(SENDDOMAIN, loxone_send),
        hass.bus.async_listen(SECUREDSENDDOMAIN, loxone_send),
    ]

    await coordinator.async_start_listening()

    return True


async def async_remove_config_entry_device(
    hass: HomeAssistant, config_entry: ConfigEntry, device_entry: DeviceEntry
) -> bool:
    """Remove a config entry from a device."""
    return True


class LoxoneEntity(Entity):
    """
    @DynamicAttrs
    """

    _SKIP_KWARGS = frozenset({"device_info"})

    def __init__(self, **kwargs):
        for key in kwargs:
            if key in self._SKIP_KWARGS:
                continue
            if not hasattr(self, key):
                if key == "name":
                    self._attr_name = kwargs[key]
                else:
                    setattr(self, key, kwargs[key])
            else:
                try:
                    setattr(self, key, kwargs[key])
                except AttributeError:
                    _LOGGER.error("Could not set %s for %s", key, self.name)
                except Exception:
                    _LOGGER.exception("Unexpected error setting %s", key)

        self.listener = None
        self._prev_available: bool | None = None

        # Initialize base extra state attributes with common Loxone fields
        self._attr_extra_state_attributes = {
            "uuid": kwargs.get("uuidAction", ""),
            "platform": "loxone",
        }

        # Add optional common attributes from Loxone JSON if they exist
        if "room" in kwargs and kwargs["room"]:
            self._attr_extra_state_attributes["room"] = kwargs["room"]
        if "cat" in kwargs and kwargs["cat"]:
            self._attr_extra_state_attributes["category"] = kwargs["cat"]

    @property
    def available(self) -> bool:
        coordinator = _get_coordinator(self.hass)
        if coordinator is None:
            return True
        return coordinator.last_update_success

    async def async_added_to_hass(self):
        """Subscribe to device events and coordinator availability updates."""
        self.listener = self.hass.bus.async_listen(EVENT, self.event_handler)
        self._register_coordinator_listener()

    def _register_coordinator_listener(self):
        """Subscribe to coordinator updates so availability changes propagate."""
        coordinator = _get_coordinator(self.hass)
        if coordinator:
            self.async_on_remove(
                coordinator.async_add_listener(self._handle_coordinator_update)
            )

    def _handle_coordinator_update(self) -> None:
        """Called when the coordinator's state changes — only write if availability flipped."""
        current = self.available
        if current != self._prev_available:
            self._prev_available = current
            self.async_write_ha_state()

    async def async_will_remove_from_hass(self):
        """Disconnect callbacks."""
        self.listener = None

    async def event_handler(self, e):
        pass

    @property
    def device_info(self) -> DeviceInfo | None:
        """Return device info linking this entity to a Loxone device."""
        if hasattr(self, "_attr_device_info") and self._attr_device_info is not None:
            return self._attr_device_info
        if not hasattr(self, "uuidAction"):
            return None
        info = DeviceInfo(
            identifiers={(DOMAIN, self.uuidAction)},
            name=self._attr_name,
            manufacturer="Loxone",
            model=getattr(self, "type", None),
            suggested_area=getattr(self, "room", None),
        )
        try:
            serial = get_miniserver_from_hass(self.hass).serial
            if serial:
                info["via_device"] = (DOMAIN, serial)
        except (KeyError, AttributeError):
            pass
        return info

    @cached_property
    def name(self):
        return self._attr_name

    # @name.setter
    # def name(self, n):
    #     self._attr_name = n

    @staticmethod
    def _clean_unit(lox_format):
        search = re.search(cfmt, lox_format, flags=re.X)
        if search:
            unit = lox_format.replace(search.group(0).strip(), "").strip()
            if unit == "%%":
                unit = unit.replace("%%", "%")
            return unit
        else:
            return lox_format

    @staticmethod
    def _get_format(lox_format):
        search = re.search(cfmt, lox_format, flags=re.X)
        if search:
            return search.group(0).strip()
        return None

    @cached_property
    def unique_id(self) -> str:
        """Return a unique ID."""
        return self.uuidAction
