"""Tests for the Loxone config flow."""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import aiohttp
from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.loxone.const import (
    CONF_LIGHTCONTROLLER_SUBCONTROLS_GEN,
    CONF_SCENE_GEN,
    CONF_SCENE_GEN_DELAY,
    DOMAIN,
)

VALID_USER_INPUT = {
    "username": "admin",
    "password": "secret",
    "host": "192.168.1.77",
    "port": 8080,
    "generate_scenes": True,
    "generate_scenes_delay": 3,
    "generate_lightcontroller_subcontrols": False,
    "create_areas_on_setup": True,
}


def _mock_response(status=200):
    """Create a mock aiohttp response with the given status."""
    resp = MagicMock(spec=aiohttp.ClientResponse)
    resp.status = status
    return resp


@pytest.fixture(autouse=True)
def mock_miniserver_reachable(request):
    """Mock the HTTP connection test to the Miniserver.

    Tests that explicitly test connection failures should use
    @pytest.mark.parametrize or patch themselves.
    """
    if "no_auto_mock_connection" in request.keywords:
        yield
        return

    async def _mock_get(*args, **kwargs):
        return _mock_response(200)

    with patch(
        "custom_components.loxone.config_flow.async_get_clientsession"
    ) as mock_session_fn:
        session = MagicMock()
        session.get = _mock_get
        mock_session_fn.return_value = session
        yield session


# ---------------------------------------------------------------------------
# Config flow (initial setup)
# ---------------------------------------------------------------------------


async def test_user_flow_creates_entry(hass: HomeAssistant) -> None:
    """Complete user flow should create a config entry."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=VALID_USER_INPUT,
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "PyLoxone (192.168.1.77)"
    assert result["options"]["host"] == "192.168.1.77"
    assert result["options"]["port"] == 8080
    assert result["options"]["username"] == "admin"


async def test_user_flow_coerces_port_to_int(hass: HomeAssistant) -> None:
    """Port should be stored as int even if input is float."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={**VALID_USER_INPUT, "port": 9090.0},
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["options"]["port"] == 9090
    assert isinstance(result["options"]["port"], int)


async def test_user_flow_rejects_non_latin1_username(hass: HomeAssistant) -> None:
    """Username with non-latin-1 chars should fail validation."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={**VALID_USER_INPUT, "username": "user\u4e16"},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"]["base"] == "Username contains characters that are not latin-1 compatible"


async def test_user_flow_rejects_non_latin1_password(hass: HomeAssistant) -> None:
    """Password with non-latin-1 chars should fail validation."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={**VALID_USER_INPUT, "password": "p\u00e4ss\u4e16"},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"]["base"] == "Password contains characters that are not latin-1 compatible"


async def test_user_flow_accepts_latin1_special_chars(hass: HomeAssistant) -> None:
    """Latin-1 special chars (umlauts, accents) should be accepted."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            **VALID_USER_INPUT,
            "username": "b\u00fcro",
            "password": "p\u00e4ssw\u00f6rd",
        },
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY


# ---------------------------------------------------------------------------
# Config flow — connection validation
# ---------------------------------------------------------------------------


@pytest.mark.no_auto_mock_connection
async def test_user_flow_rejects_invalid_credentials(hass: HomeAssistant) -> None:
    """HTTP 401 from the Miniserver should show invalid_auth error."""
    async def _mock_get(*args, **kwargs):
        return _mock_response(401)

    with patch(
        "custom_components.loxone.config_flow.async_get_clientsession"
    ) as mock_session_fn:
        session = MagicMock()
        session.get = _mock_get
        mock_session_fn.return_value = session

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input=VALID_USER_INPUT,
        )
        assert result["type"] is FlowResultType.FORM
        assert result["errors"]["base"] == "invalid_auth"


@pytest.mark.no_auto_mock_connection
async def test_user_flow_rejects_unreachable_host(hass: HomeAssistant) -> None:
    """Connection error should show cannot_connect."""
    async def _mock_get(*args, **kwargs):
        raise aiohttp.ClientConnectorError(
            connection_key=MagicMock(), os_error=OSError("Connection refused")
        )

    with patch(
        "custom_components.loxone.config_flow.async_get_clientsession"
    ) as mock_session_fn:
        session = MagicMock()
        session.get = _mock_get
        mock_session_fn.return_value = session

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input=VALID_USER_INPUT,
        )
        assert result["type"] is FlowResultType.FORM
        assert result["errors"]["base"] == "cannot_connect"


@pytest.mark.no_auto_mock_connection
async def test_user_flow_rejects_timeout(hass: HomeAssistant) -> None:
    """Timeout should show cannot_connect."""
    async def _mock_get(*args, **kwargs):
        raise TimeoutError()

    with patch(
        "custom_components.loxone.config_flow.async_get_clientsession"
    ) as mock_session_fn:
        session = MagicMock()
        session.get = _mock_get
        mock_session_fn.return_value = session

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input=VALID_USER_INPUT,
        )
        assert result["type"] is FlowResultType.FORM
        assert result["errors"]["base"] == "cannot_connect"


# ---------------------------------------------------------------------------
# Options flow — menu and settings
# ---------------------------------------------------------------------------


async def test_options_flow_shows_menu(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
) -> None:
    """Options flow init should present a menu."""
    entry = init_integration
    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] is FlowResultType.MENU
    assert "settings" in result["menu_options"]
    assert "bridge_menu" in result["menu_options"]


async def test_options_flow_settings(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
) -> None:
    """Settings path should allow changing connection options."""
    entry = init_integration

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] is FlowResultType.MENU

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"next_step_id": "settings"},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "settings"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            **VALID_USER_INPUT,
            "host": "10.0.0.50",
            "port": 9999,
        },
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert entry.options["host"] == "10.0.0.50"
    assert entry.options["port"] == 9999


# ---------------------------------------------------------------------------
# Options flow — device bridges UI
# ---------------------------------------------------------------------------


async def test_bridge_menu_shows_no_bridges(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
) -> None:
    """Bridge menu with no bridges should show add and done (no remove)."""
    entry = init_integration

    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"next_step_id": "bridge_menu"},
    )
    assert result["type"] is FlowResultType.MENU
    assert result["step_id"] == "bridge_menu"
    assert "bridge_add" in result["menu_options"]
    assert "bridge_done" in result["menu_options"]
    assert "bridge_remove" not in result["menu_options"]


async def test_bridge_add(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    mock_loxone_connection,
) -> None:
    """Adding a bridge via the UI should persist it."""
    entry = init_integration

    mock_loxone_connection.structure_file = {
        "rooms": {"r1": {"name": "Living Room"}},
        "controls": {
            "lc-uuid": {
                "name": "Main Light Controller",
                "type": "LightControllerV2",
                "uuidAction": "lc-uuid",
                "room": "r1",
                "subControls": {
                    "sc-dimmer": {
                        "name": "Spot Dimmer",
                        "type": "Dimmer",
                        "uuidAction": "dim-action-uuid",
                        "states": {"position": "pos-uuid", "min": "min-uuid", "max": "max-uuid"},
                    },
                },
            },
        },
    }

    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"next_step_id": "bridge_menu"},
    )
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"next_step_id": "bridge_add"},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "bridge_add"

    hass.states.async_set("light.hue_spot", "on", {"brightness": 200})
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            "entity_id": "light.hue_spot",
            "loxone_control": "dim-action-uuid",
            "cooldown": 2.0,
        },
    )
    assert result["type"] is FlowResultType.MENU
    assert result["step_id"] == "bridge_menu"
    assert "bridge_remove" in result["menu_options"]

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"next_step_id": "bridge_done"},
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY

    bridge_list = entry.options.get("bridges", [])
    assert len(bridge_list) == 1
    assert bridge_list[0]["entity_id"] == "light.hue_spot"
    assert bridge_list[0]["loxone_uuid"] == "dim-action-uuid"
    assert bridge_list[0]["loxone_type"] == "Dimmer"
    assert bridge_list[0]["cooldown"] == 2.0
    assert bridge_list[0]["loxone_states"]["position"] == "pos-uuid"


async def test_bridge_add_top_level_switch(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    mock_loxone_connection,
) -> None:
    """Adding a bridge to a top-level Switch control."""
    entry = init_integration

    mock_loxone_connection.structure_file = {
        "rooms": {"r1": {"name": "Kitchen"}},
        "controls": {
            "sw-uuid": {
                "name": "VI_Presence",
                "type": "Switch",
                "uuidAction": "sw-uuid",
                "room": "r1",
                "states": {"active": "act-uuid"},
            },
        },
    }

    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"next_step_id": "bridge_menu"},
    )
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"next_step_id": "bridge_add"},
    )

    hass.states.async_set("binary_sensor.presence", "on")
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            "entity_id": "binary_sensor.presence",
            "loxone_control": "sw-uuid",
            "cooldown": 1.0,
        },
    )
    assert result["type"] is FlowResultType.MENU

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"next_step_id": "bridge_done"},
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY

    bridge_list = entry.options.get("bridges", [])
    assert len(bridge_list) == 1
    assert bridge_list[0]["loxone_type"] == "Switch"


async def test_bridge_remove(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_loxone_connection,
) -> None:
    """Removing a bridge via the UI should update options."""
    mock_config_entry.add_to_hass(hass)
    hass.config_entries.async_update_entry(
        mock_config_entry,
        options={
            **mock_config_entry.options,
            "bridges": [
                {
                    "entity_id": "light.hue",
                    "loxone_uuid": "dim-uuid",
                    "loxone_type": "Dimmer",
                    "loxone_states": {"position": "pos-uuid"},
                    "loxone_name": "Test Dimmer",
                    "cooldown": 1.0,
                },
            ],
        },
    )
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(
        mock_config_entry.entry_id
    )
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"next_step_id": "bridge_menu"},
    )
    assert result["type"] is FlowResultType.MENU
    assert "bridge_remove" in result["menu_options"]

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"next_step_id": "bridge_remove"},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "bridge_remove"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"bridge": "0"},
    )
    assert result["type"] is FlowResultType.MENU
    assert "bridge_remove" not in result["menu_options"]

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"next_step_id": "bridge_done"},
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert len(mock_config_entry.options.get("bridges", [])) == 0


async def test_bridge_done_preserves_settings(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
) -> None:
    """Bridge done should preserve existing connection settings."""
    entry = init_integration
    original_host = entry.options["host"]

    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"next_step_id": "bridge_menu"},
    )
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"next_step_id": "bridge_done"},
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert entry.options["host"] == original_host
