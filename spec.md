# Integration Tracker

Home Assistant custom integration for tracking, organizing, reviewing, and documenting installed integrations and custom components.

**Suggested repository:** `ha-integration-tracker`

## 1. Overview

**Integration Tracker** is a Home Assistant custom integration designed to help users understand and maintain the integrations and custom components installed in their Home Assistant instance.

The main problem it solves is not installation or updates, but **lifecycle management**.

As a Home Assistant installation grows, it becomes increasingly difficult to answer questions such as:

* Why was this integration installed?
* Where is it currently being used?
* Is it still necessary?
* When was it last reviewed?
* Was it useful?
* Has it been replaced by something else?
* Is an uninstalled integration something that was intentionally removed?
* Which integrations have not been reviewed recently?

The Integration Tracker maintains a persistent registry containing this information.

The first version will focus exclusively on integrations and repositories installed through **HACS**, but the internal architecture MUST be source-agnostic so other Home Assistant integrations can be supported later.

---

# 2. Goals

The MVP must provide:

* Automatic discovery of repositories installed through HACS.
* Persistent tracking of discovered repositories.
* A custom Home Assistant panel.
* Rating system.
* Status management.
* Notes.
* Tags.
* Manual usage tracking.
* Optional links for usages.
* Review tracking.
* Review history.
* Identification of integrations requiring review.
* Detection of repositories that were removed from HACS.
* Preservation of historical information after uninstall.
* Filtering and searching.

The integration MUST NOT delete its internal record when an integration is no longer installed.

---

# 3. Non-goals for MVP

The following features are explicitly outside the first version:

* Automatically detecting where an integration is used.
* Parsing dashboards looking for custom cards.
* Parsing automations/scripts for references.
* Automatically determining whether an integration is useful.
* Automatically assigning ratings.
* Automatically removing old records.
* Managing HACS installations.
* Installing HACS repositories.
* Updating HACS repositories.
* Removing HACS repositories.
* Managing native Home Assistant integrations.

Integration Tracker is initially a **tracking and organization tool**, not a replacement for HACS.

---

# 4. Architecture

The core registry MUST NOT depend directly on HACS-specific data structures.

Use a provider/source abstraction.

Conceptually:

```text
Integration Tracker
        │
        ├── Registry
        │
        ├── Review Manager
        │
        ├── Storage
        │
        ├── Panel/API
        │
        └── Providers
             │
             ├── HACS Provider       [MVP]
             ├── Home Assistant      [Future]
             └── Manual Provider     [Future]
```

Every tracked item MUST have a source.

Example:

```yaml
source: hacs
```

Future values could include:

```yaml
source: home_assistant
source: manual
```

The registry and frontend should avoid assumptions that every item comes from HACS.

---

# 5. Tracked Item

A tracked item represents an integration, frontend repository, plugin, theme, or other component discovered through a provider.

Example conceptual model:

```yaml
id: apexcharts-card
source: hacs

name: ApexCharts Card
repository: RomRider/apexcharts-card
url: https://github.com/RomRider/apexcharts-card

category: plugin

installed: true

version: 2.1.0
available_version: 2.1.1

discovered_at: "2026-09-17T10:00:00Z"
uninstalled_at: null

rating: 3
status: active

notes: >
  Main chart library used in dashboards.

tags:
  - dashboard
  - charts
  - important

last_reviewed_at: "2026-09-17T14:00:00Z"

usages:
  - id: usage-001
    name: Health Dashboard
    type: dashboard
    url: /dashboard-health

  - id: usage-002
    name: Weight evolution chart
    type: card
    url: /dashboard-health/body

review_history:
  - reviewed_at: "2026-06-10T12:00:00Z"
  - reviewed_at: "2026-09-17T14:00:00Z"
```

The exact storage representation can differ, but these concepts must be preserved.

---

# 6. Identity

Every tracked item MUST have a stable internal identifier.

The identifier must not depend exclusively on the display name.

Prefer using information from the provider such as:

```text
source + repository identifier
```

For example:

```text
hacs:RomRider/apexcharts-card
```

This prevents duplicate records if the display name changes.

The internal ID should remain stable after uninstall.

---

# 7. HACS Provider

The HACS provider is responsible for discovering currently installed HACS repositories.

When synchronization runs, it should retrieve as much metadata as reasonably available, such as:

* Repository identifier.
* Name.
* Repository URL.
* Category/type.
* Installed version.
* Available version.
* Icon/logo when available.
* HACS metadata relevant for display.

The provider MUST gracefully handle unavailable optional metadata.

For example, an item without an icon must still be displayed normally.

---

# 8. Synchronization

Synchronization compares the current HACS state against the Integration Tracker registry.

## New repository

When a repository is discovered for the first time:

```text
Create registry entry
installed = true
discovered_at = now
```

User-maintained fields start empty/default.

For example:

```yaml
rating: null
status: null
notes: null
tags: []
usages: []
last_reviewed_at: null
review_history: []
```

## Existing repository

Update provider-controlled metadata while preserving user-controlled metadata.

Provider-controlled examples:

* Name.
* Installed version.
* Available version.
* Repository URL.
* Category.
* Icon.
* Installed state.

User-controlled examples:

* Rating.
* Status.
* Notes.
* Tags.
* Usages.
* Review history.

Provider synchronization MUST NEVER overwrite user-maintained fields.

## Repository removed from HACS

When an item previously tracked as installed can no longer be found:

```yaml
installed: false
uninstalled_at: <current timestamp>
```

DO NOT delete:

* Rating.
* Notes.
* Tags.
* Status.
* Usages.
* Review history.
* Discovery date.

## Repository installed again

If the same repository is detected again:

```yaml
installed: true
uninstalled_at: null
```

Existing history and user metadata MUST be restored/reused rather than creating another item.

---

# 9. Rating

Users can assign a rating from **1 to 3 stars**.

Values:

```text
★☆☆ = 1
★★☆ = 2
★★★ = 3
```

Rating is optional.

No rating must be represented as:

```yaml
rating: null
```

The UI should allow changing or clearing the rating.

---

# 10. Status

Rating and status represent different concepts.

Rating represents the user's opinion about the integration.

Status represents its current lifecycle.

Initial supported statuses:

```text
active
testing
unused
replace
archived
```

Suggested meanings:

### Active

Currently used and expected to remain installed.

### Testing

Currently being evaluated.

### Unused

Installed or tracked but currently not known to be used.

### Replace

Still used, but the user intends to replace it.

### Archived

No longer relevant for normal use but retained for historical purposes.

Status is optional.

Future versions may allow custom statuses, but this is not required for the MVP.

---

# 11. Notes

Each tracked item has a free-text notes field.

Example:

```text
Used mainly because it supports the graph configuration needed by the health dashboard.

Consider replacing it if native HA charts gain equivalent support.
```

Notes should support multiline text.

The MVP does not require Markdown rendering.

---

# 12. Tags

Each tracked item can have zero or more tags.

Examples:

```text
dashboard
charts
tablet
frontend
automation
important
experimental
```

Tags are user-defined.

The UI should autocomplete existing tags when possible so the user can reuse tags consistently.

Tags should be filterable.

Tags MUST survive uninstall/reinstall.

---

# 13. Usage Tracking

Users can manually register places where an integration is being used.

Each usage contains:

```yaml
id: usage-001
name: Health Dashboard
type: dashboard
url: /dashboard-health
```

Required:

```text
name
type
```

Optional:

```text
url
```

The URL may be either:

* Home Assistant relative URL.
* Absolute external URL.

Examples:

```text
/dashboard-health

/lovelace/tablet

/config/automation/edit/123456789

https://example.com/documentation
```

When a URL exists, the frontend should make the usage clickable.

For internal Home Assistant paths, navigation should preferably happen using Home Assistant frontend navigation rather than forcing a complete browser reload.

---

# 14. Usage Types

Initial predefined types:

```text
dashboard
card
automation
script
integration
other
```

The internal representation should not make it unnecessarily difficult to add new types later.

The frontend may associate icons with known types.

Example:

```text
dashboard    → mdi:view-dashboard
card         → mdi:card
automation   → mdi:robot
script       → mdi:script-text
integration  → mdi:puzzle
other        → mdi:link
```

The exact icons can be adjusted during implementation.

---

# 15. Review System

One of the main features of Integration Tracker is periodically reviewing tracked items.

Each item has:

```yaml
last_reviewed_at: timestamp | null
```

The details view must provide a clear action:

```text
Mark as reviewed
```

When executed:

```text
last_reviewed_at = now
```

and a new historical entry MUST be created.

Example:

```yaml
review_history:
  - reviewed_at: "2026-03-01T10:00:00Z"
  - reviewed_at: "2026-06-10T12:00:00Z"
  - reviewed_at: "2026-09-17T14:00:00Z"
```

Review history should not be overwritten.

---

# 16. Review Interval

The integration should have a global configurable review interval.

Suggested default:

```text
90 days
```

The value should be configurable through Integration Tracker options.

Based on this interval, items can be classified dynamically as:

### Up to date

```text
now - last_reviewed_at <= review_interval
```

### Needs review

```text
now - last_reviewed_at > review_interval
```

### Never reviewed

```text
last_reviewed_at == null
```

This is a calculated review state and MUST NOT be stored as the item's lifecycle `status`.

---

# 17. Custom Panel

Integration Tracker must register a custom Home Assistant panel.

The panel should be available through the Home Assistant sidebar.

Suggested name:

```text
Integration Tracker
```

Suggested icon:

```text
mdi:puzzle-check
```

The frontend should follow Home Assistant visual conventions whenever practical.

---

# 18. Main Dashboard

The main screen should provide a summary followed by the integration table.

Example:

```text
Integration Tracker

42 tracked integrations

31 Active
4 Testing
3 Unused
4 Archived

11 need review
5 have no known usage
8 were never reviewed
3 are currently uninstalled
```

These metrics should be calculated from the registry.

---

# 19. Integration Table

Suggested columns:

| Column      | Description                   |
| ----------- | ----------------------------- |
| Integration | Icon + name                   |
| Source      | HACS                          |
| Category    | Integration/plugin/theme/etc. |
| Status      | Active/testing/etc.           |
| Rating      | 1–3 stars                     |
| Uses        | Number of registered usages   |
| Last Review | Relative or absolute date     |
| Installed   | Installed/uninstalled         |
| Version     | Installed version             |

The table should support responsive behavior.

On smaller screens, less important columns may be hidden and available through the details view.

---

# 20. Integration Details

Selecting an item should open either:

* A side drawer.
* A modal.
* A dedicated details page.

The implementation can choose whichever fits Home Assistant frontend conventions best.

The details view should show:

```text
Icon
Name
Source
Category
Repository link
Installed version
Available version
Installation status
Discovery date
Uninstall date (when applicable)

Rating
Status
Tags

Notes

Known usages

Last reviewed
Review history

[ Mark as reviewed ]
```

Editable fields should be clearly separated from provider-controlled metadata.

---

# 21. Filters

The main table must support filtering by:

### Installation

```text
All
Installed
Uninstalled
```

### Status

```text
Active
Testing
Unused
Replace
Archived
No status
```

### Rating

```text
★★★
★★
★
No rating
```

### Review state

```text
Up to date
Needs review
Never reviewed
```

### Source

Initially:

```text
HACS
```

This filter must already exist conceptually because more providers will be supported later.

### Category

Based on provider categories.

### Tags

One or more user-defined tags.

---

# 22. Search

The table must provide text search.

At minimum search:

* Name.
* Repository.
* Notes.
* Tags.

Searching usage names would also be useful and should be implemented if straightforward.

---

# 23. Useful Derived States

The frontend should calculate useful conditions.

Examples:

## No known usage

```text
usages.length == 0
```

## Needs review

Based on review interval.

## Never reviewed

```text
last_reviewed_at == null
```

## Uninstalled

```text
installed == false
```

## Installed but marked unused

```text
installed == true && status == unused
```

## Installed and marked replace

```text
installed == true && status == replace
```

These states can be used for filters, dashboard counters and visual indicators.

---

# 24. Sorting

The table should support sorting.

Useful sort fields:

* Name.
* Rating.
* Status.
* Last reviewed.
* Discovered date.
* Usage count.
* Installed/uninstalled.

A particularly useful workflow is:

```text
Last reviewed → oldest first
```

allowing the user to periodically audit old integrations.

---

# 25. Persistence

Integration Tracker MUST persist its registry independently of HACS.

Home Assistant's standard storage mechanisms should be preferred.

The storage must survive:

* Home Assistant restart.
* Integration reload.
* HACS restart/reload.
* Repository uninstall.
* Repository reinstall.

User-entered metadata is considered important data and MUST NOT disappear because provider discovery temporarily fails.

---

# 26. Provider Failure

Failure to query HACS MUST NOT cause items to be marked as uninstalled immediately.

This distinction is important:

```text
HACS successfully queried + repository absent
```

is different from:

```text
HACS unavailable / provider query failed
```

Only a successful synchronization may change installation state based on absence.

This prevents temporary HACS failures from incorrectly marking every repository as uninstalled.

---

# 27. Data Ownership

Fields should conceptually have an owner.

## Provider-owned

Examples:

```text
name
repository
repository_url
category
icon
installed
version
available_version
```

## Integration Tracker-owned

Examples:

```text
rating
status
notes
tags
usages
last_reviewed_at
review_history
discovered_at
uninstalled_at
```

Provider synchronization must respect this separation.

---

# 28. Services / API

The frontend will need backend endpoints or WebSocket commands for registry operations.

At minimum support operations equivalent to:

```text
list_items
get_item
update_item
add_usage
update_usage
remove_usage
mark_reviewed
sync
```

`update_item` should only allow user-editable properties.

Synchronization should also be callable manually from the panel.

The preferred communication mechanism should follow current Home Assistant custom integration/frontend conventions.

---

# 29. Manual Synchronization

The panel should provide an action such as:

```text
Sync now
```

The UI should display:

```text
Last synchronized: <timestamp>
```

Automatic synchronization should also occur at appropriate lifecycle points, such as Home Assistant startup/integration setup.

Periodic synchronization may be implemented if useful, but aggressive polling is unnecessary.

---

# 30. Uninstalled Items

Uninstalled integrations should remain visible by default, but clearly distinguished from installed integrations.

Example:

```text
ApexCharts Card
★★★
Archived
Uninstalled
Last used/reviewed: ...
```

The UI should allow filtering them out.

An uninstalled item MUST retain:

* Rating.
* Status.
* Notes.
* Tags.
* Usages.
* Review history.

This historical registry is a core feature, not temporary cache.

---

# 31. Safety Against Accidental Deletion

The MVP does not need a normal "Delete tracked item" action.

Because historical information is valuable, removing something from HACS should simply archive its installation state.

If permanent deletion is added later, it should require explicit confirmation.

---

# 32. Future: Automatic Usage Detection

The data model should anticipate automatic usage discovery without implementing it yet.

Future usages may contain:

```yaml
id: usage-123
name: Health Dashboard
type: dashboard
url: /dashboard-health
source: detected
```

While manually entered usages could become:

```yaml
source: manual
```

Potential future scanners include:

* Lovelace dashboards.
* Custom cards.
* Automations.
* Scripts.
* Scenes.
* Entities.
* Services.
* Other integrations.

A future UI could then show:

```text
Known usages

3 manual
7 detected
```

Do not implement automatic detection in the MVP.

---

# 33. Future Providers

The architecture should allow future providers without redesigning the registry.

Potential providers:

```text
HACS
Home Assistant integrations
Manual entries
Custom frontend modules
Add-ons
```

Not all of these necessarily need to be implemented.

The important requirement is that the core domain model does not assume:

```text
tracked item == HACS repository
```

Instead:

```text
tracked item → source/provider
```

---

# 34. Suggested Project Structure

The exact structure can follow Home Assistant best practices, but conceptually:

```text
custom_components/
└── integration_tracker/
    ├── __init__.py
    ├── manifest.json
    ├── config_flow.py
    ├── const.py
    ├── models.py
    ├── storage.py
    ├── registry.py
    ├── review.py
    ├── websocket.py
    │
    ├── providers/
    │   ├── __init__.py
    │   ├── base.py
    │   └── hacs.py
    │
    └── frontend/
        └── ...
```

This is a suggestion rather than a strict requirement.

The implementation should prioritize maintainability and Home Assistant conventions.

---

# 35. MVP Acceptance Criteria

The MVP is considered complete when the user can:

1. Install Integration Tracker.
2. Open its custom panel.
3. See currently installed HACS repositories.
4. See basic metadata for each repository.
5. Open repository links.
6. Assign 1–3 stars.
7. Clear an existing rating.
8. Assign a lifecycle status.
9. Write/edit notes.
10. Add/remove tags.
11. Add a manual usage.
12. Specify usage name, type and optional URL.
13. Edit/remove an existing usage.
14. Open a usage URL.
15. Mark an integration as reviewed.
16. See its last review date.
17. Preserve review history.
18. Identify items requiring review.
19. Search integrations.
20. Filter integrations.
21. Sort integrations.
22. Trigger manual synchronization.
23. See when synchronization last occurred.
24. Keep metadata when a HACS repository is uninstalled.
25. Clearly see that the repository is no longer installed.
26. Reassociate the historical record if the same repository is installed again.
27. Preserve all data across Home Assistant restarts.

---

# 36. Guiding Principle

Integration Tracker should answer four simple questions about every integration:

> **What is this?**
> **Why do I have it?**
> **Where am I using it?**
> **Do I still need it?**

HACS remains responsible for installation and updates.

Integration Tracker is responsible for **inventory, context, lifecycle and review**.
