"""Constants for Integration Tracker."""

from datetime import timedelta
from typing import Final

DOMAIN: Final = "integration_tracker"
NAME: Final = "Integration Tracker"
INTEGRATION_VERSION: Final = "2026.9.1"

CONF_REVIEW_INTERVAL_DAYS: Final = "review_interval_days"
DEFAULT_REVIEW_INTERVAL_DAYS: Final = 90
MIN_REVIEW_INTERVAL_DAYS: Final = 1
MAX_REVIEW_INTERVAL_DAYS: Final = 3650

PANEL_URL: Final = "integration-tracker"
PANEL_TITLE: Final = "Integration Tracker"
PANEL_ICON: Final = "mdi:puzzle-check"
PANEL_COMPONENT: Final = "integration-tracker-panel"
STATIC_URL: Final = "/integration_tracker_static"

STORAGE_KEY: Final = DOMAIN
STORAGE_VERSION: Final = 1

SYNC_INTERVAL: Final = timedelta(hours=6)
INITIAL_SYNC_RETRY_SECONDS: Final = 60

STATUSES: Final = ("active", "testing", "unused", "replace", "archived")
USAGE_TYPES: Final = (
    "dashboard",
    "card",
    "automation",
    "script",
    "integration",
    "other",
)
