"""
Tests for the off-device dead man's switch.

The property under test is narrow but critical: the heartbeat must stop when
Nightwatch stops monitoring. A switch that keeps pinging while the detectors
are dead is worse than none, because it manufactures confidence.
"""

from __future__ import annotations

import pytest

from nightwatch.core.config import HeartbeatConfig
from nightwatch.core.heartbeat import HeartbeatReporter


class _FakeResponse:
    def raise_for_status(self) -> None:
        return None


class _FakeClient:
    """Records pings instead of making them."""

    def __init__(self, fail: bool = False):
        self.calls: list[tuple[str, str | None]] = []
        self._fail = fail

    async def post(self, url: str, content: str | None = None):
        self.calls.append((url, content))
        if self._fail:
            raise RuntimeError("network down")
        return _FakeResponse()

    async def aclose(self) -> None:
        return None


def _reporter(probe, *, fail: bool = False, grace: float = 0.0):
    config = HeartbeatConfig(
        enabled=True,
        url="https://hc-ping.com/test-uuid",
        startup_grace_seconds=grace,
    )
    reporter = HeartbeatReporter(config, probe)
    reporter._client = _FakeClient(fail=fail)
    return reporter


async def _healthy():
    return True, ""


async def _unhealthy():
    return False, "detector(s) not running: radar"


class TestHeartbeatReporter:
    @pytest.mark.asyncio
    async def test_pings_when_monitoring(self):
        reporter = _reporter(_healthy)

        assert await reporter.beat_once() is True
        assert reporter._client.calls == [("https://hc-ping.com/test-uuid", None)]
        assert reporter.last_success_at is not None

    @pytest.mark.asyncio
    async def test_signals_fault_when_not_monitoring(self):
        """The whole point: a running process with dead sensors must not ping OK."""
        reporter = _reporter(_unhealthy)

        assert await reporter.beat_once() is False

        url, body = reporter._client.calls[0]
        assert url == "https://hc-ping.com/test-uuid/fail"
        assert "radar" in body
        assert reporter.last_success_at is None
        assert reporter.last_failure_reason == "detector(s) not running: radar"

    @pytest.mark.asyncio
    async def test_startup_grace_suppresses_early_fault(self):
        """The USB radar can take minutes to enumerate; don't page over warm-up."""
        reporter = _reporter(_unhealthy, grace=600.0)

        assert await reporter.beat_once() is False
        assert reporter._client.calls == []

    @pytest.mark.asyncio
    async def test_ping_failure_is_counted_not_swallowed(self):
        reporter = _reporter(_healthy, fail=True)

        assert await reporter.beat_once() is False
        assert reporter.consecutive_failures == 1
        assert reporter.last_success_at is None

    @pytest.mark.asyncio
    async def test_disabled_without_url(self):
        reporter = HeartbeatReporter(HeartbeatConfig(enabled=True, url=""))
        assert reporter.enabled is False

        await reporter.start()  # must not raise
        await reporter.stop()

    @pytest.mark.asyncio
    async def test_health_probe_ignored_when_not_required(self):
        config = HeartbeatConfig(
            enabled=True,
            url="https://hc-ping.com/test-uuid",
            require_healthy=False,
        )
        reporter = HeartbeatReporter(config, _unhealthy)
        reporter._client = _FakeClient()

        assert await reporter.beat_once() is True
