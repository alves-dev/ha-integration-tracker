"""Runtime collection for automatic usage detection."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from homeassistant.components import automation, scene, script
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import device_registry, entity_registry
from homeassistant.helpers.storage import Store

from ..models import TrackedItem
from .detectors import (
    ComponentRecord,
    _item_tokens,
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
    error: str | None = None


async def async_detect_all(
    hass: HomeAssistant, items: Sequence[TrackedItem]
) -> list[DetectionSnapshot]:
    """Collect all currently supported detector snapshots."""
    snapshots: list[DetectionSnapshot] = []
    sync_detectors = (
        ("integrations", lambda: DetectionSnapshot(
            "integrations",
            True,
            detect_configured_integrations(
                items,
                {domain.casefold() for domain in hass.config_entries.async_domains()},
            ),
        )),
        ("automations", lambda: _component_snapshot(
            hass, items, automation.DATA_COMPONENT, "automations"
        )),
        ("scripts", lambda: _component_snapshot(hass, items, script.DOMAIN, "scripts")),
        ("scenes", lambda: _component_snapshot(hass, items, scene.DATA_COMPONENT, "scenes")),
        ("themes", lambda: _theme_snapshot(hass, items)),
        ("blueprints", lambda: _blueprint_snapshot(hass, items)),
    )
    for detector, collect in sync_detectors:
        try:
            snapshots.append(collect())
        except Exception as err:
            snapshots.append(DetectionSnapshot(detector, False, [], str(err)))
    try:
        snapshots.append(await _dashboard_snapshot(hass, items))
    except Exception as err:
        snapshots.append(DetectionSnapshot("dashboards", False, [], str(err)))
    return snapshots


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
            url=_entity_url(
                detector,
                getattr(entity, "entity_id", ""),
                getattr(entity, "raw_config", None),
            ),
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
    _add_entity_domains(domains, config_entries, entity_registry_data.entities.values())
    _add_device_domains(domains, config_entries, device_registry_data.devices.values())
    _add_entity_area_domains(domains, entity_registry_data.entities.values())
    _add_device_area_domains(domains, device_registry_data.devices.values())
    return domains


def _add_domain(domains: dict[str, set[str]], reference: str, domain: str | None) -> None:
    """Associate a normalized reference with a normalized integration domain."""
    if domain:
        domains.setdefault(reference.casefold(), set()).add(domain.casefold())


def _add_entity_domains(domains, config_entries, entities) -> None:
    """Add entity and device references from entity registry entries."""
    for entity in entities:
        domain = config_entries.get(entity.config_entry_id)
        _add_domain(domains, entity.entity_id, domain)
        if entity.device_id:
            _add_domain(domains, entity.device_id, domain)


def _add_device_domains(domains, config_entries, devices) -> None:
    """Add device references from device registry entries."""
    for device in devices:
        for entry_id in device.config_entries:
            _add_domain(domains, device.id, config_entries.get(entry_id))


def _add_entity_area_domains(domains, entities) -> None:
    """Propagate entity and device domains to their areas."""
    for entity in entities:
        if not entity.area_id:
            continue
        _propagate_area_domains(domains, entity.area_id, entity.entity_id)
        if entity.device_id:
            _propagate_area_domains(domains, entity.area_id, entity.device_id)


def _add_device_area_domains(domains, devices) -> None:
    """Propagate device domains to device areas."""
    for device in devices:
        area_id = getattr(device, "area_id", None)
        if area_id:
            _propagate_area_domains(domains, area_id, device.id)


def _propagate_area_domains(domains, area_id: str, source: str) -> None:
    """Copy domains associated with an entity or device onto its area."""
    for domain in domains.get(source.casefold(), set()):
        _add_domain(domains, area_id, domain)


def _theme_snapshot(
    hass: HomeAssistant, items: Sequence[TrackedItem]
) -> DetectionSnapshot:
    """Detect tracked themes exposed by Home Assistant frontend storage."""
    themes = hass.data.get("frontend_themes")
    if not isinstance(themes, Mapping):
        return DetectionSnapshot("themes", False, [])
    defaults = {
        str(hass.data.get("frontend_default_theme") or "default").casefold(),
        str(hass.data.get("frontend_default_dark_theme") or "").casefold(),
    }
    detections: list[DetectedUsage] = []
    for item in items:
        if item.category and item.category.casefold() == "theme":
            detections.extend(_theme_detections(item, themes, defaults))
    return DetectionSnapshot("themes", True, detections)


def _theme_detections(item, themes, defaults) -> list[DetectedUsage]:
    """Return theme matches for one tracked item."""
    tokens = _item_tokens(item)
    detections = []
    for theme_name, theme_config in themes.items():
        name = str(theme_name)
        name_lower = name.casefold()
        serialized = str(theme_config).casefold()
        if not _theme_matches(name_lower, serialized, tokens):
            continue
        detections.append(
            DetectedUsage(
                item_id=item.id,
                name=f"Theme: {name}",
                type="theme",
                detection_key=f"themes:theme:{name_lower}:{item.id}",
                detector="themes",
                confidence="high" if name_lower in defaults else "medium",
                evidence={
                    "theme": name,
                    "active": name_lower in defaults,
                    "source": "frontend_themes",
                },
            )
        )
    return detections


def _theme_matches(name: str, serialized: str, tokens: set[str]) -> bool:
    """Return whether a theme name or configuration contains an item token."""
    return (
        name in tokens
        or any(token in name for token in tokens)
        or any(token in serialized for token in tokens)
    )


def _blueprint_snapshot(
    hass: HomeAssistant, items: Sequence[TrackedItem]
) -> DetectionSnapshot:
    """Detect blueprints whose installed path identifies a tracked repository."""
    blueprints_root = Path(hass.config.path("blueprints"))
    if not blueprints_root.is_dir():
        return DetectionSnapshot("blueprints", False, [])
    detections: list[DetectedUsage] = []
    for path in blueprints_root.rglob("*.y*ml"):
        path_text = path.relative_to(blueprints_root).as_posix().casefold()
        for item in items:
            if not any(token in path_text for token in _item_tokens(item)):
                continue
            detections.append(
                DetectedUsage(
                    item_id=item.id,
                    name=f"Blueprint: {path.stem}",
                    type="blueprint",
                    detection_key=f"blueprints:{path_text}:{item.id}",
                    detector="blueprints",
                    confidence="high",
                    url="/config/automation/blueprint",
                    evidence={"path": path_text, "source": "blueprints"},
                )
            )
    return DetectionSnapshot("blueprints", True, detections)


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
    if isinstance(lovelace, dict) and "dashboards" in lovelace:
        records, loaded_sources = await _load_exposed_dashboards(lovelace)
        records.extend(await _load_exposed_resources(lovelace))
    else:
        records, loaded_sources = [], 0

    if not records:
        records, loaded_sources = await _async_load_storage_dashboards(hass)

    return DetectionSnapshot(
        "dashboards",
        loaded_sources > 0,
        detect_dashboard_usages(items, records, _reference_domains(hass)),
    )


async def _load_exposed_dashboards(lovelace: dict[str, Any]) -> tuple[list[ComponentRecord], int]:
    """Load dashboards exposed by the active Lovelace runtime."""
    records: list[ComponentRecord] = []
    loaded_sources = 0
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
    return records, loaded_sources


async def _load_exposed_resources(lovelace: dict[str, Any]) -> list[ComponentRecord]:
    """Load resources exposed by the active Lovelace runtime."""
    resources = lovelace.get("resources")
    if resources is None:
        return []
    try:
        if not getattr(resources, "loaded", True):
            await resources.async_load()
        return [
            ComponentRecord(
                identifier=f"resource:{resource.get('url') or ''}",
                name=f"Lovelace resource: {resource.get('url') or ''}",
                url=str(resource.get("url") or ""),
                config=resource,
            )
            for resource in resources.async_items() or []
        ]
    except (HomeAssistantError, KeyError, TypeError, ValueError):
        return []


async def _async_load_storage_dashboards(
    hass: HomeAssistant,
) -> tuple[list[ComponentRecord], int]:
    """Load storage-mode dashboards when Lovelace is not exposed in hass.data."""
    records: list[ComponentRecord] = []
    loaded_sources = 0
    try:
        records, loaded_sources = await _load_storage_dashboard_records(hass)
        records.extend(await _load_storage_resources(hass))
        loaded_sources += 1
    except (HomeAssistantError, KeyError, TypeError, ValueError):
        return [], 0
    return records, loaded_sources


async def _load_storage_dashboard_records(hass: HomeAssistant) -> tuple[list[ComponentRecord], int]:
    """Load the default and storage-mode dashboard records."""
    records: list[ComponentRecord] = []
    loaded_sources = 0
    default_data = await Store(hass, 1, "lovelace").async_load()
    default_config = default_data.get("config") if isinstance(default_data, dict) else None
    if isinstance(default_config, dict):
        records.extend(
            _dashboard_view_records(
                "dashboard:lovelace",
                str(default_config.get("title") or "lovelace"),
                "/lovelace",
                default_config,
            )
        )
        loaded_sources += 1

    dashboard_data = await Store(hass, 1, "lovelace_dashboards").async_load()
    dashboards = dashboard_data.get("items", []) if isinstance(dashboard_data, dict) else []
    for dashboard in dashboards:
        records_for_dashboard = await _load_one_storage_dashboard(hass, dashboard)
        if records_for_dashboard:
            records.extend(records_for_dashboard)
            loaded_sources += 1
    return records, loaded_sources


async def _load_one_storage_dashboard(hass: HomeAssistant, dashboard: Any) -> list[ComponentRecord]:
    """Load one storage-mode dashboard, if its metadata is usable."""
    if not isinstance(dashboard, dict) or dashboard.get("mode") != "storage":
        return []
    dashboard_id = dashboard.get("id")
    if not dashboard_id:
        return []
    stored = await Store(hass, 1, f"lovelace.{dashboard_id}").async_load()
    config = stored.get("config") if isinstance(stored, dict) else None
    if not isinstance(config, dict):
        return []
    url_path = str(dashboard.get("url_path") or dashboard_id)
    return _dashboard_view_records(
        f"dashboard:{url_path}",
        str(dashboard.get("title") or url_path),
        f"/{url_path}",
        config,
    )


async def _load_storage_resources(hass: HomeAssistant) -> list[ComponentRecord]:
    """Load Lovelace resources from storage."""
    resources = await Store(hass, 1, "lovelace_resources").async_load()
    items = resources.get("items", []) if isinstance(resources, dict) else []
    return [
        ComponentRecord(
            identifier=f"resource:{resource.get('url') or ''}",
            name=f"Lovelace resource: {resource.get('url') or ''}",
            url=str(resource.get("url") or ""),
            config=resource,
        )
        for resource in items
        if isinstance(resource, dict)
    ]


def _entity_url(detector: str, entity_id: str, config: Any = None) -> str | None:
    """Build a useful Home Assistant configuration URL for a component entity."""
    if detector == "automations" and isinstance(config, Mapping) and config.get("id"):
        return f"/config/automation/edit/{config['id']}"
    object_id = entity_id.split(".", 1)[-1] if "." in entity_id else entity_id
    if detector == "automations":
        return f"/config/automation/edit/{object_id}"
    if detector == "scripts":
        return f"/config/script/edit/{object_id}"
    return None
