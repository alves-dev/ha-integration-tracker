"""Home Assistant Marketplace discovery provider."""

from __future__ import annotations

from typing import Any

from homeassistant.core import HomeAssistant

from ..models import ProviderItem
from .base import IntegrationProvider, ProviderUnavailableError
from .icons import async_resolve_icon


def _string_value(value: Any) -> str | None:
    """Normalize Marketplace values and string enums."""
    if value is None:
        return None
    normalized = getattr(value, "value", value)
    text = str(normalized)
    return text or None


class MarketplaceProvider(IntegrationProvider):
    """Discover repositories installed by Home Assistant's Marketplace."""

    # Keep the source identifier stable so HACS records are reused after the
    # Marketplace migration.
    source = "hacs"

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the provider."""
        self._hass = hass

    async def async_discover(self) -> list[ProviderItem]:
        """Return installed Marketplace repositories as a complete snapshot."""
        entries = self._hass.config_entries.async_loaded_entries("marketplace")
        if not entries:
            raise ProviderUnavailableError("Marketplace is not loaded")

        marketplace = getattr(entries[0], "runtime_data", None)
        if marketplace is None:
            raise ProviderUnavailableError("Marketplace runtime data is unavailable")

        system = getattr(marketplace, "system", None)
        if system is not None and getattr(system, "disabled", False):
            reason = getattr(system, "disabled_reason", "unknown reason")
            raise ProviderUnavailableError(f"Marketplace is disabled: {reason}")

        status = getattr(marketplace, "status", None)
        if status is not None and getattr(status, "startup", False):
            raise ProviderUnavailableError("Marketplace is still starting")

        repositories = getattr(marketplace, "repositories", None)
        installed = getattr(repositories, "list_installed", None)
        if installed is None:
            raise ProviderUnavailableError("Marketplace repository data is unavailable")

        discovered: list[ProviderItem] = []
        for repository in installed:
            data = getattr(repository, "data", None)
            full_name = _string_value(getattr(data, "full_name", None))
            if not full_name:
                continue

            domain = _string_value(getattr(data, "domain", None))
            icon = await async_resolve_icon(
                self._hass, domain, getattr(repository, "localpath", None)
            )
            discovered.append(
                ProviderItem(
                    source=self.source,
                    repository=full_name,
                    name=_string_value(getattr(repository, "display_name", None))
                    or full_name,
                    repository_url=f"https://github.com/{full_name}",
                    category=_string_value(getattr(data, "category", None)),
                    version=_string_value(
                        getattr(repository, "display_installed_version", None)
                    ),
                    available_version=_string_value(
                        getattr(repository, "display_available_version", None)
                    ),
                    icon=icon,
                    provider_data={
                        "description": _string_value(getattr(data, "description", None)),
                        "domain": domain,
                        "marketplace_id": _string_value(getattr(data, "id", None)),
                        "pending_update": bool(
                            getattr(repository, "pending_update", False)
                        ),
                        "topics": list(getattr(data, "topics", []) or []),
                        "store": "marketplace",
                    },
                )
            )

        return discovered
