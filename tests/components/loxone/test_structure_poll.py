"""Tests for structure file change detection."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.loxone.coordinator import (
    ConnectionState,
    LoxoneCoordinator,
)


@pytest.fixture
def coordinator(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry
) -> LoxoneCoordinator:
    """Create a coordinator without full integration setup."""
    mock_config_entry.add_to_hass(hass)
    coord = LoxoneCoordinator(hass, mock_config_entry)
    coord.connection_state = ConnectionState.CONNECTED
    coord._structure_last_modified = "2026-01-01 00:00:00"
    return coord


def _mock_session(response_data: dict, status: int = 200) -> MagicMock:
    """Create a mock aiohttp session returning the given response."""
    mock_resp = AsyncMock()
    mock_resp.status = status
    mock_resp.json = AsyncMock(return_value=response_data)

    mock_session = MagicMock()
    mock_session.get = AsyncMock(return_value=mock_resp)
    return mock_session


async def test_structure_poll_detects_change(
    hass: HomeAssistant, coordinator: LoxoneCoordinator
) -> None:
    """When lastModified changes, the integration should reload."""
    session = _mock_session({"lastModified": "2026-04-03 12:00:00"})

    with patch(
        "custom_components.loxone.coordinator.async_get_clientsession",
        return_value=session,
    ), patch.object(
        hass.config_entries, "async_reload", new_callable=AsyncMock
    ) as mock_reload:
        await coordinator._check_structure_change()

    mock_reload.assert_called_once_with(coordinator.config_entry.entry_id)
    assert coordinator._structure_last_modified == "2026-04-03 12:00:00"


async def test_structure_poll_no_change(
    hass: HomeAssistant, coordinator: LoxoneCoordinator
) -> None:
    """When lastModified is unchanged, no reload should happen."""
    session = _mock_session({"lastModified": "2026-01-01 00:00:00"})

    with patch(
        "custom_components.loxone.coordinator.async_get_clientsession",
        return_value=session,
    ), patch.object(
        hass.config_entries, "async_reload", new_callable=AsyncMock
    ) as mock_reload:
        await coordinator._check_structure_change()

    mock_reload.assert_not_called()


async def test_structure_poll_http_error_ignored(
    hass: HomeAssistant, coordinator: LoxoneCoordinator
) -> None:
    """HTTP errors during structure poll should be silently ignored."""
    session = _mock_session({}, status=503)

    with patch(
        "custom_components.loxone.coordinator.async_get_clientsession",
        return_value=session,
    ), patch.object(
        hass.config_entries, "async_reload", new_callable=AsyncMock
    ) as mock_reload:
        await coordinator._check_structure_change()

    mock_reload.assert_not_called()


async def test_structure_poll_skips_when_disconnected(
    hass: HomeAssistant, coordinator: LoxoneCoordinator
) -> None:
    """Poll callback should skip when not connected."""
    coordinator.connection_state = ConnectionState.RECONNECTING

    with patch(
        "custom_components.loxone.coordinator.async_get_clientsession"
    ) as mock_fn:
        await coordinator._async_poll_structure()

    mock_fn.assert_not_called()
