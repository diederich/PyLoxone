"""Tests for the Device Bridge module."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant, State
from pytest_homeassistant_custom_component.common import MockConfigEntry

from tests.components.loxone.conftest import fire_loxone_event

from custom_components.loxone.bridge import (
    BridgeRuntime,
    DeviceBridge,
    _values_equal,
)
from custom_components.loxone.bridge_mappers import (
    AnalogExposeMapper,
    BinarySensorExposeMapper,
    ColorPickerMapper,
    DimmerMapper,
    LightSwitchMapper,
    SwitchMapper,
    get_mapper,
)
from custom_components.loxone.const import DOMAIN


def _mock_hass():
    """Return a lightweight mock hass for mapper unit tests."""
    hass = MagicMock()
    hass.services.async_call = AsyncMock()
    return hass


# ---------------------------------------------------------------------------
# DeviceBridge serialisation
# ---------------------------------------------------------------------------


class TestDeviceBridge:
    def test_round_trip(self):
        bridge = DeviceBridge(
            entity_id="light.hue_living",
            loxone_uuid="abc-123",
            loxone_type="Dimmer",
            loxone_states={"position": "pos-uuid"},
            loxone_name="Living Dimmer",
            cooldown=2.0,
            details={"some": "detail"},
        )
        d = bridge.to_dict()
        restored = DeviceBridge.from_dict(d)
        assert restored.entity_id == bridge.entity_id
        assert restored.loxone_uuid == bridge.loxone_uuid
        assert restored.loxone_type == bridge.loxone_type
        assert restored.loxone_states == bridge.loxone_states
        assert restored.loxone_name == bridge.loxone_name
        assert restored.cooldown == 2.0
        assert restored.details == {"some": "detail"}

    def test_from_dict_defaults(self):
        d = {
            "entity_id": "sensor.temp",
            "loxone_uuid": "uuid-1",
            "loxone_type": "Slider",
        }
        bridge = DeviceBridge.from_dict(d)
        assert bridge.loxone_states == {}
        assert bridge.loxone_name == ""
        assert bridge.cooldown == 1.0
        assert bridge.details == {}


# ---------------------------------------------------------------------------
# _values_equal
# ---------------------------------------------------------------------------


class TestValuesEqual:
    def test_both_none(self):
        assert _values_equal(None, None) is True

    def test_one_none(self):
        assert _values_equal(None, 5) is False
        assert _values_equal(5, None) is False

    def test_numeric_within_epsilon(self):
        assert _values_equal(50, 50.3) is True

    def test_numeric_outside_epsilon(self):
        assert _values_equal(50, 51) is False

    def test_string_equal(self):
        assert _values_equal("hsv(120,50,80)", "hsv(120,50,80)") is True

    def test_string_not_equal(self):
        assert _values_equal("On", "Off") is False


# ---------------------------------------------------------------------------
# get_mapper factory
# ---------------------------------------------------------------------------


class TestGetMapper:
    def _bridge(self, lox_type, states=None, details=None):
        return DeviceBridge(
            entity_id="light.test",
            loxone_uuid="uuid-action",
            loxone_type=lox_type,
            loxone_states=states or {},
            details=details or {},
        )

    def test_light_colorpicker(self):
        m = get_mapper(self._bridge("ColorPickerV2", {"color": "c-uuid"}), "light")
        assert isinstance(m, ColorPickerMapper)

    def test_light_dimmer(self):
        m = get_mapper(self._bridge("Dimmer", {"position": "p-uuid"}), "light")
        assert isinstance(m, DimmerMapper)

    def test_light_eibdimmer(self):
        m = get_mapper(self._bridge("EIBDimmer", {"position": "p-uuid"}), "light")
        assert isinstance(m, DimmerMapper)

    def test_light_switch(self):
        m = get_mapper(self._bridge("Switch", {"active": "a-uuid"}), "light")
        assert isinstance(m, LightSwitchMapper)

    def test_switch_domain(self):
        m = get_mapper(self._bridge("Switch", {"active": "a-uuid"}), "switch")
        assert isinstance(m, SwitchMapper)

    def test_binary_sensor(self):
        m = get_mapper(self._bridge("Switch"), "binary_sensor")
        assert isinstance(m, BinarySensorExposeMapper)

    def test_sensor(self):
        m = get_mapper(self._bridge("Slider"), "sensor")
        assert isinstance(m, AnalogExposeMapper)

    def test_unsupported_raises(self):
        with pytest.raises(ValueError, match="No mapper"):
            get_mapper(self._bridge("Unknown"), "climate")


# ---------------------------------------------------------------------------
# DimmerMapper
# ---------------------------------------------------------------------------


class TestDimmerMapper:
    _SENTINEL = object()

    def _make(self, states=_SENTINEL):
        if states is self._SENTINEL:
            states = {"position": "pos-uuid"}
        bridge = DeviceBridge(
            entity_id="light.test",
            loxone_uuid="dim-uuid",
            loxone_type="Dimmer",
            loxone_states=states,
        )
        return DimmerMapper(bridge)

    def test_expose_and_subscribe(self):
        m = self._make()
        assert m.expose_supported is True
        assert m.subscribe_supported is True
        assert m.subscribe_uuids == {"pos-uuid"}

    def test_expose_only_when_no_states(self):
        m = self._make(states={})
        assert m.subscribe_supported is False
        assert m.subscribe_uuids == set()

    def test_ha_off_to_command(self):
        state = State("light.test", "off")
        cmd = self._make().ha_state_to_command(state)
        assert cmd == ("dim-uuid", "Off")

    def test_ha_on_with_brightness(self):
        state = State("light.test", "on", {"brightness": 255})
        cmd = self._make().ha_state_to_command(state)
        assert cmd == ("dim-uuid", 100)

    def test_ha_on_with_half_brightness(self):
        state = State("light.test", "on", {"brightness": 128})
        cmd = self._make().ha_state_to_command(state)
        assert cmd == ("dim-uuid", 50)

    def test_ha_on_no_brightness(self):
        state = State("light.test", "on")
        cmd = self._make().ha_state_to_command(state)
        assert cmd == ("dim-uuid", "On")

    @pytest.mark.asyncio
    async def test_loxone_to_ha_brightness(self):
        m = self._make()
        hass = _mock_hass()
        await m.loxone_value_to_ha(hass, "pos-uuid", 50.0)
        hass.services.async_call.assert_called_once_with(
            "light", "turn_on",
            {"entity_id": "light.test", "brightness": 128},
        )

    @pytest.mark.asyncio
    async def test_loxone_to_ha_off(self):
        m = self._make()
        hass = _mock_hass()
        await m.loxone_value_to_ha(hass, "pos-uuid", 0.0)
        hass.services.async_call.assert_called_once_with(
            "light", "turn_off", {"entity_id": "light.test"},
        )


# ---------------------------------------------------------------------------
# ColorPickerMapper
# ---------------------------------------------------------------------------


class TestColorPickerMapper:
    def _make(self):
        bridge = DeviceBridge(
            entity_id="light.hue",
            loxone_uuid="cp-uuid",
            loxone_type="ColorPickerV2",
            loxone_states={"color": "color-uuid"},
        )
        return ColorPickerMapper(bridge)

    def test_subscribe_uuids(self):
        m = self._make()
        assert m.subscribe_uuids == {"color-uuid"}
        assert m.subscribe_supported is True

    def test_ha_off(self):
        state = State("light.hue", "off")
        cmd = self._make().ha_state_to_command(state)
        assert cmd == ("cp-uuid", "Off")

    def test_ha_hs_color(self):
        state = State("light.hue", "on", {
            "brightness": 255,
            "color_mode": "hs",
            "hs_color": (120, 50),
        })
        cmd = self._make().ha_state_to_command(state)
        uuid, value = cmd
        assert uuid == "cp-uuid"
        assert value.startswith("hsv(")
        assert "100.0" in value

    def test_ha_rgbw_color(self):
        """RGBW lights still have hs_color derived by HA."""
        state = State("light.hue", "on", {
            "brightness": 200,
            "color_mode": "rgbw",
            "hs_color": (240, 100),
            "rgbw_color": (0, 0, 255, 50),
        })
        cmd = self._make().ha_state_to_command(state)
        uuid, value = cmd
        assert uuid == "cp-uuid"
        assert value.startswith("hsv(")

    def test_ha_rgb_color(self):
        """RGB color mode uses hs_color derived by HA."""
        state = State("light.hue", "on", {
            "brightness": 255,
            "color_mode": "rgb",
            "hs_color": (0, 100),
            "rgb_color": (255, 0, 0),
        })
        cmd = self._make().ha_state_to_command(state)
        uuid, value = cmd
        assert uuid == "cp-uuid"
        assert value.startswith("hsv(")
        assert "100.0" in value

    def test_ha_xy_color(self):
        """XY color mode uses hs_color derived by HA."""
        state = State("light.hue", "on", {
            "brightness": 128,
            "color_mode": "xy",
            "hs_color": (30, 80),
            "xy_color": (0.5, 0.4),
        })
        cmd = self._make().ha_state_to_command(state)
        uuid, value = cmd
        assert uuid == "cp-uuid"
        assert value.startswith("hsv(")

    def test_ha_color_temp(self):
        state = State("light.hue", "on", {
            "brightness": 128,
            "color_mode": "color_temp",
            "color_temp_kelvin": 4000,
        })
        cmd = self._make().ha_state_to_command(state)
        uuid, value = cmd
        assert uuid == "cp-uuid"
        assert value.startswith("temp(")
        assert "4000" in value

    @pytest.mark.asyncio
    async def test_loxone_hsv_to_ha(self):
        m = self._make()
        hass = _mock_hass()
        await m.loxone_value_to_ha(hass, "color-uuid", "hsv(120,80,50)")
        call = hass.services.async_call.call_args
        assert call[0][0] == "light"
        assert call[0][1] == "turn_on"
        data = call[0][2]
        assert "brightness" in data
        assert "hs_color" in data

    @pytest.mark.asyncio
    async def test_loxone_temp_to_ha(self):
        m = self._make()
        hass = _mock_hass()
        await m.loxone_value_to_ha(hass, "color-uuid", "temp(50,4000)")
        call = hass.services.async_call.call_args
        assert call[0][1] == "turn_on"
        data = call[0][2]
        assert data["color_temp_kelvin"] == 4000
        assert data["brightness"] > 0

    @pytest.mark.asyncio
    async def test_loxone_off_to_ha(self):
        m = self._make()
        hass = _mock_hass()
        await m.loxone_value_to_ha(hass, "color-uuid", "hsv(0,0,0)")
        hass.services.async_call.assert_called_once_with(
            "light", "turn_off", {"entity_id": "light.hue"},
        )


# ---------------------------------------------------------------------------
# LightSwitchMapper
# ---------------------------------------------------------------------------


class TestLightSwitchMapper:
    def _make(self):
        bridge = DeviceBridge(
            entity_id="light.test",
            loxone_uuid="sw-uuid",
            loxone_type="Switch",
            loxone_states={"active": "active-uuid"},
        )
        return LightSwitchMapper(bridge)

    def test_ha_on(self):
        cmd = self._make().ha_state_to_command(State("light.test", "on"))
        assert cmd == ("sw-uuid", "on")

    def test_ha_off(self):
        cmd = self._make().ha_state_to_command(State("light.test", "off"))
        assert cmd == ("sw-uuid", "off")

    @pytest.mark.asyncio
    async def test_loxone_to_ha(self):
        m = self._make()
        hass = _mock_hass()
        await m.loxone_value_to_ha(hass, "active-uuid", 1.0)
        hass.services.async_call.assert_called_once_with(
            "light", "turn_on", {"entity_id": "light.test"},
        )


# ---------------------------------------------------------------------------
# SwitchMapper
# ---------------------------------------------------------------------------


class TestSwitchMapper:
    def _make(self):
        bridge = DeviceBridge(
            entity_id="switch.test",
            loxone_uuid="sw-uuid",
            loxone_type="Switch",
            loxone_states={"active": "active-uuid"},
        )
        return SwitchMapper(bridge)

    def test_ha_on(self):
        cmd = self._make().ha_state_to_command(State("switch.test", "on"))
        assert cmd == ("sw-uuid", 1)

    def test_ha_off(self):
        cmd = self._make().ha_state_to_command(State("switch.test", "off"))
        assert cmd == ("sw-uuid", 0)


# ---------------------------------------------------------------------------
# Expose-only mappers
# ---------------------------------------------------------------------------


class TestBinarySensorExposeMapper:
    def _make(self):
        bridge = DeviceBridge(
            entity_id="binary_sensor.presence",
            loxone_uuid="vi-uuid",
            loxone_type="Switch",
        )
        return BinarySensorExposeMapper(bridge)

    def test_on(self):
        cmd = self._make().ha_state_to_command(State("binary_sensor.presence", "on"))
        assert cmd == ("vi-uuid", 1)

    def test_off(self):
        cmd = self._make().ha_state_to_command(State("binary_sensor.presence", "off"))
        assert cmd == ("vi-uuid", 0)

    def test_subscribe_not_supported(self):
        m = self._make()
        assert m.subscribe_supported is False
        assert m.subscribe_uuids == set()


class TestAnalogExposeMapper:
    def _make(self):
        bridge = DeviceBridge(
            entity_id="sensor.brightness",
            loxone_uuid="vi-uuid",
            loxone_type="Slider",
        )
        return AnalogExposeMapper(bridge)

    def test_numeric(self):
        cmd = self._make().ha_state_to_command(State("sensor.brightness", "42.5"))
        assert cmd == ("vi-uuid", 42.5)

    def test_non_numeric_returns_none(self):
        cmd = self._make().ha_state_to_command(State("sensor.brightness", "unavailable"))
        assert cmd is None


# ---------------------------------------------------------------------------
# BridgeRuntime (integration-level)
# ---------------------------------------------------------------------------


class TestBridgeRuntime:
    @pytest.fixture
    def bridge_config(self):
        return {
            "entity_id": "light.test_bridge",
            "loxone_uuid": "dim-uuid",
            "loxone_type": "Dimmer",
            "loxone_states": {"position": "pos-uuid"},
            "loxone_name": "Test Dimmer",
            "cooldown": 0.0,
        }

    @pytest.fixture
    def mock_coordinator(self):
        coord = MagicMock()
        coord.api = MagicMock()
        coord.api.send_websocket_command = AsyncMock()
        return coord

    @pytest.mark.asyncio
    async def test_setup_restores_bridges(
        self, hass: HomeAssistant, bridge_config, mock_coordinator
    ):
        entry = MockConfigEntry(
            domain=DOMAIN,
            data={},
            options={"bridges": [bridge_config]},
        )
        entry.add_to_hass(hass)

        runtime = BridgeRuntime(hass, mock_coordinator, entry)
        await runtime.async_setup()

        assert len(runtime._active) == 1
        assert runtime._active[0].bridge.entity_id == "light.test_bridge"
        assert runtime.bridged_uuids == {"dim-uuid"}

        await runtime.async_teardown()

    @pytest.mark.asyncio
    async def test_expose_sends_command(
        self, hass: HomeAssistant, bridge_config, mock_coordinator
    ):
        entry = MockConfigEntry(
            domain=DOMAIN,
            data={},
            options={"bridges": [bridge_config]},
        )
        entry.add_to_hass(hass)

        hass.states.async_set("light.test_bridge", "on", {"brightness": 128})

        runtime = BridgeRuntime(hass, mock_coordinator, entry)
        await runtime.async_setup()
        await hass.async_block_till_done()

        mock_coordinator.api.send_websocket_command.assert_called_once_with(
            "dim-uuid", 50
        )

        await runtime.async_teardown()

    @pytest.mark.asyncio
    async def test_subscribe_fires_loxone_value(
        self, hass: HomeAssistant, bridge_config, mock_coordinator
    ):
        """When a Loxone event arrives, the mapper's loxone_value_to_ha is called."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            data={},
            options={"bridges": [bridge_config]},
        )
        entry.add_to_hass(hass)

        mock_coordinator.dispatcher_prefix = f"loxone_{entry.entry_id}_uuid_"
        runtime = BridgeRuntime(hass, mock_coordinator, entry)
        await runtime.async_setup()

        ab = runtime._active[0]
        with patch.object(
            ab.mapper, "loxone_value_to_ha", new_callable=AsyncMock
        ) as mock_lox:
            fire_loxone_event(hass, {"pos-uuid": 75.0})
            await hass.async_block_till_done()

            mock_lox.assert_called_once_with(hass, "pos-uuid", 75.0)

        await runtime.async_teardown()

    @pytest.mark.asyncio
    async def test_teardown_cleans_listeners(
        self, hass: HomeAssistant, bridge_config, mock_coordinator
    ):
        entry = MockConfigEntry(
            domain=DOMAIN,
            data={},
            options={"bridges": [bridge_config]},
        )
        entry.add_to_hass(hass)

        runtime = BridgeRuntime(hass, mock_coordinator, entry)
        await runtime.async_setup()
        assert len(runtime._active) == 1

        await runtime.async_teardown()
        assert len(runtime._active) == 0

    @pytest.mark.asyncio
    async def test_empty_bridges(
        self, hass: HomeAssistant, mock_coordinator
    ):
        entry = MockConfigEntry(
            domain=DOMAIN,
            data={},
            options={},
        )
        entry.add_to_hass(hass)

        runtime = BridgeRuntime(hass, mock_coordinator, entry)
        await runtime.async_setup()
        assert len(runtime._active) == 0

        await runtime.async_teardown()


# ---------------------------------------------------------------------------
# Bridged entity disabling
# ---------------------------------------------------------------------------


@pytest.fixture
def structure_fixture_name() -> str:
    return "structure_lights.json"


async def test_bridged_entity_is_disabled_not_removed(
    hass: HomeAssistant,
    mock_loxone_connection: MagicMock,
) -> None:
    """Bridged sub-controls should be created but disabled by integration."""
    from homeassistant.helpers import entity_registry as er
    from custom_components.loxone.const import (
        CONF_CREATE_AREAS,
        CONF_LIGHTCONTROLLER_SUBCONTROLS_GEN,
        CONF_SCENE_GEN,
        CONF_SCENE_GEN_DELAY,
    )
    from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, CONF_USERNAME

    bridged_uuid = "lc01sp00-0000-0000-0000000000000000"
    opts = {
        CONF_HOST: "192.168.1.100",
        CONF_PORT: 8080,
        CONF_USERNAME: "admin",
        CONF_PASSWORD: "password",
        CONF_SCENE_GEN: True,
        CONF_SCENE_GEN_DELAY: 3,
        CONF_LIGHTCONTROLLER_SUBCONTROLS_GEN: True,
        CONF_CREATE_AREAS: True,
        "bridges": [
            {
                "entity_id": "light.external_light",
                "loxone_uuid": bridged_uuid,
                "loxone_type": "ColorPickerV2",
                "loxone_states": {"color": "lc01sp00-0000-0000-0000000000000001"},
            },
        ],
    }
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={},
        options=opts,
        unique_id="504F94A0FEA2",
        version=3,
    )
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    registry = er.async_get(hass)
    ent_entry = None
    for ent in registry.entities.values():
        if ent.platform == DOMAIN and ent.unique_id == bridged_uuid:
            ent_entry = ent
            break

    assert ent_entry is not None, (
        "Bridged entity should still exist in the entity registry"
    )
    assert ent_entry.disabled_by == er.RegistryEntryDisabler.INTEGRATION, (
        "Bridged entity should be disabled by integration"
    )
