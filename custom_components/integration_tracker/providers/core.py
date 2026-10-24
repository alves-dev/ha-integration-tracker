"""Home Assistant Core integration discovery provider."""

from __future__ import annotations

from homeassistant.const import __version__ as HOME_ASSISTANT_VERSION
from homeassistant.core import HomeAssistant
from homeassistant.loader import Integration, async_get_integrations

from ..models import ProviderItem
from .base import IntegrationProvider, ProviderUnavailableError


class CoreProvider(IntegrationProvider):
    """Discover built-in integrations loaded in this Home Assistant instance."""

    source = "core"

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the provider."""
        self._hass = hass

    async def async_discover(self) -> list[ProviderItem]:
        """Return configured built-in integrations as a complete snapshot."""
        domains = sorted(self._hass.config_entries.async_domains())
        try:
            integrations = await async_get_integrations(self._hass, domains)
        except Exception as err:
            raise ProviderUnavailableError(
                f"Home Assistant Core data is unavailable: {err}"
            ) from err

        discovered: list[ProviderItem] = []
        for domain, integration in integrations.items():
            if not isinstance(integration, Integration) or not integration.is_built_in:
                continue

            manifest = integration.manifest
            name = str(manifest.get("name") or domain.replace("_", " ").title())
            discovered.append(
                ProviderItem(
                    source=self.source,
                    repository=domain,
                    name=name,
                    repository_url=(
                        "https://github.com/home-assistant/core/tree/dev/"
                        f"homeassistant/components/{domain}"
                    ),
                    category="integration",
                    version=HOME_ASSISTANT_VERSION,
                    icon=f"https://brands.home-assistant.io/{domain}/icon.png",
                    provider_data={
                        "domain": domain,
                        "integration_type": manifest.get("integration_type"),
                        "quality_scale": manifest.get("quality_scale"),
                        "store": "core",
                    },
                )
            )

        return discovered
