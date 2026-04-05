"""Shared types for the device bridge subsystem.

Kept in a separate module so that both ``bridge.py`` (runtime) and
``bridge_mappers.py`` (concrete mapper implementations) can import them
without creating a circular dependency.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from typing import Any

from homeassistant.core import HomeAssistant, State

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
        """To dict."""
        d = asdict(self)
        return {k: v for k, v in d.items() if v or k == "cooldown"}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DeviceBridge:
        """From dict."""
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
# Mapper abstract base class
# ---------------------------------------------------------------------------


class BridgeMapper(ABC):
    """Translates between HA entity state and Loxone control values."""

    def __init__(self, bridge: DeviceBridge) -> None:
        """Initialize the BridgeMapper."""
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

    async def loxone_value_to_ha(self, hass: HomeAssistant, uuid: str, value: Any) -> None:
        """Push a Loxone value into the bound HA entity.

        Default implementation does nothing (expose-only mappers).
        """

    @property
    def description(self) -> str:
        """Human-readable summary for the options-flow UI."""
        return f"{self.bridge.loxone_type} bridge"
