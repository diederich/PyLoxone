"""Tests for Loxone sensor entities."""

import pytest
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.loxone.const import EVENT


@pytest.fixture
def structure_fixture_name() -> str:
    return "structure_sensors.json"


TEMP_ENTITY_ID = "sensor.room_temperature"
TEMP_ACTION_UUID = "sen10000-0000-0000-0000000000000000"

WIND_ENTITY_ID = "sensor.wind_speed"

TEXT_ENTITY_ID = "sensor.status_display"
TEXT_STATE_UUID = "txt10000-0000-0000-0000000000000001"

METER_ACTUAL_UUID = "mtr10000-0000-0000-0000000000000010"
METER_TOTAL_UUID = "mtr10000-0000-0000-0000000000000011"

VERSION_ENTITY_ID = "sensor.loxone_software_version"
KEEPALIVE_ENTITY_ID = "sensor.loxone_last_keep_alive_message"


# -- Built-in sensors (always created) ----------------------------------------


async def test_version_sensor_created(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """softwareVersion [14,5,12,7] should become '14.5.12.7'."""
    state = hass.states.get(VERSION_ENTITY_ID)
    assert state is not None
    assert state.state == "14.5.12.7"


async def test_keep_alive_sensor_created(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """Keep-alive sensor should always be present."""
    state = hass.states.get(KEEPALIVE_ENTITY_ID)
    assert state is not None


# -- InfoOnlyAnalog (LoxoneSensor) -------------------------------------------


async def test_analog_sensor_created(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """InfoOnlyAnalog should create a sensor entity."""
    state = hass.states.get(TEMP_ENTITY_ID)
    assert state is not None


async def test_sensor_unit_from_format(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """Format '%.1f °C' should yield '°C' as unit."""
    state = hass.states.get(TEMP_ENTITY_ID)
    assert state.attributes.get("unit_of_measurement") == "°C"


async def test_sensor_entity_description_matched(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """Temperature unit should match SENSOR_TYPES and set device_class."""
    state = hass.states.get(TEMP_ENTITY_ID)
    assert state.attributes.get("device_class") == SensorDeviceClass.TEMPERATURE


async def test_wind_sensor_unit(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """Wind sensor with '%.1f km/h' should get wind_speed device_class."""
    state = hass.states.get(WIND_ENTITY_ID)
    assert state is not None
    assert state.attributes.get("unit_of_measurement") == "km/h"
    assert state.attributes.get("device_class") == SensorDeviceClass.WIND_SPEED


async def test_sensor_state_from_event(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """Firing the sensor UUID should update native_value."""
    hass.bus.async_fire(EVENT, {TEMP_ACTION_UUID: 21.5})
    await hass.async_block_till_done()

    state = hass.states.get(TEMP_ENTITY_ID)
    assert float(state.state) == pytest.approx(21.5)


async def test_sensor_ignores_unrelated_event(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """Unrelated UUID should not change sensor state."""
    hass.bus.async_fire(EVENT, {TEMP_ACTION_UUID: 20.0})
    await hass.async_block_till_done()

    hass.bus.async_fire(EVENT, {"unrelated-uuid": 99.0})
    await hass.async_block_till_done()

    state = hass.states.get(TEMP_ENTITY_ID)
    assert float(state.state) == pytest.approx(20.0)


# -- TextInput (LoxoneTextSensor) --------------------------------------------


async def test_text_sensor_created(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """TextInput should create a sensor entity."""
    state = hass.states.get(TEXT_ENTITY_ID)
    assert state is not None


async def test_text_sensor_state_from_event(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """Firing the text state UUID should update the sensor."""
    hass.bus.async_fire(EVENT, {TEXT_STATE_UUID: "All systems normal"})
    await hass.async_block_till_done()

    state = hass.states.get(TEXT_ENTITY_ID)
    assert state.state == "All systems normal"


# -- Meter (LoxoneMeterSensor subsensors) ------------------------------------


async def test_meter_creates_subsensors(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """One Meter control should produce Actual, Total, and TotalNeg child sensors."""
    actual = hass.states.get("sensor.energy_meter_actual")
    total = hass.states.get("sensor.energy_meter_total")
    total_neg = hass.states.get("sensor.energy_meter_total_neg")

    assert actual is not None, "Actual subsensor missing"
    assert total is not None, "Total subsensor missing"
    assert total_neg is not None, "TotalNeg subsensor missing"


async def test_meter_actual_state_from_event(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """Firing the actual state UUID should update the actual subsensor."""
    hass.bus.async_fire(EVENT, {METER_ACTUAL_UUID: 1234.5})
    await hass.async_block_till_done()

    state = hass.states.get("sensor.energy_meter_actual")
    assert float(state.state) == pytest.approx(1234.5)


async def test_meter_total_state_from_event(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """Firing the total state UUID should update the total subsensor."""
    hass.bus.async_fire(EVENT, {METER_TOTAL_UUID: 9876.0})
    await hass.async_block_till_done()

    state = hass.states.get("sensor.energy_meter_total")
    assert float(state.state) == pytest.approx(9876.0)


async def test_meter_actual_unit(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """Actual subsensor with '%.1f W' format should have W unit and POWER class."""
    state = hass.states.get("sensor.energy_meter_actual")
    assert state.attributes.get("unit_of_measurement") == "W"
    assert state.attributes.get("device_class") == SensorDeviceClass.POWER
