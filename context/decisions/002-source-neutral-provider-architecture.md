# Decision: Source-Neutral Provider Architecture

## Context

The current discovery source is HACS, while the product concept is broader lifecycle tracking. The core registry must not depend on HACS runtime objects or prevent future sources from being added.

## Decision

Use an abstract provider contract that returns source-neutral provider items. Keep HACS-specific discovery inside a dedicated adapter and identify each item with a normalized source-and-repository identifier. The registry, review logic, API, and panel operate on the source-neutral model.

## Rationale

This isolates HACS availability and object shapes from the core domain. It also makes identity stable across display-name changes and leaves room for future Home Assistant or manual providers without rewriting registry behavior.

## Alternatives Considered

Alternatives are not documented in the existing codebase. Directly storing HACS objects in the registry would couple the domain to HACS and is not used by the implementation.

## Outcomes

The current HACS provider can report unavailable or incomplete runtime state without corrupting the registry. Future providers can implement the same discovery contract.

## Related

- [Project Intent](../intent/project-intent.md)
- [Feature: HACS Repository Tracking](../intent/feature-hacs-repository-tracking.md)
- [Pattern: Provider Adapter](../knowledge/patterns/provider-adapter.md)

## Status

- **Created**: 2026-09-22 (Phase: Intent)
- **Status**: Accepted
- **Note**: Documented from existing implementation.

