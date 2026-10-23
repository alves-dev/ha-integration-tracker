"""Tests for HACS and Marketplace provider compatibility."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from custom_components.integration_tracker.providers import CommunityStoreProvider
from custom_components.integration_tracker.providers.base import ProviderUnavailableError


class FakeConfigEntries:
    """Minimal config-entry collection for provider tests."""

    def __init__(self, marketplace=None, marketplace_configured=False) -> None:
        self.marketplace = marketplace
        self.marketplace_configured = marketplace_configured

    def async_loaded_entries(self, domain: str):
        if domain == "marketplace" and self.marketplace is not None:
            return [SimpleNamespace(runtime_data=self.marketplace)]
        return []

    def async_entries(self, domain: str):
        if domain == "marketplace" and self.marketplace_configured:
            return [SimpleNamespace()]
        return []


def marketplace_repository():
    """Return a repository shaped like the Marketplace runtime object."""
    data = SimpleNamespace(
        full_name="owner/example",
        category="integration",
        description="An example repository",
        domain="example",
        id=42,
        topics=["home-assistant"],
    )
    return SimpleNamespace(
        data=data,
        display_name="Example",
        display_installed_version="1.2.0",
        display_available_version="1.3.0",
        pending_update=True,
    )


@pytest.mark.asyncio
async def test_marketplace_snapshot_preserves_hacs_identity():
    """Marketplace items keep the source identity used by existing records."""
    marketplace = SimpleNamespace(
        status=SimpleNamespace(startup=False),
        system=SimpleNamespace(disabled=False),
        repositories=SimpleNamespace(list_installed=[marketplace_repository()]),
    )
    hass = SimpleNamespace(config_entries=FakeConfigEntries(marketplace))

    items = await CommunityStoreProvider(hass).async_discover()

    assert len(items) == 1
    assert items[0].item_id == "hacs:owner/example"
    assert items[0].name == "Example"
    assert items[0].version == "1.2.0"
    assert items[0].available_version == "1.3.0"
    assert items[0].provider_data["pending_update"] is True


@pytest.mark.asyncio
async def test_marketplace_startup_is_non_destructive():
    """A Marketplace startup state must not be treated as an empty snapshot."""
    marketplace = SimpleNamespace(
        status=SimpleNamespace(startup=True),
        system=SimpleNamespace(disabled=False),
        repositories=SimpleNamespace(list_installed=[]),
    )
    hass = SimpleNamespace(config_entries=FakeConfigEntries(marketplace))

    with pytest.raises(ProviderUnavailableError, match="still starting"):
        await CommunityStoreProvider(hass).async_discover()


@pytest.mark.asyncio
async def test_configured_marketplace_waits_for_runtime_before_hacs_fallback():
    """A configured but not loaded Marketplace must not select HACS."""
    hass = SimpleNamespace(
        config_entries=FakeConfigEntries(marketplace_configured=True),
        data={},
    )

    with pytest.raises(ProviderUnavailableError, match="Marketplace is not loaded"):
        await CommunityStoreProvider(hass).async_discover()


@pytest.mark.asyncio
async def test_legacy_hacs_backend_remains_supported():
    """Older Home Assistant versions continue using the HACS adapter."""
    repository = SimpleNamespace(
        data=SimpleNamespace(
            full_name="owner/legacy",
            category="integration",
            description="Legacy repository",
            domain="legacy",
            id=7,
            topics=[],
        ),
        display_name="Legacy",
        display_installed_version="1.0.0",
        display_available_version="1.1.0",
        pending_update=False,
    )
    hass = SimpleNamespace(
        config_entries=FakeConfigEntries(),
        data=SimpleNamespace(),
    )
    hass.data = {
        "hacs": SimpleNamespace(
            system=SimpleNamespace(disabled=False),
            status=SimpleNamespace(startup=False),
            repositories=SimpleNamespace(list_downloaded=[repository]),
        )
    }

    items = await CommunityStoreProvider(hass).async_discover()

    assert items[0].item_id == "hacs:owner/legacy"
