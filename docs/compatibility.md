# Compatibility

| Integration version | Minimum Home Assistant | HACS provider | Notes                                                     |
|---------------------|------------------------|---------------|-----------------------------------------------------------|
| `2026.9.1`          | `2025.1`               | HACS 2.x      | Adds review repairs and opens usage links in a new tab    |
| `2026.9.0`          | `2025.1`               | HACS 2.x      | Initial release with custom panel and persistent registry |

Integration Tracker reads HACS's in-memory repository registry through a dedicated provider adapter. HACS is an optional startup dependency: the integration still loads and preserves stored data when HACS is absent, disabled, or starting.
