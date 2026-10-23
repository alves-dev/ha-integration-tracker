"""Pure automatic usage detectors and matching helpers."""

from __future__ import annotations

import re
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from ..models import TrackedItem
from .models import DetectedUsage

_ENTITY_ID = re.compile(r"^[a-z0-9_]+\.[a-z0-9_]+$")
_SERVICE = re.compile(r"^[a-z0-9_]+\.[a-z0-9_]+$")


@dataclass(slots=True, frozen=True)
class ComponentRecord:
    """A normalized automation or script configuration."""

    identifier: str
    name: str
    url: str | None
    config: Any


@dataclass(slots=True, frozen=True)
class ConfigReference:
    """A reference extracted from a Home Assistant configuration object."""

    kind: str
    value: str
    path: str


def iter_config_references(value: Any, path: str = "config") -> Iterator[ConfigReference]:
    """Yield entity, service, custom card, and resource references."""
    if isinstance(value, Mapping):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if isinstance(child, str):
                key_text = str(key).casefold()
                if key_text in {"service", "action", "service_template", "action_template"}:
                    if _SERVICE.match(child):
                        yield ConfigReference("service", child, child_path)
                elif key_text in {"entity_id", "entity", "entities"} and _ENTITY_ID.match(
                    child
                ):
                    yield ConfigReference("entity", child, child_path)
                if child.startswith("custom:"):
                    yield ConfigReference("card", child.removeprefix("custom:"), child_path)
                if _looks_like_resource(child):
                    yield ConfigReference("resource", child, child_path)
            yield from iter_config_references(child, child_path)
        return
    if isinstance(value, Sequence) and not isinstance(value, str | bytes | bytearray):
        for index, child in enumerate(value):
            yield from iter_config_references(child, f"{path}[{index}]")


def detect_component_usages(
    items: Sequence[TrackedItem], records: Sequence[ComponentRecord], detector: str
) -> list[DetectedUsage]:
    """Detect tracked integrations referenced by automation or script records."""
    detections: dict[tuple[str, str], DetectedUsage] = {}
    for record in records:
        for reference in iter_config_references(record.config):
            for item in items:
                match = match_reference(item, reference)
                if match is None:
                    continue
                key = f"{detector}:{record.identifier}:{reference.kind}:{reference.value}"
                detections.setdefault(
                    (item.id, key),
                    DetectedUsage(
                        item_id=item.id,
                        name=record.name,
                        type=detector.removesuffix("s"),
                        url=record.url,
                        detection_key=key,
                        detector=detector,
                        confidence=match,
                        evidence={
                            "reference": reference.value,
                            "reference_type": reference.kind,
                            "path": reference.path,
                            "record_id": record.identifier,
                        },
                    ),
                )
    return list(detections.values())


def detect_dashboard_usages(
    items: Sequence[TrackedItem], dashboards: Sequence[ComponentRecord]
) -> list[DetectedUsage]:
    """Detect tracked integrations referenced by Lovelace dashboards or resources."""
    return detect_component_usages(items, dashboards, "dashboards")


def detect_configured_integrations(
    items: Sequence[TrackedItem], configured_domains: set[str] | None = None
) -> list[DetectedUsage]:
    """Create high-confidence uses for tracked integrations with a configured domain."""
    detections: list[DetectedUsage] = []
    for item in items:
        domain = _item_domain(item)
        if (
            not domain
            or item.source.casefold() not in {"core", "hacs"}
            or (configured_domains is not None and domain not in configured_domains)
        ):
            continue
        key = f"integrations:configured:{item.id}"
        detections.append(
            DetectedUsage(
                item_id=item.id,
                name=f"Configured integration: {item.name}",
                type="integration",
                detection_key=key,
                detector="integrations",
                confidence="high",
                url=f"/config/integrations/integration/{domain}",
                evidence={"domain": domain, "source": "config_entries"},
            )
        )
    return detections


def match_reference(item: TrackedItem, reference: ConfigReference) -> str | None:
    """Return the confidence for a reference matched to an item."""
    domain = _item_domain(item)
    value = reference.value.casefold()
    if domain and (
        value == domain
        or value.startswith(f"{domain}.")
        or (reference.kind == "entity" and value.split(".", 1)[0] == domain)
    ):
        return "high"

    tokens = _item_tokens(item)
    if reference.kind == "card" and any(token in value for token in tokens):
        return "high"
    if reference.kind == "resource" and any(token in value for token in tokens):
        return "high"
    if any(token in value for token in tokens):
        return "medium"
    return None


def _item_domain(item: TrackedItem) -> str | None:
    """Return a normalized integration domain when provider metadata has one."""
    domain = item.provider_data.get("domain")
    return str(domain).casefold() if domain else None


def _item_tokens(item: TrackedItem) -> set[str]:
    """Build conservative matching tokens from provider-owned metadata."""
    repository = item.repository.rsplit("/", 1)[-1].casefold()
    tokens = {repository}
    for value in (item.provider_data.get("hacs_id"), item.name):
        if value:
            tokens.add(str(value).casefold().replace(" ", "-"))
    return {token for token in tokens if len(token) >= 3}


def _looks_like_resource(value: str) -> bool:
    """Return whether a string looks like a Lovelace resource URL."""
    return value.startswith(("/hacsfiles/", "/local/", "http://", "https://")) and (
        value.endswith((".js", ".css")) or "/hacsfiles/" in value
    )
