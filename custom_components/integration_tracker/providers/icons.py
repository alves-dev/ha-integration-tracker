"""Icon resolution for installed Home Assistant integrations."""

from __future__ import annotations

import base64
import re
from pathlib import Path

from homeassistant.core import HomeAssistant

DOMAIN_PATTERN = re.compile(r"^[a-z0-9_]+$")


async def async_resolve_icon(
    hass: HomeAssistant,
    domain: str | None,
    repository_path: str | None = None,
) -> str | None:
    """Return the installed icon, falling back to Home Assistant's brand route."""
    icon_paths: list[Path] = []
    if repository_path:
        icon_paths.append(Path(repository_path) / "brand" / "icon.png")
    if domain and DOMAIN_PATTERN.fullmatch(domain):
        icon_paths.append(
            Path(hass.config.path("custom_components", domain, "brand", "icon.png"))
        )

    for icon_path in icon_paths:
        try:
            icon_data = await hass.async_add_executor_job(icon_path.read_bytes)
        except OSError:
            continue
        encoded = base64.b64encode(icon_data).decode("ascii")
        return f"data:image/png;base64,{encoded}"

    if domain and DOMAIN_PATTERN.fullmatch(domain):
        return f"/api/brands/integration/{domain}/icon.png?placeholder=no"
    return None
