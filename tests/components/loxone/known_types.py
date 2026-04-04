"""Mapping of Loxone control types to Home Assistant platforms.

Used by both the dump-based unit tests and the live integration tests
to identify which control types the integration handles and which are
unrecognized.

Kept in sync automatically: test_known_types_sync.py scans the platform
source files for get_all() calls and fails if this dict is stale.
"""

KNOWN_CONTROL_TYPES: dict[str, str] = {
    "InfoOnlyDigital": "binary_sensor",
    "PresenceDetector": "binary_sensor",
    "SmokeAlarm": "binary_sensor",
    "InfoOnlyAnalog": "sensor",
    "TextInput": "text",
    "Meter": "sensor",
    "Switch": "switch",
    "TimedSwitch": "switch",
    "Intercom": "switch",
    "Jalousie": "cover",
    "Gate": "cover",
    "Window": "cover",
    "Dimmer": "light",
    "EIBDimmer": "light",
    "LightControllerV2": "light",
    "IRoomControllerV2": "climate",
    "IRoomController": "climate",
    "AcControl": "climate",
    "Ventilation": "fan",
    "Alarm": "alarm_control_panel",
    "AudioZoneV2": "media_player",
    "Slider": "number",
    "Pushbutton": "button",
}

KNOWN_SUBCONTROL_TYPES: dict[str, str] = {
    "Switch": "light",
    "Dimmer": "light",
    "EIBDimmer": "light",
    "ColorPickerV2": "light",
}
