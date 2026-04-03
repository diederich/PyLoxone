"""Tests for Loxone repair issues (issue registry integration)."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.loxone.const import DOMAIN
from custom_components.loxone.coordinator import (
    ConnectionState,
    LoxoneCoordinator,
)
from custom_components.loxone.pyloxone_api.exceptions import LoxoneTokenError


async def test_token_error_creates_repair_issue(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """A token error should create a repair issue."""
    coordinator: LoxoneCoordinator = init_integration.runtime_data

    listening_task = asyncio.Future()
    listening_task.set_exception(LoxoneTokenError("token expired"))

    with patch.object(coordinator, "_async_reconnect", new_callable=AsyncMock):
        coordinator._handle_task_result(listening_task)

    await hass.async_block_till_done()

    issues = ir.async_get(hass)
    issue = issues.async_get_issue(DOMAIN, "token_expired")
    assert issue is not None
    assert issue.severity == ir.IssueSeverity.WARNING


async def test_successful_reconnect_clears_repair_issues(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """On successful reconnect, repair issues should be cleared."""
    ir.async_create_issue(
        hass, DOMAIN, "token_expired",
        is_fixable=False, is_persistent=False,
        severity=ir.IssueSeverity.WARNING,
        translation_key="token_expired",
    )
    ir.async_create_issue(
        hass, DOMAIN, "persistent_disconnect",
        is_fixable=False, is_persistent=False,
        severity=ir.IssueSeverity.ERROR,
        translation_key="persistent_disconnect",
        translation_placeholders={"host": "192.168.1.100"},
    )

    issues = ir.async_get(hass)
    assert issues.async_get_issue(DOMAIN, "token_expired") is not None
    assert issues.async_get_issue(DOMAIN, "persistent_disconnect") is not None

    coordinator: LoxoneCoordinator = init_integration.runtime_data

    with patch.object(
        coordinator, "_create_api"
    ), patch.object(
        coordinator, "async_start_listening", new_callable=AsyncMock
    ), patch.object(
        coordinator, "async_save_token", new_callable=AsyncMock
    ):
        mock_api = MagicMock()
        mock_api.open = AsyncMock(return_value=MagicMock())
        mock_api.close = AsyncMock()
        mock_api.structure_file = coordinator.api.structure_file
        mock_api.connection = MagicMock()
        mock_api.get_token_dict = MagicMock(
            return_value={"token": "fake", "hash_alg": "SHA256", "valid_until": "9999"}
        )
        coordinator.api = mock_api

        coordinator._shutting_down = False
        coordinator.connection_state = ConnectionState.RECONNECTING

        await coordinator._async_reconnect()

    assert issues.async_get_issue(DOMAIN, "token_expired") is None
    assert issues.async_get_issue(DOMAIN, "persistent_disconnect") is None
