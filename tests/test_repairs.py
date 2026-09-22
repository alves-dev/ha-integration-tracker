"""Tests for review repair issue projection."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import Mock, patch

from custom_components.integration_tracker.models import ProviderItem, TrackedItem
from custom_components.integration_tracker.repairs import (
    _issue_id,
    async_update_review_issues,
)


def tracked_item(repository: str, name: str) -> TrackedItem:
    """Return a tracked item for repair tests."""
    return TrackedItem.from_provider(
        ProviderItem(source="hacs", repository=repository, name=name),
        datetime.now(UTC).isoformat(),
    )


def test_creates_repairs_for_never_reviewed_and_overdue_items():
    """Create one issue for each review state represented in the registry."""
    never_reviewed = tracked_item("owner/never-reviewed", "Never Reviewed")
    needs_review = tracked_item("owner/needs-review", "Needs Review")
    needs_review.last_reviewed_at = (
        datetime.now(UTC) - timedelta(days=91)
    ).isoformat()

    with patch("custom_components.integration_tracker.repairs.issue_registry") as registry:
        registry.async_get.return_value.issues = {}
        async_update_review_issues(Mock(), [never_reviewed, needs_review], 90)

    created = registry.async_create_issue.call_args_list
    assert {call.args[2] for call in created} == {
        _issue_id("never_reviewed", never_reviewed.id),
        _issue_id("needs_review", needs_review.id),
    }
    assert {call.kwargs["translation_placeholders"]["integration"] for call in created} == {
        "Never Reviewed",
        "Needs Review",
    }


def test_removes_repairs_when_no_item_matches():
    """Remove both issue types when all items are up to date."""
    item = tracked_item("owner/example", "Example")
    item.last_reviewed_at = datetime.now(UTC).isoformat()

    with patch("custom_components.integration_tracker.repairs.issue_registry") as registry:
        registry.async_get.return_value.issues = {
            ("integration_tracker", _issue_id("never_reviewed", item.id)): Mock(),
            ("integration_tracker", _issue_id("needs_review", "hacs:owner/old")): Mock(),
        }
        async_update_review_issues(Mock(), [item], 90)

    assert {call.args[2] for call in registry.async_delete_issue.call_args_list} == {
        _issue_id("never_reviewed", item.id),
        _issue_id("needs_review", "hacs:owner/old"),
    }
