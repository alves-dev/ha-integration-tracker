"""Tests for Integration Tracker configuration flows."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from custom_components.integration_tracker.config_flow import (
    IntegrationTrackerConfigFlow,
    IntegrationTrackerOptionsFlow,
)
from custom_components.integration_tracker.const import (
    CONF_ENABLE_REPAIRS,
    CONF_INCLUDE_CORE,
    CONF_REVIEW_INTERVAL_DAYS,
)


@pytest.mark.asyncio
async def test_user_flow_shows_form_then_creates_entry(monkeypatch):
    """The config flow creates one empty entry after the form."""
    flow = IntegrationTrackerConfigFlow()
    flow.async_set_unique_id = AsyncMock()
    monkeypatch.setattr(flow, "_abort_if_unique_id_configured", lambda: None)

    form = await flow.async_step_user()
    entry = await flow.async_step_user({"ignored": True})

    assert form["type"] == "form"
    assert entry["type"] == "create_entry"
    assert entry["data"] == {}


def test_config_flow_returns_options_flow():
    """The config flow exposes the options flow factory."""
    assert isinstance(
        IntegrationTrackerConfigFlow.async_get_options_flow(SimpleNamespace()),
        IntegrationTrackerOptionsFlow,
    )


@pytest.mark.asyncio
async def test_options_flow_uses_defaults_and_saves_values():
    """Options are shown with defaults and persisted on submit."""
    flow = IntegrationTrackerOptionsFlow()
    flow._config_entry = SimpleNamespace(options={})

    form = await flow.async_step_init()
    result = await flow.async_step_init(
        {
            CONF_ENABLE_REPAIRS: False,
            CONF_REVIEW_INTERVAL_DAYS: 30,
            CONF_INCLUDE_CORE: True,
        }
    )

    assert form["type"] == "form"
    assert result["type"] == "create_entry"
    assert result["data"][CONF_REVIEW_INTERVAL_DAYS] == 30
