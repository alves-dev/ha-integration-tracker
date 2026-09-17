"""Register the Integration Tracker admin panel."""

from __future__ import annotations

from pathlib import Path

from homeassistant.components import panel_custom
from homeassistant.components.frontend import async_remove_panel
from homeassistant.components.http import StaticPathConfig
from homeassistant.core import HomeAssistant

from .const import (
    INTEGRATION_VERSION,
    PANEL_COMPONENT,
    PANEL_ICON,
    PANEL_TITLE,
    PANEL_URL,
    STATIC_URL,
)

FRONTEND_REGISTERED = "integration_tracker_frontend_registered"


async def async_register_panel(hass: HomeAssistant) -> None:
    """Register static assets and the admin-only sidebar panel."""
    if not hass.data.get(FRONTEND_REGISTERED):
        frontend_dir = Path(__file__).parent / "frontend"
        await hass.http.async_register_static_paths(
            [StaticPathConfig(STATIC_URL, str(frontend_dir), cache_headers=False)]
        )
        hass.data[FRONTEND_REGISTERED] = True

    if PANEL_URL not in hass.data.get("frontend_panels", {}):
        await panel_custom.async_register_panel(
            hass=hass,
            frontend_url_path=PANEL_URL,
            webcomponent_name=PANEL_COMPONENT,
            sidebar_title=PANEL_TITLE,
            sidebar_icon=PANEL_ICON,
            module_url=(
                f"{STATIC_URL}/integration-tracker-panel.js?v={INTEGRATION_VERSION}"
            ),
            embed_iframe=False,
            require_admin=True,
            config_panel_domain="integration_tracker",
        )


def async_unregister_panel(hass: HomeAssistant) -> None:
    """Remove the sidebar panel when the config entry unloads."""
    if PANEL_URL in hass.data.get("frontend_panels", {}):
        async_remove_panel(hass, PANEL_URL)
