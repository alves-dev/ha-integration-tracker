# Pattern: Ownership-Preserving Synchronization

## Description

Synchronize provider-controlled metadata while explicitly protecting user-controlled fields and historical records.

## When to Use

Use this pattern when an external snapshot refreshes part of a record but users own another part of that record.

## Pattern

Give the domain model an update method that changes only provider-owned fields. Create missing records from provider data, mark omitted installed records as uninstalled only after successful discovery, and leave user-owned fields untouched.

## Example

```python
def update_from_provider(self, item: ProviderItem) -> None:
    self.name = item.name
    self.repository_url = item.repository_url
    self.category = item.category
    self.version = item.version
    self.available_version = item.available_version
    self.provider_data = item.provider_data
    self.installed = True
    self.uninstalled_at = None
```

The synchronization boundary obtains the provider snapshot before mutating the registry:

```python
discovered = await provider.async_discover()
async with self._lock:
    # Apply the complete, successful snapshot and then persist once.
    ...
```

## Files Using This Pattern

- `custom_components/integration_tracker/models.py` — provider-only update method.
- `custom_components/integration_tracker/registry.py` — complete-snapshot synchronization.
- `tests/test_registry.py` — preservation and failed-snapshot coverage.

## Related

- [Decision: Persistent Registry and Snapshot Synchronization](../../decisions/003-persistent-registry-synchronization.md)
- [Feature: HACS Repository Tracking](../../intent/feature-hacs-repository-tracking.md)
- [Feature: Repository Context Management](../../intent/feature-repository-context.md)

## Status

- **Created**: 2026-09-22
- **Status**: Active

