# Compatibility

| Integration version | Minimum Home Assistant | Discovery backend | Notes                                                                |
|---------------------|------------------------|-------------------|----------------------------------------------------------------------|
| `2026.10.0`         | `2025.1`               | Marketplace/HACS  | Marketplace on HA 2026.11+; preserves existing HACS record identity |
| `2026.9.1`          | `2025.1`               | HACS 2.x          | Adds review repairs and opens usage links in a new tab               |
| `2026.9.0`          | `2025.1`               | HACS 2.x          | Initial release with custom panel and persistent registry            |

Integration Tracker reads the active community-store in-memory repository registry through a dedicated provider adapter. Marketplace is used on Home Assistant 2026.11 and newer; HACS remains the fallback on older versions. The active provider is optional at startup: the integration still loads and preserves stored data when it is absent, disabled, or starting.
