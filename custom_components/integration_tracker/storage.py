"""Persistent storage for Integration Tracker."""

from __future__ import annotations

from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import STORAGE_KEY, STORAGE_VERSION


class RegistryStorage:
    """Store registry state in Home Assistant's standard storage directory."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize storage."""
        self._store: Store[dict[str, Any]] = Store(
            hass,
            STORAGE_VERSION,
            STORAGE_KEY,
            private=True,
            atomic_writes=True,
        )

    async def async_load(self) -> dict[str, Any]:
        """Load registry state."""
        return await self._store.async_load() or {"items": {}, "metadata": {}}

    async def async_save(self, data: dict[str, Any]) -> None:
        """Persist registry state immediately."""
        await self._store.async_save(data)
