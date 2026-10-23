"""Icon resolution for installed Home Assistant integrations."""

from __future__ import annotations

import base64
import re
from pathlib import Path

from homeassistant.core import HomeAssistant

DOMAIN_PATTERN = re.compile(r"^[a-z0-9_]+$")


async def async_resolve_icon(hass: HomeAssistant, domain: str | None) -> str | None:
    """Return the installed integration icon, falling back to HA Brands."""
    if not domain or not DOMAIN_PATTERN.fullmatch(domain):
        return None

    icon_path = Path(hass.config.path("custom_components", domain, "brand", "icon.png"))
    try:
        icon_data = await hass.async_add_executor_job(icon_path.read_bytes)
    except OSError:
        return f"https://brands.home-assistant.io/{domain}/icon.png"

    encoded = base64.b64encode(icon_data).decode("ascii")
    return f"data:image/png;base64,{encoded}"
