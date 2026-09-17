# Development

## Setup

Python 3.12 and `uv` are used for local checks.

```sh
uv sync --all-groups
```

## Quality checks

```sh
uv run ruff check custom_components tests
uv run pytest --cov=custom_components/integration_tracker --cov-report=term
python3 /home/alves-dev/.codex/skills/home-assistant-integration-standards/scripts/validate_integration_structure.py .
```

The registry tests cover metadata preservation, failed provider snapshots, uninstall/reinstall behavior, persistence, and usage operations.

## Local Home Assistant

The `dev/` helpers target the shared local Home Assistant instance:

```sh
dev/copy-to-core.sh
dev/start-ha.sh
dev/stop-ha.sh
```

`copy-to-core.sh` stops the shared instance, copies this integration into its configuration, and starts it again. Check `AGENTS.md` before invoking helpers in an automated workflow.

## Frontend

The panel uses browser-native JavaScript and Home Assistant custom elements. It does not have a Node build step. The backend serves `frontend/integration-tracker-panel.js` directly through a versioned static URL.

When testing the panel, verify an administrator can open and mutate it, a non-administrator cannot see or call it, and the interface remains legible under light, dark, and custom themes. Also check narrow screens, empty registries, HACS failure, and loading states.
