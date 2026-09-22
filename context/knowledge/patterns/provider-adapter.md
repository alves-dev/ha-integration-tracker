# Pattern: Provider Adapter

## Description

Hide an external discovery source behind a small asynchronous provider interface and translate external runtime objects into source-neutral domain models.

## When to Use

Use this pattern when the core domain should support multiple data sources or when an external integration’s runtime objects and availability rules should not leak into core logic.

## Pattern

Define a provider with a source identifier and an async method that returns a complete list of normalized items. Keep source-specific validation and field extraction in the adapter. Raise a provider-specific availability error when a trustworthy snapshot cannot be returned.

## Example

```python
class IntegrationProvider(ABC):
    source: str

    @abstractmethod
    async def async_discover(self) -> list[ProviderItem]:
        """Return a complete snapshot of currently installed items."""


class HacsProvider(IntegrationProvider):
    source = "hacs"

    async def async_discover(self) -> list[ProviderItem]:
        hacs = self._hass.data.get("hacs")
        if hacs is None:
            raise ProviderUnavailableError("HACS is not loaded")
        # Translate HACS repository objects into ProviderItem values.
```

## Files Using This Pattern

- `custom_components/integration_tracker/providers/base.py` — provider contract and errors.
- `custom_components/integration_tracker/providers/hacs.py` — HACS adapter.
- `custom_components/integration_tracker/models.py` — source-neutral `ProviderItem`.

## Related

- [Decision: Source-Neutral Provider Architecture](../../decisions/002-source-neutral-provider-architecture.md)
- [Feature: HACS Repository Tracking](../../intent/feature-hacs-repository-tracking.md)

## Status

- **Created**: 2026-09-22
- **Status**: Active

