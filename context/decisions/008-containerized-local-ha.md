# Decision: Containerized Local Home Assistant Helpers

## Context

The shared local Home Assistant environment moved from a source checkout started
with `uv` to the Docker container `hass-dev-homeassistant`. The integration must
still be deployed without modifying files while Home Assistant is running.

## Decision

- `dev/start-ha.sh` and `dev/stop-ha.sh` manage the `hass-dev-homeassistant`
  container and are idempotent when it is already running or stopped. Docker
  inspection is the only source of truth; no local PID file is maintained.
- `dev/deploy-to-ha.sh` stages `custom_components/integration_tracker` into
  `/home/alves-dev/projects/others/infra/local-dev/hass-dev/data/custom_components`
  while the container is stopped, then starts it again.
- The container remains the owner of the Home Assistant runtime and lifecycle;
  the repository helpers do not start Home Assistant directly with `uv`.

## Rationale

The container is now the authoritative local runtime and its mounted data
directory is the authoritative configuration location. Keeping the lifecycle
commands in the existing helpers preserves the repository workflow while
avoiding a second Home Assistant process.

## Related

- [Project Intent](../intent/project-intent.md)
- [Decision: Technology Stack](001-tech-stack.md)

## Status

- **Created**: 2026-10-27 (Phase: Build)
- **Status**: Accepted
