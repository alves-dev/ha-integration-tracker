"""Tests for automatic usage detection."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from custom_components.integration_tracker.models import ProviderItem, TrackedItem
from custom_components.integration_tracker.usage_detection import coordinator
from custom_components.integration_tracker.usage_detection.detectors import (
    ComponentRecord,
    detect_component_usages,
    detect_configured_integrations,
    detect_dashboard_usages,
    iter_config_references,
)


def tracked_item(category="integration", domain="example"):
    return TrackedItem.from_provider(
        ProviderItem(
            source="hacs",
            repository="owner/example",
            name="Example",
            category=category,
            provider_data={"domain": domain},
        ),
        "2026-10-23T00:00:00Z",
    )


def test_iter_config_references_extracts_nested_entities_services_cards_and_resources():
    references = list(
        iter_config_references(
            {
                "trigger": {"entity_id": "example.sensor"},
                "action": [{"service": "example.run"}],
                "card": "custom:example-card",
                "resource": "/hacsfiles/example-card/card.js",
            }
        )
    )

    assert {(reference.kind, reference.value) for reference in references} == {
        ("entity", "example.sensor"),
        ("service", "example.run"),
        ("card", "example-card"),
        ("resource", "/hacsfiles/example-card/card.js"),
    }


def test_iter_config_references_extracts_entity_lists():
    references = list(iter_config_references({"entities": ["example.one", "other.two"]}))

    assert [(reference.kind, reference.value) for reference in references] == [
        ("entity", "example.one"),
        ("entity", "other.two"),
    ]


def test_iter_config_references_extracts_devices_areas_events_and_blueprints():
    references = list(
        iter_config_references(
            {
                "device_id": ["device-1"],
                "area_id": "area-1",
                "event_type": "example_event",
                "use_blueprint": {"path": "owner/example/notify.yaml"},
            }
        )
    )

    assert {(reference.kind, reference.value) for reference in references} == {
        ("device", "device-1"),
        ("area", "area-1"),
        ("event", "example_event"),
        ("blueprint", "owner/example/notify.yaml"),
    }


def test_iter_config_references_extracts_dashboard_theme():
    references = list(iter_config_references({"theme": "Catppuccin Mocha"}))

    assert [(reference.kind, reference.value) for reference in references] == [
        ("theme", "Catppuccin Mocha")
    ]


@pytest.mark.asyncio
async def test_async_detect_all_keeps_partial_detector_errors(monkeypatch):
    """One detector failure does not discard snapshots from the others."""
    hass = SimpleNamespace(
        config_entries=SimpleNamespace(async_domains=lambda: {"example"}),
    )
    available = coordinator.DetectionSnapshot("stub", True, [])
    failed = RuntimeError("dashboard source unavailable")
    monkeypatch.setattr(coordinator, "detect_configured_integrations", lambda *_args: [])
    monkeypatch.setattr(coordinator, "_component_snapshot", lambda *_args: available)
    monkeypatch.setattr(coordinator, "_theme_snapshot", lambda *_args: available)
    monkeypatch.setattr(coordinator, "_blueprint_snapshot", lambda *_args: available)

    async def fail_dashboard(*_args):
        raise failed

    monkeypatch.setattr(coordinator, "_dashboard_snapshot", fail_dashboard)

    snapshots = await coordinator.async_detect_all(hass, [tracked_item()])

    assert len(snapshots) == 7
    assert sum(snapshot.available for snapshot in snapshots) == 6
    assert snapshots[-1].detector == "dashboards"
    assert snapshots[-1].error == str(failed)


def test_dashboard_detector_matches_catppuccin_theme_name():
    item = TrackedItem.from_provider(
        ProviderItem(
            source="hacs",
            repository="catppuccin/home-assistant",
            name="Catppuccin Theme",
            category="theme",
        ),
        "2026-10-24T00:00:00Z",
    )
    detections = detect_dashboard_usages(
        [item],
        [
            ComponentRecord(
                "dashboard:infra:view:infra",
                "Infra — Server",
                "/dashboard-infra/infra",
                {"view": {"cards": [{"type": "gauge", "theme": "Catppuccin Mocha"}]}},
            )
        ],
    )

    assert len(detections) == 1
    assert detections[0].confidence == "high"
    assert detections[0].evidence["reference_type"] == "theme"


def test_component_detector_matches_registry_resolved_device_reference():
    item = tracked_item()
    detections = detect_component_usages(
        [item],
        [
            ComponentRecord(
                "automation.one",
                "Device automation",
                None,
                {"trigger": {"device_id": "device-1"}},
            )
        ],
        "automations",
        {"device-1": {"example"}},
    )

    assert len(detections) == 1
    assert detections[0].confidence == "high"
    assert detections[0].evidence["reference_type"] == "device"


def test_automation_url_uses_persistent_automation_id():
    assert coordinator._entity_url(
        "automations",
        "automation.notification_ai_usage_limit_reached",
        {"id": "1780921324759"},
    ) == "/config/automation/edit/1780921324759"


def test_automation_url_falls_back_to_entity_object_id():
    assert coordinator._entity_url(
        "automations", "automation.example", {"alias": "Example"}
    ) == "/config/automation/edit/example"


def test_theme_snapshot_matches_tracked_theme_and_marks_active_theme():
    item = tracked_item(category="theme")
    item.provider_data = {"domain": None}
    hass = SimpleNamespace(
        data={
            "frontend_themes": {"Example": {"primary-color": "#123456"}},
            "frontend_default_theme": "Example",
        }
    )

    snapshot = coordinator._theme_snapshot(hass, [item])

    assert snapshot.available is True
    assert snapshot.detections[0].type == "theme"
    assert snapshot.detections[0].evidence["active"] is True


def test_blueprint_snapshot_matches_repository_path(tmp_path):
    blueprint = tmp_path / "blueprints" / "automation" / "owner" / "example" / "notify.yaml"
    blueprint.parent.mkdir(parents=True)
    blueprint.write_text("blueprint: {}", encoding="utf-8")
    hass = SimpleNamespace(
        config=SimpleNamespace(path=lambda name: str(tmp_path / name)),
    )

    snapshot = coordinator._blueprint_snapshot(hass, [tracked_item()])

    assert snapshot.available is True
    assert snapshot.detections[0].type == "blueprint"
    assert snapshot.detections[0].evidence["path"] == "automation/owner/example/notify.yaml"


def test_reference_domains_resolves_area_without_area_entry_collections(monkeypatch):
    config_entry = SimpleNamespace(entry_id="entry-1", domain="example")
    entity = SimpleNamespace(
        entity_id="example.sensor",
        config_entry_id="entry-1",
        device_id="device-1",
        area_id="area-1",
    )
    device = SimpleNamespace(
        id="device-1",
        config_entries={"entry-1"},
        area_id="area-1",
    )

    monkeypatch.setattr(
        coordinator.entity_registry,
        "async_get",
        lambda _hass: SimpleNamespace(entities={"entity": entity}),
    )
    monkeypatch.setattr(
        coordinator.device_registry,
        "async_get",
        lambda _hass: SimpleNamespace(devices={"device": device}),
    )
    hass = SimpleNamespace(
        config_entries=SimpleNamespace(async_entries=lambda: [config_entry])
    )

    domains = coordinator._reference_domains(hass)

    assert domains["area-1"] == {"example"}


def test_dashboard_view_records_use_dashboard_url_path_and_view_path():
    records = coordinator._dashboard_view_records(
        "dashboard:dashboard-infra",
        "Infra",
        "/dashboard-infra",
        {
            "views": [
                {"path": "infra", "title": "Infra", "cards": []},
                {"path": "ip", "title": "IP", "cards": []},
            ]
        },
    )

    assert [record.url for record in records] == [
        "/dashboard-infra/infra",
        "/dashboard-infra/ip",
    ]


def test_component_detector_matches_domain_and_preserves_evidence():
    item = tracked_item()
    detections = detect_component_usages(
        [item],
        [
            ComponentRecord(
                "automation.one",
                "Turn on example",
                "/config/automation/edit/one",
                {"action": {"service": "example.run"}},
            )
        ],
        "automations",
    )

    assert len(detections) == 1
    assert detections[0].confidence == "high"
    assert detections[0].evidence["reference"] == "example.run"
    assert detections[0].evidence["path"] == "config.action.service"


def test_dashboard_detector_matches_custom_card_by_repository_token():
    item = tracked_item(category="plugin", domain=None)
    item.provider_data = {"domain": None}
    detections = detect_dashboard_usages(
        [item],
        [
            ComponentRecord(
                "dashboard:main",
                "Main dashboard",
                "/lovelace/main",
                {"cards": [{"type": "custom:example-card"}]},
            )
        ],
    )

    assert len(detections) == 1
    assert detections[0].type == "dashboard"
    assert detections[0].evidence["reference_type"] == "card"


def test_configured_integration_detector_only_returns_configured_domains():
    item = tracked_item()
    assert detect_configured_integrations([item], {"other"}) == []
    detections = detect_configured_integrations([item], {"example"})
    assert len(detections) == 1
    assert detections[0].type == "integration"


@pytest.mark.asyncio
async def test_storage_dashboard_fallback_loads_dashboard_and_resources(monkeypatch):
    stored = {
        "lovelace": {"config": {"views": [{"cards": [{"entity": "sun.sun"}]}]}},
        "lovelace_dashboards": {
            "items": [
                {
                    "id": "dashboard_testes",
                    "title": "Testes",
                    "url_path": "dashboard-testes",
                    "mode": "storage",
                }
            ]
        },
        "lovelace.dashboard_testes": {
            "config": {"views": [{"cards": [{"entity": "sun.sun"}]}]}
        },
        "lovelace_resources": {"items": [{"url": "/hacsfiles/example-card/card.js"}]},
    }

    class FakeStore:
        def __init__(self, _hass, _version, key):
            self.key = key

        async def async_load(self):
            return stored.get(self.key)

    monkeypatch.setattr(coordinator, "Store", FakeStore)
    records, loaded = await coordinator._async_load_storage_dashboards(object())

    assert loaded == 3
    assert {record.identifier for record in records} == {
        "dashboard:lovelace:view:0",
        "dashboard:dashboard-testes:view:0",
        "resource:/hacsfiles/example-card/card.js",
    }
