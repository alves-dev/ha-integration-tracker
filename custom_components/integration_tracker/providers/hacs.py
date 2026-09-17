"""HACS discovery provider."""

from __future__ import annotations

from typing import Any

from homeassistant.core import HomeAssistant

from ..models import ProviderItem
from .base import IntegrationProvider, ProviderUnavailableError


def _string_value(value: Any) -> str | None:
    """Normalize HACS values and string enums."""
    if value is None:
        return None
    normalized = getattr(value, "value", value)
    text = str(normalized)
    return text or None


class HacsProvider(IntegrationProvider):
    """Discover repositories from HACS without exposing HACS objects to the core."""

    source = "hacs"

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the provider."""
        self._hass = hass

    async def async_discover(self) -> list[ProviderItem]:
        """Return installed HACS repositories as a complete snapshot."""
        hacs = self._hass.data.get("hacs")
        if hacs is None:
            raise ProviderUnavailableError("HACS is not loaded")

        system = getattr(hacs, "system", None)
        if system is not None and getattr(system, "disabled", False):
            reason = getattr(system, "disabled_reason", "unknown reason")
            raise ProviderUnavailableError(f"HACS is disabled: {reason}")

        status = getattr(hacs, "status", None)
        if status is not None and getattr(status, "startup", False):
            raise ProviderUnavailableError("HACS is still starting")

        repositories = getattr(hacs, "repositories", None)
        if repositories is None or not hasattr(repositories, "list_downloaded"):
            raise ProviderUnavailableError("HACS repository data is unavailable")

        discovered: list[ProviderItem] = []
        for repository in repositories.list_downloaded:
            data = getattr(repository, "data", None)
            full_name = _string_value(getattr(data, "full_name", None))
            if not full_name:
                continue

            name = _string_value(getattr(repository, "display_name", None)) or full_name
            discovered.append(
                ProviderItem(
                    source=self.source,
                    repository=full_name,
                    name=name,
                    repository_url=f"https://github.com/{full_name}",
                    category=_string_value(getattr(data, "category", None)),
                    version=_string_value(
                        getattr(repository, "display_installed_version", None)
                    ),
                    available_version=_string_value(
                        getattr(repository, "display_available_version", None)
                    ),
                    provider_data={
                        "description": _string_value(
                            getattr(data, "description", None)
                        ),
                        "domain": _string_value(getattr(data, "domain", None)),
                        "hacs_id": _string_value(getattr(data, "id", None)),
                        "pending_update": bool(
                            getattr(repository, "pending_update", False)
                        ),
                        "topics": list(getattr(data, "topics", []) or []),
                    },
                )
            )

        return discovered
