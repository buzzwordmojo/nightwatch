"""
Base detector interface for Nightwatch.

All detectors (radar, audio, BCG, etc.) inherit from BaseDetector
and implement the same interface for consistency.
"""

from __future__ import annotations

import asyncio
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Awaitable

from nightwatch.core.events import Event, EventState, Publisher


class DetectorStatus(str, Enum):
    """Operational status of a detector."""

    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    CALIBRATING = "calibrating"
    ERROR = "error"
    DISCONNECTED = "disconnected"


@dataclass
class DetectorState:
    """Current state of a detector."""

    status: DetectorStatus
    connected: bool = False
    last_event_time: float | None = None
    error_message: str | None = None
    events_emitted: int = 0
    uptime_seconds: float = 0.0
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class CalibrationResult:
    """Result of detector calibration."""

    success: bool
    message: str
    baseline_values: dict[str, float] = field(default_factory=dict)
    recommended_settings: dict[str, Any] = field(default_factory=dict)
    duration_seconds: float = 0.0


class BaseDetector(ABC):
    """
    Abstract base class for all Nightwatch detectors.

    Detectors are responsible for:
    1. Connecting to hardware (serial port, USB device, GPIO, etc.)
    2. Processing raw sensor data
    3. Emitting standardized Event objects
    4. Providing calibration routines
    5. Reporting health status

    Each detector runs as an independent process and communicates
    via ZeroMQ pub/sub.
    """

    def __init__(self, name: str, publisher: Publisher | None = None):
        """
        Initialize detector.

        Args:
            name: Unique detector identifier (e.g., "radar", "audio", "bcg")
            publisher: ZeroMQ publisher for emitting events
        """
        self._name = name
        self._publisher = publisher
        self._status = DetectorStatus.STOPPED
        self._connected = False
        self._start_time: float | None = None
        self._last_event_time: float | None = None
        self._events_emitted = 0
        self._error_message: str | None = None
        self._sequence = 0
        self._session_id = ""
        self._running = False

        # Callbacks
        self._on_event: Callable[[Event], Awaitable[None]] | None = None
        self._on_error: Callable[[Exception], Awaitable[None]] | None = None

    @property
    def name(self) -> str:
        """Unique detector identifier."""
        return self._name

    @property
    def status(self) -> DetectorStatus:
        """Current operational status."""
        return self._status

    @property
    def is_running(self) -> bool:
        """Whether detector is actively running."""
        return self._running and self._status == DetectorStatus.RUNNING

    def set_publisher(self, publisher: Publisher) -> None:
        """Set the ZeroMQ publisher for event emission."""
        self._publisher = publisher

    def set_session_id(self, session_id: str) -> None:
        """Set the monitoring session ID for all emitted events."""
        self._session_id = session_id

    def set_on_event(self, callback: Callable[[Event], Awaitable[None]]) -> None:
        """Set callback for when events are emitted (for local handling)."""
        self._on_event = callback

    def set_on_error(self, callback: Callable[[Exception], Awaitable[None]]) -> None:
        """Set callback for when errors occur."""
        self._on_error = callback

    # ========================================================================
    # Abstract Methods (must be implemented by subclasses)
    # ========================================================================

    @abstractmethod
    async def _connect(self) -> None:
        """
        Connect to hardware.

        Raises:
            ConnectionError: If connection fails
        """
        pass

    @abstractmethod
    async def _disconnect(self) -> None:
        """Disconnect from hardware."""
        pass

    @abstractmethod
    async def _read_loop(self) -> None:
        """
        Main read loop that processes sensor data and emits events.

        This method should run continuously until self._running is False.
        Use await asyncio.sleep() to control update rate.
        """
        pass

    @abstractmethod
    async def _calibrate_impl(self) -> CalibrationResult:
        """
        Perform hardware-specific calibration.

        Returns:
            CalibrationResult with calibration outcome
        """
        pass

    @abstractmethod
    def _get_detector_specific_state(self) -> dict[str, Any]:
        """
        Get detector-specific state information.

        Returns:
            Dictionary with detector-specific status info
        """
        pass

    # ========================================================================
    # Public Methods
    # ========================================================================

    async def start(self) -> None:
        """Start the detector."""
        if self._running:
            return

        self._status = DetectorStatus.STARTING
        self._error_message = None

        try:
            await self._connect()
            self._connected = True
            self._start_time = time.time()
            self._running = True
            self._status = DetectorStatus.RUNNING

            # Start read loop
            asyncio.create_task(self._run_read_loop())

        except Exception as e:
            self._status = DetectorStatus.ERROR
            self._error_message = str(e)
            self._connected = False
            raise

    async def stop(self) -> None:
        """Stop the detector."""
        self._running = False

        try:
            await self._disconnect()
        except Exception:
            pass  # Best effort disconnect

        self._connected = False
        self._status = DetectorStatus.STOPPED

    async def calibrate(self) -> CalibrationResult:
        """
        Run calibration routine.

        This temporarily pauses normal operation, performs calibration,
        and returns results with recommended settings.
        """
        was_running = self._running
        old_status = self._status

        try:
            self._status = DetectorStatus.CALIBRATING
            if not self._connected:
                await self._connect()
                self._connected = True

            result = await self._calibrate_impl()
            return result

        finally:
            self._status = old_status if was_running else DetectorStatus.STOPPED

    def get_state(self) -> DetectorState:
        """Get current detector state."""
        uptime = 0.0
        if self._start_time:
            uptime = time.time() - self._start_time

        return DetectorState(
            status=self._status,
            connected=self._connected,
            last_event_time=self._last_event_time,
            error_message=self._error_message,
            events_emitted=self._events_emitted,
            uptime_seconds=uptime,
            extra=self._get_detector_specific_state(),
        )

    # ========================================================================
    # Protected Methods (for use by subclasses)
    # ========================================================================

    async def _emit_event(
        self,
        state: EventState,
        confidence: float,
        value: dict[str, Any],
    ) -> Event:
        """
        Emit an event.

        Args:
            state: Event state (normal, warning, alert, etc.)
            confidence: Detection confidence 0.0-1.0
            value: Detector-specific event data

        Returns:
            The emitted Event
        """
        self._sequence += 1

        event = Event(
            detector=self._name,
            timestamp=time.time(),
            confidence=confidence,
            state=state,
            value=value,
            sequence=self._sequence,
            session_id=self._session_id,
        )

        # Publish via ZeroMQ
        if self._publisher:
            await self._publisher.send(event)

        # Local callback
        if self._on_event:
            await self._on_event(event)

        self._last_event_time = event.timestamp
        self._events_emitted += 1

        return event

    async def _handle_error(self, error: Exception) -> None:
        """Handle an error during operation."""
        self._error_message = str(error)

        if self._on_error:
            await self._on_error(error)

    async def _run_read_loop(self) -> None:
        """Wrapper around read loop with error handling."""
        try:
            await self._read_loop()
        except Exception as e:
            self._status = DetectorStatus.ERROR
            await self._handle_error(e)


class MockDetector(BaseDetector):
    """
    Mock detector for testing and development.

    Generates synthetic events with configurable parameters.
    Useful for testing the alert engine and dashboard without hardware.
    """

    def __init__(
        self,
        name: str = "mock",
        publisher: Publisher | None = None,
        update_rate_hz: float = 10.0,
        base_respiration_rate: float = 14.0,
        base_heart_rate: float = 70.0,
        noise_level: float = 0.1,
    ):
        super().__init__(name, publisher)
        self._update_rate_hz = update_rate_hz
        self._base_respiration_rate = base_respiration_rate
        self._base_heart_rate = base_heart_rate
        self._noise_level = noise_level

        # Anomaly injection
        self._inject_anomaly: str | None = None
        self._anomaly_start: float | None = None
        self._anomaly_duration: float = 0

    async def _connect(self) -> None:
        """Mock connection always succeeds."""
        await asyncio.sleep(0.1)  # Simulate connection time

    async def _disconnect(self) -> None:
        """Mock disconnection."""
        pass

    async def _read_loop(self) -> None:
        """Generate synthetic events."""
        import random

        interval = 1.0 / self._update_rate_hz

        while self._running:
            # Add noise to base values
            noise_r = random.gauss(0, self._noise_level * 2)
            noise_h = random.gauss(0, self._noise_level * 5)

            respiration_rate = self._base_respiration_rate + noise_r
            heart_rate = self._base_heart_rate + noise_h
            movement = random.random() * 0.3

            # Check for active anomaly
            if self._inject_anomaly and self._anomaly_start:
                elapsed = time.time() - self._anomaly_start
                if elapsed < self._anomaly_duration:
                    if self._inject_anomaly == "apnea":
                        respiration_rate = max(0, respiration_rate * 0.2)
                    elif self._inject_anomaly == "bradycardia":
                        heart_rate = max(30, heart_rate * 0.5)
                    elif self._inject_anomaly == "seizure":
                        movement = min(1.0, movement + 0.7)
                else:
                    self._inject_anomaly = None

            # Determine state
            state = EventState.NORMAL
            if respiration_rate < 8:
                state = EventState.WARNING
            if respiration_rate < 5:
                state = EventState.ALERT

            await self._emit_event(
                state=state,
                confidence=0.9,
                value={
                    "respiration_rate": round(respiration_rate, 1),
                    "heart_rate": round(heart_rate, 1),
                    "movement": round(movement, 2),
                    "presence": True,
                },
            )

            await asyncio.sleep(interval)

    async def _calibrate_impl(self) -> CalibrationResult:
        """Mock calibration."""
        await asyncio.sleep(1.0)  # Simulate calibration time
        return CalibrationResult(
            success=True,
            message="Mock calibration complete",
            baseline_values={
                "respiration_rate": self._base_respiration_rate,
                "heart_rate": self._base_heart_rate,
            },
            duration_seconds=1.0,
        )

    def _get_detector_specific_state(self) -> dict[str, Any]:
        return {
            "update_rate_hz": self._update_rate_hz,
            "base_respiration_rate": self._base_respiration_rate,
            "base_heart_rate": self._base_heart_rate,
            "active_anomaly": self._inject_anomaly,
        }

    def inject_anomaly(self, anomaly_type: str, duration: float) -> None:
        """
        Inject an anomaly into the mock data.

        Args:
            anomaly_type: "apnea", "bradycardia", or "seizure"
            duration: How long the anomaly should last (seconds)
        """
        self._inject_anomaly = anomaly_type
        self._anomaly_start = time.time()
        self._anomaly_duration = duration
