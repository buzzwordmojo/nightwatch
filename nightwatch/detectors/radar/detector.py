"""
Radar detector implementation for Nightwatch.

Uses HLK-LD2450 mmWave radar for:
- Respiration rate monitoring
- Movement detection
- Heart rate estimation
- Presence detection
"""

from __future__ import annotations

import asyncio
import time
from typing import Any

from nightwatch.core.config import RadarConfig
from nightwatch.core.events import Event, EventState, Publisher
from nightwatch.detectors.base import BaseDetector, CalibrationResult, DetectorStatus
from nightwatch.detectors.radar.ld2450 import LD2450Driver, LD2450Frame, LD2450Target
from nightwatch.detectors.radar.processing import (
    RespirationExtractor,
    HeartRateEstimator,
    MovementDetector,
)


class RadarDetector(BaseDetector):
    """
    mmWave radar detector for respiration, movement, and presence.

    Uses the HLK-LD2450 radar module via serial UART connection.
    Processes radar data to extract vital signs and emit events.
    """

    def __init__(
        self,
        config: RadarConfig | None = None,
        publisher: Publisher | None = None,
    ):
        super().__init__("radar", publisher)

        self._config = config or RadarConfig()
        self._driver: LD2450Driver | None = None

        # Signal processors
        self._respiration = RespirationExtractor(
            sample_rate=self._config.update_rate_hz,
        )
        self._heart_rate = HeartRateEstimator(
            sample_rate=self._config.update_rate_hz,
        )
        self._movement = MovementDetector(
            sample_rate=self._config.update_rate_hz,
        )

        # State tracking
        self._last_target: LD2450Target | None = None
        self._presence = False
        self._no_target_count = 0
        self._frames_processed = 0

        # Calibration baseline
        self._baseline_y: float | None = None

    async def _connect(self) -> None:
        """Connect to radar via serial port."""
        self._driver = LD2450Driver(
            port=self._config.device,
            baud_rate=self._config.baud_rate,
        )
        await self._driver.connect()

    async def _disconnect(self) -> None:
        """Disconnect from radar."""
        if self._driver:
            await self._driver.disconnect()
            self._driver = None

    async def _read_loop(self) -> None:
        """Main loop reading frames from radar and emitting events."""
        if not self._driver:
            raise RuntimeError("Driver not connected")

        # Calculate target interval between events
        target_interval = 1.0 / self._config.update_rate_hz
        last_emit_time = 0.0

        async for frame in self._driver.read_frames():
            if not self._running:
                break

            self._frames_processed += 1

            # Process frame
            self._process_frame(frame)

            # Rate limit event emission
            now = time.time()
            if now - last_emit_time >= target_interval:
                await self._emit_current_state()
                last_emit_time = now

    def _process_frame(self, frame: LD2450Frame) -> None:
        """Process a radar frame and update internal state."""
        if not frame.targets:
            self._no_target_count += 1
            if self._no_target_count > 10:  # ~1 second at 10 Hz
                self._presence = False
            return

        self._no_target_count = 0
        self._presence = True

        # Use the closest target (smallest Y value)
        closest = min(frame.targets, key=lambda t: t.y)
        self._last_target = closest

        # Update signal processors
        timestamp = time.time()

        # Respiration (uses Y position for chest movement)
        self._respiration.update(float(closest.y), timestamp)

        # Heart rate (also from Y position micro-movements)
        self._heart_rate.update(float(closest.y))

        # Movement
        self._movement.update(
            float(closest.x),
            float(closest.y),
            float(closest.speed),
        )

    async def _emit_current_state(self) -> None:
        """Emit an event with current detector state."""
        # Get processed values
        resp_analysis = self._respiration.update(
            float(self._last_target.y) if self._last_target else 0,
            time.time(),
        ) if self._last_target else None

        respiration_rate = resp_analysis.rate_bpm if resp_analysis and resp_analysis.is_valid else None
        respiration_amplitude = resp_analysis.amplitude if resp_analysis else 0.0
        resp_confidence = resp_analysis.confidence if resp_analysis else 0.0

        heart_rate_estimate = self._heart_rate.update(
            float(self._last_target.y) if self._last_target else 0
        )

        movement = self._movement.update(
            float(self._last_target.x) if self._last_target else 0,
            float(self._last_target.y) if self._last_target else 0,
            float(self._last_target.speed) if self._last_target else 0,
        ) if self._last_target else None

        # Determine state
        state = EventState.NORMAL
        confidence = 0.5  # Base confidence

        if not self._presence:
            state = EventState.UNCERTAIN
            confidence = 0.3
        elif respiration_rate is not None:
            confidence = resp_confidence
            if respiration_rate < 6:
                state = EventState.ALERT
            elif respiration_rate < 8:
                state = EventState.WARNING

        # Build event value
        value = {
            "respiration_rate": round(respiration_rate, 1) if respiration_rate else None,
            "respiration_amplitude": round(respiration_amplitude, 2),
            "heart_rate_estimate": round(heart_rate_estimate, 1) if heart_rate_estimate else None,
            "movement": round(movement.level, 2) if movement else 0.0,
            "movement_is_macro": movement.is_macro if movement else False,
            "presence": self._presence,
            "target_distance": round(self._last_target.distance_m, 2) if self._last_target else None,
            "target_angle": round(self._last_target.angle_degrees, 1) if self._last_target else None,
        }

        await self._emit_event(state, confidence, value)

    async def _calibrate_impl(self) -> CalibrationResult:
        """
        Calibrate radar detector.

        Establishes baseline Y position and optimal sensitivity.
        Should be run when subject is lying still in normal position.
        """
        if not self._driver:
            return CalibrationResult(
                success=False,
                message="Radar not connected",
            )

        start_time = time.time()
        y_samples: list[float] = []
        calibration_duration = 10.0  # seconds

        # Collect samples
        async for frame in self._driver.read_frames():
            elapsed = time.time() - start_time
            if elapsed >= calibration_duration:
                break

            if frame.targets:
                closest = min(frame.targets, key=lambda t: t.y)
                y_samples.append(float(closest.y))

        if len(y_samples) < 50:
            return CalibrationResult(
                success=False,
                message="Not enough samples collected. Ensure subject is in view.",
                duration_seconds=time.time() - start_time,
            )

        # Calculate baseline
        import numpy as np

        baseline_y = float(np.median(y_samples))
        y_std = float(np.std(y_samples))

        self._baseline_y = baseline_y

        # Reset processors with new baseline
        self._respiration.reset()
        self._heart_rate.reset()
        self._movement.reset()

        return CalibrationResult(
            success=True,
            message=f"Calibration complete. Subject detected at {baseline_y/1000:.2f}m",
            baseline_values={
                "y_position": baseline_y,
                "y_std": y_std,
            },
            recommended_settings={
                "sensitivity": min(1.0, self._config.sensitivity * (10 / y_std)) if y_std > 0 else 0.8,
            },
            duration_seconds=time.time() - start_time,
        )

    def _get_detector_specific_state(self) -> dict[str, Any]:
        """Get radar-specific state information."""
        return {
            "device": self._config.device,
            "model": self._config.model,
            "frames_processed": self._frames_processed,
            "presence_detected": self._presence,
            "last_target_distance": self._last_target.distance_m if self._last_target else None,
            "baseline_y": self._baseline_y,
            "current_respiration_rate": self._respiration.get_rate(),
        }


class MockRadarDetector(RadarDetector):
    """
    Mock radar detector for testing without hardware.

    Generates synthetic radar data that mimics real sensor behavior.
    """

    def __init__(
        self,
        config: RadarConfig | None = None,
        publisher: Publisher | None = None,
        base_respiration_rate: float = 14.0,
        base_distance: float = 1.5,
    ):
        super().__init__(config, publisher)
        self._base_respiration_rate = base_respiration_rate
        self._base_distance = base_distance
        self._time_offset = 0.0

        # Anomaly injection
        self._anomaly_type: str | None = None
        self._anomaly_start: float | None = None
        self._anomaly_duration: float = 0.0

    async def _connect(self) -> None:
        """Mock connection."""
        await asyncio.sleep(0.1)

    async def _disconnect(self) -> None:
        """Mock disconnection."""
        pass

    async def _read_loop(self) -> None:
        """Generate synthetic radar data."""
        import math
        import random

        interval = 1.0 / self._config.update_rate_hz
        self._time_offset = time.time()

        while self._running:
            now = time.time()
            t = now - self._time_offset

            # Base Y position (distance) with breathing modulation
            # Breathing causes ~10mm chest movement
            breath_freq = self._base_respiration_rate / 60.0  # Hz
            breath_amplitude = 10.0  # mm

            # Check for anomaly
            if self._anomaly_type and self._anomaly_start:
                elapsed = now - self._anomaly_start
                if elapsed < self._anomaly_duration:
                    if self._anomaly_type == "apnea":
                        breath_amplitude *= 0.1  # Almost no breathing
                else:
                    self._anomaly_type = None

            y_base = self._base_distance * 1000  # Convert to mm
            y_breath = breath_amplitude * math.sin(2 * math.pi * breath_freq * t)
            y_noise = random.gauss(0, 1)  # Small noise

            y = y_base + y_breath + y_noise

            # X position (mostly stable with small noise)
            x = random.gauss(0, 10)

            # Speed (mostly 0 with small variations)
            speed = random.gauss(0, 2)

            # Create mock target
            mock_target = LD2450Target(
                x=int(x),
                y=int(y),
                speed=int(speed),
                resolution=100,
            )
            self._last_target = mock_target
            self._presence = True

            # Update processors
            self._respiration.update(float(y), now)
            self._heart_rate.update(float(y))
            self._movement.update(float(x), float(y), float(speed))

            self._frames_processed += 1

            # Emit event
            await self._emit_current_state()

            await asyncio.sleep(interval)

    async def _emit_current_state(self) -> None:
        """Emit mock event with configured values directly (no signal processing)."""
        import random

        # Check for active anomaly
        respiration_rate = self._base_respiration_rate
        if self._anomaly_type == "apnea" and self._anomaly_start:
            elapsed = time.time() - self._anomaly_start
            if elapsed < self._anomaly_duration:
                respiration_rate = 0.0

        # Add small noise for realism
        if respiration_rate > 0:
            respiration_rate += random.gauss(0, 0.5)
            respiration_rate = max(0, respiration_rate)

        # Determine state based on rate
        state = EventState.NORMAL
        confidence = 0.9

        if respiration_rate < 6:
            state = EventState.ALERT
        elif respiration_rate < 8:
            state = EventState.WARNING

        value = {
            "respiration_rate": round(respiration_rate, 1),
            "respiration_amplitude": 0.8,
            "heart_rate_estimate": None,
            "movement": round(random.random() * 0.2, 2),
            "movement_is_macro": False,
            "presence": True,
            "target_distance": round(self._base_distance, 2),
            "target_angle": 0.0,
        }

        await self._emit_event(state, confidence, value)

    def inject_anomaly(self, anomaly_type: str, duration: float) -> None:
        """
        Inject an anomaly into the mock data.

        Args:
            anomaly_type: "apnea" to simulate breathing stop
            duration: Duration in seconds
        """
        self._anomaly_type = anomaly_type
        self._anomaly_start = time.time()
        self._anomaly_duration = duration
