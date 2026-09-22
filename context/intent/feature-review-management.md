# Feature: Review Scheduling and History

## What

Allow users to mark tracked repositories as reviewed, keep a history of review events, and identify repositories that have never been reviewed or are past the configured review interval.

## Why

Regular review helps users detect stale, unused, or replaceable repositories and keeps the Home Assistant configuration intentional over time.

## Acceptance Criteria

- [ ] Users can mark a repository as reviewed.
- [ ] Each review is retained in the repository’s history.
- [ ] The tracker identifies never-reviewed and overdue repositories.
- [ ] Users can configure the review interval.
- [ ] Review state does not overwrite the repository’s lifecycle status.

## Related

- [Project Intent](project-intent.md)
- [Decision: Persistent Registry and Snapshot Synchronization](../decisions/003-persistent-registry-synchronization.md)
- [Decision: Administrator Panel and WebSocket API](../decisions/004-administrator-panel-api.md)
- [Pattern: Derived Review State](../knowledge/patterns/derived-review-state.md)

## Status

- **Created**: 2026-09-22 (Phase: Intent)
- **Status**: Active (already implemented)

