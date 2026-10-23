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
from custom_components.integration_tracker.usage_detection.models import DetectedUsage


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


def detected(item_id="hacs:owner/example", key="automation:one:service:example.run"):
    return DetectedUsage(
        item_id=item_id,
        name="Example automation",
        type="automation",
        detection_key=key,
        detector="automations",
        confidence="high",
        url="/config/automation/edit/one",
        evidence={"reference": "example.run", "location": "action"},
    )


@pytest.mark.asyncio
async def test_detected_usage_reconciliation_is_idempotent_and_preserves_manual_usage():
    storage = MemoryStorage()
    registry = IntegrationRegistry(storage)
    await registry.async_load()
    await registry.async_sync(FakeProvider([provider_item()]))
    item_id = "hacs:owner/example"
    manual = await registry.async_add_usage(item_id, "My note", "other", None)

    counts = await registry.async_reconcile_detected_usages("automations", [detected()])
    assert counts == {"created": 1, "updated": 0, "stale": 0}
    assert len(registry.get_item(item_id).usages) == 2

    counts = await registry.async_reconcile_detected_usages("automations", [detected()])
    assert counts == {"created": 0, "updated": 1, "stale": 0}
    assert len(registry.get_item(item_id).usages) == 2
    assert registry.get_item(item_id).usages[0].id == manual.id


@pytest.mark.asyncio
async def test_detected_usage_is_marked_stale_only_for_successful_detector_snapshot():
    storage = MemoryStorage()
    registry = IntegrationRegistry(storage)
    await registry.async_load()
    await registry.async_sync(FakeProvider([provider_item()]))
    item_id = "hacs:owner/example"
    await registry.async_reconcile_detected_usages("automations", [detected()])
    usage = registry.get_item(item_id).usages[0]
    assert usage.source == "detected"
    assert usage.confirmed is False
    assert usage.stale is False

    await registry.async_reconcile_detected_usages("automations", [])
    assert usage.stale is True


@pytest.mark.asyncio
async def test_detected_usage_can_be_confirmed_or_converted_to_manual():
    storage = MemoryStorage()
    registry = IntegrationRegistry(storage)
    await registry.async_load()
    await registry.async_sync(FakeProvider([provider_item()]))
    item_id = "hacs:owner/example"
    await registry.async_reconcile_detected_usages("automations", [detected()])
    usage = registry.get_item(item_id).usages[0]

    await registry.async_confirm_detected_usage(item_id, usage.id)
    assert usage.confirmed is True
    await registry.async_convert_detected_usage(item_id, usage.id)
    assert usage.source == "manual"
    assert usage.detection_key is None
    assert usage.evidence == {}
