# Changelog

## [Current State] - Context Mesh Added

### Existing Features (documented)

- HACS repository discovery and historical installed/uninstalled tracking.
- Repository ratings, lifecycle statuses, notes, tags, search, filtering, and sorting.
- Manual usage records with optional Home Assistant or external links.
- Review timestamps, review history, configurable intervals, and derived review state.
- Administrator-only Home Assistant sidebar panel and WebSocket operations.

### Tech Stack (documented)

- Python 3.12+, Home Assistant 2025.1.4 development target.
- Home Assistant config flow, storage, custom panel, and WebSocket APIs.
- Browser-native JavaScript frontend.
- `uv`, pytest, pytest-asyncio, coverage, and Ruff.

### Patterns Identified

- Provider adapter with source-neutral models.
- Ownership-preserving complete-snapshot synchronization.
- Async registry domain operations with centralized validation and persistence.
- Administrator WebSocket command handlers.
- Derived review state.

---
*Context Mesh added: 2026-09-22*
*This changelog documents the state when Context Mesh was added.*
*Future changes will be tracked below.*

## 2026.10.23

- Documented the proposed automatic usage detection feature and its SDD.
- Defined separate handling for detected and manual usages, stable detection keys,
  evidence, confidence, stale results, and phased implementation tasks.

## 2026.10.1

- Implemented the first automatic usage detection slice with persistent detected
  usages, detector snapshots, registry reconciliation, WebSocket moderation, and
  panel actions.
- Updated the integration version and panel asset cache key for validation.

## 2026.10.0

- Added Marketplace discovery for Home Assistant 2026.11+ with HACS fallback for older versions.
- Preserved the historical `hacs` source identity across the discovery backend migration.
- Removed the ordering dependency on the HACS custom integration.
- Added separate Marketplace/HACS store display, automatic brand icons, category fallbacks, and theme-aware panel status styling.
- Added optional, independently synchronized records for configured Home Assistant Core integrations.
- Improved icon resolution with the installed repository path and Home Assistant's authenticated brand route.
- Served the panel header icon from the integration's bundled local brand asset instead of the `/api/brands` endpoint.
- Added configurable review-repair generation and review interval settings in the options flow and panel settings card.
- Limited repair generation to the same configured Core inventory scope as the panel and moved settings into a compact floating dialog.
- Placed the settings action beside the synchronization action in the panel header.

## 2026.9.1

- Added persistent Home Assistant repair issues for never-reviewed and review-overdue tracked integrations.
- Repairs are now individual per tracked integration, with the integration name in the title.
- Usage links now open in a new browser tab.
- Improved the translated titles and descriptions for review repairs.
- Bumped the integration version to `2026.9.1`.
