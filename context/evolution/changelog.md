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

