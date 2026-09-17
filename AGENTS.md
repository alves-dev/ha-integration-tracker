# Agent instructions

This repository contains the `integration_tracker` Home Assistant custom integration.

Local Home Assistant helpers are available under `dev/`:

- `dev/start-ha.sh` starts the shared local Home Assistant instance.
- `dev/stop-ha.sh` stops that same shared instance using its shared PID file.
- `dev/copy-to-core.sh` stops the shared instance, deploys `custom_components/integration_tracker`, and starts it again.

Agents may invoke these helpers when local instance testing is useful. Preserve user data and unrelated worktree changes.
