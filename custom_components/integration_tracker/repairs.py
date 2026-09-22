"""Repair issues for Integration Tracker review state."""

from __future__ import annotations

import hashlib
from collections.abc import Iterable

from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry

from .const import DOMAIN
from .models import TrackedItem

ISSUE_NEVER_REVIEWED = "never_reviewed"
ISSUE_NEEDS_REVIEW = "needs_review"
ISSUE_PREFIXES = (f"{ISSUE_NEVER_REVIEWED}_", f"{ISSUE_NEEDS_REVIEW}_")


def async_update_review_issues(
    hass: HomeAssistant, items: Iterable[TrackedItem], interval_days: int
) -> None:
    """Create one review issue per tracked item that needs attention."""
    current_issue_ids: set[str] = set()
    for item in items:
        review_state = item.review_state(interval_days)
        if review_state not in (ISSUE_NEVER_REVIEWED, ISSUE_NEEDS_REVIEW):
            continue
        issue_id = _issue_id(review_state, item.id)
        current_issue_ids.add(issue_id)
        issue_registry.async_create_issue(
            hass,
            DOMAIN,
            issue_id,
            is_fixable=False,
            is_persistent=True,
            severity=issue_registry.IssueSeverity.WARNING,
            translation_key=review_state,
            translation_placeholders={"integration": item.name},
        )

    registry = issue_registry.async_get(hass)
    for domain, issue_id in tuple(registry.issues):
        if domain != DOMAIN:
            continue
        if issue_id in (ISSUE_NEVER_REVIEWED, ISSUE_NEEDS_REVIEW) or (
            issue_id.startswith(ISSUE_PREFIXES) and issue_id not in current_issue_ids
        ):
            issue_registry.async_delete_issue(hass, DOMAIN, issue_id)


def _issue_id(review_state: str, item_id: str) -> str:
    """Return a stable, compact issue ID for one item and review state."""
    item_hash = hashlib.sha256(item_id.encode()).hexdigest()[:16]
    return f"{review_state}_{item_hash}"
