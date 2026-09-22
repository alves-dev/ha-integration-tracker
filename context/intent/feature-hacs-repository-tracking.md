# Feature: HACS Repository Tracking

## What

Discover repositories currently installed through HACS and maintain a historical record of their installation state, identity, category, versions, and available repository information. Preserve a record when a repository is uninstalled and reconnect it when the same repository is installed again.

## Why

Users need a reliable inventory of custom repositories and their lifecycle over time, including repositories that are no longer installed. This makes removal intentional and prevents useful context from disappearing when HACS state changes.

## Acceptance Criteria

- [ ] Installed HACS repositories appear in the tracker.
- [ ] A repository remains in the tracker after it is removed from HACS.
- [ ] Reinstalling the same repository restores its installed state and existing context.
- [ ] Temporary HACS unavailability does not falsely mark repositories as uninstalled.

## Related

- [Project Intent](project-intent.md)
- [Decision: Source-Neutral Provider Architecture](../decisions/002-source-neutral-provider-architecture.md)
- [Decision: Persistent Registry and Snapshot Synchronization](../decisions/003-persistent-registry-synchronization.md)
- [Pattern: Provider Adapter](../knowledge/patterns/provider-adapter.md)
- [Pattern: Ownership-Preserving Synchronization](../knowledge/patterns/ownership-preserving-synchronization.md)

## Status

- **Created**: 2026-09-22 (Phase: Intent)
- **Status**: Active (already implemented)

