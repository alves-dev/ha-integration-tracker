# Decision: Non-blocking Blueprint and In-Memory Lovelace Detection

## Context

Usage detection can run during setup, scheduled refreshes, and administrator
requests. Blueprint discovery traverses the Home Assistant configuration tree,
while Lovelace dashboards and resources are already represented by the active
Lovelace runtime.

## Decision

Run blueprint filesystem inspection through Home Assistant's executor and use
the active Lovelace runtime object, identified by `LOVELACE_DATA`, for dashboard
and resource discovery. Dashboard configuration is loaded through each runtime
dashboard's async API, and resources are read from the runtime resource
collection. Do not read Lovelace storage files directly as a fallback.

## Rationale

Filesystem traversal can block the event loop on slow local or network-backed
storage. Direct storage reads bypass Lovelace's ownership and loading semantics,
miss YAML dashboards, and can observe stale or incomplete data. The runtime
objects provide the authoritative in-memory view while preserving asynchronous
loading behavior.

## Outcome

Blueprint detection no longer performs recursive filesystem I/O on the event
loop. Dashboard detection uses active Lovelace dashboards and resources and
reports the source as unavailable when Lovelace has not initialized.

## Status

- **Created**: 2026-11-06 (Phase: Execute)
- **Status**: Accepted
