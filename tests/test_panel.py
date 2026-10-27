"""Tests for the administrator panel registration."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from custom_components.integration_tracker.const import PANEL_URL
from custom_components.integration_tracker.panel import (
    FRONTEND_REGISTERED,
    async_register_panel,
    async_unregister_panel,
)


@pytest.mark.asyncio
async def test_register_panel_registers_assets_and_requires_admin():
    """Static assets are registered once and the panel requires an admin."""
    hass = SimpleNamespace(
        data={},
        http=SimpleNamespace(async_register_static_paths=AsyncMock()),
    )

    with patch(
        "custom_components.integration_tracker.panel.panel_custom.async_register_panel",
        new=AsyncMock(),
    ) as register_panel:
        await async_register_panel(hass)
        await async_register_panel(hass)

    assert hass.data[FRONTEND_REGISTERED] is True
    hass.http.async_register_static_paths.assert_awaited_once()
    assert register_panel.await_count == 2
    assert register_panel.call_args.kwargs["require_admin"] is True


def test_unregister_panel_removes_registered_panel():
    """Unloading removes only an existing panel."""
    hass = SimpleNamespace(data={"frontend_panels": {PANEL_URL: object()}})
    with patch(
        "custom_components.integration_tracker.panel.async_remove_panel"
    ) as remove_panel:
        async_unregister_panel(hass)

    remove_panel.assert_called_once_with(hass, PANEL_URL)
