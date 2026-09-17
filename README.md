# Integration Tracker

[![Quality Gate](https://sonar.alves-dev.com/api/project_badges/measure?project=ha-integration-tracker&metric=alert_status)](https://sonar.alves-dev.com/dashboard?id=ha-integration-tracker)
[![Coverage](https://sonar.alves-dev.com/api/project_badges/measure?project=ha-integration-tracker&metric=coverage)](https://sonar.alves-dev.com/dashboard?id=ha-integration-tracker)
![Version](https://img.shields.io/badge/Version-2026.9.0-41BDF5?style=flat-square)
![Home Assistant](https://img.shields.io/badge/Home%20Assistant-2025.1%2B-41BDF5?logo=homeassistant)

Integration Tracker is a Home Assistant custom integration for understanding and maintaining the repositories installed through HACS. It keeps the context HACS does not own: why a repository is installed, where it is used, how useful it has been, and when it should be reviewed again.

HACS remains responsible for installation and updates. Integration Tracker maintains a separate historical registry, so notes and review history remain available after an uninstall and return when the same repository is installed again.

## Features

- Discovers installed HACS integrations, plugins, themes, scripts, and other repository categories.
- Keeps a persistent record of installed and uninstalled repositories.
- Provides ratings from one to three stars, lifecycle statuses, multiline notes, and reusable tags.
- Tracks manual usages with optional Home Assistant or external links.
- Records every review and highlights items that are overdue or have never been reviewed.
- Searches names, repositories, notes, tags, and usage names.
- Filters by installation, status, rating, review state, source, category, and tags.
- Sorts by name, rating, status, review date, discovery date, usage count, or installation state.
- Exposes an administrator-only panel in the Home Assistant sidebar.

## Requirements

- Home Assistant 2025.1.0 or newer.
- HACS installed and configured for repository discovery.
- An administrator account to use the panel and its API.

If HACS is temporarily unavailable, Integration Tracker preserves the registry and reports the synchronization error. Repositories are marked as uninstalled only after HACS returns a successful complete snapshot.

## HACS availability

Integration Tracker is available as a HACS custom repository and is not currently listed in the default HACS catalog. Add `https://github.com/alves-dev/ha-integration-tracker` as an `Integration` repository.

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=alves-dev&repository=ha-integration-tracker&category=integration)

## Installation

### HACS custom repository

1. Open HACS in Home Assistant.
2. Open the custom repositories dialog.
3. Add `https://github.com/alves-dev/ha-integration-tracker` with category **Integration**.
4. Find **Integration Tracker**, install it, and restart Home Assistant.
5. Open **Settings → Devices & services → Add integration** and select **Integration Tracker**.

### Manual installation

1. Download the latest release.
2. Copy `custom_components/integration_tracker` into the `custom_components` directory in your Home Assistant configuration.
3. Restart Home Assistant.
4. Add **Integration Tracker** from **Settings → Devices & services**.

## Normal operation

Open **Integration Tracker** from the sidebar. The integration synchronizes at setup, retries after HACS startup when necessary, and refreshes every six hours. Use **Sync now** after installing or removing repositories when you want the panel updated immediately.

Select a row to edit tracking data, manage known usages, open the repository, or mark the item as reviewed. Set the global review interval from the integration's **Configure** action in **Settings → Devices & services**. The default is 90 days.

Only administrator users can see the panel or call its WebSocket operations.

## Technical documentation

- [Architecture and data ownership](docs/architecture.md)
- [WebSocket API](docs/api.md)
- [Compatibility](docs/compatibility.md)
- [Development and testing](docs/development.md)

## License

Integration Tracker is available under the [MIT License](LICENSE).
