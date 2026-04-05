"""Tests for the pyloxone_api.structure module — typed structure file parsing."""

from custom_components.loxone.pyloxone_api.structure import (
    LoxoneCategory,
    LoxoneControl,
    LoxoneRoom,
    LoxoneStructure,
    MsInfo,
)

SAMPLE_STRUCTURE = {
    "msInfo": {
        "serialNr": "AABBCCDDEEFF",
        "miniserverType": 2,
        "msName": "TestMS",
        "projectName": "MyHome",
        "location": "Berlin",
        "latitude": "52.52",
        "longitude": "13.405",
        "altitude": 34,
        "currentUser": {"name": "admin", "isAdmin": True},
    },
    "softwareVersion": [16, 1, 11, 6],
    "rooms": {
        "room-001": {"name": "Living Room"},
        "room-002": {"name": "Kitchen"},
    },
    "cats": {
        "cat-001": {"name": "Lights"},
        "cat-002": {"name": "Blinds"},
    },
    "controls": {
        "ctrl-001": {
            "type": "Switch",
            "name": "Desk Lamp",
            "uuidAction": "ctrl-001-action",
            "room": "room-001",
            "cat": "cat-001",
            "states": {"active": "state-uuid-001"},
            "details": {},
        },
        "ctrl-002": {
            "type": "Jalousie",
            "name": "Bedroom Blind",
            "uuidAction": "ctrl-002-action",
            "room": "room-002",
            "cat": "cat-002",
            "states": {
                "position": "state-uuid-002",
                "shadePosition": "state-uuid-003",
            },
            "details": {"hasAutoShade": True},
            "subControls": {
                "sub-001": {
                    "type": "Switch",
                    "name": "Up/Down",
                    "uuidAction": "sub-001-action",
                    "states": {"active": "state-uuid-004"},
                },
            },
        },
    },
}


class TestMsInfo:
    def test_from_dict(self):
        info = MsInfo.from_dict(SAMPLE_STRUCTURE["msInfo"])
        assert info.serial_nr == "AABBCCDDEEFF"
        assert info.miniserver_type == 2
        assert info.ms_name == "TestMS"
        assert info.project_name == "MyHome"
        assert info.location == "Berlin"
        assert info.latitude == 52.52
        assert info.longitude == 13.405
        assert info.altitude == 34.0
        assert info.current_user["name"] == "admin"

    def test_from_empty_dict(self):
        info = MsInfo.from_dict({})
        assert info.serial_nr == ""
        assert info.miniserver_type == 0
        assert info.current_user is None


class TestLoxoneRoom:
    def test_from_dict(self):
        room = LoxoneRoom.from_dict("room-001", {"name": "Living Room"})
        assert room.uuid == "room-001"
        assert room.name == "Living Room"


class TestLoxoneCategory:
    def test_from_dict(self):
        cat = LoxoneCategory.from_dict("cat-001", {"name": "Lights"})
        assert cat.uuid == "cat-001"
        assert cat.name == "Lights"


class TestLoxoneControl:
    def test_from_dict_basic(self):
        raw = SAMPLE_STRUCTURE["controls"]["ctrl-001"]
        ctrl = LoxoneControl.from_dict("ctrl-001", raw)
        assert ctrl.uuid == "ctrl-001"
        assert ctrl.uuid_action == "ctrl-001-action"
        assert ctrl.name == "Desk Lamp"
        assert ctrl.control_type == "Switch"
        assert ctrl.room_uuid == "room-001"
        assert ctrl.cat_uuid == "cat-001"
        assert ctrl.states == {"active": "state-uuid-001"}

    def test_from_dict_with_subcontrols(self):
        raw = SAMPLE_STRUCTURE["controls"]["ctrl-002"]
        ctrl = LoxoneControl.from_dict("ctrl-002", raw)
        assert len(ctrl.sub_controls) == 1
        sub = ctrl.sub_controls["sub-001"]
        assert sub.name == "Up/Down"
        assert sub.uuid_action == "sub-001-action"

    def test_get_state_uuids(self):
        raw = SAMPLE_STRUCTURE["controls"]["ctrl-002"]
        ctrl = LoxoneControl.from_dict("ctrl-002", raw)
        uuids = ctrl.get_state_uuids()
        assert "ctrl-002-action" in uuids
        assert "state-uuid-002" in uuids
        assert "state-uuid-003" in uuids

    def test_uuid_action_defaults_to_uuid(self):
        ctrl = LoxoneControl.from_dict("myuuid", {"type": "Test", "name": "T"})
        assert ctrl.uuid_action == "myuuid"

    def test_raw_preserved(self):
        raw = SAMPLE_STRUCTURE["controls"]["ctrl-001"]
        ctrl = LoxoneControl.from_dict("ctrl-001", raw)
        assert ctrl.raw is raw


class TestLoxoneStructure:
    def test_full_parse(self):
        struct = LoxoneStructure.from_dict(SAMPLE_STRUCTURE)
        assert struct.ms_info.serial_nr == "AABBCCDDEEFF"
        assert len(struct.rooms) == 2
        assert len(struct.categories) == 2
        assert len(struct.controls) == 2
        assert struct.software_version == [16, 1, 11, 6]

    def test_software_version_str(self):
        struct = LoxoneStructure.from_dict(SAMPLE_STRUCTURE)
        assert struct.software_version_str == "16.1.11.6"

    def test_room_name_lookup(self):
        struct = LoxoneStructure.from_dict(SAMPLE_STRUCTURE)
        assert struct.room_name("room-001") == "Living Room"
        assert struct.room_name("nonexistent") == ""

    def test_category_name_lookup(self):
        struct = LoxoneStructure.from_dict(SAMPLE_STRUCTURE)
        assert struct.category_name("cat-001") == "Lights"
        assert struct.category_name("nonexistent") == ""

    def test_controls_by_type(self):
        struct = LoxoneStructure.from_dict(SAMPLE_STRUCTURE)
        switches = struct.controls_by_type("Switch")
        assert len(switches) == 1
        assert switches[0].name == "Desk Lamp"

    def test_controls_by_multiple_types(self):
        struct = LoxoneStructure.from_dict(SAMPLE_STRUCTURE)
        all_ctrls = struct.controls_by_type("Switch", "Jalousie")
        assert len(all_ctrls) == 2

    def test_empty_structure(self):
        struct = LoxoneStructure.from_dict({})
        assert struct.ms_info.serial_nr == ""
        assert len(struct.rooms) == 0
        assert len(struct.controls) == 0
        assert struct.software_version == []

    def test_software_version_as_string_is_parsed(self):
        raw = {"softwareVersion": "16.1.11.6"}
        struct = LoxoneStructure.from_dict(raw)
        assert struct.software_version == [16, 1, 11, 6]

    def test_raw_preserved(self):
        struct = LoxoneStructure.from_dict(SAMPLE_STRUCTURE)
        assert struct.raw is SAMPLE_STRUCTURE
