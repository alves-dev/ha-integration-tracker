# Feature: Usage and Link Tracking

## What

Let users record the dashboards, cards, automations, scripts, integrations, and other places where a tracked repository is used, with an optional link for quick access. Let users add, edit, and remove these usage records.

## Why

Knowing where a repository is used helps users judge its importance, understand the impact of removing it, and return directly to the relevant Home Assistant or external resource.

## Acceptance Criteria

- [ ] Users can add a named usage with a usage type.
- [ ] Users can optionally associate a Home Assistant path or HTTP(S) link.
- [ ] Users can edit and remove usage records.
- [ ] Usage records remain attached to the tracked repository across synchronization and reloads.

## Related

- [Project Intent](project-intent.md)
- [Decision: Persistent Registry and Snapshot Synchronization](../decisions/003-persistent-registry-synchronization.md)
- [Decision: Administrator Panel and WebSocket API](../decisions/004-administrator-panel-api.md)
- [Pattern: Registry Domain Operations](../knowledge/patterns/registry-domain-operations.md)

## Status

- **Created**: 2026-09-22 (Phase: Intent)
- **Status**: Active (already implemented)

