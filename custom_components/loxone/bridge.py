"""Device-level bridge between HA entities and Loxone controls.

Maps a single HA entity to a single Loxone control (or sub-control).
The integration auto-detects the mapping from the HA entity domain and
Loxone control type, handling value conversion, scaling, cooldown, and
echo protection automatically.

Bridges are persisted in ``config_entry.options["bridges"]`` and restored
on integration (re)load.

Shared types (``DeviceBridge``, ``BridgeMapper``) live in ``bridge_types``
so that ``bridge_mappers`` can import them without a circular dependency.
``BridgeMapper`` and ``DeviceBridge`` are re-exported here for backwards
compatibility with callers that import from this module.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
import logging
import time
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import CALLBACK_TYPE, Event, HomeAssistant, State, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.event import async_call_later, async_track_state_change_event

from .bridge_mappers import get_mapper
from .bridge_types import DEFAULT_COOLDOWN, VALUE_EPSILON, BridgeMapper, DeviceBridge
from .const import DOMAIN

__all__ = ["DEFAULT_COOLDOWN", "VALUE_EPSILON", "BridgeMapper", "BridgeRuntime", "DeviceBridge"]

_LOGGER = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Runtime state per active bridge
# ---------------------------------------------------------------------------


@dataclass
class _ActiveBridge:
    """Represent _ active bridge."""

    bridge: DeviceBridge
    mapper: BridgeMapper
    last_sent_value: Any = None
    last_sent_time: float = 0.0
    last_received_value: Any = None
    pending_command: tuple[str, Any] | None = field(default=None, repr=False)
    cancel_ha_listener: CALLBACK_TYPE | None = field(default=None, repr=False)
    cancel_lox_listener: CALLBACK_TYPE | None = field(default=None, repr=False)
    cancel_cooldown: CALLBACK_TYPE | None = field(default=None, repr=False)
    echo_suppress: bool = field(default=False, repr=False)


def _values_equal(a: Any, b: Any) -> bool:
    """Return values equal."""
    if a is None or b is None:
        return a is b
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return abs(float(a) - float(b)) < VALUE_EPSILON
    return str(a) == str(b)


# ---------------------------------------------------------------------------
# Bridge runtime
# ---------------------------------------------------------------------------


class BridgeRuntime:
    """Manages device bridges between HA entities and Loxone controls."""

    def __init__(
        self,
        hass: HomeAssistant,
        coordinator: Any,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the BridgeRuntime."""
        self.hass = hass
        self.coordinator = coordinator
        self.config_entry = config_entry
        self._active: list[_ActiveBridge] = []
        self._self_update = False

    @property
    def bridged_uuids(self) -> set[str]:
        """Loxone ``uuidAction`` values currently used by a bridge."""
        return {ab.bridge.loxone_uuid for ab in self._active}

    async def async_setup(self) -> None:
        """Restore persisted bridges and start listeners."""
        raw_list = self.config_entry.options.get("bridges", [])
        for raw in raw_list:
            try:
                bridge = DeviceBridge.from_dict(raw)
                self._activate(bridge)
            except Exception:
                _LOGGER.exception("Failed to restore bridge: %s", raw)
        self._sync_entity_disabled_state()

    async def async_teardown(self) -> None:
        """Cancel all listeners and timers."""
        for ab in self._active:
            self._deactivate(ab)
        self._active.clear()

    async def async_options_updated(self) -> None:
        """Re-init after config_entry.options changed externally."""
        if self._self_update:
            self._self_update = False
            return
        old_uuids = self.bridged_uuids
        await self.async_teardown()
        await self.async_setup()
        # Re-enable entities that are no longer bridged
        removed = old_uuids - self.bridged_uuids
        if removed:
            self._reenable_entities(removed)

    # -- entity disable/enable -----------------------------------------------

    def _sync_entity_disabled_state(self) -> None:
        """Disable native Loxone entities whose control is used by a bridge."""
        registry = er.async_get(self.hass)
        for uuid in self.bridged_uuids:
            entry = registry.async_get_entity_id(None, DOMAIN, uuid)
            if entry is None:
                # Try all platforms — async_get_entity_id needs a domain
                for ent in registry.entities.values():
                    if ent.platform == DOMAIN and ent.unique_id == uuid:
                        entry = ent.entity_id
                        break
            if entry is None:
                continue
            ent_entry = registry.async_get(entry)
            if ent_entry and ent_entry.disabled_by != er.RegistryEntryDisabler.INTEGRATION:
                registry.async_update_entity(entry, disabled_by=er.RegistryEntryDisabler.INTEGRATION)
                _LOGGER.info("Disabled entity %s — control used by device bridge", entry)

    def _reenable_entities(self, uuids: set[str]) -> None:
        """Re-enable entities whose bridge was removed."""
        registry = er.async_get(self.hass)
        for ent in registry.entities.values():
            if (
                ent.platform == DOMAIN
                and ent.unique_id in uuids
                and ent.disabled_by == er.RegistryEntryDisabler.INTEGRATION
            ):
                registry.async_update_entity(ent.entity_id, disabled_by=None)
                _LOGGER.info("Re-enabled entity %s — bridge removed", ent.entity_id)

    # -- internal ------------------------------------------------------------

    @property
    def active_bridges(self) -> list[_ActiveBridge]:
        """Return the list of active bridge bindings (same module; for WS API)."""
        return self._active

    def register_bridge(self, bridge: DeviceBridge) -> None:
        """Add and wire a bridge (restore, options flow, or WS)."""
        self._activate(bridge)

    def persist_bridge_options(self) -> None:
        """Persist ``bridges`` into the config entry."""
        self._persist()

    def unregister_bridge(self, ab: _ActiveBridge) -> None:
        """Tear down a bridge, re-enable native entities, and save options."""
        removed_uuid = ab.bridge.loxone_uuid
        self._deactivate(ab)
        self._active.remove(ab)
        self._reenable_entities({removed_uuid})
        self._persist()

    def _activate(self, bridge: DeviceBridge) -> None:
        """Attach mapper, listeners, and logging for one bridge."""
        entity_domain = bridge.entity_id.split(".")[0]
        mapper = get_mapper(bridge, entity_domain)

        ab = _ActiveBridge(bridge=bridge, mapper=mapper)
        self._active.append(ab)

        if mapper.expose_supported:
            ab.cancel_ha_listener = async_track_state_change_event(
                self.hass, [bridge.entity_id], self._make_ha_listener(ab)
            )
            state = self.hass.states.get(bridge.entity_id)
            if state is not None:
                self._process_ha_state(ab, state)

        if mapper.subscribe_supported and mapper.subscribe_uuids:
            listener = self._make_lox_listener(ab)
            prefix = self.coordinator.dispatcher_prefix
            cancel_fns = [
                async_dispatcher_connect(self.hass, f"{prefix}{uuid}", listener) for uuid in mapper.subscribe_uuids
            ]
            ab.cancel_lox_listener = lambda fns=cancel_fns: [fn() for fn in fns]

        _LOGGER.info(
            "Bridge activated: %s <-> %s (%s) [expose=%s, subscribe=%s]",
            bridge.entity_id,
            bridge.loxone_name or bridge.loxone_uuid,
            bridge.loxone_type,
            mapper.expose_supported,
            mapper.subscribe_supported,
        )

    def _deactivate(self, ab: _ActiveBridge) -> None:
        """Tear down listeners and timers for one active bridge."""
        if ab.cancel_ha_listener:
            ab.cancel_ha_listener()
            ab.cancel_ha_listener = None
        if ab.cancel_lox_listener:
            ab.cancel_lox_listener()
            ab.cancel_lox_listener = None
        if ab.cancel_cooldown:
            ab.cancel_cooldown()
            ab.cancel_cooldown = None

    # -- expose direction (HA -> Loxone) ------------------------------------

    def _make_ha_listener(self, ab: _ActiveBridge) -> Callable:
        """Build a callback that reacts to Home Assistant state changes."""

        @callback
        def _listener(event: Event) -> None:
            """Handle a tracked entity state change event."""
            new_state: State | None = event.data.get("new_state")
            if new_state is None:
                return
            self._process_ha_state(ab, new_state)

        return _listener

    @callback
    def _process_ha_state(self, ab: _ActiveBridge, state: State) -> None:
        """Map HA state to a Loxone command, respecting cooldown and echo."""
        if str(state.state) in (STATE_UNAVAILABLE, STATE_UNKNOWN):
            return

        cmd = ab.mapper.ha_state_to_command(state)
        if cmd is None:
            return

        _uuid, value = cmd
        if _values_equal(value, ab.last_sent_value):
            return

        now = time.monotonic()
        elapsed = now - ab.last_sent_time

        if elapsed >= ab.bridge.cooldown:
            self._send(ab, cmd)
        else:
            ab.pending_command = cmd
            if ab.cancel_cooldown is None:
                remaining = ab.bridge.cooldown - elapsed

                @callback
                def _flush(_now: Any) -> None:
                    """Send a pending command once the cooldown elapses."""
                    ab.cancel_cooldown = None
                    if ab.pending_command is not None:
                        _, pval = ab.pending_command
                        if not _values_equal(pval, ab.last_sent_value):
                            self._send(ab, ab.pending_command)
                    ab.pending_command = None

                ab.cancel_cooldown = async_call_later(self.hass, remaining, _flush)

    def _send(self, ab: _ActiveBridge, cmd: tuple[str, Any]) -> None:
        """Enqueue a websocket command to Loxone and update send bookkeeping."""
        uuid, value = cmd
        ab.last_sent_value = value
        ab.last_sent_time = time.monotonic()
        ab.pending_command = None
        if ab.mapper.subscribe_supported:
            ab.echo_suppress = True
        self.hass.async_create_task(self.coordinator.api.send_websocket_command(uuid, value))
        _LOGGER.debug(
            "Bridge %s -> %s: sent %r",
            ab.bridge.entity_id,
            ab.bridge.loxone_name or ab.bridge.loxone_uuid,
            value,
        )

    # -- subscribe direction (Loxone -> HA) ---------------------------------

    def _make_lox_listener(self, ab: _ActiveBridge) -> Callable:
        """Build a callback for Loxone dispatcher messages."""
        watch = ab.mapper.subscribe_uuids

        @callback
        def _listener(message: dict) -> None:
            """Apply incoming Loxone values for subscribed state UUIDs."""
            for uuid in watch:
                if uuid not in message:
                    continue
                value = message[uuid]

                if ab.echo_suppress:
                    ab.echo_suppress = False
                    return

                if _values_equal(value, ab.last_received_value):
                    return

                ab.last_received_value = value
                self.hass.async_create_task(self._handle_lox_value(ab, uuid, value))
                return

        return _listener

    async def _handle_lox_value(self, ab: _ActiveBridge, uuid: str, value: Any) -> None:
        """Push one Loxone value into Home Assistant via the mapper."""
        _LOGGER.debug(
            "Bridge %s <- %s: received %r",
            ab.bridge.entity_id,
            ab.bridge.loxone_name or ab.bridge.loxone_uuid,
            value,
        )
        try:
            await ab.mapper.loxone_value_to_ha(self.hass, uuid, value)
        except Exception:
            _LOGGER.exception(
                "Failed to update %s from Loxone value %r",
                ab.bridge.entity_id,
                value,
            )

    # -- persistence ---------------------------------------------------------

    def _persist(self) -> None:
        """Persist the active bridge list into the config entry options."""
        self._self_update = True
        new_opts = dict(self.config_entry.options)
        new_opts["bridges"] = [ab.bridge.to_dict() for ab in self._active]
        self.hass.config_entries.async_update_entry(self.config_entry, options=new_opts)
