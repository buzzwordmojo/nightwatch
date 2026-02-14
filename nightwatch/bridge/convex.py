"""
Convex bridge for pushing detector events to the dashboard.

Uses HTTP mutations to send data to Convex local backend.
"""

from __future__ import annotations

import asyncio
import os
import time
import logging
from dataclasses import dataclass
from typing import Any

import httpx

from nightwatch.core.events import Event, EventState

logger = logging.getLogger(__name__)


@dataclass
class ConvexConfig:
    """Configuration for Convex connection."""

    url: str = os.environ.get("CONVEX_URL", "http://localhost:3210")
    timeout: float = 5.0
    batch_interval: float = 1.0  # Batch readings every N seconds
    retry_attempts: int = 3


class ConvexBridge:
    """
    Bridge between Nightwatch detectors and Convex.

    Pushes detector state updates and readings to Convex
    for real-time display in the dashboard.
    """

    def __init__(self, config: ConvexConfig | None = None):
        """
        Initialize Convex bridge.

        Args:
            config: Convex connection configuration
        """
        self._config = config or ConvexConfig()
        self._client: httpx.AsyncClient | None = None
        self._running = False

        # Batching state
        self._pending_readings: list[dict[str, Any]] = []
        self._last_flush = time.time()

        # Last known state per detector
        self._detector_states: dict[str, dict[str, Any]] = {}

    async def start(self) -> None:
        """Start the bridge."""
        self._client = httpx.AsyncClient(
            base_url=self._config.url,
            timeout=self._config.timeout,
        )
        self._running = True
        logger.info(f"Convex bridge started, connecting to {self._config.url}")

    async def stop(self) -> None:
        """Stop the bridge and flush pending data."""
        self._running = False

        # Flush any pending readings
        if self._pending_readings:
            await self._flush_readings()

        if self._client:
            await self._client.aclose()
            self._client = None

        logger.info("Convex bridge stopped")

    async def push_event(self, event: Event) -> bool:
        """
        Push a detector event to Convex.

        Args:
            event: Event from a detector

        Returns:
            True if successful
        """
        if not self._client or not self._running:
            return False

        try:
            # Update detector state
            await self._update_detector_state(event)

            # Add to readings batch
            self._add_reading(event)

            # Flush readings if interval passed
            if time.time() - self._last_flush >= self._config.batch_interval:
                await self._flush_readings()

            return True

        except Exception as e:
            logger.error(f"Failed to push event to Convex: {e}")
            return False

    async def push_alert(
        self,
        alert_id: str,
        level: str,
        source: str,
        message: str,
    ) -> bool:
        """
        Push an alert to Convex.

        Args:
            alert_id: Unique alert identifier
            level: "warning" or "critical"
            source: Detector or component name
            message: Alert message

        Returns:
            True if successful
        """
        if not self._client or not self._running:
            return False

        try:
            await self._mutation("alerts:create", {
                "alertId": alert_id,
                "level": level,
                "source": source,
                "message": message,
            })
            return True

        except Exception as e:
            logger.error(f"Failed to push alert to Convex: {e}")
            return False

    async def update_system_status(
        self,
        component: str,
        status: str,
        message: str | None = None,
    ) -> bool:
        """
        Update system component status.

        Args:
            component: Component name (radar, audio, bcg, engine)
            status: "online", "offline", or "error"
            message: Optional status message

        Returns:
            True if successful
        """
        if not self._client or not self._running:
            return False

        try:
            await self._mutation("system:updateStatus", {
                "component": component,
                "status": status,
                "message": message,
            })
            return True

        except Exception as e:
            logger.error(f"Failed to update system status: {e}")
            return False

    async def _update_detector_state(self, event: Event) -> None:
        """Update detector state in Convex."""
        state_str = self._event_state_to_string(event.state)

        await self._mutation("vitals:updateDetector", {
            "detector": event.detector,
            "state": state_str,
            "confidence": event.confidence,
            "value": event.value,
        })

        # Cache for reference
        self._detector_states[event.detector] = {
            "state": state_str,
            "confidence": event.confidence,
            "value": event.value,
        }

    def _add_reading(self, event: Event) -> None:
        """Add event data to readings batch."""
        reading: dict[str, Any] = {}

        # Extract relevant values based on detector type
        if event.detector == "radar":
            if "respiration_rate" in event.value:
                reading["respirationRate"] = event.value["respiration_rate"]

        elif event.detector == "audio":
            if "breathing_rate" in event.value:
                reading["respirationRate"] = event.value["breathing_rate"]
            if "breathing_amplitude" in event.value:
                reading["breathingAmplitude"] = event.value["breathing_amplitude"]

        elif event.detector == "bcg":
            if "heart_rate" in event.value:
                reading["heartRate"] = event.value["heart_rate"]
            if "bed_occupied" in event.value:
                reading["bedOccupied"] = event.value["bed_occupied"]
            if "signal_quality" in event.value:
                reading["signalQuality"] = event.value["signal_quality"]

        if reading:
            self._pending_readings.append(reading)

    async def _flush_readings(self) -> None:
        """Flush batched readings to Convex."""
        if not self._pending_readings:
            return

        # Merge readings from same time period
        merged = self._merge_readings(self._pending_readings)

        try:
            await self._mutation("vitals:insertReading", merged)
        except Exception as e:
            logger.error(f"Failed to flush readings: {e}")

        self._pending_readings = []
        self._last_flush = time.time()

    def _merge_readings(self, readings: list[dict[str, Any]]) -> dict[str, Any]:
        """Merge multiple readings into one."""
        merged: dict[str, Any] = {}

        for reading in readings:
            for key, value in reading.items():
                if value is not None:
                    # Take latest non-null value
                    merged[key] = value

        return merged

    async def _mutation(self, path: str, args: dict[str, Any]) -> Any:
        """
        Call a Convex mutation.

        Args:
            path: Mutation path (e.g., "vitals:updateDetector")
            args: Mutation arguments

        Returns:
            Mutation result
        """
        if not self._client:
            raise RuntimeError("Client not initialized")

        # Convex local uses a simple HTTP API
        # Format: POST /api/mutation/{path}
        response = await self._client.post(
            f"/api/mutation",
            json={
                "path": path,
                "args": args,
            },
        )

        if response.status_code != 200:
            raise RuntimeError(f"Convex mutation failed: {response.text}")

        return response.json()

    @staticmethod
    def _event_state_to_string(state: EventState) -> str:
        """Convert EventState enum to string."""
        return {
            EventState.NORMAL: "normal",
            EventState.WARNING: "warning",
            EventState.ALERT: "alert",
            EventState.UNCERTAIN: "uncertain",
        }.get(state, "uncertain")


class ConvexEventHandler:
    """
    Event handler that forwards events to Convex.

    Can be attached to detector event callbacks.
    """

    def __init__(self, bridge: ConvexBridge):
        """
        Initialize handler.

        Args:
            bridge: Convex bridge instance
        """
        self._bridge = bridge

    async def __call__(self, event: Event) -> None:
        """Handle an event by pushing to Convex."""
        await self._bridge.push_event(event)
