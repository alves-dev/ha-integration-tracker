# Decision: Marketplace-Compatible Community Store Provider

## Context

Home Assistant 2026.11 moves HACS into the built-in Marketplace integration.
Integration Tracker currently discovers repositories through the HACS runtime
object at `hass.data["hacs"]`, which is unavailable after that migration.
Historical tracker records use the source-scoped `hacs:<owner>/<repository>`
identity and must not be duplicated when the discovery backend changes.

## Decision

Use a compatibility provider that selects the loaded Marketplace runtime on
Home Assistant versions that provide it and falls back to the HACS runtime on
older versions. Both backends emit the existing source-neutral `ProviderItem`
with source `hacs`, preserving historical IDs. Marketplace-specific access
stays inside its provider adapter and an unavailable backend remains
non-destructive to registry synchronization.

Remove the integration's ordering dependency on the HACS custom integration;
startup retry behavior remains responsible for eventual provider readiness.

## Rationale

The Marketplace migration changes the discovery owner, not the repository
identity or the user's tracker data. Selecting the backend at runtime supports
both the existing supported Home Assistant range and 2026.11+ without
duplicating records or treating migration timing as an uninstall.

## Related

- [Project Intent](../intent/project-intent.md)
- [Feature: HACS Repository Tracking](../intent/feature-hacs-repository-tracking.md)
- [Decision: Source-Neutral Provider Architecture](002-source-neutral-provider-architecture.md)
- [Decision: Persistent Registry and Snapshot Synchronization](003-persistent-registry-synchronization.md)

## Outcomes

- Marketplace discovery and legacy HACS fallback are implemented in separate adapters.
- Existing `hacs:owner/repository` IDs remain stable across the backend migration.
- A configured but not-yet-loaded Marketplace is treated as unavailable, not as an HACS installation or an empty snapshot.
- Unit tests cover Marketplace discovery, startup timing, HACS fallback, and identity preservation.

## Status

- **Created**: 2026-10-23 (Phase: Build)
- **Status**: Accepted
