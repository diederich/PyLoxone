"""Tests for Loxone sensor entities."""

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.loxone.const import DOMAIN
from custom_components.loxone.coordinator import ConnectionState, LoxoneCoordinator
from custom_components.loxone.pyloxone_api.exceptions import LoxoneConnectionError
from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er

from .conftest import fire_loxone_event

MINISERVER_SERIAL = "504F94A0FEA2"

FIXTURE_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def structure_fixture_name() -> str:
    return "structure_sensors.json"


TEMP_ENTITY_ID = "sensor.room_temperature"
TEMP_ACTION_UUID = "sen10000-0000-0000-0000000000000000"

WIND_ENTITY_ID = "sensor.wind_speed"


METER_ACTUAL_UUID = "mtr10000-0000-0000-0000000000000010"
METER_TOTAL_UUID = "mtr10000-0000-0000-0000000000000011"

VERSION_ENTITY_ID = "sensor.test_miniserver_software_version"
KEEPALIVE_ENTITY_ID = "sensor.test_miniserver_keep_alive"
PROJECT_ENTITY_ID = "sensor.test_miniserver_project_name"
LOCATION_ENTITY_ID = "sensor.test_miniserver_location"
USER_ENTITY_ID = "sensor.test_miniserver_connected_user"

# Unique IDs for the coordinator diagnostic sensors
CONN_STATE_UNIQUE_ID = f"{MINISERVER_SERIAL}_connection_state"
RECONNECT_COUNT_UNIQUE_ID = f"{MINISERVER_SERIAL}_reconnect_count"


def _get_entity_id_by_unique_id(hass: HomeAssistant, unique_id: str) -> str | None:
    """Look up an entity's actual entity_id from its unique_id.

    This avoids hardcoding entity_id slugs which depend on the device name
    and HA's slug generation rules (especially for has_entity_name=True).
    """
    ent_reg = er.async_get(hass)
    return ent_reg.async_get_entity_id("sensor", DOMAIN, unique_id)


async def _setup_with_enabled_sensor(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    unique_id: str,
) -> str:
    """Set up the integration with a normally-disabled sensor force-enabled.

    Returns the entity_id of the enabled sensor.
    """
    mock_config_entry.add_to_hass(hass)

    ent_reg = er.async_get(hass)
    ent_reg.async_get_or_create(
        "sensor",
        DOMAIN,
        unique_id,
        config_entry=mock_config_entry,
        disabled_by=None,
    )

    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    entity_id = ent_reg.async_get_entity_id("sensor", DOMAIN, unique_id)
    assert entity_id is not None, f"Entity with unique_id={unique_id} not found after setup"
    return entity_id


# -- Built-in sensors (always created) ----------------------------------------


async def test_version_sensor_disabled_by_default(hass: HomeAssistant, init_integration: MockConfigEntry) -> None:
    """Version sensor should be registered but disabled by default."""
    ent_reg = er.async_get(hass)
    entry = ent_reg.async_get(VERSION_ENTITY_ID)
    assert entry is not None
    assert entry.unique_id == f"{MINISERVER_SERIAL}_software_version"
    assert entry.disabled_by == er.RegistryEntryDisabler.INTEGRATION


async def test_version_sensor_on_miniserver_device(hass: HomeAssistant, init_integration: MockConfigEntry) -> None:
    """Version sensor should be attached to the miniserver device."""
    ent_reg = er.async_get(hass)
    entry = ent_reg.async_get(VERSION_ENTITY_ID)
    assert entry is not None
    assert entry.entity_category == EntityCategory.DIAGNOSTIC

    dev_reg = dr.async_get(hass)
    device = dev_reg.async_get(entry.device_id)
    assert device is not None
    assert (DOMAIN, MINISERVER_SERIAL) in device.identifiers


async def test_keep_alive_sensor_created(hass: HomeAssistant, init_integration: MockConfigEntry) -> None:
    """Keep-alive sensor should always be present."""
    state = hass.states.get(KEEPALIVE_ENTITY_ID)
    assert state is not None


async def test_keep_alive_sensor_on_miniserver_device(hass: HomeAssistant, init_integration: MockConfigEntry) -> None:
    """Keep-alive sensor should be attached to the miniserver device."""
    ent_reg = er.async_get(hass)
    entry = ent_reg.async_get(KEEPALIVE_ENTITY_ID)
    assert entry is not None
    assert entry.unique_id == f"{MINISERVER_SERIAL}_keep_alive"
    assert entry.entity_category == EntityCategory.DIAGNOSTIC

    dev_reg = dr.async_get(hass)
    device = dev_reg.async_get(entry.device_id)
    assert device is not None
    assert (DOMAIN, MINISERVER_SERIAL) in device.identifiers


# -- Miniserver info sensors (Tier 2) ----------------------------------------


async def test_project_name_sensor(hass: HomeAssistant, init_integration: MockConfigEntry) -> None:
    """Project name sensor should show the Loxone Config project name."""
    state = hass.states.get(PROJECT_ENTITY_ID)
    assert state is not None
    assert state.state == "Test Project"

    ent_reg = er.async_get(hass)
    entry = ent_reg.async_get(PROJECT_ENTITY_ID)
    assert entry.unique_id == f"{MINISERVER_SERIAL}_project_name"
    assert entry.entity_category == EntityCategory.DIAGNOSTIC

    dev_reg = dr.async_get(hass)
    device = dev_reg.async_get(entry.device_id)
    assert (DOMAIN, MINISERVER_SERIAL) in device.identifiers


async def test_location_sensor(hass: HomeAssistant, init_integration: MockConfigEntry) -> None:
    """Location sensor should show the location name with coordinate attributes."""
    state = hass.states.get(LOCATION_ENTITY_ID)
    assert state is not None
    assert state.state == "Kollerschlag"
    assert state.attributes["latitude"] == pytest.approx(48.6082)
    assert state.attributes["longitude"] == pytest.approx(13.8384)
    assert state.attributes["altitude"] == 94

    ent_reg = er.async_get(hass)
    entry = ent_reg.async_get(LOCATION_ENTITY_ID)
    assert entry.unique_id == f"{MINISERVER_SERIAL}_location"
    assert entry.entity_category == EntityCategory.DIAGNOSTIC

    dev_reg = dr.async_get(hass)
    device = dev_reg.async_get(entry.device_id)
    assert (DOMAIN, MINISERVER_SERIAL) in device.identifiers


async def test_connected_user_sensor(hass: HomeAssistant, init_integration: MockConfigEntry) -> None:
    """Connected user sensor should show the API username with is_admin attribute."""
    state = hass.states.get(USER_ENTITY_ID)
    assert state is not None
    assert state.state == "admin"
    assert state.attributes["is_admin"] is True

    ent_reg = er.async_get(hass)
    entry = ent_reg.async_get(USER_ENTITY_ID)
    assert entry.unique_id == f"{MINISERVER_SERIAL}_connected_user"
    assert entry.entity_category == EntityCategory.DIAGNOSTIC

    dev_reg = dr.async_get(hass)
    device = dev_reg.async_get(entry.device_id)
    assert (DOMAIN, MINISERVER_SERIAL) in device.identifiers


async def test_miniserver_sensors_missing_data(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_loxone_connection,
) -> None:
    """Sensors should not be created when msInfo fields are absent."""
    minimal = json.loads((FIXTURE_DIR / "structure_minimal.json").read_text())
    minimal["msInfo"].pop("projectName", None)
    mock_loxone_connection.structure_file = minimal

    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert hass.states.get("sensor.test_miniserver_project_name") is None
    assert hass.states.get("sensor.test_miniserver_location") is None
    assert hass.states.get("sensor.test_miniserver_connected_user") is None


# -- InfoOnlyAnalog (LoxoneSensor) -------------------------------------------


async def test_analog_sensor_created(hass: HomeAssistant, init_integration: MockConfigEntry) -> None:
    """InfoOnlyAnalog should create a sensor entity."""
    state = hass.states.get(TEMP_ENTITY_ID)
    assert state is not None


async def test_sensor_unit_from_format(hass: HomeAssistant, init_integration: MockConfigEntry) -> None:
    """Format '%.1f °C' should yield '°C' as unit."""
    state = hass.states.get(TEMP_ENTITY_ID)
    assert state.attributes.get("unit_of_measurement") == "°C"


async def test_sensor_entity_description_matched(hass: HomeAssistant, init_integration: MockConfigEntry) -> None:
    """Temperature unit should match SENSOR_TYPES and set device_class."""
    state = hass.states.get(TEMP_ENTITY_ID)
    assert state.attributes.get("device_class") == SensorDeviceClass.TEMPERATURE


async def test_wind_sensor_unit(hass: HomeAssistant, init_integration: MockConfigEntry) -> None:
    """Wind sensor with '%.1f km/h' should get wind_speed device_class."""
    state = hass.states.get(WIND_ENTITY_ID)
    assert state is not None
    assert state.attributes.get("unit_of_measurement") == "km/h"
    assert state.attributes.get("device_class") == SensorDeviceClass.WIND_SPEED


async def test_sensor_state_from_event(hass: HomeAssistant, init_integration: MockConfigEntry) -> None:
    """Firing the sensor UUID should update native_value."""
    fire_loxone_event(hass, {TEMP_ACTION_UUID: 21.5})
    await hass.async_block_till_done()

    state = hass.states.get(TEMP_ENTITY_ID)
    assert float(state.state) == pytest.approx(21.5)


async def test_sensor_ignores_unrelated_event(hass: HomeAssistant, init_integration: MockConfigEntry) -> None:
    """Unrelated UUID should not change sensor state."""
    fire_loxone_event(hass, {TEMP_ACTION_UUID: 20.0})
    await hass.async_block_till_done()

    fire_loxone_event(hass, {"unrelated-uuid": 99.0})
    await hass.async_block_till_done()

    state = hass.states.get(TEMP_ENTITY_ID)
    assert float(state.state) == pytest.approx(20.0)


# -- Meter (LoxoneMeterSensor subsensors) ------------------------------------


async def test_meter_creates_subsensors(hass: HomeAssistant, init_integration: MockConfigEntry) -> None:
    """One Meter control should produce Actual, Total, and TotalNeg child sensors."""
    actual = hass.states.get("sensor.energy_meter_actual")
    total = hass.states.get("sensor.energy_meter_total")
    total_returned = hass.states.get("sensor.energy_meter_total_returned")

    assert actual is not None, "Actual subsensor missing"
    assert total is not None, "Total subsensor missing"
    assert total_returned is not None, "Total Returned subsensor missing"


async def test_meter_actual_state_from_event(hass: HomeAssistant, init_integration: MockConfigEntry) -> None:
    """Firing the actual state UUID should update the actual subsensor."""
    fire_loxone_event(hass, {METER_ACTUAL_UUID: 1234.5})
    await hass.async_block_till_done()

    state = hass.states.get("sensor.energy_meter_actual")
    assert float(state.state) == pytest.approx(1234.5)


async def test_meter_total_state_from_event(hass: HomeAssistant, init_integration: MockConfigEntry) -> None:
    """Firing the total state UUID should update the total subsensor."""
    fire_loxone_event(hass, {METER_TOTAL_UUID: 9876.0})
    await hass.async_block_till_done()

    state = hass.states.get("sensor.energy_meter_total")
    assert float(state.state) == pytest.approx(9876.0)


async def test_meter_actual_unit(hass: HomeAssistant, init_integration: MockConfigEntry) -> None:
    """Actual subsensor with '%.1f W' format should have W unit and POWER class."""
    state = hass.states.get("sensor.energy_meter_actual")
    assert state.attributes.get("unit_of_measurement") == "W"
    assert state.attributes.get("device_class") == SensorDeviceClass.POWER


async def test_meter_total_energy_dashboard_attrs(hass: HomeAssistant, init_integration: MockConfigEntry) -> None:
    """Total subsensor should be ENERGY/TOTAL_INCREASING for the energy dashboard."""
    state = hass.states.get("sensor.energy_meter_total")
    assert state.attributes.get("device_class") == SensorDeviceClass.ENERGY
    assert state.attributes.get("state_class") == SensorStateClass.TOTAL_INCREASING
    assert state.attributes.get("unit_of_measurement") == "kWh"


async def test_meter_total_returned_energy_dashboard_attrs(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """Total Returned subsensor should also be ENERGY/TOTAL_INCREASING."""
    state = hass.states.get("sensor.energy_meter_total_returned")
    assert state.attributes.get("device_class") == SensorDeviceClass.ENERGY
    assert state.attributes.get("state_class") == SensorStateClass.TOTAL_INCREASING
    assert state.attributes.get("unit_of_measurement") == "kWh"


async def test_meter_actual_state_class(hass: HomeAssistant, init_integration: MockConfigEntry) -> None:
    """Actual (power) subsensor should be POWER/MEASUREMENT."""
    state = hass.states.get("sensor.energy_meter_actual")
    assert state.attributes.get("state_class") == SensorStateClass.MEASUREMENT


async def test_meter_fallback_classification_from_type(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_loxone_connection,
) -> None:
    """When the format string has no recognisable unit, details.type forces classification."""
    fixture = json.loads((FIXTURE_DIR / "structure_sensors.json").read_text())
    fixture["controls"]["mtr10000-0000-0000-0000000000000000"]["details"]["totalFormat"] = "%.2f units"
    mock_loxone_connection.structure_file = fixture

    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    total = hass.states.get("sensor.energy_meter_total")
    assert total is not None
    assert total.attributes.get("device_class") == SensorDeviceClass.ENERGY
    assert total.attributes.get("state_class") == SensorStateClass.TOTAL_INCREASING


async def test_meter_unit_mismatch_creates_repair(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_loxone_connection,
) -> None:
    """A repair issue is created when the format-string unit contradicts the meter type."""
    from homeassistant.helpers import issue_registry as ir

    fixture = json.loads((FIXTURE_DIR / "structure_sensors.json").read_text())
    # Energy meter with a temperature format → device_class will resolve to
    # TEMPERATURE, which conflicts with the declared meter type "energy".
    fixture["controls"]["mtr10000-0000-0000-0000000000000000"]["details"]["totalFormat"] = "%.1f °C"
    mock_loxone_connection.structure_file = fixture

    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    issues = ir.async_get(hass)
    issue = issues.async_get_issue(DOMAIN, "meter_unit_mismatch_mtr10000-0000-0000-0000000000000000_total")
    assert issue is not None
    assert issue.severity == ir.IssueSeverity.WARNING
    assert issue.translation_key == "meter_unit_mismatch"


async def test_meter_matching_unit_no_repair(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_loxone_connection,
) -> None:
    """No repair issue when format-string unit matches the meter type."""
    from homeassistant.helpers import issue_registry as ir

    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    issues = ir.async_get(hass)
    issue = issues.async_get_issue(DOMAIN, "meter_unit_mismatch_mtr10000-0000-0000-0000000000000000_total")
    assert issue is None


# -- Connection state diagnostic sensor (LoxoneConnectionStateSensor) ---------


async def test_connection_state_sensor_registered(hass: HomeAssistant, init_integration: MockConfigEntry) -> None:
    """Connection state sensor should be registered (disabled by default)."""
    ent_reg = er.async_get(hass)
    entity_id = ent_reg.async_get_entity_id("sensor", DOMAIN, CONN_STATE_UNIQUE_ID)
    assert entity_id is not None, f"No entity registered with unique_id={CONN_STATE_UNIQUE_ID}"

    entry = ent_reg.async_get(entity_id)
    assert entry.unique_id == CONN_STATE_UNIQUE_ID
    assert entry.disabled_by == er.RegistryEntryDisabler.INTEGRATION


async def test_connection_state_sensor_unique_id_no_uuidaction(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """Connection state sensor unique_id must not require uuidAction (regression)."""
    ent_reg = er.async_get(hass)
    entity_id = ent_reg.async_get_entity_id("sensor", DOMAIN, CONN_STATE_UNIQUE_ID)
    assert entity_id is not None
    entry = ent_reg.async_get(entity_id)
    assert entry.unique_id == CONN_STATE_UNIQUE_ID


async def test_connection_state_sensor_on_miniserver_device(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """Connection state sensor should be attached to the miniserver device."""
    ent_reg = er.async_get(hass)
    entity_id = ent_reg.async_get_entity_id("sensor", DOMAIN, CONN_STATE_UNIQUE_ID)
    assert entity_id is not None

    entry = ent_reg.async_get(entity_id)
    assert entry.entity_category == EntityCategory.DIAGNOSTIC

    dev_reg = dr.async_get(hass)
    device = dev_reg.async_get(entry.device_id)
    assert device is not None
    assert (DOMAIN, MINISERVER_SERIAL) in device.identifiers


async def test_connection_state_sensor_shows_connected(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_loxone_connection: MagicMock,
) -> None:
    """When enabled, connection state sensor should show 'connected' after setup."""
    entity_id = await _setup_with_enabled_sensor(hass, mock_config_entry, CONN_STATE_UNIQUE_ID)

    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == ConnectionState.CONNECTED.value


async def test_connection_state_sensor_reflects_disconnect(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_loxone_connection: MagicMock,
) -> None:
    """Connection state sensor should update when coordinator disconnects."""
    entity_id = await _setup_with_enabled_sensor(hass, mock_config_entry, CONN_STATE_UNIQUE_ID)

    coordinator: LoxoneCoordinator = mock_config_entry.runtime_data
    coordinator.connection_state = ConnectionState.DISCONNECTED
    coordinator.async_set_update_error(LoxoneConnectionError("Disconnected"))
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == ConnectionState.DISCONNECTED.value


# -- Reconnect count diagnostic sensor (LoxoneReconnectCountSensor) -----------


async def test_reconnect_count_sensor_registered(hass: HomeAssistant, init_integration: MockConfigEntry) -> None:
    """Reconnect count sensor should be registered (disabled by default)."""
    ent_reg = er.async_get(hass)
    entity_id = ent_reg.async_get_entity_id("sensor", DOMAIN, RECONNECT_COUNT_UNIQUE_ID)
    assert entity_id is not None, f"No entity registered with unique_id={RECONNECT_COUNT_UNIQUE_ID}"

    entry = ent_reg.async_get(entity_id)
    assert entry.unique_id == RECONNECT_COUNT_UNIQUE_ID
    assert entry.disabled_by == er.RegistryEntryDisabler.INTEGRATION


async def test_reconnect_count_sensor_unique_id_no_uuidaction(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """Reconnect count sensor unique_id must not require uuidAction (regression)."""
    ent_reg = er.async_get(hass)
    entity_id = ent_reg.async_get_entity_id("sensor", DOMAIN, RECONNECT_COUNT_UNIQUE_ID)
    assert entity_id is not None
    entry = ent_reg.async_get(entity_id)
    assert entry.unique_id == RECONNECT_COUNT_UNIQUE_ID


async def test_reconnect_count_sensor_on_miniserver_device(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """Reconnect count sensor should be attached to the miniserver device."""
    ent_reg = er.async_get(hass)
    entity_id = ent_reg.async_get_entity_id("sensor", DOMAIN, RECONNECT_COUNT_UNIQUE_ID)
    assert entity_id is not None

    entry = ent_reg.async_get(entity_id)
    assert entry.entity_category == EntityCategory.DIAGNOSTIC

    dev_reg = dr.async_get(hass)
    device = dev_reg.async_get(entry.device_id)
    assert device is not None
    assert (DOMAIN, MINISERVER_SERIAL) in device.identifiers


async def test_reconnect_count_sensor_initial_value(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_loxone_connection: MagicMock,
) -> None:
    """When enabled, reconnect count should start at 0."""
    entity_id = await _setup_with_enabled_sensor(hass, mock_config_entry, RECONNECT_COUNT_UNIQUE_ID)

    state = hass.states.get(entity_id)
    assert state is not None
    assert int(state.state) == 0


async def test_reconnect_count_sensor_state_class(hass: HomeAssistant, init_integration: MockConfigEntry) -> None:
    """Reconnect count sensor should be TOTAL_INCREASING."""
    ent_reg = er.async_get(hass)
    entity_id = ent_reg.async_get_entity_id("sensor", DOMAIN, RECONNECT_COUNT_UNIQUE_ID)
    assert entity_id is not None
