"""Tests for Loxone diagnostics."""

from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.loxone.diagnostics import (
    async_get_config_entry_diagnostics,
)


async def test_diagnostics_redacts_credentials(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """Diagnostics should redact username, password, host, and token."""
    diag = await async_get_config_entry_diagnostics(hass, init_integration)

    config = diag["config_entry"]
    assert config["options"]["username"] == "**REDACTED**"
    assert config["options"]["password"] == "**REDACTED**"
    assert config["options"]["host"] == "**REDACTED**"


async def test_diagnostics_includes_connection_state(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """Diagnostics should include the current connection state."""
    diag = await async_get_config_entry_diagnostics(hass, init_integration)
    assert diag["connection_state"] == "connected"


async def test_diagnostics_includes_miniserver_info(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """Diagnostics should include non-sensitive Miniserver metadata."""
    diag = await async_get_config_entry_diagnostics(hass, init_integration)
    ms = diag["miniserver"]
    assert "serial" in ms
    assert "software_version" in ms
    assert "project_name" in ms


async def test_diagnostics_redacts_structure(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """Structure file should redact msInfo and users, but keep controls summary."""
    diag = await async_get_config_entry_diagnostics(hass, init_integration)
    structure = diag["structure"]

    if "msInfo" in structure:
        assert structure["msInfo"] == "**REDACTED**"

    if "controls" in structure:
        for _uuid, ctrl in structure["controls"].items():
            assert "name" in ctrl
            assert "type" in ctrl
            assert "details" not in ctrl
