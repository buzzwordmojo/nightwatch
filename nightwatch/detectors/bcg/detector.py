"""
BCG detector for Nightwatch.

Uses a piezoelectric sensor under the mattress to detect heart rate,
heart rate variability, and respiration from ballistocardiography signals.
"""

from __future__ import annotations

import asyncio
import time
from typing import Any

import numpy as np

from nightwatch.core.config import BCGConfig
from nightwatch.core.events import EventState, Publisher
from nightwatch.detectors.base import BaseDetector, CalibrationResult
from nightwatch.detectors.bcg.processing import (
    BCGProcessor,
    BCGProcessorConfig,
    BCGAnalysis,
)


class BCGDetector(BaseDetector):
    """
    Detect heart rate and respiration via BCG sensor.

    Uses a piezoelectric film sensor under the mattress connected
    to an ADC (MCP3008) via SPI. The sensor picks up micro-vibrations
    from heartbeats and breathing.

    Event value format:
    {
        "heart_rate": float | None,           # BPM (accurate)
        "heart_rate_variability": float | None,  # RMSSD in ms
        "respiration_rate": float | None,     # BPM
        "bed_occupied": bool,
        "signal_quality": float,              # 0-1
        "movement_detected": bool,
    }
    """

    def __init__(
        self,
        config: BCGConfig | None = None,
        publisher: Publisher | None = None,
    ):
        """
        Initialize BCG detector.

        Args:
            config: BCG configuration, or None for defaults
            publisher: ZeroMQ publisher for events
        """
        super().__init__("bcg", publisher)

        self._config = config or BCGConfig()

        # Processing
        proc_config = BCGProcessorConfig(
            sample_rate=self._config.sample_rate,
        )
        self._processor = BCGProcessor(proc_config)

        # SPI interface for MCP3008 ADC
        self._spi = None
        self._adc_channel = self._config.adc_channel

        # State
        self._last_analysis: BCGAnalysis | None = None
        self._calibrated = False
        self._baseline_amplitude = 0.0

    async def _connect(self) -> None:
        """Connect to BCG sensor via SPI."""
        try:
            import spidev
        except ImportError:
            raise ConnectionError(
                "spidev not installed. Run: pip install spidev"
            )

        try:
            self._spi = spidev.SpiDev()
            self._spi.open(0, 0)  # Bus 0, Device 0 (CE0)
            self._spi.max_speed_hz = 1000000  # 1 MHz
            self._spi.mode = 0
        except Exception as e:
            raise ConnectionError(f"Failed to open SPI: {e}")

    async def _disconnect(self) -> None:
        """Close SPI connection."""
        if self._spi is not None:
            try:
                self._spi.close()
            except Exception:
                pass
            self._spi = None

    def _read_adc(self) -> int:
        """
        Read value from MCP3008 ADC.

        Returns:
            10-bit ADC value (0-1023)
        """
        if self._spi is None:
            return 512  # Mid-scale if not connected

        # MCP3008 SPI protocol
        # Send: 0x01 (start bit), (0x80 | channel << 4), 0x00
        # Receive: ignore, 2 bits, 8 bits of data
        channel = self._adc_channel
        cmd = [1, (8 + channel) << 4, 0]

        response = self._spi.xfer2(cmd)

        # Extract 10-bit value
        value = ((response[1] & 3) << 8) | response[2]
        return value

    async def _read_loop(self) -> None:
        """Read BCG data and emit events."""
        sample_period = 1.0 / self._config.sample_rate
        emit_interval = 1.0 / self._config.update_rate_hz

        buffer = []
        buffer_start_time = time.time()
        last_emit = time.time()

        while self._running:
            try:
                # Read ADC sample
                value = self._read_adc()

                # Normalize to -1 to 1 (assuming mid-scale is rest)
                normalized = (value - 512) / 512.0
                buffer.append(normalized)

                # Check if we have enough samples for processing
                current_time = time.time()
                buffer_duration = current_time - buffer_start_time

                if buffer_duration >= 0.1:  # Process every 100ms
                    signal = np.array(buffer, dtype=np.float32)
                    analysis = self._processor.process(signal, buffer_start_time)
                    self._last_analysis = analysis

                    # Reset buffer
                    buffer = []
                    buffer_start_time = current_time

                # Emit at configured rate
                if current_time - last_emit >= emit_interval:
                    if self._last_analysis:
                        await self._emit_analysis(self._last_analysis)
                    last_emit = current_time

                # Maintain sample rate
                await asyncio.sleep(sample_period)

            except Exception as e:
                await self._handle_error(e)
                await asyncio.sleep(0.1)

    async def _emit_analysis(self, analysis: BCGAnalysis) -> None:
        """Emit event based on BCG analysis."""
        # Determine state
        state = EventState.NORMAL

        if not analysis.bed_occupied:
            state = EventState.UNCERTAIN
        elif analysis.movement_detected:
            state = EventState.UNCERTAIN
        elif analysis.heart_rate is not None:
            # Check for concerning heart rate
            if analysis.heart_rate < 40 or analysis.heart_rate > 150:
                state = EventState.WARNING
            if analysis.heart_rate < 30 or analysis.heart_rate > 180:
                state = EventState.ALERT

        # Confidence based on signal quality
        confidence = analysis.signal_quality

        await self._emit_event(
            state=state,
            confidence=confidence,
            value={
                "heart_rate": round(analysis.heart_rate, 1) if analysis.heart_rate else None,
                "heart_rate_variability": round(analysis.heart_rate_variability, 1)
                if analysis.heart_rate_variability
                else None,
                "respiration_rate": round(analysis.respiration_rate, 1)
                if analysis.respiration_rate
                else None,
                "bed_occupied": analysis.bed_occupied,
                "signal_quality": round(analysis.signal_quality, 2),
                "movement_detected": analysis.movement_detected,
            },
        )

    async def _calibrate_impl(self) -> CalibrationResult:
        """
        Calibrate BCG sensor.

        Measures baseline signal when bed is empty and occupied.
        """
        start_time = time.time()
        empty_samples = []
        occupied_samples = []

        # Phase 1: Measure empty bed (5 seconds)
        phase_start = time.time()
        while time.time() - phase_start < 5.0:
            value = self._read_adc()
            empty_samples.append(value)
            await asyncio.sleep(1.0 / self._config.sample_rate)

        # Phase 2: Wait for bed to be occupied
        # (In real implementation, would prompt user)
        await asyncio.sleep(2.0)

        # Phase 3: Measure occupied bed (5 seconds)
        phase_start = time.time()
        while time.time() - phase_start < 5.0:
            value = self._read_adc()
            occupied_samples.append(value)
            await asyncio.sleep(1.0 / self._config.sample_rate)

        if not empty_samples or not occupied_samples:
            return CalibrationResult(
                success=False,
                message="Insufficient samples for calibration",
            )

        # Calculate baselines
        empty_std = float(np.std(empty_samples))
        occupied_std = float(np.std(occupied_samples))
        self._baseline_amplitude = empty_std

        # Occupancy threshold should be between empty and occupied
        recommended_threshold = (empty_std + occupied_std) / 2

        self._calibrated = True

        return CalibrationResult(
            success=True,
            message=f"Calibration complete. Empty noise: {empty_std:.4f}, Occupied: {occupied_std:.4f}",
            baseline_values={
                "empty_noise": empty_std,
                "occupied_signal": occupied_std,
            },
            recommended_settings={
                "occupancy_threshold": recommended_threshold,
            },
            duration_seconds=time.time() - start_time,
        )

    def _get_detector_specific_state(self) -> dict[str, Any]:
        """Get BCG detector state."""
        return {
            "sample_rate": self._config.sample_rate,
            "adc_channel": self._adc_channel,
            "calibrated": self._calibrated,
            "baseline_amplitude": self._baseline_amplitude,
            "last_analysis": {
                "heart_rate": self._last_analysis.heart_rate,
                "bed_occupied": self._last_analysis.bed_occupied,
                "signal_quality": self._last_analysis.signal_quality,
            }
            if self._last_analysis
            else None,
        }


class MockBCGDetector(BaseDetector):
    """
    Mock BCG detector for testing.

    Generates synthetic heart rate and respiration data
    without requiring actual hardware.
    """

    def __init__(
        self,
        publisher: Publisher | None = None,
        update_rate_hz: float = 10.0,
        base_heart_rate: float = 70.0,
        base_respiration_rate: float = 14.0,
        noise_level: float = 0.1,
    ):
        """
        Initialize mock BCG detector.

        Args:
            publisher: ZeroMQ publisher
            update_rate_hz: Event emission rate
            base_heart_rate: Simulated heart rate BPM
            base_respiration_rate: Simulated respiration rate BPM
            noise_level: Amount of noise to add
        """
        super().__init__("bcg", publisher)

        self._update_rate_hz = update_rate_hz
        self._base_heart_rate = base_heart_rate
        self._base_respiration_rate = base_respiration_rate
        self._noise_level = noise_level

        # State
        self._bed_occupied = True
        self._movement = False
        self._inject_bradycardia = False
        self._inject_tachycardia = False

        # Simulated HRV
        self._hrv_intervals: list[float] = []

    async def _connect(self) -> None:
        """Mock connection."""
        await asyncio.sleep(0.05)

    async def _disconnect(self) -> None:
        """Mock disconnect."""
        pass

    async def _read_loop(self) -> None:
        """Generate synthetic BCG events."""
        import random

        interval = 1.0 / self._update_rate_hz

        while self._running:
            # Add noise to base values
            hr_noise = random.gauss(0, self._noise_level * 5)
            resp_noise = random.gauss(0, self._noise_level * 2)

            heart_rate = self._base_heart_rate + hr_noise
            resp_rate = self._base_respiration_rate + resp_noise

            # Handle injected anomalies
            if self._inject_bradycardia:
                heart_rate = max(25, heart_rate * 0.4)
            elif self._inject_tachycardia:
                heart_rate = min(200, heart_rate * 2)

            # Simulate HRV
            hrv = random.gauss(40, 10)  # RMSSD typically 20-60ms
            hrv = max(10, min(100, hrv))

            # Determine state
            state = EventState.NORMAL
            signal_quality = 0.9

            if not self._bed_occupied:
                state = EventState.UNCERTAIN
                signal_quality = 0.0
                heart_rate = None
                resp_rate = None
                hrv = None
            elif self._movement:
                state = EventState.UNCERTAIN
                signal_quality = 0.3
            elif heart_rate and (heart_rate < 40 or heart_rate > 150):
                state = EventState.WARNING
            elif heart_rate and (heart_rate < 30 or heart_rate > 180):
                state = EventState.ALERT

            await self._emit_event(
                state=state,
                confidence=signal_quality,
                value={
                    "heart_rate": round(heart_rate, 1) if heart_rate else None,
                    "heart_rate_variability": round(hrv, 1) if hrv else None,
                    "respiration_rate": round(resp_rate, 1) if resp_rate else None,
                    "bed_occupied": self._bed_occupied,
                    "signal_quality": round(signal_quality, 2),
                    "movement_detected": self._movement,
                },
            )

            await asyncio.sleep(interval)

    async def _calibrate_impl(self) -> CalibrationResult:
        """Mock calibration."""
        await asyncio.sleep(1.0)
        return CalibrationResult(
            success=True,
            message="Mock BCG calibration complete",
            baseline_values={
                "empty_noise": 0.005,
                "occupied_signal": 0.05,
            },
            duration_seconds=1.0,
        )

    def _get_detector_specific_state(self) -> dict[str, Any]:
        """Get mock state."""
        return {
            "mock": True,
            "base_heart_rate": self._base_heart_rate,
            "bed_occupied": self._bed_occupied,
        }

    def set_bed_occupied(self, occupied: bool) -> None:
        """Set bed occupancy state."""
        self._bed_occupied = occupied

    def set_movement(self, moving: bool) -> None:
        """Set movement state."""
        self._movement = moving

    def inject_bradycardia(self, enable: bool = True) -> None:
        """Inject low heart rate."""
        self._inject_bradycardia = enable
        self._inject_tachycardia = False

    def inject_tachycardia(self, enable: bool = True) -> None:
        """Inject high heart rate."""
        self._inject_tachycardia = enable
        self._inject_bradycardia = False
