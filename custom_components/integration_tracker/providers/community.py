"""Compatibility provider for HACS and the Home Assistant Marketplace."""

from __future__ import annotations

from homeassistant.core import HomeAssistant

from ..models import ProviderItem
from .base import IntegrationProvider
from .hacs import HacsProvider
from .marketplace import MarketplaceProvider


class CommunityStoreProvider(IntegrationProvider):
    """Use Marketplace on new Home Assistant versions and HACS on older ones."""

    source = "hacs"

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize both compatible discovery backends."""
        self._hass = hass
        self._marketplace = MarketplaceProvider(hass)
        self._hacs = HacsProvider(hass)

    async def async_discover(self) -> list[ProviderItem]:
        """Return a complete snapshot from the active community store."""
        config_entries = self._hass.config_entries
        if config_entries.async_loaded_entries("marketplace") or config_entries.async_entries(
            "marketplace"
        ):
            return await self._marketplace.async_discover()
        return await self._hacs.async_discover()
