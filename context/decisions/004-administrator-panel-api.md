# Decision: Administrator Panel and WebSocket API

## Context

The integration needs a Home Assistant-native interface for inventory management while ensuring that only administrators can view or mutate the tracked data.

## Decision

Register a custom sidebar panel that is restricted to administrators and serve a browser-native JavaScript web component. Expose reads and mutations through named Home Assistant WebSocket commands, with administrator guards, schema validation, and domain errors. Keep calculated review state and summary counters in API responses rather than persisting them as lifecycle fields.

## Rationale

The panel integrates with Home Assistant navigation and themes, while WebSocket commands provide the existing frontend with authenticated access to backend operations. API-level validation gives consistent behavior regardless of the caller. Derived review state changes with time and configuration, so it should be calculated rather than stored.

## Alternatives Considered

Alternatives are not documented in the existing codebase. No REST API, frontend framework, or non-administrator interface is implemented.

## Outcomes

The API currently supports listing, retrieving, updating, usage CRUD, marking reviewed, and manual synchronization. Local documentation calls out administrator, failure, theme, and responsive-panel checks.

## Related

- [Project Intent](../intent/project-intent.md)
- [Feature: Administrator Tracker Panel](../intent/feature-administrator-panel.md)
- [Feature: Review Scheduling and History](../intent/feature-review-management.md)
- [Pattern: Administrator WebSocket Command](../knowledge/patterns/administrator-websocket-command.md)
- [Pattern: Derived Review State](../knowledge/patterns/derived-review-state.md)

## Status

- **Created**: 2026-09-22 (Phase: Intent)
- **Status**: Accepted
- **Note**: Documented from existing implementation.

