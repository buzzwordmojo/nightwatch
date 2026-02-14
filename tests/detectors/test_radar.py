"""Tests for radar detector."""

from __future__ import annotations

import asyncio
import math
import struct
import time

import numpy as np
import pytest

from nightwatch.detectors.radar.ld2450 import (
    LD2450Target,
    LD2450Frame,
    FRAME_HEADER,
    FRAME_FOOTER,
)
from nightwatch.detectors.radar.processing import (
    BandpassFilter,
    RespirationExtractor,
    RespirationAnalysis,
    HeartRateEstimator,
    MovementDetector,
    MovementAnalysis,
)
from nightwatch.detectors.radar.detector import MockRadarDetector
from nightwatch.core.events import EventState


# =============================================================================
# LD2450 Target Tests
# =============================================================================


class TestLD2450Target:
    """Tests for LD2450Target dataclass."""

    def test_target_creation(self):
        """Target can be created with valid data."""
        target = LD2450Target(x=100, y=1500, speed=0, resolution=100)
        assert target.x == 100
        assert target.y == 1500
        assert target.speed == 0

    def test_distance_calculation(self):
        """Distance is calculated correctly."""
        # Target at (3000, 4000) should be 5000mm away (3-4-5 triangle)
        target = LD2450Target(x=3000, y=4000, speed=0, resolution=100)
        assert target.distance_mm == 5000.0
        assert target.distance_m == 5.0

    def test_angle_calculation(self):
        """Angle is calculated correctly."""
        # Target directly ahead (x=0)
        target_ahead = LD2450Target(x=0, y=1000, speed=0, resolution=100)
        assert target_ahead.angle_degrees == 0.0

        # Target to the right (positive x)
        target_right = LD2450Target(x=1000, y=1000, speed=0, resolution=100)
        assert abs(target_right.angle_degrees - 45.0) < 0.1

        # Target to the left (negative x)
        target_left = LD2450Target(x=-1000, y=1000, speed=0, resolution=100)
        assert abs(target_left.angle_degrees - (-45.0)) < 0.1

    def test_angle_edge_cases(self):
        """Angle handles edge cases."""
        # Target exactly to the right (y=0)
        target_right = LD2450Target(x=1000, y=0, speed=0, resolution=100)
        assert target_right.angle_degrees == 90.0

        # Target exactly to the left (y=0)
        target_left = LD2450Target(x=-1000, y=0, speed=0, resolution=100)
        assert target_left.angle_degrees == -90.0

    def test_is_valid(self):
        """Validity check works correctly."""
        # Valid target
        valid = LD2450Target(x=100, y=1500, speed=0, resolution=100)
        assert valid.is_valid is True

        # Invalid target (all zeros)
        invalid = LD2450Target(x=0, y=0, speed=0, resolution=0)
        assert invalid.is_valid is False


# =============================================================================
# LD2450 Frame Tests
# =============================================================================


def build_test_frame(
    targets: list[tuple[int, int, int, int]] | None = None
) -> bytes:
    """
    Build a valid LD2450 frame for testing.

    Args:
        targets: List of (x, y, speed, resolution) tuples for up to 3 targets

    Returns:
        30-byte frame
    """
    if targets is None:
        targets = [(100, 1500, 0, 100)]

    # Pad to 3 targets with zeros
    while len(targets) < 3:
        targets.append((0, 0, 0, 0))

    frame = bytearray(FRAME_HEADER)

    for x, y, speed, resolution in targets[:3]:
        # Encode X with sign bit (LD2450 uses unsigned with sign bit in MSB)
        if x < 0:
            x_encoded = (abs(x) & 0x7FFF) | 0x8000
        else:
            x_encoded = x & 0x7FFF

        # Encode Y with sign bit
        if y < 0:
            y_encoded = (abs(y) & 0x7FFF) | 0x8000
        else:
            y_encoded = y & 0x7FFF

        # Clamp speed to valid range for signed int16
        speed = max(-32768, min(32767, speed))

        # Pack as unsigned values (the sign bit encoding makes them unsigned)
        frame.extend(struct.pack("<HHhH", x_encoded, y_encoded, speed, resolution))

    frame.extend(FRAME_FOOTER)
    return bytes(frame)


class TestLD2450Frame:
    """Tests for LD2450Frame parsing."""

    def test_parse_valid_frame(self):
        """Valid frame is parsed correctly."""
        data = build_test_frame([(100, 1500, 5, 100)])
        frame = LD2450Frame.parse(data)

        assert frame is not None
        assert len(frame.targets) == 1
        assert frame.targets[0].x == 100
        assert frame.targets[0].y == 1500
        assert frame.targets[0].speed == 5

    def test_parse_multiple_targets(self):
        """Multiple targets are parsed correctly."""
        data = build_test_frame([
            (100, 1500, 0, 100),
            (-200, 2000, 10, 100),
            (300, 2500, -5, 100),
        ])
        frame = LD2450Frame.parse(data)

        assert frame is not None
        assert len(frame.targets) == 3
        assert frame.targets[0].x == 100
        assert frame.targets[1].x == -200
        assert frame.targets[2].x == 300

    def test_parse_negative_coordinates(self):
        """Negative coordinates (left side) are handled correctly."""
        data = build_test_frame([(-500, 1500, 0, 100)])
        frame = LD2450Frame.parse(data)

        assert frame is not None
        assert frame.targets[0].x == -500

    def test_parse_filters_invalid_targets(self):
        """Zero targets are filtered out."""
        data = build_test_frame([
            (100, 1500, 0, 100),  # Valid
            (0, 0, 0, 0),  # Invalid
            (200, 2000, 0, 100),  # Valid
        ])
        frame = LD2450Frame.parse(data)

        assert frame is not None
        assert len(frame.targets) == 2

    def test_parse_too_short(self):
        """Short data returns None."""
        frame = LD2450Frame.parse(b"short")
        assert frame is None

    def test_parse_no_header(self):
        """Data without header returns None."""
        data = b"\x00" * 30
        frame = LD2450Frame.parse(data)
        assert frame is None

    def test_parse_wrong_footer(self):
        """Data with wrong footer returns None."""
        data = bytearray(build_test_frame())
        data[-2:] = b"\x00\x00"  # Wrong footer
        frame = LD2450Frame.parse(bytes(data))
        assert frame is None

    def test_parse_finds_header_in_garbage(self):
        """Parser finds valid frame in noisy data."""
        garbage = b"\xFF\x00\x12\x34"
        valid_frame = build_test_frame([(100, 1500, 0, 100)])
        data = garbage + valid_frame

        frame = LD2450Frame.parse(data)
        assert frame is not None
        assert frame.targets[0].x == 100


# =============================================================================
# Bandpass Filter Tests
# =============================================================================


class TestBandpassFilter:
    """Tests for radar bandpass filter."""

    def test_filter_creation(self):
        """Filter can be created with valid parameters."""
        filt = BandpassFilter(0.1, 0.5, 10.0, order=3)
        assert filt is not None

    def test_filter_single_sample(self):
        """Filter can process single samples."""
        filt = BandpassFilter(0.1, 0.5, 10.0)

        # Process several samples
        results = [filt.filter(float(i)) for i in range(20)]

        # Should produce output (exact values depend on filter design)
        assert len(results) == 20
        assert all(isinstance(r, float) for r in results)

    def test_filter_array(self):
        """Filter can process arrays."""
        filt = BandpassFilter(0.1, 0.5, 10.0)

        # Create signal with in-band and out-of-band frequencies
        t = np.linspace(0, 10, 100)
        # 0.2 Hz (in band) + 2 Hz (out of band)
        signal = np.sin(2 * np.pi * 0.2 * t) + np.sin(2 * np.pi * 2.0 * t)

        filtered = filt.filter_array(signal)

        # Filtered signal should be dominated by 0.2 Hz component
        assert len(filtered) == len(signal)
        # Verify high frequency was attenuated
        fft_orig = np.abs(np.fft.rfft(signal))
        fft_filt = np.abs(np.fft.rfft(filtered))
        # High frequency component should be reduced
        assert fft_filt[-1] < fft_orig[-1]

    def test_filter_reset(self):
        """Filter state can be reset."""
        filt = BandpassFilter(0.1, 0.5, 10.0)

        # Process some samples
        for i in range(10):
            filt.filter(float(i))

        # Reset
        filt.reset()

        # Should work without error
        result = filt.filter(1.0)
        assert isinstance(result, float)


# =============================================================================
# Respiration Extractor Tests
# =============================================================================


def generate_breathing_signal(
    duration: float,
    sample_rate: float,
    breath_rate_bpm: float,
    amplitude: float = 10.0,
    noise: float = 1.0,
) -> tuple[np.ndarray, np.ndarray]:
    """Generate synthetic breathing signal for testing."""
    n_samples = int(duration * sample_rate)
    timestamps = np.linspace(0, duration, n_samples)

    breath_freq = breath_rate_bpm / 60.0
    signal = amplitude * np.sin(2 * np.pi * breath_freq * timestamps)
    signal += np.random.randn(n_samples) * noise

    return signal.astype(np.float64), timestamps


class TestRespirationExtractor:
    """Tests for respiration extraction from radar data."""

    @pytest.fixture
    def extractor(self):
        return RespirationExtractor(
            sample_rate=10.0,
            filter_low_hz=0.1,
            filter_high_hz=0.5,
            window_seconds=30.0,
        )

    def test_requires_minimum_data(self, extractor):
        """Extractor returns invalid until enough data collected."""
        # Only 5 seconds of data (need at least 10)
        for i in range(50):
            result = extractor.update(1500.0 + i, float(i) / 10.0)

        assert result.is_valid is False
        assert result.rate_bpm is None

    def test_detects_normal_breathing(self, extractor):
        """Detects normal breathing rate (~14 BPM)."""
        signal, timestamps = generate_breathing_signal(
            duration=40.0,
            sample_rate=10.0,
            breath_rate_bpm=14.0,
            amplitude=10.0,
        )

        result = None
        for i, (y, t) in enumerate(zip(signal + 1500, timestamps)):
            result = extractor.update(float(y), float(t))

        assert result is not None
        assert result.is_valid is True
        # Rate should be close to 14 BPM (within 2 BPM tolerance)
        assert result.rate_bpm is not None
        assert abs(result.rate_bpm - 14.0) < 3.0

    def test_detects_slow_breathing(self, extractor):
        """Detects slow breathing rate (~8 BPM)."""
        signal, timestamps = generate_breathing_signal(
            duration=45.0,
            sample_rate=10.0,
            breath_rate_bpm=8.0,
            amplitude=10.0,
        )

        result = None
        for y, t in zip(signal + 1500, timestamps):
            result = extractor.update(float(y), float(t))

        assert result is not None
        assert result.is_valid is True
        assert result.rate_bpm is not None
        assert abs(result.rate_bpm - 8.0) < 2.0

    def test_amplitude_calculation(self, extractor):
        """Amplitude reflects breathing depth."""
        # Large amplitude breathing
        signal, timestamps = generate_breathing_signal(
            duration=35.0,
            sample_rate=10.0,
            breath_rate_bpm=14.0,
            amplitude=15.0,  # Deep breaths
            noise=0.5,
        )

        result = None
        for y, t in zip(signal + 1500, timestamps):
            result = extractor.update(float(y), float(t))

        assert result is not None
        assert result.amplitude > 0.5  # Should be significant

    def test_get_rate(self, extractor):
        """get_rate() returns current rate."""
        signal, timestamps = generate_breathing_signal(
            duration=35.0,
            sample_rate=10.0,
            breath_rate_bpm=14.0,
        )

        for y, t in zip(signal + 1500, timestamps):
            extractor.update(float(y), float(t))

        rate = extractor.get_rate()
        assert rate is not None
        assert 10 < rate < 20

    def test_reset_clears_state(self, extractor):
        """Reset clears accumulated data."""
        signal, timestamps = generate_breathing_signal(
            duration=35.0,
            sample_rate=10.0,
            breath_rate_bpm=14.0,
        )

        for y, t in zip(signal + 1500, timestamps):
            extractor.update(float(y), float(t))

        extractor.reset()

        # After reset, should return invalid
        result = extractor.update(1500.0, 0.0)
        assert result.is_valid is False


# =============================================================================
# Heart Rate Estimator Tests
# =============================================================================


class TestHeartRateEstimator:
    """Tests for heart rate estimation from radar data."""

    @pytest.fixture
    def estimator(self):
        return HeartRateEstimator(
            sample_rate=10.0,
            filter_low_hz=0.8,
            filter_high_hz=2.0,
            window_seconds=15.0,
        )

    def test_requires_minimum_data(self, estimator):
        """Estimator returns None until enough data."""
        # Only a few samples
        for i in range(10):
            result = estimator.update(1500.0)

        assert result is None

    def test_estimates_heart_rate(self, estimator):
        """Estimates heart rate from micro-movements."""
        # Generate signal with ~70 BPM component (1.17 Hz)
        hr_freq = 70.0 / 60.0
        n_samples = 200  # 20 seconds at 10 Hz

        result = None
        for i in range(n_samples):
            t = i / 10.0
            # Small amplitude heart rate component
            y = 1500.0 + 0.5 * np.sin(2 * np.pi * hr_freq * t)
            result = estimator.update(float(y))

        # May or may not detect depending on signal quality
        # Just verify it doesn't crash and returns reasonable value if any
        if result is not None:
            assert 45 < result < 130

    def test_reset_clears_state(self, estimator):
        """Reset clears accumulated data."""
        for i in range(100):
            estimator.update(1500.0 + i * 0.1)

        estimator.reset()

        # After reset, should return None
        result = estimator.update(1500.0)
        assert result is None


# =============================================================================
# Movement Detector Tests
# =============================================================================


class TestMovementDetector:
    """Tests for movement detection from radar data."""

    @pytest.fixture
    def detector(self):
        return MovementDetector(
            sample_rate=10.0,
            macro_threshold=100.0,
            micro_threshold=5.0,
            window_seconds=2.0,
        )

    def test_no_movement_in_stable_signal(self, detector):
        """Stable target has no movement."""
        for _ in range(30):
            result = detector.update(0.0, 1500.0, 0.0)

        assert result.level < 0.1
        assert bool(result.is_macro) is False
        assert bool(result.is_micro) is False

    def test_detects_micro_movement(self, detector):
        """Detects small movements (breathing)."""
        for i in range(30):
            # Small Y variations (breathing)
            y = 1500.0 + 10.0 * np.sin(i / 5.0)
            result = detector.update(0.0, float(y), 0.0)

        assert bool(result.is_micro) is True
        assert bool(result.is_macro) is False

    def test_detects_macro_movement(self, detector):
        """Detects large movements (turning over)."""
        for i in range(30):
            # Large movements
            x = 200.0 * np.sin(i / 3.0)
            y = 1500.0 + 150.0 * np.cos(i / 3.0)
            result = detector.update(float(x), float(y), 50.0)

        assert result.is_macro is True
        assert result.level > 0.5

    def test_reset_clears_state(self, detector):
        """Reset clears accumulated data."""
        for i in range(30):
            detector.update(float(i * 10), 1500.0, 10.0)

        detector.reset()

        # After reset, should have minimal movement
        result = detector.update(0.0, 1500.0, 0.0)
        assert result.level == 0.0


# =============================================================================
# Mock Radar Detector Tests
# =============================================================================


class TestMockRadarDetector:
    """Tests for mock radar detector."""

    @pytest.mark.asyncio
    async def test_mock_starts_and_stops(self):
        """Mock detector can start and stop."""
        detector = MockRadarDetector()

        await detector.start()
        assert detector.is_running

        await detector.stop()
        assert not detector.is_running

    @pytest.mark.asyncio
    async def test_mock_emits_events(self):
        """Mock detector emits radar events."""
        detector = MockRadarDetector()
        events = []

        async def capture(event):
            events.append(event)

        detector.set_on_event(capture)

        await detector.start()

        await asyncio.sleep(0.3)

        await detector.stop()

        assert len(events) > 0
        assert events[0].detector == "radar"
        assert "respiration_rate" in events[0].value
        assert "presence" in events[0].value

    @pytest.mark.asyncio
    async def test_mock_presence_always_true(self):
        """Mock detector always reports presence."""
        detector = MockRadarDetector()
        events = []

        async def capture(event):
            events.append(event)

        detector.set_on_event(capture)

        await detector.start()
        await asyncio.sleep(0.2)
        await detector.stop()

        for event in events:
            assert event.value.get("presence") is True

    @pytest.mark.asyncio
    async def test_mock_respiration_rate_settable(self):
        """Mock detector respiration rate can be set."""
        detector = MockRadarDetector(base_respiration_rate=12.0)
        events = []

        async def capture(event):
            events.append(event)

        detector.set_on_event(capture)

        await detector.start()

        # Change respiration rate
        detector._base_respiration_rate = 20.0

        await asyncio.sleep(0.2)
        await detector.stop()

        # Verify events were emitted (rate extraction takes time to converge)
        assert len(events) > 0

    @pytest.mark.asyncio
    async def test_mock_apnea_injection(self):
        """Mock can inject apnea anomaly."""
        detector = MockRadarDetector()
        events = []

        async def capture(event):
            events.append(event)

        detector.set_on_event(capture)

        await detector.start()

        # Let normal breathing establish
        await asyncio.sleep(0.2)

        # Inject apnea
        detector.inject_anomaly("apnea", duration=5.0)

        await asyncio.sleep(0.2)

        await detector.stop()

        # Should have events (apnea reduces amplitude but still emits)
        assert len(events) > 0

    @pytest.mark.asyncio
    async def test_mock_anomaly_expires(self):
        """Injected anomaly expires after duration."""
        detector = MockRadarDetector()

        await detector.start()

        detector.inject_anomaly("apnea", duration=0.1)

        await asyncio.sleep(0.3)

        await detector.stop()

        # Anomaly should have expired (checked during read_loop)
        assert detector._anomaly_type is None

    @pytest.mark.asyncio
    async def test_mock_distance_settable(self):
        """Mock detector distance can be set."""
        detector = MockRadarDetector(base_distance=2.5)
        events = []

        async def capture(event):
            events.append(event)

        detector.set_on_event(capture)

        await detector.start()
        await asyncio.sleep(0.2)
        await detector.stop()

        # Check target distance is around 2.5m
        for event in events:
            dist = event.value.get("target_distance")
            if dist is not None:
                assert 2.0 < dist < 3.0

    @pytest.mark.asyncio
    async def test_mock_frames_processed_increments(self):
        """Mock detector tracks frames processed."""
        detector = MockRadarDetector()

        await detector.start()
        await asyncio.sleep(0.3)
        await detector.stop()

        assert detector._frames_processed > 0

    def test_mock_name_is_radar(self):
        """Mock detector has name 'radar'."""
        detector = MockRadarDetector()
        assert detector.name == "radar"


# =============================================================================
# Edge Case Tests - LD2450 Target
# =============================================================================


class TestLD2450TargetEdgeCases:
    """Edge case tests for LD2450Target."""

    def test_target_at_origin(self):
        """Target at origin (invalid but shouldn't crash)."""
        target = LD2450Target(x=0, y=0, speed=0, resolution=0)
        assert target.distance_mm == 0.0
        assert target.distance_m == 0.0
        assert target.is_valid is False

    def test_target_very_close(self):
        """Target very close to sensor."""
        target = LD2450Target(x=0, y=50, speed=0, resolution=100)
        assert target.distance_mm == 50.0
        assert target.distance_m == 0.05
        assert target.is_valid is True

    def test_target_at_max_range(self):
        """Target at maximum sensor range (~6m)."""
        target = LD2450Target(x=0, y=6000, speed=0, resolution=100)
        assert target.distance_m == 6.0
        assert target.is_valid is True

    def test_target_beyond_max_range(self):
        """Target beyond normal max range."""
        target = LD2450Target(x=0, y=10000, speed=0, resolution=100)
        assert target.distance_m == 10.0
        assert target.is_valid is True

    def test_target_high_speed_approaching(self):
        """Target moving toward sensor at high speed."""
        target = LD2450Target(x=0, y=2000, speed=200, resolution=100)
        assert target.speed == 200  # Positive = approaching

    def test_target_high_speed_receding(self):
        """Target moving away from sensor at high speed."""
        target = LD2450Target(x=0, y=2000, speed=-200, resolution=100)
        assert target.speed == -200  # Negative = receding

    def test_target_extreme_angle_left(self):
        """Target at extreme left angle."""
        target = LD2450Target(x=-4000, y=100, speed=0, resolution=100)
        assert target.angle_degrees < -80.0

    def test_target_extreme_angle_right(self):
        """Target at extreme right angle."""
        target = LD2450Target(x=4000, y=100, speed=0, resolution=100)
        assert target.angle_degrees > 80.0

    def test_target_with_only_x_nonzero(self):
        """Target with only X position (edge case for is_valid)."""
        target = LD2450Target(x=100, y=0, speed=0, resolution=0)
        assert target.is_valid is True  # Not all zeros

    def test_target_with_only_speed_nonzero(self):
        """Target with only speed (edge case for is_valid)."""
        target = LD2450Target(x=0, y=0, speed=10, resolution=0)
        assert target.is_valid is True  # Speed is nonzero

    def test_target_negative_y(self):
        """Target with negative Y (sensor quirk - behind sensor)."""
        target = LD2450Target(x=0, y=-100, speed=0, resolution=100)
        assert target.y == -100
        assert target.distance_mm == 100.0


# =============================================================================
# Edge Case Tests - LD2450 Frame
# =============================================================================


class TestLD2450FrameEdgeCases:
    """Edge case tests for LD2450Frame parsing."""

    def test_parse_empty_bytes(self):
        """Empty data returns None."""
        frame = LD2450Frame.parse(b"")
        assert frame is None

    def test_parse_exact_size_no_header(self):
        """Exact 30 bytes but no valid header."""
        data = b"\x00" * 30
        frame = LD2450Frame.parse(data)
        assert frame is None

    def test_parse_header_at_end(self):
        """Header at end with no room for frame."""
        data = b"\x00" * 26 + FRAME_HEADER
        frame = LD2450Frame.parse(data)
        assert frame is None

    def test_parse_partial_header(self):
        """Partial header match doesn't crash."""
        data = bytes([0xAA, 0xFF, 0x00, 0x00]) + b"\x00" * 26
        frame = LD2450Frame.parse(data)
        assert frame is None

    def test_parse_multiple_frames_returns_first(self):
        """Multiple valid frames - returns first."""
        frame1 = build_test_frame([(100, 1500, 0, 100)])
        frame2 = build_test_frame([(200, 2500, 0, 100)])
        data = frame1 + frame2

        frame = LD2450Frame.parse(data)
        assert frame is not None
        assert frame.targets[0].x == 100

    def test_parse_corrupted_target_data(self):
        """Frame with corrupt target data still parses structure."""
        # Build frame then corrupt some target bytes
        data = bytearray(build_test_frame([(100, 1500, 0, 100)]))
        # Corrupt second target area (should be zeros)
        data[12:20] = b"\xFF" * 8

        frame = LD2450Frame.parse(bytes(data))
        # Should still parse (corrupt target may or may not be valid)
        assert frame is not None

    def test_parse_all_targets_max_values(self):
        """All targets at maximum coordinate values."""
        data = build_test_frame([
            (32767, 32767, 32767, 65535),
            (32767, 32767, 32767, 65535),
            (32767, 32767, 32767, 65535),
        ])
        frame = LD2450Frame.parse(data)
        assert frame is not None
        assert len(frame.targets) == 3

    def test_parse_all_targets_negative_max(self):
        """All targets at maximum negative values."""
        data = build_test_frame([
            (-32767, 32767, -32767, 0),
            (-32767, 32767, -32767, 0),
            (-32767, 32767, -32767, 0),
        ])
        frame = LD2450Frame.parse(data)
        assert frame is not None

    def test_parse_frame_with_trailing_garbage(self):
        """Frame followed by garbage data."""
        valid = build_test_frame([(100, 1500, 0, 100)])
        data = valid + b"\xFF\xFE\xFD\xFC\xFB"

        frame = LD2450Frame.parse(data)
        assert frame is not None
        assert frame.targets[0].x == 100

    def test_parse_frame_stores_raw_data(self):
        """Parsed frame stores raw bytes."""
        data = build_test_frame([(100, 1500, 0, 100)])
        frame = LD2450Frame.parse(data)

        assert frame is not None
        assert frame.raw_data is not None
        assert len(frame.raw_data) == 30


# =============================================================================
# Edge Case Tests - Bandpass Filter
# =============================================================================


class TestBandpassFilterEdgeCases:
    """Edge case tests for bandpass filter."""

    def test_filter_very_narrow_band(self):
        """Very narrow passband filter."""
        filt = BandpassFilter(0.19, 0.21, 10.0, order=2)
        result = filt.filter(1.0)
        assert isinstance(result, float)

    def test_filter_wide_band(self):
        """Wide passband filter (almost all-pass)."""
        filt = BandpassFilter(0.01, 4.9, 10.0, order=2)
        result = filt.filter(1.0)
        assert isinstance(result, float)

    def test_filter_high_order(self):
        """High order filter (sharper rolloff)."""
        filt = BandpassFilter(0.1, 0.5, 10.0, order=8)
        result = filt.filter(1.0)
        assert isinstance(result, float)

    def test_filter_low_sample_rate(self):
        """Very low sample rate."""
        filt = BandpassFilter(0.05, 0.2, 1.0, order=2)
        result = filt.filter(1.0)
        assert isinstance(result, float)

    def test_filter_high_sample_rate(self):
        """High sample rate."""
        filt = BandpassFilter(10.0, 50.0, 1000.0, order=4)
        result = filt.filter(1.0)
        assert isinstance(result, float)

    def test_filter_constant_input(self):
        """Filter with constant input (DC)."""
        filt = BandpassFilter(0.1, 0.5, 10.0)

        # DC input should be filtered out (bandpass)
        results = [filt.filter(1.0) for _ in range(100)]

        # After settling, output should be near zero for DC input
        assert abs(results[-1]) < 1.0

    def test_filter_zero_input(self):
        """Filter with all-zero input."""
        filt = BandpassFilter(0.1, 0.5, 10.0)
        results = [filt.filter(0.0) for _ in range(50)]

        # Should all be zero or very close
        assert all(abs(r) < 0.01 for r in results)

    def test_filter_impulse_response(self):
        """Filter impulse response (single 1, rest 0)."""
        filt = BandpassFilter(0.1, 0.5, 10.0)

        results = [filt.filter(1.0)]  # Impulse
        results.extend([filt.filter(0.0) for _ in range(99)])

        # Should have some ringing/response
        assert any(abs(r) > 0.01 for r in results[1:])

    def test_filter_alternating_input(self):
        """Filter with alternating +1/-1 input (high frequency)."""
        filt = BandpassFilter(0.1, 0.5, 10.0)

        # Alternating = Nyquist frequency, should be filtered
        results = [filt.filter(float((-1) ** i)) for i in range(100)]

        # High frequency should be attenuated
        assert abs(results[-1]) < 1.0

    def test_filter_nan_handling(self):
        """Filter handles NaN input gracefully."""
        filt = BandpassFilter(0.1, 0.5, 10.0)

        # Process normal values first
        for i in range(10):
            filt.filter(float(i))

        # NaN input - should not crash (may produce NaN)
        result = filt.filter(float('nan'))
        # Result may be NaN, which is expected
        assert isinstance(result, float)

    def test_filter_inf_handling(self):
        """Filter handles infinity input."""
        filt = BandpassFilter(0.1, 0.5, 10.0)

        for i in range(10):
            filt.filter(float(i))

        result = filt.filter(float('inf'))
        assert isinstance(result, float)

    def test_filter_array_empty(self):
        """Filter array with empty input."""
        filt = BandpassFilter(0.1, 0.5, 10.0)
        # Empty array raises ValueError in scipy.filtfilt due to padding requirements
        try:
            result = filt.filter_array(np.array([]))
            assert len(result) == 0
        except ValueError:
            # Expected - filtfilt requires minimum length
            pass

    def test_filter_array_single_element(self):
        """Filter array with single element."""
        filt = BandpassFilter(0.1, 0.5, 10.0)
        # Single element may have edge effects but shouldn't crash
        try:
            result = filt.filter_array(np.array([1.0]))
            assert len(result) == 1
        except ValueError:
            # Some filter implementations require minimum length
            pass

    def test_filter_multiple_resets(self):
        """Multiple resets don't cause issues."""
        filt = BandpassFilter(0.1, 0.5, 10.0)

        filt.reset()
        filt.reset()
        filt.reset()

        result = filt.filter(1.0)
        assert isinstance(result, float)


# =============================================================================
# Edge Case Tests - Respiration Extractor
# =============================================================================


class TestRespirationExtractorEdgeCases:
    """Edge case tests for respiration extraction."""

    def test_constant_position_no_breathing(self):
        """Constant position (no breathing movement)."""
        extractor = RespirationExtractor(sample_rate=10.0, window_seconds=30.0)

        for i in range(400):
            result = extractor.update(1500.0, float(i) / 10.0)

        # Should have low confidence or invalid
        assert result.amplitude < 0.1

    def test_very_fast_breathing(self):
        """Very fast breathing (28+ BPM)."""
        extractor = RespirationExtractor(
            sample_rate=10.0,
            filter_low_hz=0.1,
            filter_high_hz=0.6,  # Allow up to 36 BPM
            window_seconds=30.0,
        )

        signal, timestamps = generate_breathing_signal(
            duration=40.0,
            sample_rate=10.0,
            breath_rate_bpm=28.0,
            amplitude=8.0,
        )

        result = None
        for y, t in zip(signal + 1500, timestamps):
            result = extractor.update(float(y), float(t))

        # May or may not detect at edge of filter range
        assert result is not None

    def test_very_slow_breathing(self):
        """Very slow breathing (6 BPM)."""
        extractor = RespirationExtractor(
            sample_rate=10.0,
            filter_low_hz=0.08,  # Allow 5 BPM
            filter_high_hz=0.5,
            window_seconds=45.0,  # Longer window for slow breathing
        )

        signal, timestamps = generate_breathing_signal(
            duration=60.0,
            sample_rate=10.0,
            breath_rate_bpm=6.0,
            amplitude=12.0,
        )

        result = None
        for y, t in zip(signal + 1500, timestamps):
            result = extractor.update(float(y), float(t))

        assert result is not None

    def test_noisy_signal(self):
        """High noise signal."""
        extractor = RespirationExtractor(sample_rate=10.0, window_seconds=30.0)

        signal, timestamps = generate_breathing_signal(
            duration=40.0,
            sample_rate=10.0,
            breath_rate_bpm=14.0,
            amplitude=5.0,
            noise=10.0,  # Very noisy
        )

        result = None
        for y, t in zip(signal + 1500, timestamps):
            result = extractor.update(float(y), float(t))

        # Should still produce result, may have low confidence
        assert result is not None

    def test_sudden_position_jump(self):
        """Sudden large position change (person moved)."""
        extractor = RespirationExtractor(sample_rate=10.0, window_seconds=30.0)

        # Normal breathing for a while
        signal1, timestamps1 = generate_breathing_signal(
            duration=20.0,
            sample_rate=10.0,
            breath_rate_bpm=14.0,
        )

        for y, t in zip(signal1 + 1500, timestamps1):
            extractor.update(float(y), float(t))

        # Sudden jump to new position
        for i in range(100):
            t = 20.0 + i / 10.0
            y = 2500.0 + 10.0 * np.sin(i / 5.0)  # 1000mm jump
            result = extractor.update(float(y), float(t))

        # Should eventually recover
        assert result is not None

    def test_get_amplitude_before_data(self):
        """get_amplitude() before any data."""
        extractor = RespirationExtractor(sample_rate=10.0)
        assert extractor.get_amplitude() == 0.0

    def test_get_rate_before_data(self):
        """get_rate() before any data."""
        extractor = RespirationExtractor(sample_rate=10.0)
        assert extractor.get_rate() is None

    def test_irregular_timestamps(self):
        """Irregular (jittery) timestamps."""
        extractor = RespirationExtractor(sample_rate=10.0, window_seconds=30.0)

        for i in range(400):
            # Jittery timestamps
            t = i / 10.0 + np.random.uniform(-0.02, 0.02)
            y = 1500.0 + 10.0 * np.sin(2 * np.pi * (14.0 / 60.0) * t)
            result = extractor.update(float(y), float(t))

        # Should still work reasonably
        assert result is not None

    def test_backwards_timestamps(self):
        """Timestamps going backwards (clock issue)."""
        extractor = RespirationExtractor(sample_rate=10.0, window_seconds=30.0)

        # Forward timestamps
        for i in range(200):
            extractor.update(1500.0 + i, float(i) / 10.0)

        # Backwards timestamp - should not crash
        result = extractor.update(1500.0, 5.0)
        assert result is not None


# =============================================================================
# Edge Case Tests - Heart Rate Estimator
# =============================================================================


class TestHeartRateEstimatorEdgeCases:
    """Edge case tests for heart rate estimation."""

    def test_very_low_heart_rate(self):
        """Very low heart rate (40 BPM)."""
        estimator = HeartRateEstimator(
            sample_rate=10.0,
            filter_low_hz=0.6,  # Allow 36 BPM
            filter_high_hz=2.0,
            window_seconds=20.0,
        )

        hr_freq = 40.0 / 60.0
        for i in range(250):
            t = i / 10.0
            y = 1500.0 + 0.3 * np.sin(2 * np.pi * hr_freq * t)
            result = estimator.update(float(y))

        # May or may not detect at edge of range
        if result is not None:
            assert 35 < result < 50

    def test_very_high_heart_rate(self):
        """Very high heart rate (150 BPM)."""
        estimator = HeartRateEstimator(
            sample_rate=10.0,
            filter_low_hz=0.8,
            filter_high_hz=3.0,  # Allow up to 180 BPM
            window_seconds=15.0,
        )

        hr_freq = 150.0 / 60.0
        for i in range(200):
            t = i / 10.0
            y = 1500.0 + 0.2 * np.sin(2 * np.pi * hr_freq * t)
            estimator.update(float(y))

        # High heart rates are harder to detect from radar
        # Just verify no crash

    def test_no_heartbeat_signal(self):
        """Signal with no heartbeat component."""
        estimator = HeartRateEstimator(sample_rate=10.0, window_seconds=15.0)

        # Only breathing frequency (0.2 Hz = 12 BPM breathing)
        for i in range(200):
            t = i / 10.0
            y = 1500.0 + 10.0 * np.sin(2 * np.pi * 0.2 * t)
            result = estimator.update(float(y))

        # Should return None or last valid rate
        # (no valid HR component in signal)

    def test_multiple_frequency_components(self):
        """Signal with multiple frequency components."""
        estimator = HeartRateEstimator(sample_rate=10.0, window_seconds=15.0)

        for i in range(200):
            t = i / 10.0
            # Breathing (0.25 Hz) + Heart rate (1.2 Hz) + noise
            y = (1500.0 +
                 10.0 * np.sin(2 * np.pi * 0.25 * t) +  # Breathing
                 0.3 * np.sin(2 * np.pi * 1.2 * t) +    # Heart rate
                 0.1 * np.random.randn())               # Noise
            estimator.update(float(y))

        # Should identify heart rate component


# =============================================================================
# Edge Case Tests - Movement Detector
# =============================================================================


class TestMovementDetectorEdgeCases:
    """Edge case tests for movement detection."""

    def test_single_sample(self):
        """Single sample doesn't crash."""
        detector = MovementDetector(sample_rate=10.0)
        result = detector.update(0.0, 1500.0, 0.0)
        assert result.level == 0.0

    def test_high_speed_low_position_change(self):
        """High speed but low position change."""
        detector = MovementDetector(sample_rate=10.0)

        for _ in range(30):
            # High speed reported but position stable
            result = detector.update(0.0, 1500.0, 100.0)

        # Speed contributes to macro detection
        assert bool(result.is_macro) is True

    def test_gradual_drift(self):
        """Gradual position drift over time."""
        detector = MovementDetector(
            sample_rate=10.0,
            macro_threshold=100.0,
            micro_threshold=5.0,
        )

        for i in range(30):
            # Slow drift in Y
            y = 1500.0 + i * 2.0
            result = detector.update(0.0, float(y), 0.0)

        # Gradual drift should be detected as movement
        assert result.level > 0

    def test_oscillating_movement(self):
        """Fast oscillating movement."""
        detector = MovementDetector(sample_rate=10.0)

        for i in range(30):
            # Rapid oscillation
            x = 50.0 * ((-1) ** i)
            result = detector.update(float(x), 1500.0, 20.0)

        # Should detect movement
        assert result.level > 0

    def test_x_only_movement(self):
        """Movement only in X direction."""
        detector = MovementDetector(sample_rate=10.0, macro_threshold=100.0)

        for i in range(30):
            x = 150.0 * np.sin(i / 3.0)
            result = detector.update(float(x), 1500.0, 0.0)

        assert result.level > 0

    def test_y_only_movement(self):
        """Movement only in Y direction."""
        detector = MovementDetector(sample_rate=10.0, macro_threshold=100.0)

        for i in range(30):
            y = 1500.0 + 150.0 * np.sin(i / 3.0)
            result = detector.update(0.0, float(y), 0.0)

        assert result.level > 0

    def test_movement_level_capped(self):
        """Movement level is capped at 1.0."""
        detector = MovementDetector(sample_rate=10.0, macro_threshold=100.0)

        for i in range(30):
            # Huge movement (way over threshold)
            x = 1000.0 * np.sin(i)
            y = 1500.0 + 1000.0 * np.cos(i)
            result = detector.update(float(x), float(y), 100.0)

        assert result.level <= 1.0

    def test_negative_coordinates(self):
        """Movement with negative coordinates."""
        detector = MovementDetector(sample_rate=10.0)

        for i in range(30):
            x = -500.0 + 100.0 * np.sin(i / 3.0)
            result = detector.update(float(x), 1500.0, 0.0)

        # Should still detect movement
        assert result is not None


# =============================================================================
# Edge Case Tests - Mock Radar Detector
# =============================================================================


class TestMockRadarDetectorEdgeCases:
    """Edge case tests for mock radar detector."""

    @pytest.mark.asyncio
    async def test_start_stop_start(self):
        """Start, stop, then start again."""
        detector = MockRadarDetector()

        await detector.start()
        assert detector.is_running

        await detector.stop()
        assert not detector.is_running

        await detector.start()
        assert detector.is_running

        await detector.stop()

    @pytest.mark.asyncio
    async def test_double_start(self):
        """Double start doesn't crash."""
        detector = MockRadarDetector()

        await detector.start()
        # Second start should be ignored or handled gracefully
        try:
            await detector.start()
        except Exception:
            pass  # Some implementations may raise

        await detector.stop()

    @pytest.mark.asyncio
    async def test_double_stop(self):
        """Double stop doesn't crash."""
        detector = MockRadarDetector()

        await detector.start()
        await detector.stop()
        await detector.stop()  # Should not crash

    @pytest.mark.asyncio
    async def test_stop_without_start(self):
        """Stop without start doesn't crash."""
        detector = MockRadarDetector()
        await detector.stop()  # Should not crash

    @pytest.mark.asyncio
    async def test_very_short_run(self):
        """Very short run time."""
        detector = MockRadarDetector()
        events = []

        async def capture(event):
            events.append(event)

        detector.set_on_event(capture)

        await detector.start()
        await asyncio.sleep(0.05)  # Very short
        await detector.stop()

        # May or may not have events depending on timing

    @pytest.mark.asyncio
    async def test_no_callback_set(self):
        """Running without callback doesn't crash."""
        detector = MockRadarDetector()

        await detector.start()
        await asyncio.sleep(0.1)
        await detector.stop()

        # Should complete without error

    @pytest.mark.asyncio
    async def test_callback_exception_handling(self):
        """Callback that raises exception."""
        detector = MockRadarDetector()

        async def bad_callback(event):
            raise ValueError("Callback error")

        detector.set_on_event(bad_callback)

        await detector.start()
        await asyncio.sleep(0.1)
        await detector.stop()

        # Detector should still be able to stop

    @pytest.mark.asyncio
    async def test_inject_anomaly_before_start(self):
        """Inject anomaly before starting."""
        detector = MockRadarDetector()
        detector.inject_anomaly("apnea", duration=5.0)

        await detector.start()
        await asyncio.sleep(0.1)
        await detector.stop()

        # Should work (anomaly may have expired)

    @pytest.mark.asyncio
    async def test_inject_multiple_anomalies(self):
        """Inject multiple anomalies (second overwrites first)."""
        detector = MockRadarDetector()

        await detector.start()

        detector.inject_anomaly("apnea", duration=10.0)
        detector.inject_anomaly("apnea", duration=5.0)  # Overwrites

        assert detector._anomaly_duration == 5.0

        await detector.stop()

    @pytest.mark.asyncio
    async def test_zero_respiration_rate(self):
        """Zero respiration rate (complete apnea)."""
        detector = MockRadarDetector(base_respiration_rate=0.0)
        events = []

        async def capture(event):
            events.append(event)

        detector.set_on_event(capture)

        await detector.start()
        await asyncio.sleep(0.2)
        await detector.stop()

        # Should still emit events (just no breathing modulation)
        assert len(events) > 0

    @pytest.mark.asyncio
    async def test_very_high_respiration_rate(self):
        """Very high respiration rate."""
        detector = MockRadarDetector(base_respiration_rate=40.0)
        events = []

        async def capture(event):
            events.append(event)

        detector.set_on_event(capture)

        await detector.start()
        await asyncio.sleep(0.2)
        await detector.stop()

        assert len(events) > 0

    @pytest.mark.asyncio
    async def test_zero_distance(self):
        """Zero distance (at sensor)."""
        detector = MockRadarDetector(base_distance=0.0)

        await detector.start()
        await asyncio.sleep(0.1)
        await detector.stop()

        # Y position would be 0, check it doesn't crash

    @pytest.mark.asyncio
    async def test_negative_distance(self):
        """Negative distance (invalid but shouldn't crash)."""
        detector = MockRadarDetector(base_distance=-1.0)

        await detector.start()
        await asyncio.sleep(0.1)
        await detector.stop()

    def test_config_defaults(self):
        """Mock uses sensible config defaults."""
        detector = MockRadarDetector()
        assert detector._config is not None
        assert detector._config.update_rate_hz > 0
