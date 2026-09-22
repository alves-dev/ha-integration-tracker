# Project Intent: Integration Tracker

## What

Integration Tracker is a Home Assistant custom integration that helps users understand, organize, and maintain repositories installed through HACS. It keeps a durable record of why tracked repositories matter, where they are used, how useful they have been, and when they should be reviewed again.

## Why

HACS manages installation and updates, but it does not preserve the user’s lifecycle context. Integration Tracker fills that gap so users can make informed decisions about keeping, reviewing, replacing, or removing custom components without losing history after an uninstall.

## Current State

The implemented project provides a configured Home Assistant integration with a persistent registry, HACS discovery, synchronization, administrator panel, WebSocket operations, review tracking, manual usage tracking, filtering and sorting, and tests covering the registry lifecycle. It is version `2026.9.0` and targets Home Assistant `2025.1+`.

## Current Features

- [HACS repository discovery and lifecycle tracking](feature-hacs-repository-tracking.md)
- [Repository context management](feature-repository-context.md)
- [Usage and link tracking](feature-usage-tracking.md)
- [Review scheduling and history](feature-review-management.md)
- [Administrator tracker panel](feature-administrator-panel.md)

## Related

- [Decision: Technology Stack](../decisions/001-tech-stack.md)
- [Decision: Source-Neutral Provider Architecture](../decisions/002-source-neutral-provider-architecture.md)
- [Decision: Persistent Registry and Snapshot Synchronization](../decisions/003-persistent-registry-synchronization.md)
- [Decision: Administrator Panel and WebSocket API](../decisions/004-administrator-panel-api.md)

## Status

- **Created**: 2026-09-22 (Phase: Intent)
- **Status**: Active
- **Note**: Generated from existing codebase analysis.

