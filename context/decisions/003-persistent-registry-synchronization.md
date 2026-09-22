# Decision: Persistent Registry and Snapshot Synchronization

## Context

Provider state can change, become temporarily unavailable, or omit repositories after an uninstall. User-owned notes and lifecycle data must survive those changes, and a partial provider result must not cause destructive state changes.

## Decision

Use a persistent source-neutral registry backed by Home Assistant’s atomic private storage. Synchronize from a complete provider snapshot under a registry lock. Update provider-owned fields only; preserve user-owned fields. Mark previously installed items uninstalled only after a successful snapshot omits them, and reuse their records if they are rediscovered.

## Rationale

Atomic persistence and a locked mutation boundary keep registry state consistent. Complete-snapshot semantics make absence meaningful while provider errors remain non-destructive. Explicit ownership prevents synchronization from overwriting user context.

## Alternatives Considered

Alternatives are not documented in the existing codebase. Deleting records on uninstall, treating an error as an empty snapshot, or storing only the latest provider result would lose historical context and are not used.

## Outcomes

The registry tests cover user metadata preservation, failed snapshots, uninstall/reinstall behavior, storage reload, and usage operations.

## Related

- [Project Intent](../intent/project-intent.md)
- [Feature: HACS Repository Tracking](../intent/feature-hacs-repository-tracking.md)
- [Feature: Repository Context Management](../intent/feature-repository-context.md)
- [Feature: Usage and Link Tracking](../intent/feature-usage-tracking.md)
- [Feature: Review Scheduling and History](../intent/feature-review-management.md)
- [Pattern: Ownership-Preserving Synchronization](../knowledge/patterns/ownership-preserving-synchronization.md)
- [Pattern: Registry Domain Operations](../knowledge/patterns/registry-domain-operations.md)

## Status

- **Created**: 2026-09-22 (Phase: Intent)
- **Status**: Accepted
- **Note**: Documented from existing implementation.

