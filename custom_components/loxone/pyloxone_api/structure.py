"""Typed representation of the Loxone structure file (LoxAPP3.json).

Provides dataclass models for the top-level structure, miniserver info,
rooms, categories, and controls.  Parse a raw dict (from the Miniserver
HTTP API) via ``LoxoneStructure.from_dict()``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class MsInfo:
    """Miniserver metadata from ``msInfo``."""

    serial_nr: str = ""
    miniserver_type: int = 0
    ms_name: str = ""
    project_name: str = ""
    location: str = ""
    latitude: float = 0.0
    longitude: float = 0.0
    altitude: float = 0.0
    current_user: dict[str, Any] | None = None

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> MsInfo:
        return cls(
            serial_nr=raw.get("serialNr", ""),
            miniserver_type=raw.get("miniserverType", 0),
            ms_name=raw.get("msName", ""),
            project_name=raw.get("projectName", ""),
            location=raw.get("location", ""),
            latitude=_to_float(raw.get("latitude", 0.0)),
            longitude=_to_float(raw.get("longitude", 0.0)),
            altitude=_to_float(raw.get("altitude", 0.0)),
            current_user=raw.get("currentUser"),
        )


@dataclass(slots=True)
class LoxoneRoom:
    """A Loxone room."""

    uuid: str
    name: str

    @classmethod
    def from_dict(cls, uuid: str, raw: dict[str, Any]) -> LoxoneRoom:
        return cls(uuid=uuid, name=raw.get("name", ""))


@dataclass(slots=True)
class LoxoneCategory:
    """A Loxone category."""

    uuid: str
    name: str

    @classmethod
    def from_dict(cls, uuid: str, raw: dict[str, Any]) -> LoxoneCategory:
        return cls(uuid=uuid, name=raw.get("name", ""))


@dataclass(slots=True)
class LoxoneControl:
    """A single Loxone control (or sub-control).

    Common fields are typed; control-type-specific ``states`` and
    ``details`` remain dicts to avoid an explosion of per-type
    dataclasses at this stage.
    """

    uuid: str
    uuid_action: str
    name: str
    control_type: str
    room_uuid: str = ""
    cat_uuid: str = ""
    states: dict[str, str | list] = field(default_factory=dict)
    details: dict[str, Any] = field(default_factory=dict)
    sub_controls: dict[str, LoxoneControl] = field(default_factory=dict)
    raw: dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, uuid: str, raw: dict[str, Any]) -> LoxoneControl:
        sub_controls: dict[str, LoxoneControl] = {}
        for sc_uuid, sc_raw in raw.get("subControls", {}).items():
            sub_controls[sc_uuid] = cls.from_dict(sc_uuid, sc_raw)

        return cls(
            uuid=uuid,
            uuid_action=raw.get("uuidAction", uuid),
            name=raw.get("name", ""),
            control_type=raw.get("type", ""),
            room_uuid=raw.get("room", ""),
            cat_uuid=raw.get("cat", ""),
            states=dict(raw.get("states", {})),
            details=dict(raw.get("details", {})),
            sub_controls=sub_controls,
            raw=raw,
        )

    def get_state_uuids(self) -> set[str]:
        """Return all state UUIDs this control listens to."""
        uuids: set[str] = set()
        uuids.add(self.uuid_action)
        for v in self.states.values():
            if isinstance(v, str):
                uuids.add(v)
        return uuids


@dataclass(slots=True)
class LoxoneStructure:
    """Parsed LoxAPP3.json structure file.

    Provides typed access to the miniserver metadata, rooms,
    categories, and controls.  The original raw dict is preserved
    in ``raw`` for backward compatibility.
    """

    ms_info: MsInfo = field(default_factory=MsInfo)
    rooms: dict[str, LoxoneRoom] = field(default_factory=dict)
    categories: dict[str, LoxoneCategory] = field(default_factory=dict)
    controls: dict[str, LoxoneControl] = field(default_factory=dict)
    software_version: list[int] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> LoxoneStructure:
        ms_info = MsInfo.from_dict(raw.get("msInfo", {}))

        rooms: dict[str, LoxoneRoom] = {}
        for uuid, room_raw in raw.get("rooms", {}).items():
            rooms[uuid] = LoxoneRoom.from_dict(uuid, room_raw)

        categories: dict[str, LoxoneCategory] = {}
        for uuid, cat_raw in raw.get("cats", {}).items():
            categories[uuid] = LoxoneCategory.from_dict(uuid, cat_raw)

        controls: dict[str, LoxoneControl] = {}
        for uuid, ctrl_raw in raw.get("controls", {}).items():
            controls[uuid] = LoxoneControl.from_dict(uuid, ctrl_raw)

        sw_ver = raw.get("softwareVersion", [])
        if isinstance(sw_ver, str):
            try:
                sw_ver = [int(x) for x in sw_ver.split(".")]
            except ValueError:
                sw_ver = []

        return cls(
            ms_info=ms_info,
            rooms=rooms,
            categories=categories,
            controls=controls,
            software_version=sw_ver if isinstance(sw_ver, list) else [],
            raw=raw,
        )

    @property
    def software_version_str(self) -> str:
        return ".".join(str(x) for x in self.software_version)

    def room_name(self, room_uuid: str) -> str:
        """Look up a room name by UUID, returning empty string if not found."""
        room = self.rooms.get(room_uuid)
        return room.name if room else ""

    def category_name(self, cat_uuid: str) -> str:
        """Look up a category name by UUID, returning empty string if not found."""
        cat = self.categories.get(cat_uuid)
        return cat.name if cat else ""

    def controls_by_type(self, *control_types: str) -> list[LoxoneControl]:
        """Return all controls matching the given type(s)."""
        type_set = set(control_types)
        return [
            ctrl for ctrl in self.controls.values()
            if ctrl.control_type in type_set
        ]


def _to_float(val: Any) -> float:
    try:
        return float(val)
    except (ValueError, TypeError):
        return 0.0
