"""Admin-only WebSocket API for the Integration Tracker panel."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant, callback

from .const import CONF_REVIEW_INTERVAL_DAYS, DEFAULT_REVIEW_INTERVAL_DAYS, DOMAIN
from .registry import RegistryError
from .review import build_summary

WS_PREFIX = "integration_tracker"


def _runtime(hass: HomeAssistant):
    runtimes = hass.data.get(DOMAIN, {})
    if not runtimes:
        raise RegistryError("Integration Tracker is not loaded")
    return next(iter(runtimes.values()))


def _interval(runtime) -> int:
    return int(
        runtime.config_entry.options.get(
            CONF_REVIEW_INTERVAL_DAYS, DEFAULT_REVIEW_INTERVAL_DAYS
        )
    )


def _send_domain_error(connection, msg: dict[str, Any], err: Exception) -> None:
    connection.send_error(msg["id"], "integration_tracker_error", str(err))


@callback
def async_register_websocket_commands(hass: HomeAssistant) -> None:
    """Register all panel commands once per Home Assistant process."""
    marker = f"{DOMAIN}_websocket_registered"
    if hass.data.get(marker):
        return
    for command in (
        websocket_list_items,
        websocket_get_item,
        websocket_update_item,
        websocket_add_usage,
        websocket_update_usage,
        websocket_remove_usage,
        websocket_mark_reviewed,
        websocket_sync,
    ):
        websocket_api.async_register_command(hass, command)
    hass.data[marker] = True


@websocket_api.require_admin
@websocket_api.websocket_command({vol.Required("type"): f"{WS_PREFIX}/list"})
@callback
def websocket_list_items(hass, connection, msg) -> None:
    """List items and dashboard metadata."""
    try:
        runtime = _runtime(hass)
        interval = _interval(runtime)
        items = runtime.registry.list_items()
        serialized = [item.to_dict(interval) for item in items]
        connection.send_result(
            msg["id"],
            {
                "items": serialized,
                "summary": build_summary(items, interval),
                "last_synced_at": runtime.registry.last_synced_at,
                "sync_error": runtime.sync_error,
                "review_interval_days": interval,
                "tags": sorted({tag for item in items for tag in item.tags}, key=str.casefold),
                "categories": sorted(
                    {item.category for item in items if item.category}, key=str.casefold
                ),
                "sources": sorted({item.source for item in items}, key=str.casefold),
            },
        )
    except RegistryError as err:
        _send_domain_error(connection, msg, err)


@websocket_api.require_admin
@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{WS_PREFIX}/get",
        vol.Required("item_id"): str,
    }
)
@callback
def websocket_get_item(hass, connection, msg) -> None:
    """Get one tracked item."""
    try:
        runtime = _runtime(hass)
        connection.send_result(
            msg["id"], runtime.registry.get_item(msg["item_id"]).to_dict(_interval(runtime))
        )
    except RegistryError as err:
        _send_domain_error(connection, msg, err)


@websocket_api.require_admin
@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{WS_PREFIX}/update",
        vol.Required("item_id"): str,
        vol.Optional("rating"): vol.Any(None, vol.All(int, vol.Range(min=1, max=3))),
        vol.Optional("status"): vol.Any(None, str),
        vol.Optional("notes"): vol.Any(None, str),
        vol.Optional("tags"): [str],
    }
)
@websocket_api.async_response
async def websocket_update_item(hass, connection, msg) -> None:
    """Update only user-owned item fields."""
    try:
        runtime = _runtime(hass)
        changes = {
            key: msg[key]
            for key in ("rating", "status", "notes", "tags")
            if key in msg
        }
        item = await runtime.registry.async_update_item(msg["item_id"], changes)
        connection.send_result(msg["id"], item.to_dict(_interval(runtime)))
    except RegistryError as err:
        _send_domain_error(connection, msg, err)


USAGE_SCHEMA = {
    vol.Required("item_id"): str,
    vol.Required("name"): str,
    vol.Required("usage_type"): str,
    vol.Optional("url"): vol.Any(None, str),
}


@websocket_api.require_admin
@websocket_api.websocket_command(
    {vol.Required("type"): f"{WS_PREFIX}/usage/add", **USAGE_SCHEMA}
)
@websocket_api.async_response
async def websocket_add_usage(hass, connection, msg) -> None:
    """Add a manual usage."""
    try:
        usage = await _runtime(hass).registry.async_add_usage(
            msg["item_id"], msg["name"], msg["usage_type"], msg.get("url")
        )
        connection.send_result(
            msg["id"],
            {
                "id": usage.id,
                "name": usage.name,
                "type": usage.type,
                "url": usage.url,
                "source": usage.source,
            },
        )
    except RegistryError as err:
        _send_domain_error(connection, msg, err)


@websocket_api.require_admin
@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{WS_PREFIX}/usage/update",
        vol.Required("usage_id"): str,
        **USAGE_SCHEMA,
    }
)
@websocket_api.async_response
async def websocket_update_usage(hass, connection, msg) -> None:
    """Edit a manual usage."""
    try:
        usage = await _runtime(hass).registry.async_update_usage(
            msg["item_id"],
            msg["usage_id"],
            msg["name"],
            msg["usage_type"],
            msg.get("url"),
        )
        connection.send_result(
            msg["id"],
            {
                "id": usage.id,
                "name": usage.name,
                "type": usage.type,
                "url": usage.url,
                "source": usage.source,
            },
        )
    except RegistryError as err:
        _send_domain_error(connection, msg, err)


@websocket_api.require_admin
@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{WS_PREFIX}/usage/remove",
        vol.Required("item_id"): str,
        vol.Required("usage_id"): str,
    }
)
@websocket_api.async_response
async def websocket_remove_usage(hass, connection, msg) -> None:
    """Remove a manual usage."""
    try:
        await _runtime(hass).registry.async_remove_usage(msg["item_id"], msg["usage_id"])
        connection.send_result(msg["id"])
    except RegistryError as err:
        _send_domain_error(connection, msg, err)


@websocket_api.require_admin
@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{WS_PREFIX}/review",
        vol.Required("item_id"): str,
    }
)
@websocket_api.async_response
async def websocket_mark_reviewed(hass, connection, msg) -> None:
    """Mark an item as reviewed and append history."""
    try:
        runtime = _runtime(hass)
        item = await runtime.registry.async_mark_reviewed(msg["item_id"])
        runtime.async_update_repairs()
        connection.send_result(msg["id"], item.to_dict(_interval(runtime)))
    except RegistryError as err:
        _send_domain_error(connection, msg, err)


@websocket_api.require_admin
@websocket_api.websocket_command({vol.Required("type"): f"{WS_PREFIX}/sync"})
@websocket_api.async_response
async def websocket_sync(hass, connection, msg) -> None:
    """Run a manual provider synchronization."""
    runtime = _runtime(hass)
    try:
        counts = await runtime.async_sync()
    except Exception as err:  # Provider exceptions are surfaced without mutating the registry.
        connection.send_error(msg["id"], "provider_unavailable", str(err))
        return
    connection.send_result(
        msg["id"],
        {"counts": counts, "last_synced_at": runtime.registry.last_synced_at},
    )
