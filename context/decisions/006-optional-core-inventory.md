# Decision: Optional Configured Core Inventory

## Context

Home Assistant exposes many built-in domains as loaded components even when
the user has not configured or installed an integration for them. Showing that
set made the tracker look like a catalog of all Home Assistant functionality,
instead of an inventory of the user's installation.

## Decision

Make Core inventory opt-in through the Integration Tracker options flow. When
enabled, discover only built-in domains with active Home Assistant config
entries. When disabled, Core records are excluded from the panel while their
historical data remains available if the option is enabled again later.

## Rationale

Config entries represent integrations configured in the user's instance and
avoid treating default services such as `sensor`, `automation`, and `logbook`
as installed integrations. Keeping the option disabled by default preserves
the original community-repository focus and prevents an unexpectedly large
panel.

## Related

- [Feature: HACS Repository Tracking](../intent/feature-hacs-repository-tracking.md)
- [Decision: Source-Neutral Provider Architecture](002-source-neutral-provider-architecture.md)

## Status

- **Created**: 2026-10-23 (Phase: Build)
- **Status**: Accepted
