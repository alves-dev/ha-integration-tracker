# Pattern: Registry Domain Operations

## Description

Keep validation, domain mutations, and persistence in an asynchronous registry service rather than duplicating them in each transport handler.

## When to Use

Use this pattern for operations that mutate persisted domain state through multiple interfaces or need one consistent validation boundary.

## Pattern

Expose focused async methods for each domain operation. Validate and normalize inputs before mutation, serialize after mutation, and use domain-specific exceptions for invalid or missing records. Protect concurrent mutations with a lock.

## Example

```python
async def async_update_item(self, item_id: str, changes: dict[str, Any]) -> TrackedItem:
    allowed = {"rating", "status", "notes", "tags"}
    unknown = set(changes) - allowed
    if unknown:
        raise RegistryError("Provider-owned or unknown fields")
    async with self._lock:
        item = self.get_item(item_id)
        # validate and apply changes
        await self._async_save()
        return item
```

## Files Using This Pattern

- `custom_components/integration_tracker/registry.py` — domain operations and normalization.
- `custom_components/integration_tracker/websocket.py` — thin transport handlers.
- `tests/test_registry.py` — operation and persistence coverage.

## Related

- [Decision: Persistent Registry and Snapshot Synchronization](../../decisions/003-persistent-registry-synchronization.md)
- [Feature: Repository Context Management](../../intent/feature-repository-context.md)
- [Feature: Usage and Link Tracking](../../intent/feature-usage-tracking.md)

## Status

- **Created**: 2026-09-22
- **Status**: Active

