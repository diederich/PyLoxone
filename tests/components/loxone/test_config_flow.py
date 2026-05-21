"""Tests for the Loxone config flow."""

from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.loxone.const import DOMAIN
from homeassistant.config_entries import SOURCE_REAUTH, SOURCE_RECONFIGURE, SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

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


def _mock_response(status=200, json_payload: dict | None = None):
    """Create a mock aiohttp response with the given status."""
    resp = MagicMock(spec=aiohttp.ClientResponse)
    resp.status = status
    resp.json = AsyncMock(return_value=json_payload or {})
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

    with patch("custom_components.loxone.config_flow.async_get_clientsession") as mock_session_fn:
        session = MagicMock()
        session.get = _mock_get
        mock_session_fn.return_value = session
        yield session


# ---------------------------------------------------------------------------
# Config flow (initial setup)
# ---------------------------------------------------------------------------


async def test_user_flow_creates_entry(hass: HomeAssistant) -> None:
    """Complete user flow should create a config entry."""
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
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
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={**VALID_USER_INPUT, "port": 9090.0},
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["options"]["port"] == 9090
    assert isinstance(result["options"]["port"], int)


async def test_user_flow_rejects_non_latin1_username(hass: HomeAssistant) -> None:
    """Username with non-latin-1 chars should fail validation."""
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={**VALID_USER_INPUT, "username": "user\u4e16"},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"]["base"] == "username_not_latin1"


async def test_user_flow_rejects_non_latin1_password(hass: HomeAssistant) -> None:
    """Password with non-latin-1 chars should fail validation."""
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={**VALID_USER_INPUT, "password": "p\u00e4ss\u4e16"},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"]["base"] == "password_not_latin1"


async def test_user_flow_accepts_latin1_special_chars(hass: HomeAssistant) -> None:
    """Latin-1 special chars (umlauts, accents) should be accepted."""
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
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

    with patch("custom_components.loxone.config_flow.async_get_clientsession") as mock_session_fn:
        session = MagicMock()
        session.get = _mock_get
        mock_session_fn.return_value = session

        result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
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
        raise aiohttp.ClientConnectorError(connection_key=MagicMock(), os_error=OSError("Connection refused"))

    with patch("custom_components.loxone.config_flow.async_get_clientsession") as mock_session_fn:
        session = MagicMock()
        session.get = _mock_get
        mock_session_fn.return_value = session

        result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
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
        raise TimeoutError

    with patch("custom_components.loxone.config_flow.async_get_clientsession") as mock_session_fn:
        session = MagicMock()
        session.get = _mock_get
        mock_session_fn.return_value = session

        result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
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

    result = await hass.config_entries.options.async_init(mock_config_entry.entry_id)
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


# ---------------------------------------------------------------------------
# Config flow — duplicate serial detection
# ---------------------------------------------------------------------------


async def test_user_flow_aborts_duplicate_serial(hass: HomeAssistant) -> None:
    """Second entry with same serial should abort."""
    MockConfigEntry(
        domain=DOMAIN,
        unique_id="AABBCCDDEEFF",
        options=VALID_USER_INPUT,
    ).add_to_hass(hass)

    with patch(
        "custom_components.loxone.config_flow._async_fetch_serial",
        return_value="AABBCCDDEEFF",
    ):
        result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input=VALID_USER_INPUT,
        )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


# ---------------------------------------------------------------------------
# Config flow — HTTP 500 from Miniserver
# ---------------------------------------------------------------------------


@pytest.mark.no_auto_mock_connection
async def test_user_flow_rejects_server_error(hass: HomeAssistant) -> None:
    """HTTP 500 should show cannot_connect."""

    async def _mock_get(*args, **kwargs):
        return _mock_response(500)

    with patch("custom_components.loxone.config_flow.async_get_clientsession") as mock_session_fn:
        session = MagicMock()
        session.get = _mock_get
        mock_session_fn.return_value = session

        result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input=VALID_USER_INPUT,
        )
        assert result["type"] is FlowResultType.FORM
        assert result["errors"]["base"] == "cannot_connect"


# ---------------------------------------------------------------------------
# Reauth flow
# ---------------------------------------------------------------------------


async def test_reauth_flow_updates_credentials(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
) -> None:
    """Successful reauth should update the entry and reload."""
    entry = init_integration

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_REAUTH, "entry_id": entry.entry_id},
        data=entry.options,
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            "username": "new_admin",
            "password": "new_secret",
            "host": entry.options["host"],
            "port": entry.options["port"],
        },
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"
    assert entry.options["username"] == "new_admin"


@pytest.mark.no_auto_mock_connection
async def test_reauth_flow_rejects_invalid_auth(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
) -> None:
    """Reauth with bad credentials should show error."""
    entry = init_integration

    async def _mock_get(*args, **kwargs):
        return _mock_response(401)

    with patch("custom_components.loxone.config_flow.async_get_clientsession") as mock_session_fn:
        session = MagicMock()
        session.get = _mock_get
        mock_session_fn.return_value = session

        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_REAUTH, "entry_id": entry.entry_id},
            data=entry.options,
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                "username": "wrong",
                "password": "wrong",
                "host": entry.options["host"],
                "port": entry.options["port"],
            },
        )
        assert result["type"] is FlowResultType.FORM
        assert result["errors"]["base"] == "invalid_auth"


# ---------------------------------------------------------------------------
# Reconfigure flow
# ---------------------------------------------------------------------------


async def test_reconfigure_flow_updates_connection(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
) -> None:
    """Reconfigure should update the entry with new connection settings."""
    entry = init_integration

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_RECONFIGURE, "entry_id": entry.entry_id},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            "username": "admin",
            "password": "new_pass",
            "host": "10.0.0.99",
            "port": 7777,
        },
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert entry.options["host"] == "10.0.0.99"
    assert entry.options["port"] == 7777


@pytest.mark.no_auto_mock_connection
async def test_reconfigure_flow_rejects_bad_credentials(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
) -> None:
    """Reconfigure with bad credentials should show error."""
    entry = init_integration

    async def _mock_get(*args, **kwargs):
        return _mock_response(401)

    with patch("custom_components.loxone.config_flow.async_get_clientsession") as mock_session_fn:
        session = MagicMock()
        session.get = _mock_get
        mock_session_fn.return_value = session

        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_RECONFIGURE, "entry_id": entry.entry_id},
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                "username": "admin",
                "password": "wrong",
                "host": "10.0.0.99",
                "port": 7777,
            },
        )
        assert result["type"] is FlowResultType.FORM
        assert result["errors"]["base"] == "invalid_auth"


# ---------------------------------------------------------------------------
# Options flow — latin-1 validation
# ---------------------------------------------------------------------------


async def test_options_settings_rejects_non_latin1_username(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
) -> None:
    """Options settings should reject non-latin-1 username with translation key."""
    entry = init_integration

    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"next_step_id": "settings"},
    )
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={**VALID_USER_INPUT, "username": "user\u4e16"},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"]["base"] == "username_not_latin1"


async def test_options_settings_rejects_non_latin1_password(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
) -> None:
    """Options settings should reject non-latin-1 password with translation key."""
    entry = init_integration

    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"next_step_id": "settings"},
    )
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={**VALID_USER_INPUT, "password": "p\u00e4ss\u4e16"},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"]["base"] == "password_not_latin1"


# ---------------------------------------------------------------------------
# Bridge flow — control not found
# ---------------------------------------------------------------------------


async def test_bridge_add_rejects_unknown_control(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    mock_loxone_connection,
) -> None:
    """Adding a bridge with a UUID not in the structure file should be rejected."""
    from homeassistant.data_entry_flow import InvalidData

    entry = init_integration
    mock_loxone_connection.structure_file = {
        "rooms": {},
        "controls": {},
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

    hass.states.async_set("light.test_light", "on")
    await hass.async_block_till_done()

    # The SelectSelector rejects values not in its options list
    with pytest.raises(InvalidData):
        await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={
                "entity_id": "light.test_light",
                "loxone_control": "nonexistent-uuid",
                "cooldown": 1.0,
            },
        )


# ---------------------------------------------------------------------------
# DHCP discovery
# ---------------------------------------------------------------------------

DHCP_DISCOVERY = MagicMock(
    ip="192.168.1.77",
    hostname="loxone",
    macaddress="504F94A0FEA2",
)


async def test_dhcp_discovery_creates_flow(hass: HomeAssistant) -> None:
    """DHCP discovery should show the user form with the host pre-filled."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": "dhcp"},
        data=DHCP_DISCOVERY,
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"


async def test_dhcp_discovery_aborts_if_already_configured(
    hass: HomeAssistant,
) -> None:
    """DHCP discovery should abort if the Miniserver is already set up."""
    MockConfigEntry(
        domain=DOMAIN,
        unique_id="504F94A0FEA2",
        options=VALID_USER_INPUT,
    ).add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": "dhcp"},
        data=DHCP_DISCOVERY,
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_dhcp_discovery_aborts_second_nic_same_ip(
    hass: HomeAssistant,
) -> None:
    """DHCP with a different MAC but same IP should abort as already_configured."""
    MockConfigEntry(
        domain=DOMAIN,
        unique_id="504F94AAAAAA",
        options=VALID_USER_INPUT,
    ).add_to_hass(hass)

    different_mac_discovery = MagicMock(
        ip="192.168.1.77",
        hostname="loxone",
        macaddress="504F94BBBBBB",
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": "dhcp"},
        data=different_mac_discovery,
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"
