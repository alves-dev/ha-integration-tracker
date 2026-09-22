# Feature: Repository Context Management

## What

Let users record a repository’s usefulness and lifecycle context through a rating, status, notes, and reusable tags. Provide search, filtering, and sorting so the inventory can be understood and maintained as it grows.

## Why

An inventory alone does not explain whether a repository is important, unused, temporary, or ready to replace. Personal context helps users maintain their Home Assistant configuration with less guesswork.

## Acceptance Criteria

- [ ] Users can assign or clear a one-to-three-star rating.
- [ ] Users can assign or clear a lifecycle status.
- [ ] Users can save notes and reusable tags.
- [ ] Users can find records by names, repositories, notes, tags, and usage names.
- [ ] Users can filter and sort the inventory by relevant lifecycle information.

## Related

- [Project Intent](project-intent.md)
- [Decision: Persistent Registry and Snapshot Synchronization](../decisions/003-persistent-registry-synchronization.md)
- [Decision: Administrator Panel and WebSocket API](../decisions/004-administrator-panel-api.md)
- [Pattern: Ownership-Preserving Synchronization](../knowledge/patterns/ownership-preserving-synchronization.md)

## Status

- **Created**: 2026-09-22 (Phase: Intent)
- **Status**: Active (already implemented)

