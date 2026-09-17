# WebSocket API

All Integration Tracker WebSocket commands require an authenticated Home Assistant administrator. Errors use the normal Home Assistant WebSocket error response.

| Command | Purpose | Main fields |
| --- | --- | --- |
| `integration_tracker/list` | List items and dashboard metadata | none |
| `integration_tracker/get` | Get one item | `item_id` |
| `integration_tracker/update` | Update user-owned fields | `item_id`, optional `rating`, `status`, `notes`, `tags` |
| `integration_tracker/usage/add` | Add a usage | `item_id`, `name`, `usage_type`, optional `url` |
| `integration_tracker/usage/update` | Edit a usage | add fields plus `usage_id` |
| `integration_tracker/usage/remove` | Remove a usage | `item_id`, `usage_id` |
| `integration_tracker/review` | Mark an item reviewed | `item_id` |
| `integration_tracker/sync` | Run HACS synchronization | none |

`integration_tracker/list` returns calculated `review_state` values and dashboard counters using the configured review interval. Review state is never persisted as lifecycle status.

`integration_tracker/update` rejects provider-owned keys. A rating is `null` or an integer from 1 through 3. Supported initial lifecycle statuses are `active`, `testing`, `unused`, `replace`, and `archived`.

Usage URLs may be Home Assistant paths beginning with `/` or absolute HTTP(S) URLs. Usages include `source: manual` so future detected usages can use the same data model.
