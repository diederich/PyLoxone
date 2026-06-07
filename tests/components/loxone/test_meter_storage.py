"""Tests for Loxone storage (battery) meter sub-sensors.

Covers the meter-type-aware sub-sensor layout (`_meter_state_layout`) and the
one-shot Repair issue that prompts users with legacy entity slugs to verify
their HA Energy Dashboard mapping for battery storage.
"""

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.loxone.const import DOMAIN
from custom_components.loxone.sensor import _METER_LAYOUT_DEFAULT, _METER_LAYOUT_STORAGE, _meter_state_layout
from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
import homeassistant.helpers.issue_registry as ir

from .conftest import fire_loxone_event

METER_UUID = "bat10000-0000-0000-0000000000000000"
ACTUAL_UUID = "bat10000-0000-0000-0000000000000010"
TOTAL_UUID = "bat10000-0000-0000-0000000000000011"
TOTAL_NEG_UUID = "bat10000-0000-0000-0000000000000012"
STORAGE_UUID = "bat10000-0000-0000-0000000000000013"


@pytest.fixture
def structure_fixture_name() -> str:
    return "structure_meter_storage.json"


# -- _meter_state_layout (pure-unit) ------------------------------------------


class TestMeterStateLayout:
    def test_storage_layout_uses_discharge_and_charge_labels(self):
        layout = {row[0]: row for row in _meter_state_layout("storage")}
        assert layout["total"][1] == "Discharge energy"
        assert layout["total"][2] == "meter_storage_discharge"
        assert layout["totalNeg"][1] == "Charge energy"
        assert layout["totalNeg"][2] == "meter_storage_charge"
        assert layout["storage"][2] == "meter_storage_level"
        # actual stays on the shared key — see SOUL of the plan
        assert layout["actual"][2] == "meter_actual"

    def test_energy_layout_unchanged(self):
        layout = {row[0]: row for row in _meter_state_layout("energy")}
        assert layout["total"][2] == "meter_total"
        assert layout["totalNeg"][2] == "meter_total_returned"
        assert layout["storage"][2] == "meter_storage"

    def test_default_layout_for_unknown_type(self):
        # Anything that isn't "storage" should fall through to the default
        assert _meter_state_layout("water") == _METER_LAYOUT_DEFAULT
        assert _meter_state_layout("") == _METER_LAYOUT_DEFAULT
        assert _meter_state_layout("storage") == _METER_LAYOUT_STORAGE


# -- Integration: storage meter wiring ----------------------------------------


def _ent_by_uid(hass: HomeAssistant, state_uuid: str) -> str | None:
    return er.async_get(hass).async_get_entity_id("sensor", DOMAIN, state_uuid)


async def test_storage_meter_uses_discharge_charge_labels(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """The four storage sub-sensors should be registered with the new translation keys."""
    ent_reg = er.async_get(hass)
    for state_uuid, expected_key in [
        (ACTUAL_UUID, "meter_actual"),
        (TOTAL_UUID, "meter_storage_discharge"),
        (TOTAL_NEG_UUID, "meter_storage_charge"),
        (STORAGE_UUID, "meter_storage_level"),
    ]:
        entity_id = _ent_by_uid(hass, state_uuid)
        assert entity_id is not None, f"No entity for state UUID {state_uuid}"
        entry = ent_reg.async_get(entity_id)
        assert entry.translation_key == expected_key, (
            f"{entity_id} translation_key={entry.translation_key!r}, expected {expected_key!r}"
        )


async def test_storage_discharge_is_energy_total_increasing(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """state['total'] for a storage meter -> kWh ENERGY TOTAL_INCREASING (= discharge accumulator)."""
    fire_loxone_event(hass, {TOTAL_UUID: 13.4})
    await hass.async_block_till_done()
    state = hass.states.get(_ent_by_uid(hass, TOTAL_UUID))
    assert float(state.state) == pytest.approx(13.4)
    assert state.attributes["device_class"] == SensorDeviceClass.ENERGY
    assert state.attributes["state_class"] == SensorStateClass.TOTAL_INCREASING
    assert state.attributes["unit_of_measurement"] == "kWh"


async def test_storage_charge_is_energy_total_increasing(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """state['totalNeg'] for a storage meter -> kWh ENERGY TOTAL_INCREASING (= charge accumulator)."""
    fire_loxone_event(hass, {TOTAL_NEG_UUID: 20.7})
    await hass.async_block_till_done()
    state = hass.states.get(_ent_by_uid(hass, TOTAL_NEG_UUID))
    assert float(state.state) == pytest.approx(20.7)
    assert state.attributes["device_class"] == SensorDeviceClass.ENERGY
    assert state.attributes["state_class"] == SensorStateClass.TOTAL_INCREASING
    assert state.attributes["unit_of_measurement"] == "kWh"


async def test_storage_level_is_battery_pct(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """state['storage'] for a storage meter -> BATTERY in %, MEASUREMENT."""
    fire_loxone_event(hass, {STORAGE_UUID: 99.3})
    await hass.async_block_till_done()
    state = hass.states.get(_ent_by_uid(hass, STORAGE_UUID))
    assert float(state.state) == pytest.approx(99.3)
    assert state.attributes["device_class"] == SensorDeviceClass.BATTERY
    assert state.attributes["state_class"] == SensorStateClass.MEASUREMENT
    assert state.attributes["unit_of_measurement"] == "%"


async def test_storage_actual_is_power(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """state['actual'] for a storage meter stays POWER in W (signed: +W = discharge)."""
    fire_loxone_event(hass, {ACTUAL_UUID: 7.42})
    await hass.async_block_till_done()
    state = hass.states.get(_ent_by_uid(hass, ACTUAL_UUID))
    assert float(state.state) == pytest.approx(7.42)
    assert state.attributes["device_class"] == SensorDeviceClass.POWER
    assert state.attributes["unit_of_measurement"] == "W"


# -- Repair issue for legacy installs -----------------------------------------


async def test_no_repair_issue_on_fresh_install(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """A fresh install (no legacy entity in the registry) does NOT create a repair issue."""
    issues = ir.async_get(hass)
    issue = issues.async_get_issue(DOMAIN, f"meter_storage_legacy_labels_{METER_UUID}")
    assert issue is None


async def test_repair_issue_created_when_legacy_entity_exists(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_loxone_connection,
) -> None:
    """Pre-register entities with the legacy ``_total`` / ``_total_returned`` slugs.

    Simulates a user who installed the integration before the storage relabel:
    their `total` and `totalNeg` entities are still registered with the old
    suffix. Setup must produce a repair issue for the meter so the user can
    cross-check their Energy Dashboard.
    """
    mock_config_entry.add_to_hass(hass)

    ent_reg = er.async_get(hass)
    ent_reg.async_get_or_create(
        "sensor",
        DOMAIN,
        TOTAL_UUID,
        suggested_object_id="byd_hvb_total",
        config_entry=mock_config_entry,
    )
    ent_reg.async_get_or_create(
        "sensor",
        DOMAIN,
        TOTAL_NEG_UUID,
        suggested_object_id="byd_hvb_total_returned",
        config_entry=mock_config_entry,
    )

    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    issues = ir.async_get(hass)
    issue = issues.async_get_issue(DOMAIN, f"meter_storage_legacy_labels_{METER_UUID}")
    assert issue is not None
    assert issue.severity == ir.IssueSeverity.WARNING
    assert issue.translation_key == "meter_storage_legacy_labels"
    assert issue.is_fixable is False
    placeholders = issue.translation_placeholders or {}
    assert placeholders.get("name") == "BYD HVB"
    assert placeholders.get("discharge_entity") == "sensor.byd_hvb_total"
    assert placeholders.get("charge_entity") == "sensor.byd_hvb_total_returned"
