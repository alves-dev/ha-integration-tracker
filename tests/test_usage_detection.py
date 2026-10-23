"""Tests for automatic usage detection."""

from __future__ import annotations

from custom_components.integration_tracker.models import ProviderItem, TrackedItem
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
