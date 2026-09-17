"""Review calculations and dashboard summaries."""

from __future__ import annotations

from collections import Counter
from typing import Any

from .models import TrackedItem


def build_summary(items: list[TrackedItem], interval_days: int) -> dict[str, Any]:
    """Build dashboard counters from current registry state."""
    statuses = Counter(item.status or "none" for item in items)
    review_states = Counter(item.review_state(interval_days) for item in items)
    return {
        "total": len(items),
        "installed": sum(item.installed for item in items),
        "uninstalled": sum(not item.installed for item in items),
        "no_known_usage": sum(not item.usages for item in items),
        "needs_review": review_states["needs_review"],
        "never_reviewed": review_states["never_reviewed"],
        "statuses": dict(statuses),
    }
