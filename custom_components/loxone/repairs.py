"""Repair flows for PyLoxone."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import data_entry_flow
from homeassistant.components.repairs import RepairsFlow
from homeassistant.core import HomeAssistant


class AuthFailedRepairFlow(RepairsFlow):
    """Walk the user through re-authenticating after a credential failure."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> data_entry_flow.FlowResult:
        """Step init asynchronously."""
        return await self.async_step_confirm()

    async def async_step_confirm(self, user_input: dict[str, Any] | None = None) -> data_entry_flow.FlowResult:
        """Step confirm asynchronously."""
        if user_input is not None:
            entry_id = self.issue_id.removeprefix("token_expired_")
            entry = self.hass.config_entries.async_get_entry(entry_id)
            if entry:
                entry.async_start_reauth(self.hass)
            return self.async_create_entry(data={})

        return self.async_show_form(
            step_id="confirm",
            data_schema=vol.Schema({}),
            description_placeholders={},
        )


async def async_create_fix_flow(
    hass: HomeAssistant,
    issue_id: str,
    data: dict[str, str | int | float | None] | None,
) -> RepairsFlow:
    """Create the appropriate repair flow for the given issue."""
    if issue_id.startswith("token_expired_"):
        return AuthFailedRepairFlow()
    raise ValueError(f"Unknown issue: {issue_id}")
