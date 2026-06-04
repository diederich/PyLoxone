"""Tests for Loxone helper functions.

These are pure functions with no HA dependency — fast, high-value tests.
"""

import pytest

from custom_components.loxone.helpers import (
    add_room_and_cat_to_value_values,
    get_all,
    get_all_including_subcontrols,
    get_cat_name_from_cat_uuid,
    get_miniserver_type,
    get_room_name_from_room_uuid,
    hass_to_lox,
    lox2hass_mapped,
    lox2lox_mapped,
    lox_to_hass,
    map_range,
    to_hass_color_temp,
    to_loxone_color_temp,
)

# -- map_range ---------------------------------------------------------------


class TestMapRange:
    @pytest.mark.parametrize(
        ("value", "in_min", "in_max", "out_min", "out_max", "expected"),
        [
            (50, 0, 100, 0, 1.0, 0.5),
            (0, 0, 100, 0, 1.0, 0.0),
            (100, 0, 100, 0, 1.0, 1.0),
            # Loxone cover position inversion: 0→100, 100→0
            (0, 0, 100, 100, 0, 100),
            (100, 0, 100, 100, 0, 0),
            (75, 0, 100, 100, 0, 25),
            # Arbitrary range
            (5, 0, 10, 100, 200, 150),
        ],
    )
    def test_map_range(self, value, in_min, in_max, out_min, out_max, expected):
        assert map_range(value, in_min, in_max, out_min, out_max) == pytest.approx(expected)

    def test_map_range_same_input_raises(self):
        """Division by zero when in_min == in_max."""
        with pytest.raises(ZeroDivisionError):
            map_range(5, 10, 10, 0, 100)


# -- Brightness conversions --------------------------------------------------


class TestBrightnessConversions:
    @pytest.mark.parametrize(
        ("hass_val", "lox_val"),
        [
            (0, 0.0),
            (255, 100.0),
            (127.5, 50.0),
        ],
    )
    def test_hass_to_lox(self, hass_val, lox_val):
        assert hass_to_lox(hass_val) == pytest.approx(lox_val)

    @pytest.mark.parametrize(
        ("lox_val", "hass_val"),
        [
            (0.0, 0),
            (100.0, 255.0),
            (50.0, 127.5),
        ],
    )
    def test_lox_to_hass(self, lox_val, hass_val):
        assert lox_to_hass(lox_val) == pytest.approx(hass_val)

    def test_roundtrip(self):
        """hass→lox→hass should be identity."""
        for val in (0, 64, 128, 191, 255):
            assert lox_to_hass(hass_to_lox(val)) == pytest.approx(val)


# -- Clamped brightness conversions ------------------------------------------


class TestClampedBrightness:
    def test_lox2lox_mapped_below_min(self):
        assert lox2lox_mapped(5, 10, 100) == 0

    def test_lox2lox_mapped_at_min(self):
        assert lox2lox_mapped(10, 10, 100) == 0

    def test_lox2lox_mapped_above_max(self):
        assert lox2lox_mapped(110, 10, 100) == 100

    def test_lox2lox_mapped_in_range(self):
        assert lox2lox_mapped(50, 10, 100) == 50

    def test_lox2hass_mapped_below_min(self):
        assert lox2hass_mapped(5, 10, 100) == 0

    def test_lox2hass_mapped_above_max(self):
        assert lox2hass_mapped(110, 10, 100) == lox_to_hass(100)

    def test_lox2hass_mapped_in_range(self):
        assert lox2hass_mapped(50, 10, 100) == lox_to_hass(50)


# -- Color temperature conversions -------------------------------------------


class TestColorTempConversions:
    @pytest.mark.parametrize(
        ("kelvin", "mired"),
        [
            (2700, 500),  # warmest
            (6500, 153),  # coolest
        ],
    )
    def test_to_hass_boundaries(self, kelvin, mired):
        assert to_hass_color_temp(kelvin) == pytest.approx(mired)

    @pytest.mark.parametrize(
        ("mired", "kelvin"),
        [
            (500, 2700),
            (153, 6500),
        ],
    )
    def test_to_loxone_boundaries(self, mired, kelvin):
        assert to_loxone_color_temp(mired) == pytest.approx(kelvin)

    def test_to_hass_clamps_below(self):
        assert to_hass_color_temp(2000) == 500

    def test_to_hass_clamps_above(self):
        assert to_hass_color_temp(8000) == 153

    def test_to_loxone_clamps_below(self):
        assert to_loxone_color_temp(100) == 6500

    def test_to_loxone_clamps_above(self):
        assert to_loxone_color_temp(600) == 2700

    def test_roundtrip_midpoint(self):
        """Convert a mid-range kelvin through both directions."""
        kelvin = 4600  # midpoint
        mired = to_hass_color_temp(kelvin)
        assert to_loxone_color_temp(mired) == pytest.approx(kelvin)


# -- get_miniserver_type ------------------------------------------------------


class TestGetMiniserverType:
    @pytest.mark.parametrize(
        ("type_id", "expected"),
        [
            (0, "Miniserver (Gen 1)"),
            (1, "Miniserver Go (Gen 1)"),
            (2, "Miniserver (Gen 2)"),
            (3, "Miniserver Go (Gen 2)"),
            (4, "Miniserver Compact"),
            (99, "Unknown type"),
            (-1, "Unknown type"),
        ],
    )
    def test_all_types(self, type_id, expected):
        assert get_miniserver_type(type_id) == expected


# -- get_all ------------------------------------------------------------------

SAMPLE_STRUCTURE = {
    "controls": {
        "aaa": {"type": "Switch", "name": "S1"},
        "bbb": {"type": "Switch", "name": "S2"},
        "ccc": {"type": "Dimmer", "name": "D1"},
        "ddd": {"type": "TimedSwitch", "name": "TS1"},
    }
}


class TestGetAll:
    def test_single_type(self):
        result = get_all(SAMPLE_STRUCTURE, "Switch")
        assert len(result) == 2
        names = {c["name"] for c in result}
        assert names == {"S1", "S2"}

    def test_list_of_types(self):
        result = get_all(SAMPLE_STRUCTURE, ["Switch", "TimedSwitch"])
        assert len(result) == 3

    def test_no_match(self):
        assert get_all(SAMPLE_STRUCTURE, "Gate") == []

    def test_empty_controls(self):
        assert get_all({"controls": {}}, "Switch") == []


# -- get_all_including_subcontrols -------------------------------------------

NESTED_STRUCTURE = {
    "controls": {
        "top-meter": {
            "type": "Meter",
            "name": "TopMeter",
            "uuidAction": "top-meter",
            "room": "room-1",
            "cat": "cat-1",
            "states": {"actual": "top-meter-actual"},
        },
        "power-unit": {
            "type": "PowerUnit",
            "name": "PSU",
            "uuidAction": "power-unit",
            "room": "room-2",
            "cat": "cat-2",
            "states": {},
            "subControls": {
                "sub-meter-1": {
                    "type": "Meter",
                    "name": "SubMeter1",
                    "uuidAction": "sub-meter-1",
                    "states": {"actual": "sub-meter-1-actual"},
                },
                "sub-meter-2": {
                    "type": "Meter",
                    "name": "SubMeter2",
                    "uuidAction": "sub-meter-2",
                    "room": "room-3",
                    "cat": "cat-3",
                    "states": {"actual": "sub-meter-2-actual"},
                },
                "sub-tracker": {
                    "type": "Tracker",
                    "name": "Events",
                    "states": {},
                },
            },
        },
        "switch-1": {
            "type": "Switch",
            "name": "S",
            "uuidAction": "switch-1",
            "states": {},
        },
    }
}


class TestGetAllIncludingSubcontrols:
    def test_includes_top_level_and_subcontrol_meters(self):
        result = get_all_including_subcontrols(NESTED_STRUCTURE, "Meter")
        names = {c["name"] for c in result}
        assert names == {"TopMeter", "SubMeter1", "SubMeter2"}

    def test_subcontrol_inherits_room_and_cat_from_parent(self):
        result = get_all_including_subcontrols(NESTED_STRUCTURE, "Meter")
        sub1 = next(c for c in result if c["name"] == "SubMeter1")
        # SubMeter1 has no room/cat → inherits from PowerUnit (room-2, cat-2)
        assert sub1["room"] == "room-2"
        assert sub1["cat"] == "cat-2"

    def test_subcontrol_keeps_explicit_room_and_cat(self):
        result = get_all_including_subcontrols(NESTED_STRUCTURE, "Meter")
        sub2 = next(c for c in result if c["name"] == "SubMeter2")
        # SubMeter2 has its own room/cat → not overwritten
        assert sub2["room"] == "room-3"
        assert sub2["cat"] == "cat-3"

    def test_ignores_other_subcontrol_types(self):
        result = get_all_including_subcontrols(NESTED_STRUCTURE, "Meter")
        # Tracker subcontrol is filtered out
        assert all(c["type"] == "Meter" for c in result)

    def test_list_of_types(self):
        result = get_all_including_subcontrols(NESTED_STRUCTURE, ["Meter", "Switch"])
        types = [c["type"] for c in result]
        assert types.count("Meter") == 3
        assert types.count("Switch") == 1

    def test_empty_controls(self):
        assert get_all_including_subcontrols({"controls": {}}, "Meter") == []

    def test_no_match(self):
        assert get_all_including_subcontrols(NESTED_STRUCTURE, "Gate") == []


# -- Room / category lookup ---------------------------------------------------

SAMPLE_CONFIG = {
    "rooms": {
        "room-1": {"name": "Living Room"},
        "room-2": {"name": "Kitchen"},
    },
    "cats": {
        "cat-1": {"name": "Lighting"},
    },
}


class TestRoomCatLookup:
    def test_room_found(self):
        assert get_room_name_from_room_uuid(SAMPLE_CONFIG, "room-1") == "Living Room"

    def test_room_not_found(self):
        assert get_room_name_from_room_uuid(SAMPLE_CONFIG, "room-999") == ""

    def test_room_no_rooms_key(self):
        assert get_room_name_from_room_uuid({}, "room-1") == ""

    def test_cat_found(self):
        assert get_cat_name_from_cat_uuid(SAMPLE_CONFIG, "cat-1") == "Lighting"

    def test_cat_not_found(self):
        assert get_cat_name_from_cat_uuid(SAMPLE_CONFIG, "cat-999") == ""

    def test_cat_no_cats_key(self):
        assert get_cat_name_from_cat_uuid({}, "cat-1") == ""


class TestAddRoomAndCat:
    def test_resolves_both(self):
        sensor = {"room": "room-1", "cat": "cat-1", "name": "Test"}
        config = {**SAMPLE_CONFIG, "controls": {}}
        result = add_room_and_cat_to_value_values(config, sensor)
        assert result["room"] == "Living Room"
        assert result["cat"] == "Lighting"

    def test_missing_room_uuid(self):
        sensor = {"name": "Test"}
        config = {**SAMPLE_CONFIG, "controls": {}}
        result = add_room_and_cat_to_value_values(config, sensor)
        assert result["room"] == ""
        assert result["cat"] == ""
