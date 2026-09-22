# AGENTS.md

This repository contains the `integration_tracker` Home Assistant custom integration.

## Setup Commands

- Install dependencies: `uv sync --all-groups`
- Lint: `uv run ruff check custom_components tests`
- Test: `uv run pytest --cov=custom_components/integration_tracker --cov-report=term`
- Validate integration structure: `python3 /home/alves-dev/.codex/skills/home-assistant-integration-standards/scripts/validate_integration_structure.py .`
- Start shared Home Assistant: `dev/start-ha.sh`
- Deploy to shared Home Assistant and restart: `dev/copy-to-core.sh`
- Stop shared Home Assistant: `dev/stop-ha.sh`

## Code Style

- Python targets 3.12 and uses a 100-character Ruff line length.
- Prefer typed, asynchronous Home Assistant APIs and focused domain methods.
- Keep provider-specific data behind provider adapters and preserve the ownership boundary between provider and user fields.
- Keep panel operations behind administrator-only, schema-validated WebSocket commands.
- Follow patterns from `context/knowledge/patterns/`.

## Context Files to Load

Before starting work, load:

- `@context/.context-mesh-framework.md`
- `@context/intent/project-intent.md` (always)
- The relevant `@context/intent/feature-*.md`
- Relevant `@context/decisions/*.md`
- Relevant `@context/knowledge/patterns/*.md`

## Project Structure

```text
root/
├── AGENTS.md
├── context/
│   ├── .context-mesh-framework.md
│   ├── intent/
│   ├── decisions/
│   ├── knowledge/
│   ├── agents/
│   └── evolution/
├── custom_components/integration_tracker/
├── tests/
├── docs/
└── dev/
```

## AI Agent Rules

### Always

- Load Context Mesh before implementing.
- Follow accepted decisions and existing patterns.
- Preserve unrelated worktree changes and user data.
- Update relevant context after changes.

### Never

- Mix technical implementation details into feature intent files.
- Ignore documented decisions or bypass the provider/user ownership boundary.
- Treat a failed provider snapshot as an uninstall event.
- Leave context stale after a functional or architectural change.

### After Any Changes

- Update the relevant feature intent if functionality changed.
- Add outcomes to decision files if the approach changed or produced a notable result.
- Update `context/evolution/changelog.md`.
- Create a learning document only for significant reusable insights.

## Definition of Done

- [ ] Relevant context is loaded.
- [ ] An ADR/decision exists before a new technical approach is implemented.
- [ ] Code follows documented patterns.
- [ ] Tests and appropriate quality checks pass.
- [ ] Context and changelog reflect the change.

## Local Home Assistant Helpers

The `dev/` helpers target a shared local Home Assistant instance. `dev/copy-to-core.sh` stops the shared instance, deploys `custom_components/integration_tracker`, and starts it again. Check the helper behavior before invoking it and preserve user data and unrelated worktree changes.
