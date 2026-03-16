"""Device-level bridge between HA entities and Loxone controls.

Maps a single HA entity to a single Loxone control (or sub-control).
The integration auto-detects the mapping from the HA entity domain and
Loxone control type, handling value conversion, scaling, cooldown, and
echo protection automatically.

Bridges are persisted in ``config_entry.options["bridges"]`` and restored
on integration (re)load.
"""

from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from typing import Any, Callable

from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import (
    CALLBACK_TYPE,
    Event,
    HomeAssistant,
    State,
    callback,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.event import async_track_state_change_event, async_call_later

from .const import EVENT

_LOGGER = logging.getLogger(__name__)

DEFAULT_COOLDOWN = 1.0
VALUE_EPSILON = 0.5


# ---------------------------------------------------------------------------
# Persistence model
# ---------------------------------------------------------------------------

@dataclass
class DeviceBridge:
    """Persisted configuration for a single device bridge."""

    entity_id: str
    loxone_uuid: str
    loxone_type: str
    loxone_states: dict[str, str] = field(default_factory=dict)
    loxone_name: str = ""
    cooldown: float = DEFAULT_COOLDOWN
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        return {k: v for k, v in d.items() if v or k in ("cooldown",)}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DeviceBridge:
        return cls(
            entity_id=data["entity_id"],
            loxone_uuid=data["loxone_uuid"],
            loxone_type=data["loxone_type"],
            loxone_states=data.get("loxone_states", {}),
            loxone_name=data.get("loxone_name", ""),
            cooldown=data.get("cooldown", DEFAULT_COOLDOWN),
            details=data.get("details", {}),
        )


# ---------------------------------------------------------------------------
# Mapper ABC
# ---------------------------------------------------------------------------

class BridgeMapper(ABC):
    """Translates between HA entity state and Loxone control values."""

    def __init__(self, bridge: DeviceBridge) -> None:
        self.bridge = bridge

    @property
    @abstractmethod
    def expose_supported(self) -> bool:
        """Whether HA -> Loxone direction is active."""

    @property
    @abstractmethod
    def subscribe_supported(self) -> bool:
        """Whether Loxone -> HA direction is active."""

    @property
    def subscribe_uuids(self) -> set[str]:
        """Loxone state UUIDs to watch for incoming changes."""
        return set()

    @abstractmethod
    def ha_state_to_command(self, state: State) -> tuple[str, Any] | None:
        """Convert HA state to a single ``(loxone_uuid, value)`` command.

        Return *None* when nothing should be sent (e.g. unavailable state).
        """

    async def loxone_value_to_ha(
        self, hass: HomeAssistant, uuid: str, value: Any
    ) -> None:
        """Push a Loxone value into the bound HA entity.

        Default implementation does nothing (expose-only mappers).
        """

    @property
    def description(self) -> str:
        """Human-readable summary for the options-flow UI."""
        return f"{self.bridge.loxone_type} bridge"


# ---------------------------------------------------------------------------
# Runtime state per active bridge
# ---------------------------------------------------------------------------

@dataclass
class _ActiveBridge:
    bridge: DeviceBridge
    mapper: BridgeMapper
    last_sent_value: Any = None
    last_sent_time: float = 0.0
    last_received_value: Any = None
    pending_command: tuple[str, Any] | None = field(default=None, repr=False)
    cancel_ha_listener: CALLBACK_TYPE | None = field(default=None, repr=False)
    cancel_lox_listener: CALLBACK_TYPE | None = field(default=None, repr=False)
    cancel_cooldown: CALLBACK_TYPE | None = field(default=None, repr=False)
    _echo_suppress: bool = field(default=False, repr=False)


def _values_equal(a: Any, b: Any) -> bool:
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
        await self.async_teardown()
        await self.async_setup()

    # -- internal ------------------------------------------------------------

    def _activate(self, bridge: DeviceBridge) -> None:
        from .bridge_mappers import get_mapper

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
            ab.cancel_lox_listener = self.hass.bus.async_listen(
                EVENT, self._make_lox_listener(ab)
            )

        _LOGGER.info(
            "Bridge activated: %s <-> %s (%s) [expose=%s, subscribe=%s]",
            bridge.entity_id,
            bridge.loxone_name or bridge.loxone_uuid,
            bridge.loxone_type,
            mapper.expose_supported,
            mapper.subscribe_supported,
        )

    def _deactivate(self, ab: _ActiveBridge) -> None:
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
        @callback
        def _listener(event: Event) -> None:
            new_state: State | None = event.data.get("new_state")
            if new_state is None:
                return
            self._process_ha_state(ab, new_state)
        return _listener

    @callback
    def _process_ha_state(self, ab: _ActiveBridge, state: State) -> None:
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
                    ab.cancel_cooldown = None
                    if ab.pending_command is not None:
                        _, pval = ab.pending_command
                        if not _values_equal(pval, ab.last_sent_value):
                            self._send(ab, ab.pending_command)
                    ab.pending_command = None

                ab.cancel_cooldown = async_call_later(
                    self.hass, remaining, _flush
                )

    def _send(self, ab: _ActiveBridge, cmd: tuple[str, Any]) -> None:
        uuid, value = cmd
        ab.last_sent_value = value
        ab.last_sent_time = time.monotonic()
        ab.pending_command = None
        if ab.mapper.subscribe_supported:
            ab._echo_suppress = True
        self.hass.async_create_task(
            self.coordinator.api.send_websocket_command(uuid, value)
        )
        _LOGGER.debug(
            "Bridge %s -> %s: sent %r",
            ab.bridge.entity_id,
            ab.bridge.loxone_name or ab.bridge.loxone_uuid,
            value,
        )

    # -- subscribe direction (Loxone -> HA) ---------------------------------

    def _make_lox_listener(self, ab: _ActiveBridge) -> Callable:
        watch = ab.mapper.subscribe_uuids

        @callback
        def _listener(event: Event) -> None:
            for uuid in watch:
                if uuid not in event.data:
                    continue
                value = event.data[uuid]

                if ab._echo_suppress:
                    ab._echo_suppress = False
                    return

                if _values_equal(value, ab.last_received_value):
                    return

                ab.last_received_value = value
                self.hass.async_create_task(
                    self._handle_lox_value(ab, uuid, value)
                )
                return
        return _listener

    async def _handle_lox_value(
        self, ab: _ActiveBridge, uuid: str, value: Any
    ) -> None:
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
                ab.bridge.entity_id, value,
            )

    # -- persistence ---------------------------------------------------------

    def _persist(self) -> None:
        self._self_update = True
        new_opts = dict(self.config_entry.options)
        new_opts["bridges"] = [ab.bridge.to_dict() for ab in self._active]
        self.hass.config_entries.async_update_entry(
            self.config_entry, options=new_opts
        )
