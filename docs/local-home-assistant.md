# Shared local Home Assistant test instance

This repository uses the shared containerized Home Assistant development
instance. Do not start a second Home Assistant process for this integration.

- Container: `hass-dev-homeassistant`
- Image: `homeassistant/home-assistant:dev`
- Host configuration: `/home/alves-dev/projects/others/infra/local-dev/hass-dev/data`
- Container configuration: `/config`
- Web interface: `http://localhost:8123`
- Administrator username: `homer`
- Administrator password: `HomerSimpson123!`

The host configuration is mounted into the container and contains shared
Home Assistant state, configuration, and `custom_components/`. Use
`dev/start-ha.sh` and `dev/stop-ha.sh` to control the container. Use
`dev/deploy-to-ha.sh` to stop the instance, replace this integration in the
mounted configuration, and start it again.

These credentials are for the local development instance only. Never reuse
them in production, end-user documentation, or automated release workflows.
