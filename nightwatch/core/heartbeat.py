"""
Off-device dead man's switch for Nightwatch.

Everything that would normally raise an alarm - the alert engine, the
notifiers, the database, the dashboard - runs on the monitoring device. When
that device dies, all of it dies silently, and "no alert" becomes
indistinguishable from "nothing is wrong".

This module inverts that. Nightwatch periodically pings an external service;
if the pings stop, that service raises the alarm. The alarm therefore does not
depend on the device being alive, which is the entire point.

Two properties matter:

1. The endpoint must be off-premises. A watchdog in the same building shares
   the same power and internet, so one blackout takes out the monitor and the
   watchdog together.
2. The ping is gated on actually monitoring, not merely running. A bare
   liveness ping would keep the watchdog green while the detectors sat dead.
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Awaitable, Callable

import httpx

from nightwatch.core.config import HeartbeatConfig

logger = logging.getLogger(__name__)

# A health probe returns (healthy, reason). The reason is reported on failure
# so the resulting page says what broke, not just that something did.
HealthProbe = Callable[[], Awaitable[tuple[bool, str]]]


class HeartbeatReporter:
    """Pings an external watchdog while Nightwatch is genuinely monitoring."""

    def __init__(self, config: HeartbeatConfig, health_probe: HealthProbe | None = None):
        self._config = config
        self._health_probe = health_probe
        self._client: httpx.AsyncClient | None = None
        self._task: asyncio.Task | None = None
        self._running = False
        # Set at construction so the grace window is valid even if beat_once()
        # is called before start(); start() refreshes it.
        self._started_at: float = time.time()

        # Observability - surfaced so a silently failing switch is detectable.
        self.last_success_at: float | None = None
        self.last_failure_reason: str | None = None
        self.consecutive_failures = 0

    @property
    def enabled(self) -> bool:
        return self._config.enabled and bool(self._config.url)

    async def start(self) -> None:
        if self._running:
            return
        if not self.enabled:
            logger.warning(
                "Heartbeat disabled - nothing outside this device will notice "
                "if it stops monitoring."
            )
            return

        self._running = True
        self._started_at = time.time()
        self._client = httpx.AsyncClient(timeout=self._config.timeout_seconds)
        self._task = asyncio.create_task(self._loop())
        logger.info(
            "Heartbeat started - pinging every %.0fs", self._config.interval_seconds
        )

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        if self._client:
            await self._client.aclose()
            self._client = None

    async def _loop(self) -> None:
        while self._running:
            try:
                await self.beat_once()
            except asyncio.CancelledError:
                raise
            except Exception as e:  # never let the loop die
                logger.error("Heartbeat loop error: %s", e)
            await asyncio.sleep(self._config.interval_seconds)

    def _in_startup_grace(self) -> bool:
        """Detectors get time to come up before we report a fault."""
        return (time.time() - self._started_at) < self._config.startup_grace_seconds

    async def beat_once(self) -> bool:
        """
        Send a single heartbeat. Returns True if a success ping was sent.

        When unhealthy, actively signals a fault so the watchdog alerts now
        rather than after its grace period expires.
        """
        healthy, reason = True, ""
        if self._config.require_healthy and self._health_probe is not None:
            healthy, reason = await self._health_probe()

        if not healthy and self._in_startup_grace():
            # Still starting up; stay quiet rather than page over a warm-up.
            logger.debug("Heartbeat suppressed during startup grace: %s", reason)
            return False

        if healthy:
            return await self._ping(self._config.url, success=True)

        self.last_failure_reason = reason
        logger.error("Nightwatch is not monitoring (%s) - signalling watchdog", reason)
        fail_url = self._config.url.rstrip("/") + self._config.fail_path
        await self._ping(fail_url, success=False, body=reason)
        return False

    async def _ping(self, url: str, *, success: bool, body: str = "") -> bool:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self._config.timeout_seconds)
        try:
            response = await self._client.post(url, content=body or None)
            response.raise_for_status()
        except Exception as e:
            self.consecutive_failures += 1
            # Losing the heartbeat channel means the watchdog will page anyway,
            # which is the correct failure direction - but say so loudly.
            logger.error(
                "Heartbeat ping failed (%d consecutive): %s",
                self.consecutive_failures,
                e,
            )
            return False

        self.consecutive_failures = 0
        if success:
            self.last_success_at = time.time()
        return success
