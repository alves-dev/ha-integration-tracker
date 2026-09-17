"""Source-neutral models used by Integration Tracker."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4


def utcnow_iso() -> str:
    """Return a stable UTC timestamp."""
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def parse_timestamp(value: str | None) -> datetime | None:
    """Parse an ISO timestamp stored by the integration."""
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None


@dataclass(slots=True)
class ProviderItem:
    """Provider-owned representation of a discovered item."""

    source: str
    repository: str
    name: str
    repository_url: str | None = None
    category: str | None = None
    version: str | None = None
    available_version: str | None = None
    icon: str | None = None
    provider_data: dict[str, Any] = field(default_factory=dict)

    @property
    def item_id(self) -> str:
        """Return a stable source-scoped identifier."""
        return f"{self.source.casefold()}:{self.repository.casefold()}"


@dataclass(slots=True)
class Usage:
    """A known place where a tracked item is used."""

    id: str
    name: str
    type: str
    url: str | None = None
    source: str = "manual"

    @classmethod
    def create(cls, name: str, usage_type: str, url: str | None = None) -> Usage:
        """Create a manual usage."""
        return cls(
            id=f"usage-{uuid4().hex}",
            name=name,
            type=usage_type,
            url=url,
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Usage:
        """Restore a usage from storage."""
        return cls(
            id=str(data.get("id") or f"usage-{uuid4().hex}"),
            name=str(data.get("name") or ""),
            type=str(data.get("type") or "other"),
            url=data.get("url") or None,
            source=str(data.get("source") or "manual"),
        )


@dataclass(slots=True)
class TrackedItem:
    """Persisted registry item with explicit provider and user-owned fields."""

    id: str
    source: str
    repository: str
    name: str
    repository_url: str | None
    category: str | None
    installed: bool
    version: str | None
    available_version: str | None
    icon: str | None
    provider_data: dict[str, Any]
    discovered_at: str
    uninstalled_at: str | None = None
    rating: int | None = None
    status: str | None = None
    notes: str | None = None
    tags: list[str] = field(default_factory=list)
    usages: list[Usage] = field(default_factory=list)
    last_reviewed_at: str | None = None
    review_history: list[dict[str, str]] = field(default_factory=list)

    @classmethod
    def from_provider(cls, item: ProviderItem, now: str) -> TrackedItem:
        """Create a tracked item from provider metadata."""
        return cls(
            id=item.item_id,
            source=item.source,
            repository=item.repository,
            name=item.name,
            repository_url=item.repository_url,
            category=item.category,
            installed=True,
            version=item.version,
            available_version=item.available_version,
            icon=item.icon,
            provider_data=item.provider_data,
            discovered_at=now,
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TrackedItem:
        """Restore a tracked item from storage."""
        return cls(
            id=str(data["id"]),
            source=str(data["source"]),
            repository=str(data["repository"]),
            name=str(data.get("name") or data["repository"]),
            repository_url=data.get("repository_url"),
            category=data.get("category"),
            installed=bool(data.get("installed", False)),
            version=data.get("version"),
            available_version=data.get("available_version"),
            icon=data.get("icon"),
            provider_data=dict(data.get("provider_data") or {}),
            discovered_at=str(data.get("discovered_at") or utcnow_iso()),
            uninstalled_at=data.get("uninstalled_at"),
            rating=data.get("rating"),
            status=data.get("status"),
            notes=data.get("notes"),
            tags=list(data.get("tags") or []),
            usages=[Usage.from_dict(usage) for usage in data.get("usages") or []],
            last_reviewed_at=data.get("last_reviewed_at"),
            review_history=list(data.get("review_history") or []),
        )

    def update_from_provider(self, item: ProviderItem) -> None:
        """Update only provider-owned fields."""
        self.source = item.source
        self.repository = item.repository
        self.name = item.name
        self.repository_url = item.repository_url
        self.category = item.category
        self.version = item.version
        self.available_version = item.available_version
        self.icon = item.icon
        self.provider_data = item.provider_data
        self.installed = True
        self.uninstalled_at = None

    def review_state(self, interval_days: int, now: datetime | None = None) -> str:
        """Calculate review state without changing lifecycle status."""
        reviewed = parse_timestamp(self.last_reviewed_at)
        if reviewed is None:
            return "never_reviewed"
        reference = now or datetime.now(UTC)
        return (
            "needs_review"
            if reference - reviewed > timedelta(days=interval_days)
            else "up_to_date"
        )

    def to_dict(self, interval_days: int | None = None) -> dict[str, Any]:
        """Serialize the item for storage or the frontend."""
        result = asdict(self)
        if interval_days is not None:
            result["review_state"] = self.review_state(interval_days)
        return result
