"""Loxone Scenes.

For more details about this component, please refer to the documentation at
https://github.com/JoDehli/PyLoxone
"""

import logging

from homeassistant.components.scene import Scene
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_call_later

from . import LoxoneConfigEntry
from .const import CONF_SCENE_GEN, CONF_SCENE_GEN_DELAY, DEFAULT_DELAY_SCENE, DOMAIN, SENDDOMAIN
from .coordinator import LoxoneCoordinator

_LOGGER = logging.getLogger(__name__)

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: LoxoneConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Scenes after all other platforms are loaded."""
    delay_scene = config_entry.options.get(CONF_SCENE_GEN_DELAY, DEFAULT_DELAY_SCENE)
    create_scene = config_entry.options.get(CONF_SCENE_GEN, False)

    if not create_scene:
        return

    coordinator: LoxoneCoordinator = config_entry.runtime_data
    entry_id = config_entry.entry_id

    async def gen_scenes():
        """Generate scenes from light entities."""
        _LOGGER.debug("Loading scenes...")
        scenes = []

        if "light" not in hass.data:
            _LOGGER.warning("Light platform not ready, skipping scene generation")
            return

        entity_ids = hass.states.async_entity_ids("light")

        for entity_id in entity_ids:
            state = hass.states.get(entity_id)
            if not state:
                continue

            att = state.attributes
            if att.get("platform") != DOMAIN:
                continue

            entity = hass.data["light"].get_entity(entity_id)
            if not entity or entity.device_class != "LightControllerV2":
                continue

            for effect in entity.effect_list:
                mood_id = entity.get_id_by_moodname(effect)
                uuid = entity.uuidAction
                scenes.append(
                    LoxoneLightScene(
                        name=f"{entity.name}-{effect}",
                        mood_id=mood_id,
                        uuid=uuid,
                        light_controller_id=entity.unique_id,
                        entry_id=entry_id,
                        miniserver_serial=coordinator.miniserver.serial if coordinator.miniserver else None,
                    )
                )

        if scenes:
            async_add_entities(scenes)
            _LOGGER.info("Generated %d scenes", len(scenes))
        else:
            _LOGGER.warning("No scenes generated")

    async_call_later(hass, delay_scene, lambda _now: hass.async_create_task(gen_scenes()))


class LoxoneLightScene(Scene):
    """Representation of a Loxone light scene."""

    _attr_has_entity_name = True

    def __init__(self, name, mood_id, uuid, light_controller_id, entry_id, miniserver_serial=None):
        """Initialize the LoxoneLightScene."""
        self._attr_name = name
        self.mood_id = mood_id
        self.uuidAction = uuid
        self._light_controller_id = light_controller_id
        self._entry_id = entry_id
        self._miniserver_serial = miniserver_serial

    @property
    def unique_id(self) -> str:
        """Return a unique ID for this entity."""
        return f"{self._light_controller_id}-{self.mood_id}"

    @property
    def device_info(self) -> DeviceInfo | None:
        """Return device information."""
        if self._miniserver_serial:
            return DeviceInfo(
                identifiers={(DOMAIN, self._light_controller_id)},
                via_device=(DOMAIN, self._miniserver_serial),
            )
        return DeviceInfo(
            identifiers={(DOMAIN, self._light_controller_id)},
        )

    async def async_activate(self, **kwargs):
        """Activate asynchronously."""
        self.hass.bus.async_fire(
            SENDDOMAIN,
            {
                "uuid": self.uuidAction,
                "value": f"changeTo/{self.mood_id}",
                "miniserver": self._entry_id,
            },
        )
