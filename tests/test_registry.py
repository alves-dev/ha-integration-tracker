"""Tests for source-neutral registry behavior."""

from __future__ import annotations

from copy import deepcopy

import pytest

from custom_components.integration_tracker.models import ProviderItem
from custom_components.integration_tracker.providers.base import (
    IntegrationProvider,
    ProviderUnavailableError,
)
from custom_components.integration_tracker.registry import IntegrationRegistry


class MemoryStorage:
    """In-memory implementation of registry storage."""

    def __init__(self) -> None:
        self.data = {"items": {}, "metadata": {}}

    async def async_load(self):
        return deepcopy(self.data)

    async def async_save(self, data):
        self.data = deepcopy(data)


class FakeProvider(IntegrationProvider):
    """Provider with a replaceable snapshot."""

    source = "hacs"

    def __init__(self, items=None, error=None) -> None:
        self.items = items or []
        self.error = error

    async def async_discover(self):
        if self.error:
            raise self.error
        return self.items


def provider_item(version="1.0", name="Example"):
    return ProviderItem(
        source="hacs",
        repository="owner/example",
        name=name,
        repository_url="https://github.com/owner/example",
        category="integration",
        version=version,
        available_version="2.0",
    )


@pytest.mark.asyncio
async def test_sync_preserves_user_fields_and_marks_absence_uninstalled():
    storage = MemoryStorage()
    registry = IntegrationRegistry(storage)
    await registry.async_load()

    await registry.async_sync(FakeProvider([provider_item()]))
    item_id = "hacs:owner/example"
    await registry.async_update_item(
        item_id,
        {"rating": 3, "status": "active", "notes": "Needed", "tags": ["important"]},
    )
    await registry.async_add_usage(item_id, "Main dashboard", "dashboard", "/lovelace/main")
    await registry.async_mark_reviewed(item_id)

    await registry.async_sync(FakeProvider([provider_item(version="1.1", name="Renamed")]))
    item = registry.get_item(item_id)
    assert item.name == "Renamed"
    assert item.version == "1.1"
    assert item.rating == 3
    assert item.status == "active"
    assert item.notes == "Needed"
    assert item.tags == ["important"]
    assert len(item.usages) == 1
    assert len(item.review_history) == 1

    await registry.async_sync(FakeProvider([]))
    item = registry.get_item(item_id)
    assert item.installed is False
    assert item.uninstalled_at is not None
    assert item.rating == 3
    assert item.usages[0].name == "Main dashboard"


@pytest.mark.asyncio
async def test_failed_provider_snapshot_does_not_mark_items_uninstalled():
    storage = MemoryStorage()
    registry = IntegrationRegistry(storage)
    await registry.async_load()
    await registry.async_sync(FakeProvider([provider_item()]))
    last_sync = registry.last_synced_at

    with pytest.raises(ProviderUnavailableError):
        await registry.async_sync(
            FakeProvider(error=ProviderUnavailableError("HACS is unavailable"))
        )

    assert registry.get_item("hacs:owner/example").installed is True
    assert registry.last_synced_at == last_sync


@pytest.mark.asyncio
async def test_reinstall_reuses_history_and_clears_uninstall_date():
    storage = MemoryStorage()
    registry = IntegrationRegistry(storage)
    await registry.async_load()
    provider = FakeProvider([provider_item()])
    await registry.async_sync(provider)
    await registry.async_update_item("hacs:owner/example", {"rating": 2})
    await registry.async_sync(FakeProvider([]))
    await registry.async_sync(provider)

    item = registry.get_item("hacs:owner/example")
    assert item.installed is True
    assert item.uninstalled_at is None
    assert item.rating == 2
    assert len(registry.list_items()) == 1


@pytest.mark.asyncio
async def test_usage_crud_and_storage_reload():
    storage = MemoryStorage()
    registry = IntegrationRegistry(storage)
    await registry.async_load()
    await registry.async_sync(FakeProvider([provider_item()]))
    item_id = "hacs:owner/example"

    usage = await registry.async_add_usage(item_id, "Dashboard", "dashboard", "/dashboard")
    await registry.async_update_usage(
        item_id, usage.id, "Automation", "automation", "/config/automation/edit/1"
    )

    restored = IntegrationRegistry(storage)
    await restored.async_load()
    assert restored.get_item(item_id).usages[0].name == "Automation"

    await restored.async_remove_usage(item_id, usage.id)
    assert restored.get_item(item_id).usages == []
