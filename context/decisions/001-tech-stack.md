# Decision: Technology Stack

## Context

The project is a Home Assistant custom integration that must run inside Home Assistant while remaining straightforward to test and distribute through HACS. The repository contains Python backend code, a browser-native panel, and no frontend build pipeline.

## Decision

- Use Python 3.12 or newer for the integration.
- Target Home Assistant `2025.1.4` for development and Home Assistant `2025.1+` for the integration.
- Use Home Assistant’s integration APIs, config flows, WebSocket API, custom panels, and storage helpers.
- Use `uv` for environment and dependency management.
- Use `pytest`, `pytest-asyncio`, and coverage tooling for tests; use Ruff for linting.
- Implement the panel as browser-native JavaScript served directly by Home Assistant.
- Distribute as a HACS custom integration with MIT licensing.

## Rationale

The dependency list is intentionally small because Home Assistant supplies the runtime capabilities. Native Home Assistant APIs align with lifecycle, authentication, persistence, and frontend behavior. Browser-native JavaScript avoids a separate Node build step for a small custom panel. The pinned development tools make local checks reproducible.

## Alternatives Considered

Alternatives are not documented in the existing codebase. A separate frontend framework/build system and a standalone backend service are not present in the implementation.

## Outcomes

Outcomes to be documented as the project evolves.

## Related

- [Project Intent](../intent/project-intent.md)
- [Feature: Administrator Tracker Panel](../intent/feature-administrator-panel.md)
- [Decision: Administrator Panel and WebSocket API](004-administrator-panel-api.md)

## Status

- **Created**: 2026-09-22 (Phase: Intent)
- **Status**: Accepted
- **Note**: Documented from existing implementation.

