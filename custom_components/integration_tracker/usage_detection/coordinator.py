"""Runtime collection for automatic usage detection."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from homeassistant.components import automation, scene, script
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import device_registry, entity_registry
from homeassistant.helpers.storage import Store

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
        _component_snapshot(hass, items, scene.DATA_COMPONENT, "scenes"),
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
    return DetectionSnapshot(
        detector,
        True,
        detect_component_usages(
            items, records, detector, _reference_domains(hass)
        ),
    )


def _reference_domains(hass: HomeAssistant) -> dict[str, set[str]]:
    """Map device, area, and entity references to their integration domains."""
    domains: dict[str, set[str]] = {}
    config_entries = {
        entry.entry_id: entry.domain for entry in hass.config_entries.async_entries()
    }
    entity_registry_data = entity_registry.async_get(hass)
    device_registry_data = device_registry.async_get(hass)

    def add(reference: str, domain: str | None) -> None:
        if domain:
            domains.setdefault(reference.casefold(), set()).add(domain.casefold())

    for entity in entity_registry_data.entities.values():
        add(entity.entity_id, config_entries.get(entity.config_entry_id))
        if entity.device_id:
            add(entity.device_id, config_entries.get(entity.config_entry_id))

    for device in device_registry_data.devices.values():
        for entry_id in device.config_entries:
            add(device.id, config_entries.get(entry_id))

    for entity in entity_registry_data.entities.values():
        if entity.area_id:
            for domain in domains.get(entity.entity_id.casefold(), set()):
                add(entity.area_id, domain)
            if entity.device_id:
                for domain in domains.get(entity.device_id.casefold(), set()):
                    add(entity.area_id, domain)

    for device in device_registry_data.devices.values():
        area_id = getattr(device, "area_id", None)
        if area_id:
            for domain in domains.get(device.id.casefold(), set()):
                add(area_id, domain)
    return domains


def _dashboard_view_records(
    identifier: str, dashboard_name: str, base_url: str, config: dict[str, Any]
) -> list[ComponentRecord]:
    """Create records whose links point to the dashboard view containing a reference."""
    views = config.get("views")
    if not isinstance(views, list) or not views:
        return [ComponentRecord(identifier, dashboard_name, base_url, config)]

    records: list[ComponentRecord] = []
    for index, view in enumerate(views):
        if not isinstance(view, dict):
            continue
        view_path = str(view.get("path") or index)
        records.append(
            ComponentRecord(
                identifier=f"{identifier}:view:{view_path}",
                name=f"{dashboard_name} — {view.get('title') or view_path}",
                url=f"{base_url.rstrip('/')}/{view_path}",
                config={"view": view},
            )
        )
    return records or [ComponentRecord(identifier, dashboard_name, base_url, config)]


async def _dashboard_snapshot(
    hass: HomeAssistant, items: Sequence[TrackedItem]
) -> DetectionSnapshot:
    """Collect stored/YAML dashboards and Lovelace resources."""
    lovelace = hass.data.get("lovelace")
    records: list[ComponentRecord] = []
    loaded_sources = 0
    if isinstance(lovelace, dict) and "dashboards" in lovelace:
        for url_path, dashboard in lovelace["dashboards"].items():
            try:
                config = await dashboard.async_load(False)
            except (HomeAssistantError, KeyError, TypeError, ValueError):
                continue
            dashboard_path = url_path or "lovelace"
            records.extend(
                _dashboard_view_records(
                    f"dashboard:{dashboard_path}",
                    str(config.get("title") or dashboard_path),
                    f"/{dashboard_path}" if url_path else "/lovelace",
                    config,
                )
            )
            loaded_sources += 1

        try:
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
                loaded_sources += 1
        except (HomeAssistantError, KeyError, TypeError, ValueError):
            pass

    if not records:
        records, loaded_sources = await _async_load_storage_dashboards(hass)

    return DetectionSnapshot(
        "dashboards",
        loaded_sources > 0,
        detect_dashboard_usages(items, records, _reference_domains(hass)),
    )


async def _async_load_storage_dashboards(
    hass: HomeAssistant,
) -> tuple[list[ComponentRecord], int]:
    """Load storage-mode dashboards when Lovelace is not exposed in hass.data."""
    records: list[ComponentRecord] = []
    loaded_sources = 0
    try:
        default_data = await Store(hass, 1, "lovelace").async_load()
        if isinstance(default_data, dict) and isinstance(default_data.get("config"), dict):
            records.extend(
                _dashboard_view_records(
                    "dashboard:lovelace",
                    str(default_data["config"].get("title") or "lovelace"),
                    "/lovelace",
                    default_data["config"],
                )
            )
            loaded_sources += 1

        dashboard_data = await Store(hass, 1, "lovelace_dashboards").async_load()
        dashboard_items = (
            dashboard_data.get("items", []) if isinstance(dashboard_data, dict) else []
        )
        for dashboard in dashboard_items:
            if not isinstance(dashboard, dict) or dashboard.get("mode") != "storage":
                continue
            dashboard_id = dashboard.get("id")
            if not dashboard_id:
                continue
            stored = await Store(hass, 1, f"lovelace.{dashboard_id}").async_load()
            config = stored.get("config") if isinstance(stored, dict) else None
            if not isinstance(config, dict):
                continue
            url_path = str(dashboard.get("url_path") or dashboard_id)
            records.extend(
                _dashboard_view_records(
                    f"dashboard:{url_path}",
                    str(dashboard.get("title") or url_path),
                    f"/{url_path}",
                    config,
                )
            )
            loaded_sources += 1

        resources = await Store(hass, 1, "lovelace_resources").async_load()
        for resource in (resources or {}).get("items", []) if isinstance(resources, dict) else []:
            if not isinstance(resource, dict):
                continue
            url = str(resource.get("url") or "")
            records.append(
                ComponentRecord(
                    identifier=f"resource:{url}",
                    name=f"Lovelace resource: {url}",
                    url=url,
                    config=resource,
                )
            )
        loaded_sources += 1
    except (HomeAssistantError, KeyError, TypeError, ValueError):
        return [], 0
    return records, loaded_sources


def _entity_url(detector: str, entity_id: str) -> str | None:
    """Build a useful Home Assistant configuration URL for a component entity."""
    object_id = entity_id.split(".", 1)[-1] if "." in entity_id else entity_id
    if detector == "automations":
        return f"/config/automation/edit/{object_id}"
    if detector == "scripts":
        return f"/config/script/edit/{object_id}"
    return None
