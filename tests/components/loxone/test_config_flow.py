"""Tests for the Loxone config flow."""

import pytest
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
}


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
        user_input={**VALID_USER_INPUT, "username": "user\u4e16"},  # CJK character
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
            "username": "b\u00fcro",     # büro
            "password": "p\u00e4ssw\u00f6rd",  # pässwörd
        },
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY


async def test_options_flow(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
) -> None:
    """Options flow should allow changing settings on an existing entry."""
    entry = init_integration
    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] is FlowResultType.FORM

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
