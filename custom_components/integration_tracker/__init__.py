"""Integration Tracker setup."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_call_later, async_track_time_interval

from .const import DOMAIN, INITIAL_SYNC_RETRY_SECONDS, SYNC_INTERVAL
from .panel import async_register_panel, async_unregister_panel
from .providers import HacsProvider
from .registry import IntegrationRegistry
from .storage import RegistryStorage
from .websocket import async_register_websocket_commands

_LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class IntegrationTrackerRuntime:
    """Runtime state for one config entry."""

    config_entry: ConfigEntry
    registry: IntegrationRegistry
    provider: HacsProvider
    sync_error: str | None = None

    async def async_sync(self) -> dict[str, int]:
        """Synchronize and retain the latest error for the panel."""
        try:
            result = await self.registry.async_sync(self.provider)
        except Exception as err:
            self.sync_error = str(err)
            raise
        self.sync_error = None
        return result


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the integration namespace."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Integration Tracker from a config entry."""
    registry = IntegrationRegistry(RegistryStorage(hass))
    await registry.async_load()
    runtime = IntegrationTrackerRuntime(entry, registry, HacsProvider(hass))
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = runtime

    async_register_websocket_commands(hass)
    await async_register_panel(hass)

    async def _run_sync() -> None:
        try:
            await runtime.async_sync()
        except Exception as err:
            _LOGGER.warning("HACS synchronization skipped: %s", err)

    await _run_sync()

    async def _delayed_sync(_now) -> None:
        if runtime.sync_error:
            await _run_sync()

    async def _periodic_sync(_now) -> None:
        await _run_sync()

    entry.async_on_unload(
        async_call_later(hass, INITIAL_SYNC_RETRY_SECONDS, _delayed_sync)
    )
    entry.async_on_unload(async_track_time_interval(hass, _periodic_sync, SYNC_INTERVAL))
    entry.async_on_unload(entry.add_update_listener(_async_reload_entry))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload Integration Tracker."""
    hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    async_unregister_panel(hass)
    return True


async def _async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload after options change."""
    await hass.config_entries.async_reload(entry.entry_id)
