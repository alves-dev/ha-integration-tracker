# Decision: Automatic Usage Detection Design

## Context

Integration Tracker currently stores manual usage records. A future feature needs
to discover references in Home Assistant without allowing uncertain provider or
configuration data to overwrite user-owned context.

## Decision

Implement usage discovery as a read-only detector subsystem with independent
detectors for integrations, dashboards, automations and scripts. Detectors return
normalized candidates with stable keys, evidence and confidence. The registry
reconciles only records marked as detected; manual usages remain user-owned.

Missing results become stale only after a successful snapshot from the relevant
detector. An unavailable or partial source is non-destructive.

## Rationale

Separating detection, matching and registry reconciliation keeps the provider/user
ownership boundary intact. Stable detection keys avoid duplicate records, while
confidence and evidence make uncertain associations reviewable instead of
silently incorrect.

## Alternatives Considered

- Treating all discovered references as manual usages would make them impossible to
  refresh safely.
- Deleting a usage as soon as it disappears would lose useful historical context.
- Running all detection logic inside WebSocket handlers would duplicate validation
  and make scheduled or post-sync detection harder to add.

## Outcomes

The MVP is implemented with detector-scoped snapshots for integrations, dashboards,
automations, scripts, scenes, installed blueprints, and frontend-exposed themes.
Partial detector failures remain non-destructive, and the panel exposes manual
refresh plus source/state/confidence filters. Deeper template/Python analysis and
automation-to-script dependency analysis are explicitly out of scope because that
responsibility is provided by another installed integration. The detailed
implementation tasks and acceptance criteria are recorded in the [automatic usage
detection SDD](../../docs/automatic-usage-detection-sdd.md).

## Related

- [Feature: Automatic Usage Detection](../intent/feature-automatic-usage-detection.md)
- [Decision: Persistent Registry and Snapshot Synchronization](003-persistent-registry-synchronization.md)
- [Decision: Administrator Panel and WebSocket API](004-administrator-panel-api.md)

## Status

- **Created**: 2026-10-23 (Phase: Plan)
- **Status**: Accepted
