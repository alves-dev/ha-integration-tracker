"""Config and options flows for Integration Tracker."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import config_validation as cv

from .const import (
    CONF_ENABLE_REPAIRS,
    CONF_INCLUDE_CORE,
    CONF_REVIEW_INTERVAL_DAYS,
    DEFAULT_ENABLE_REPAIRS,
    DEFAULT_INCLUDE_CORE,
    DEFAULT_REVIEW_INTERVAL_DAYS,
    DOMAIN,
    MAX_REVIEW_INTERVAL_DAYS,
    MIN_REVIEW_INTERVAL_DAYS,
)


class IntegrationTrackerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Configure Integration Tracker."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        """Create the single Integration Tracker entry."""
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()
        if user_input is not None:
            return self.async_create_entry(title="Integration Tracker", data={})
        return self.async_show_form(step_id="user")

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        """Return the options flow."""
        return IntegrationTrackerOptionsFlow()


class IntegrationTrackerOptionsFlow(config_entries.OptionsFlow):
    """Configure review repairs and inventory sources."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        """Manage Integration Tracker options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current = self.config_entry.options.get(
            CONF_REVIEW_INTERVAL_DAYS, DEFAULT_REVIEW_INTERVAL_DAYS
        )
        enable_repairs = self.config_entry.options.get(
            CONF_ENABLE_REPAIRS, DEFAULT_ENABLE_REPAIRS
        )
        include_core = self.config_entry.options.get(
            CONF_INCLUDE_CORE, DEFAULT_INCLUDE_CORE
        )
        schema = vol.Schema(
            {
                vol.Required(CONF_ENABLE_REPAIRS, default=enable_repairs): cv.boolean,
                vol.Required(CONF_REVIEW_INTERVAL_DAYS, default=current): vol.All(
                    vol.Coerce(int),
                    vol.Range(
                        min=MIN_REVIEW_INTERVAL_DAYS,
                        max=MAX_REVIEW_INTERVAL_DAYS,
                    ),
                ),
                vol.Required(CONF_INCLUDE_CORE, default=include_core): cv.boolean,
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
