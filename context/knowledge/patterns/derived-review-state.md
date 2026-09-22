# Pattern: Derived Review State

## Description

Calculate time-sensitive review state from persisted review history and current configuration instead of storing it as mutable lifecycle data.

## When to Use

Use this pattern when a state is a projection of a timestamp, current time, or configurable interval and should not become stale in storage.

## Pattern

Persist the last review timestamp and history. At read time, calculate `never_reviewed`, `needs_review`, or `up_to_date` using the configured interval. Keep this projection separate from the user-selected lifecycle status.

## Example

```python
def review_state(self, interval_days: int, now: datetime | None = None) -> str:
    reviewed = parse_timestamp(self.last_reviewed_at)
    if reviewed is None:
        return "never_reviewed"
    reference = now or datetime.now(UTC)
    return "needs_review" if reference - reviewed > timedelta(days=interval_days) else "up_to_date"
```

## Files Using This Pattern

- `custom_components/integration_tracker/models.py` — review projection.
- `custom_components/integration_tracker/review.py` — summary counters.
- `custom_components/integration_tracker/websocket.py` — calculated API fields.

## Related

- [Decision: Administrator Panel and WebSocket API](../../decisions/004-administrator-panel-api.md)
- [Feature: Review Scheduling and History](../../intent/feature-review-management.md)

## Status

- **Created**: 2026-09-22
- **Status**: Active

