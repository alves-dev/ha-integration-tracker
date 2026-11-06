"""Focused tests for WebSocket response helpers."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from custom_components.integration_tracker.registry import RegistryError
from custom_components.integration_tracker.websocket import (
    _mutate_detected_usage,
    _send_domain_error,
    _usage_result,
)


def test_usage_result_serializes_detection_metadata():
    """Mutation responses expose all moderation metadata."""
    usage = SimpleNamespace(
        id="usage-1",
        name="Example",
        type="automation",
        url="/config/automation/edit/1",
        source="detected",
        detection_key="automation:1",
        detector="automations",
        confidence="high",
        confirmed=True,
        ignored=False,
        stale=False,
        last_seen_at="2026-10-24T00:00:00+00:00",
        evidence={"reference": "example.run"},
    )

    assert _usage_result(usage)["detection_key"] == "automation:1"
    assert _usage_result(usage)["evidence"] == {"reference": "example.run"}


@pytest.mark.asyncio
async def test_mutate_detected_usage_sends_result():
    """Successful moderation sends a serialized result."""
    connection = Mock()
    msg = {"id": 7, "item_id": "item", "usage_id": "usage"}
    usage = SimpleNamespace(
        id="usage", name="Example", type="automation", url=None, source="manual",
        detection_key=None, detector=None, confidence=None, confirmed=True,
        ignored=False, stale=False, last_seen_at=None, evidence={},
    )

    await _mutate_detected_usage(
        connection,
        msg,
        AsyncMock(return_value=usage),
    )

    connection.send_result.assert_called_once()
    assert connection.send_result.call_args.args[0] == 7


@pytest.mark.asyncio
async def test_mutate_detected_usage_sends_domain_error():
    """Registry errors are translated to a WebSocket error."""
    connection = Mock()
    msg = {"id": 8, "item_id": "item", "usage_id": "usage"}

    async def fail(*_args):
        raise RegistryError("Only detected usages can be confirmed")

    await _mutate_detected_usage(connection, msg, fail)

    connection.send_error.assert_called_once_with(
        8, "integration_tracker_error", "Only detected usages can be confirmed"
    )


def test_send_domain_error_uses_message_id():
    """Domain errors retain the request id."""
    connection = Mock()
    _send_domain_error(connection, {"id": 9}, RegistryError("bad request"))
    connection.send_error.assert_called_once_with(9, "integration_tracker_error", "bad request")
