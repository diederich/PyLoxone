"""Tests for the Device Bridge module."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.loxone.bridge import BridgeRuntime, DeviceBridge, _values_equal
from custom_components.loxone.bridge_mappers import (
    AnalogExposeMapper,
    BinarySensorExposeMapper,
    ColorPickerMapper,
    CoverMapper,
    DimmerMapper,
    LightSwitchMapper,
    SwitchMapper,
    get_mapper,
)
from custom_components.loxone.const import DOMAIN
from homeassistant.core import HomeAssistant, State

from .conftest import fire_loxone_event


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
            "light",
            "turn_on",
            {"entity_id": "light.test", "brightness": 128},
        )

    @pytest.mark.asyncio
    async def test_loxone_to_ha_off(self):
        m = self._make()
        hass = _mock_hass()
        await m.loxone_value_to_ha(hass, "pos-uuid", 0.0)
        hass.services.async_call.assert_called_once_with(
            "light",
            "turn_off",
            {"entity_id": "light.test"},
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
        state = State(
            "light.hue",
            "on",
            {
                "brightness": 255,
                "color_mode": "hs",
                "hs_color": (120, 50),
            },
        )
        cmd = self._make().ha_state_to_command(state)
        uuid, value = cmd
        assert uuid == "cp-uuid"
        assert value.startswith("hsv(")
        assert "100.0" in value

    def test_ha_rgbw_color(self):
        """RGBW lights still have hs_color derived by HA."""
        state = State(
            "light.hue",
            "on",
            {
                "brightness": 200,
                "color_mode": "rgbw",
                "hs_color": (240, 100),
                "rgbw_color": (0, 0, 255, 50),
            },
        )
        cmd = self._make().ha_state_to_command(state)
        uuid, value = cmd
        assert uuid == "cp-uuid"
        assert value.startswith("hsv(")

    def test_ha_rgb_color(self):
        """RGB color mode uses hs_color derived by HA."""
        state = State(
            "light.hue",
            "on",
            {
                "brightness": 255,
                "color_mode": "rgb",
                "hs_color": (0, 100),
                "rgb_color": (255, 0, 0),
            },
        )
        cmd = self._make().ha_state_to_command(state)
        uuid, value = cmd
        assert uuid == "cp-uuid"
        assert value.startswith("hsv(")
        assert "100.0" in value

    def test_ha_xy_color(self):
        """XY color mode uses hs_color derived by HA."""
        state = State(
            "light.hue",
            "on",
            {
                "brightness": 128,
                "color_mode": "xy",
                "hs_color": (30, 80),
                "xy_color": (0.5, 0.4),
            },
        )
        cmd = self._make().ha_state_to_command(state)
        uuid, value = cmd
        assert uuid == "cp-uuid"
        assert value.startswith("hsv(")

    def test_ha_color_temp(self):
        state = State(
            "light.hue",
            "on",
            {
                "brightness": 128,
                "color_mode": "color_temp",
                "color_temp_kelvin": 4000,
            },
        )
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
            "light",
            "turn_off",
            {"entity_id": "light.hue"},
        )

    def test_color_normalization_treats_small_hsv_drift_as_equal(self):
        m = self._make()
        sent = m.normalize_sent_value("hsv(308,83,100)")
        received = m.normalize_received_value("color-uuid", "hsv(307,79,98)")

        assert m.values_equal(sent, received) is True

    def test_color_normalization_detects_large_hsv_change(self):
        m = self._make()
        sent = m.normalize_sent_value("hsv(308,83,100)")
        received = m.normalize_received_value("color-uuid", "hsv(210,80,60)")

        assert m.values_equal(sent, received) is False

    def test_color_normalization_treats_zero_brightness_as_off(self):
        m = self._make()

        assert m.values_equal(m.normalize_sent_value("Off"), m.normalize_received_value("color-uuid", "hsv(120,80,0)"))


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
            "light",
            "turn_on",
            {"entity_id": "light.test"},
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
    async def test_setup_restores_bridges(self, hass: HomeAssistant, bridge_config, mock_coordinator):
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
    async def test_expose_sends_command(self, hass: HomeAssistant, bridge_config, mock_coordinator):
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

        mock_coordinator.api.send_websocket_command.assert_called_once_with("dim-uuid", 50)

        await runtime.async_teardown()

    @pytest.mark.asyncio
    async def test_subscribe_fires_loxone_value(self, hass: HomeAssistant, bridge_config, mock_coordinator):
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
        with patch.object(ab.mapper, "loxone_value_to_ha", new_callable=AsyncMock) as mock_lox:
            fire_loxone_event(hass, {"pos-uuid": 75.0})
            await hass.async_block_till_done()

            mock_lox.assert_called_once_with(hass, "pos-uuid", 75.0)

        await runtime.async_teardown()

    @pytest.mark.asyncio
    async def test_echo_suppression_only_drops_matching_value(
        self,
        hass: HomeAssistant,
        bridge_config,
        mock_coordinator,
    ):
        """Echo protection should not swallow a real Loxone-side change."""
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
        ab.echo_suppress = True
        ab.last_sent_value = 50.0
        ab.last_sent_normalized = ab.mapper.normalize_sent_value(50.0)

        with patch.object(ab.mapper, "loxone_value_to_ha", new_callable=AsyncMock) as mock_lox:
            fire_loxone_event(hass, {"pos-uuid": 75.0})
            await hass.async_block_till_done()

            mock_lox.assert_called_once_with(hass, "pos-uuid", 75.0)
            assert ab.echo_suppress is False

        await runtime.async_teardown()

    @pytest.mark.asyncio
    async def test_echo_suppression_drops_matching_value(
        self,
        hass: HomeAssistant,
        bridge_config,
        mock_coordinator,
    ):
        """Echo protection still ignores the immediate echo of our own send."""
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
        ab.echo_suppress = True
        ab.last_sent_value = 75.0
        ab.last_sent_normalized = ab.mapper.normalize_sent_value(75.0)

        with patch.object(ab.mapper, "loxone_value_to_ha", new_callable=AsyncMock) as mock_lox:
            fire_loxone_event(hass, {"pos-uuid": 75.0})
            await hass.async_block_till_done()

            mock_lox.assert_not_called()
            assert ab.echo_suppress is False

        await runtime.async_teardown()

    @pytest.mark.asyncio
    async def test_loxone_update_suppresses_followup_ha_state_change(
        self,
        hass: HomeAssistant,
        bridge_config,
        mock_coordinator,
    ):
        """A Loxone-driven HA update must not immediately echo back to Loxone."""
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
        await runtime._handle_lox_value(ab, "pos-uuid", 75.0)

        mock_coordinator.api.send_websocket_command.reset_mock()
        hass.states.async_set("light.test_bridge", "on", {"brightness": 200})
        await hass.async_block_till_done()

        mock_coordinator.api.send_websocket_command.assert_not_called()

        await runtime.async_teardown()

    @pytest.mark.asyncio
    async def test_ha_state_matching_last_loxone_value_is_not_echoed(
        self,
        hass: HomeAssistant,
        bridge_config,
        mock_coordinator,
    ):
        """Late HA state convergence should not echo the last Loxone value back."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            data={},
            options={"bridges": [bridge_config]},
        )
        entry.add_to_hass(hass)

        runtime = BridgeRuntime(hass, mock_coordinator, entry)
        await runtime.async_setup()

        ab = runtime._active[0]
        ab.last_received_value = 50
        ab.last_received_normalized = ab.mapper.normalize_received_value("pos-uuid", 50)

        mock_coordinator.api.send_websocket_command.reset_mock()
        hass.states.async_set("light.test_bridge", "on", {"brightness": 128})
        await hass.async_block_till_done()

        mock_coordinator.api.send_websocket_command.assert_not_called()
        assert ab.last_suppression_reason == "matches_last_received"

        await runtime.async_teardown()

    @pytest.mark.asyncio
    async def test_loxone_update_clears_pending_ha_command(
        self,
        hass: HomeAssistant,
        bridge_config,
        mock_coordinator,
    ):
        """Incoming Loxone ownership should cancel a queued HA command."""
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
        cancelled = False

        def _cancel_pending():
            nonlocal cancelled
            cancelled = True

        ab.pending_command = ("dim-uuid", 60)
        ab.cancel_cooldown = _cancel_pending

        fire_loxone_event(hass, {"pos-uuid": 75.0})
        await hass.async_block_till_done()

        assert cancelled is True
        assert ab.pending_command is None
        assert ab.cancel_cooldown is None

        await runtime.async_teardown()

    @pytest.mark.asyncio
    async def test_teardown_cleans_listeners(self, hass: HomeAssistant, bridge_config, mock_coordinator):
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
    async def test_empty_bridges(self, hass: HomeAssistant, mock_coordinator):
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
    from custom_components.loxone.const import (
        CONF_CREATE_AREAS,
        CONF_LIGHTCONTROLLER_SUBCONTROLS_GEN,
        CONF_SCENE_GEN,
        CONF_SCENE_GEN_DELAY,
    )
    from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, CONF_USERNAME
    from homeassistant.helpers import entity_registry as er

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

    assert ent_entry is not None, "Bridged entity should still exist in the entity registry"
    assert ent_entry.disabled_by == er.RegistryEntryDisabler.INTEGRATION, (
        "Bridged entity should be disabled by integration"
    )


# ---------------------------------------------------------------------------
# CoverMapper
# ---------------------------------------------------------------------------


class TestCoverMapper:
    """Tests for the compound cover VI/VO bridge mapper."""

    def _make(self, details=None, loxone_uuid="vi-pos-uuid"):
        bridge = DeviceBridge(
            entity_id="cover.velux_bedroom_blind",
            loxone_uuid=loxone_uuid,
            loxone_type="cover",
            loxone_states={},
            details=details or {},
        )
        return CoverMapper(bridge)

    # -- factory --

    def test_get_mapper_cover(self):
        bridge = DeviceBridge(
            entity_id="cover.velux_test",
            loxone_uuid="vi-uuid",
            loxone_type="cover",
            loxone_states={},
        )
        m = get_mapper(bridge, "cover")
        assert isinstance(m, CoverMapper)

    # -- expose direction (HA -> Loxone position VI) --------------------------

    def test_expose_supported_with_uuid(self):
        assert self._make().expose_supported is True

    def test_expose_not_supported_without_uuid(self):
        m = self._make(loxone_uuid="")
        assert m.expose_supported is False

    def test_ha_state_with_position(self):
        m = self._make()
        state = State("cover.velux_bedroom_blind", "open", {"current_cover_position": 75})
        cmd = m.ha_state_to_command(state)
        assert cmd == ("vi-pos-uuid", 75.0)

    def test_ha_state_open_no_position(self):
        m = self._make()
        state = State("cover.velux_bedroom_blind", "open")
        cmd = m.ha_state_to_command(state)
        assert cmd == ("vi-pos-uuid", 100.0)

    def test_ha_state_closed_no_position(self):
        m = self._make()
        state = State("cover.velux_bedroom_blind", "closed")
        cmd = m.ha_state_to_command(state)
        assert cmd == ("vi-pos-uuid", 0.0)

    def test_ha_state_opening_returns_none(self):
        """Mid-travel states without a settled position should not update the VI."""
        m = self._make()
        state = State("cover.velux_bedroom_blind", "opening")
        assert m.ha_state_to_command(state) is None

    def test_ha_state_closing_returns_none(self):
        m = self._make()
        state = State("cover.velux_bedroom_blind", "closing")
        assert m.ha_state_to_command(state) is None

    # -- subscribe direction (Loxone VO -> HA) --------------------------------

    def test_subscribe_supported_with_vos(self):
        m = self._make({"uuid_up_vo": "up-uuid", "uuid_target_vo": "tgt-uuid"})
        assert m.subscribe_supported is True
        assert m.subscribe_uuids == {"up-uuid", "tgt-uuid"}

    def test_subscribe_not_supported_without_vos(self):
        m = self._make()
        assert m.subscribe_supported is False
        assert m.subscribe_uuids == set()

    @pytest.mark.asyncio
    async def test_up_vo_triggers_open(self):
        m = self._make({"uuid_up_vo": "up-uuid"})
        hass = _mock_hass()
        await m.loxone_value_to_ha(hass, "up-uuid", 1)
        hass.services.async_call.assert_called_once_with(
            "cover", "open_cover", {"entity_id": "cover.velux_bedroom_blind"}
        )

    @pytest.mark.asyncio
    async def test_up_vo_false_value_ignored(self):
        """Going back to 0 (motion stopped) should NOT trigger another open."""
        m = self._make({"uuid_up_vo": "up-uuid"})
        hass = _mock_hass()
        await m.loxone_value_to_ha(hass, "up-uuid", 0)
        hass.services.async_call.assert_not_called()

    @pytest.mark.asyncio
    async def test_down_vo_triggers_close(self):
        m = self._make({"uuid_down_vo": "dn-uuid"})
        hass = _mock_hass()
        await m.loxone_value_to_ha(hass, "dn-uuid", 1)
        hass.services.async_call.assert_called_once_with(
            "cover", "close_cover", {"entity_id": "cover.velux_bedroom_blind"}
        )

    @pytest.mark.asyncio
    async def test_target_vo_intermediate_position(self):
        m = self._make({"uuid_target_vo": "tgt-uuid"})
        hass = _mock_hass()
        await m.loxone_value_to_ha(hass, "tgt-uuid", 60.0)
        hass.services.async_call.assert_called_once_with(
            "cover", "set_cover_position", {"entity_id": "cover.velux_bedroom_blind", "position": 60}
        )

    @pytest.mark.asyncio
    async def test_target_vo_100_calls_open(self):
        m = self._make({"uuid_target_vo": "tgt-uuid"})
        hass = _mock_hass()
        await m.loxone_value_to_ha(hass, "tgt-uuid", 100.0)
        hass.services.async_call.assert_called_once_with(
            "cover", "open_cover", {"entity_id": "cover.velux_bedroom_blind"}
        )

    @pytest.mark.asyncio
    async def test_target_vo_0_calls_close(self):
        m = self._make({"uuid_target_vo": "tgt-uuid"})
        hass = _mock_hass()
        await m.loxone_value_to_ha(hass, "tgt-uuid", 0.0)
        hass.services.async_call.assert_called_once_with(
            "cover", "close_cover", {"entity_id": "cover.velux_bedroom_blind"}
        )

    @pytest.mark.asyncio
    async def test_target_vo_invalid_value_ignored(self):
        m = self._make({"uuid_target_vo": "tgt-uuid"})
        hass = _mock_hass()
        await m.loxone_value_to_ha(hass, "tgt-uuid", "not-a-number")
        hass.services.async_call.assert_not_called()

    @pytest.mark.asyncio
    async def test_unknown_uuid_ignored(self):
        """A message for an unregistered UUID should not trigger any service call."""
        m = self._make({"uuid_up_vo": "up-uuid"})
        hass = _mock_hass()
        await m.loxone_value_to_ha(hass, "some-other-uuid", 1)
        hass.services.async_call.assert_not_called()

    # -- description --

    def test_description_lists_configured_vos(self):
        m = self._make({"uuid_up_vo": "up-uuid", "uuid_down_vo": "dn-uuid"})
        desc = m.description
        assert "up" in desc
        assert "down" in desc

    def test_description_position_only(self):
        m = self._make()
        assert "position-only" in m.description
