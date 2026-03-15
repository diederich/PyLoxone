"""Fixtures for Loxone HA unit tests (mocked environment)."""

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, PropertyMock, patch

import pytest
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, CONF_USERNAME


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations in all HA unit tests."""
    yield
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.loxone.const import (
    CONF_LIGHTCONTROLLER_SUBCONTROLS_GEN,
    CONF_SCENE_GEN,
    CONF_SCENE_GEN_DELAY,
    DOMAIN,
)

FIXTURE_DIR = Path(__file__).parent / "fixtures"

MOCK_OPTIONS = {
    CONF_HOST: "192.168.1.100",
    CONF_PORT: 8080,
    CONF_USERNAME: "admin",
    CONF_PASSWORD: "password",
    CONF_SCENE_GEN: True,
    CONF_SCENE_GEN_DELAY: 3,
    CONF_LIGHTCONTROLLER_SUBCONTROLS_GEN: False,
}


def _load_json_fixture(name: str) -> dict:
    return json.loads((FIXTURE_DIR / name).read_text())


@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    """Return a MockConfigEntry for the Loxone integration."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={},
        options=MOCK_OPTIONS,
        unique_id="504F94A0FEA2",
        version=3,
    )


@pytest.fixture
def structure_fixture_name() -> str:
    """Override in tests to load a different structure fixture."""
    return "structure_minimal.json"


@pytest.fixture
def mock_loxone_connection(structure_fixture_name: str):
    """Mock the LoxoneConnection used by the coordinator."""
    structure = _load_json_fixture(structure_fixture_name)

    with patch(
        "custom_components.loxone.coordinator.LoxoneConnection",
    ) as mock_cls:
        api = MagicMock()
        api.open = AsyncMock()
        api.close = AsyncMock()
        api.start_listening = AsyncMock()
        api.send_websocket_command = AsyncMock()
        api.send_secured__websocket_command = AsyncMock()
        api.get_token_dict = MagicMock(
            return_value={"token": "fake", "hash_alg": "SHA256", "valid_until": "9999"}
        )
        api.structure_file = structure
        api.connection = MagicMock()

        mock_cls.return_value = api
        yield api


@pytest.fixture
async def init_integration(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_loxone_connection: MagicMock,
) -> MockConfigEntry:
    """Set up the Loxone integration for testing."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    return mock_config_entry
