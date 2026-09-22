# Pattern: Administrator WebSocket Command

## Description

Implement each panel operation as a named, schema-validated Home Assistant WebSocket command protected by administrator authorization.

## When to Use

Use this pattern for panel operations that need authenticated Home Assistant access and consistent request validation.

## Pattern

Register commands once, decorate each handler with the administrator guard and command schema, delegate business logic to the registry, and translate domain errors into a domain-specific WebSocket error.

## Example

```python
@websocket_api.require_admin
@websocket_api.websocket_command(
    {
        vol.Required("type"): "integration_tracker/update",
        vol.Required("item_id"): str,
        vol.Optional("rating"): vol.Any(None, vol.All(int, vol.Range(min=1, max=3))),
    }
)
@websocket_api.async_response
async def websocket_update_item(hass, connection, msg) -> None:
    try:
        item = await _runtime(hass).registry.async_update_item(msg["item_id"], changes)
        connection.send_result(msg["id"], item.to_dict(_interval(_runtime(hass))))
    except RegistryError as err:
        _send_domain_error(connection, msg, err)
```

## Files Using This Pattern

- `custom_components/integration_tracker/websocket.py` — all panel commands.
- `custom_components/integration_tracker/panel.py` — administrator-only panel registration.
- `custom_components/integration_tracker/frontend/integration-tracker-panel.js` — command callers.

## Related

- [Decision: Administrator Panel and WebSocket API](../../decisions/004-administrator-panel-api.md)
- [Feature: Administrator Tracker Panel](../../intent/feature-administrator-panel.md)

## Status

- **Created**: 2026-09-22
- **Status**: Active

