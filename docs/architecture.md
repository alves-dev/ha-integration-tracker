# Architecture

Integration Tracker separates provider data from user-owned lifecycle data.

```text
HACS provider → provider snapshot → source-neutral registry → HA Store
                                      ↓
                                WebSocket API
                                      ↓
                              admin custom panel
```

## Components

- `providers/base.py` defines the provider contract. A provider returns a complete successful snapshot or raises an error.
- `providers/hacs.py` is the only HACS-aware module. It converts HACS runtime objects into `ProviderItem` values.
- `registry.py` owns synchronization, user edits, usages, reviews, and persistence boundaries.
- `storage.py` adapts the registry to Home Assistant `Store` storage.
- `websocket.py` exposes administrator-only operations used by the panel.
- `panel.py` registers the frontend as an administrator-only Home Assistant custom panel.

## Identity and ownership

The stable item identifier is `<source>:<repository>` with a case-normalized repository name. For example, `hacs:romrider/apexcharts-card`.

Provider synchronization owns name, repository URL, category, icon, versions, provider metadata, and installed state. It cannot update rating, lifecycle status, notes, tags, usages, discovery time, or review history.

When a successful provider snapshot omits a previously installed item from that provider, the registry marks it uninstalled and records the time. A provider exception leaves the entire registry unchanged. Rediscovery of the same identifier clears the uninstall time and reuses the original user data.

## Persistence

The registry is stored under Home Assistant's `.storage/integration_tracker` key. Writes occur after every mutation and after every successful synchronization. Home Assistant storage provides atomic persistence independently of HACS data files.

## Extending providers

A future provider implements `IntegrationProvider.async_discover()` and returns `ProviderItem` objects with its own `source` value. The registry, API, review logic, and panel already treat source as data and require no HACS-specific object.
