"""Runtime collection for automatic usage detection."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from homeassistant.components import automation, script
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from ..models import TrackedItem
from .detectors import (
    ComponentRecord,
    detect_component_usages,
    detect_configured_integrations,
    detect_dashboard_usages,
)
from .models import DetectedUsage


@dataclass(slots=True, frozen=True)
class DetectionSnapshot:
    """Result of one detector, including source availability."""

    detector: str
    available: bool
    detections: list[DetectedUsage]


async def async_detect_all(
    hass: HomeAssistant, items: Sequence[TrackedItem]
) -> list[DetectionSnapshot]:
    """Collect all currently supported detector snapshots."""
    return [
        DetectionSnapshot(
            "integrations",
            True,
            detect_configured_integrations(
                items,
                {domain.casefold() for domain in hass.config_entries.async_domains()},
            ),
        ),
        _component_snapshot(hass, items, automation.DATA_COMPONENT, "automations"),
        _component_snapshot(hass, items, script.DOMAIN, "scripts"),
        await _dashboard_snapshot(hass, items),
    ]


def _component_snapshot(
    hass: HomeAssistant, items: Sequence[TrackedItem], data_key: Any, detector: str
) -> DetectionSnapshot:
    """Collect automation or script entity configurations."""
    component = hass.data.get(data_key)
    if component is None:
        return DetectionSnapshot(detector, False, [])

    records = [
        ComponentRecord(
            identifier=str(getattr(entity, "entity_id", "unknown")),
            name=str(getattr(entity, "name", None) or getattr(entity, "entity_id", detector)),
            url=_entity_url(detector, getattr(entity, "entity_id", "")),
            config=getattr(entity, "raw_config", None),
        )
        for entity in getattr(component, "entities", [])
    ]
    return DetectionSnapshot(detector, True, detect_component_usages(items, records, detector))


async def _dashboard_snapshot(
    hass: HomeAssistant, items: Sequence[TrackedItem]
) -> DetectionSnapshot:
    """Collect stored/YAML dashboards and Lovelace resources."""
    lovelace = hass.data.get("lovelace")
    if not isinstance(lovelace, dict) or "dashboards" not in lovelace:
        return DetectionSnapshot("dashboards", False, [])

    records: list[ComponentRecord] = []
    try:
        for url_path, dashboard in lovelace["dashboards"].items():
            config = await dashboard.async_load(False)
            dashboard_path = url_path or "lovelace"
            records.append(
                ComponentRecord(
                    identifier=f"dashboard:{dashboard_path}",
                    name=str(config.get("title") or dashboard_path),
                    url=f"/dashboard/{dashboard_path}" if url_path else "/lovelace",
                    config=config,
                )
            )

        resources = lovelace.get("resources")
        if resources is not None:
            if not getattr(resources, "loaded", True):
                await resources.async_load()
            for resource in resources.async_items() or []:
                url = str(resource.get("url") or "")
                records.append(
                    ComponentRecord(
                        identifier=f"resource:{url}",
                        name=f"Lovelace resource: {url}",
                        url=url,
                        config=resource,
                    )
                )
    except (HomeAssistantError, KeyError, TypeError, ValueError):
        return DetectionSnapshot("dashboards", False, [])

    return DetectionSnapshot("dashboards", True, detect_dashboard_usages(items, records))


def _entity_url(detector: str, entity_id: str) -> str | None:
    """Build a useful Home Assistant configuration URL for a component entity."""
    object_id = entity_id.split(".", 1)[-1] if "." in entity_id else entity_id
    if detector == "automations":
        return f"/config/automation/edit/{object_id}"
    if detector == "scripts":
        return f"/config/script/edit/{object_id}"
    return None
