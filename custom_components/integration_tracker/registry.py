"""Persistent source-neutral registry operations."""

from __future__ import annotations

import asyncio
from typing import Any, Protocol

from .const import STATUSES
from .models import TrackedItem, Usage, utcnow_iso
from .providers.base import IntegrationProvider


class StorageProtocol(Protocol):
    """Minimal storage contract used by the registry."""

    async def async_load(self) -> dict[str, Any]: ...

    async def async_save(self, data: dict[str, Any]) -> None: ...


class RegistryError(ValueError):
    """Raised for invalid registry operations."""


class ItemNotFoundError(RegistryError):
    """Raised when an item does not exist."""


class UsageNotFoundError(RegistryError):
    """Raised when a usage does not exist."""


class IntegrationRegistry:
    """Own tracked items and preserve user metadata across provider syncs."""

    def __init__(self, storage: StorageProtocol) -> None:
        """Initialize the registry."""
        self._storage = storage
        self._items: dict[str, TrackedItem] = {}
        self._metadata: dict[str, Any] = {}
        self._lock = asyncio.Lock()

    @property
    def last_synced_at(self) -> str | None:
        """Return the timestamp of the last successful synchronization."""
        return self._metadata.get("last_synced_at")

    async def async_load(self) -> None:
        """Load stored items."""
        data = await self._storage.async_load()
        raw_items = data.get("items") or {}
        if isinstance(raw_items, list):
            raw_items = {item["id"]: item for item in raw_items}
        self._items = {
            item_id: TrackedItem.from_dict(item)
            for item_id, item in raw_items.items()
        }
        self._metadata = dict(data.get("metadata") or {})

    def get_item(self, item_id: str) -> TrackedItem:
        """Return one item or raise a domain error."""
        try:
            return self._items[item_id]
        except KeyError as err:
            raise ItemNotFoundError(f"Tracked item not found: {item_id}") from err

    def list_items(self) -> list[TrackedItem]:
        """Return all items sorted by name."""
        return sorted(self._items.values(), key=lambda item: item.name.casefold())

    async def async_sync(self, provider: IntegrationProvider) -> dict[str, int]:
        """Synchronize a complete provider snapshot atomically."""
        discovered = await provider.async_discover()
        now = utcnow_iso()
        counts = {"created": 0, "updated": 0, "uninstalled": 0}

        async with self._lock:
            discovered_ids: set[str] = set()
            for provider_item in discovered:
                item_id = provider_item.item_id
                discovered_ids.add(item_id)
                if item_id in self._items:
                    self._items[item_id].update_from_provider(provider_item)
                    counts["updated"] += 1
                else:
                    self._items[item_id] = TrackedItem.from_provider(provider_item, now)
                    counts["created"] += 1

            for item in self._items.values():
                if (
                    item.source.casefold() == provider.source.casefold()
                    and item.id not in discovered_ids
                    and item.installed
                ):
                    item.installed = False
                    item.uninstalled_at = now
                    counts["uninstalled"] += 1

            self._metadata["last_synced_at"] = now
            await self._async_save()

        return counts

    async def async_update_item(self, item_id: str, changes: dict[str, Any]) -> TrackedItem:
        """Update user-owned item fields."""
        allowed = {"rating", "status", "notes", "tags"}
        unknown = set(changes) - allowed
        if unknown:
            raise RegistryError(f"Provider-owned or unknown fields: {', '.join(sorted(unknown))}")

        async with self._lock:
            item = self.get_item(item_id)
            if "rating" in changes:
                rating = changes["rating"]
                if rating is not None and (not isinstance(rating, int) or rating not in (1, 2, 3)):
                    raise RegistryError("Rating must be 1, 2, 3, or null")
                item.rating = rating
            if "status" in changes:
                status = changes["status"] or None
                if status is not None and status not in STATUSES:
                    raise RegistryError(f"Unsupported lifecycle status: {status}")
                item.status = status
            if "notes" in changes:
                notes = changes["notes"]
                item.notes = str(notes).strip() if notes else None
            if "tags" in changes:
                item.tags = _normalize_tags(changes["tags"])
            await self._async_save()
            return item

    async def async_add_usage(
        self, item_id: str, name: str, usage_type: str, url: str | None
    ) -> Usage:
        """Add a manual usage."""
        name, usage_type, url = _normalize_usage(name, usage_type, url)
        async with self._lock:
            item = self.get_item(item_id)
            usage = Usage.create(name, usage_type, url)
            item.usages.append(usage)
            await self._async_save()
            return usage

    async def async_update_usage(
        self,
        item_id: str,
        usage_id: str,
        name: str,
        usage_type: str,
        url: str | None,
    ) -> Usage:
        """Update an existing usage."""
        name, usage_type, url = _normalize_usage(name, usage_type, url)
        async with self._lock:
            usage = self._find_usage(self.get_item(item_id), usage_id)
            usage.name = name
            usage.type = usage_type
            usage.url = url
            await self._async_save()
            return usage

    async def async_remove_usage(self, item_id: str, usage_id: str) -> None:
        """Remove a manual usage."""
        async with self._lock:
            item = self.get_item(item_id)
            usage = self._find_usage(item, usage_id)
            item.usages.remove(usage)
            await self._async_save()

    async def async_mark_reviewed(self, item_id: str) -> TrackedItem:
        """Record a review without replacing history."""
        async with self._lock:
            item = self.get_item(item_id)
            reviewed_at = utcnow_iso()
            item.last_reviewed_at = reviewed_at
            item.review_history.append({"reviewed_at": reviewed_at})
            await self._async_save()
            return item

    @staticmethod
    def _find_usage(item: TrackedItem, usage_id: str) -> Usage:
        for usage in item.usages:
            if usage.id == usage_id:
                return usage
        raise UsageNotFoundError(f"Usage not found: {usage_id}")

    async def _async_save(self) -> None:
        await self._storage.async_save(
            {
                "items": {item_id: item.to_dict() for item_id, item in self._items.items()},
                "metadata": self._metadata,
            }
        )


def _normalize_tags(tags: Any) -> list[str]:
    if not isinstance(tags, list):
        raise RegistryError("Tags must be a list")
    normalized: list[str] = []
    seen: set[str] = set()
    for raw_tag in tags:
        tag = str(raw_tag).strip()
        key = tag.casefold()
        if not tag or key in seen:
            continue
        if len(tag) > 64:
            raise RegistryError("Tags cannot exceed 64 characters")
        seen.add(key)
        normalized.append(tag)
    return normalized


def _normalize_usage(name: str, usage_type: str, url: str | None) -> tuple[str, str, str | None]:
    normalized_name = name.strip()
    normalized_type = usage_type.strip()
    normalized_url = url.strip() if url else None
    if not normalized_name:
        raise RegistryError("Usage name is required")
    if not normalized_type:
        raise RegistryError("Usage type is required")
    if normalized_url and not (
        normalized_url.startswith("/")
        or normalized_url.startswith("https://")
        or normalized_url.startswith("http://")
    ):
        raise RegistryError("Usage URL must be a Home Assistant path or an HTTP(S) URL")
    return normalized_name, normalized_type, normalized_url
