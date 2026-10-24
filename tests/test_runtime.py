"""Tests for Integration Tracker runtime orchestration."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from custom_components.integration_tracker import (
    IntegrationTrackerRuntime,
    async_setup,
    async_unload_entry,
)
from custom_components.integration_tracker.const import DOMAIN
from custom_components.integration_tracker.usage_detection.coordinator import (
    DetectionSnapshot,
)


class FakeRegistry:
    """Small registry double for runtime tests."""

    def __init__(self, items=None):
        self.items = items or []
        self.last_synced_at = "2026-10-24T00:00:00+00:00"
        self.async_sync = AsyncMock()
        self.async_reconcile_detected_usages = AsyncMock(
            return_value={"created": 1, "updated": 0, "stale": 0}
        )

    def list_items(self):
        return self.items


@pytest.mark.asyncio
async def test_async_setup_initializes_domain_namespace():
    """Basic setup creates the integration data namespace."""
    hass = SimpleNamespace(data={})
    assert await async_setup(hass, {}) is True
    assert hass.data[DOMAIN] == {}


@pytest.mark.asyncio
async def test_runtime_syncs_enabled_providers_and_updates_repairs():
    """Sync aggregates providers and performs detection and repair projection."""
    registry = FakeRegistry()
    registry.async_sync.side_effect = [
        {"created": 1, "updated": 2, "uninstalled": 0},
        {"created": 0, "updated": 1, "uninstalled": 1},
    ]
    provider = object()
    core_provider = object()
    entry = SimpleNamespace(options={"include_core": True})
    runtime = IntegrationTrackerRuntime(
        SimpleNamespace(data={}), entry, registry, provider, core_provider
    )

    with patch.object(
        IntegrationTrackerRuntime, "async_detect_usages", new=AsyncMock()
    ), patch.object(
        IntegrationTrackerRuntime, "async_update_repairs"
    ) as update_repairs:
        result = await runtime.async_sync()

    assert result == {"created": 1, "updated": 3, "uninstalled": 1}
    assert registry.async_sync.await_count == 2
    update_repairs.assert_called_once()
    assert runtime.sync_error is None


@pytest.mark.asyncio
async def test_runtime_detection_reconciles_available_snapshots():
    """Only available detector snapshots are reconciled."""
    registry = FakeRegistry()
    runtime = IntegrationTrackerRuntime(
        SimpleNamespace(data={}), SimpleNamespace(options={}), registry, object(), object()
    )
    snapshots = [
        DetectionSnapshot("integrations", True, []),
        DetectionSnapshot("dashboards", False, [], "not loaded"),
    ]

    with patch(
        "custom_components.integration_tracker.async_detect_all",
        new=AsyncMock(return_value=snapshots),
    ):
        counts = await runtime.async_detect_usages()

    assert counts == {"created": 1, "updated": 0, "stale": 0}
    registry.async_reconcile_detected_usages.assert_awaited_once_with("integrations", [])
    assert runtime.usage_detection_error == "dashboards: not loaded"


@pytest.mark.asyncio
async def test_unload_entry_removes_runtime_and_panel():
    """Unloading removes the entry runtime and unregisters the panel."""
    entry = SimpleNamespace(entry_id="entry-1")
    hass = SimpleNamespace(data={DOMAIN: {"entry-1": object()}})
    with patch("custom_components.integration_tracker.async_unregister_panel") as unregister:
        assert await async_unload_entry(hass, entry) is True

    assert hass.data[DOMAIN] == {}
    unregister.assert_called_once_with(hass)
