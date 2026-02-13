"""Tests for BCG detector."""

import time
import pytest
import numpy as np

from nightwatch.detectors.bcg.processing import (
    BCGProcessor,
    BCGProcessorConfig,
    JPeakDetector,
    HeartRateCalculator,
    RespirationExtractor,
    BedOccupancyDetector,
    MovementDetector,
    BandpassFilter,
    JPeak,
)
from nightwatch.detectors.bcg.detector import MockBCGDetector
from nightwatch.core.events import EventState


def generate_bcg_signal(
    duration: float,
    sample_rate: int,
    heart_rate: float,
    amplitude: float = 0.5,
) -> np.ndarray:
    """
    Generate synthetic BCG signal with heartbeats.

    Args:
        duration: Signal duration in seconds
        sample_rate: Samples per second
        heart_rate: Heart rate in BPM
        amplitude: Signal amplitude

    Returns:
        Synthetic BCG signal
    """
    n_samples = int(duration * sample_rate)
    t = np.linspace(0, duration, n_samples)

    # Heart rate in Hz
    hr_hz = heart_rate / 60.0

    # Generate BCG-like waveform (simplified)
    # Each heartbeat creates a spike pattern
    beat_period = 1.0 / hr_hz
    signal = np.zeros(n_samples)

    for i in range(int(duration / beat_period) + 1):
        beat_time = i * beat_period
        beat_sample = int(beat_time * sample_rate)

        if beat_sample < n_samples:
            # Create J-wave pattern (simplified as gaussian pulse)
            for j in range(-20, 20):
                idx = beat_sample + j
                if 0 <= idx < n_samples:
                    signal[idx] += amplitude * np.exp(-(j ** 2) / 50.0)

    # Add noise
    signal += np.random.randn(n_samples) * 0.05

    return signal.astype(np.float32)


class TestBandpassFilter:
    """Tests for BCG bandpass filter."""

    def test_filter_creation(self):
        """Filter can be created."""
        filt = BandpassFilter(0.5, 25.0, 100)
        assert filt is not None

    def test_filter_reduces_dc(self):
        """Filter removes DC component."""
        filt = BandpassFilter(0.5, 25.0, 100)

        # Signal with DC offset
        signal = np.ones(100, dtype=np.float32) + 0.5
        filtered = filt.filter(signal)

        # DC should be reduced
        assert abs(np.mean(filtered)) < abs(np.mean(signal))


class TestJPeakDetector:
    """Tests for J-peak detection."""

    @pytest.fixture
    def config(self):
        return BCGProcessorConfig(sample_rate=100)

    @pytest.fixture
    def detector(self, config):
        return JPeakDetector(config)

    def test_detects_peaks_in_synthetic_signal(self, detector):
        """Detector finds peaks in synthetic BCG."""
        signal = generate_bcg_signal(
            duration=5.0,
            sample_rate=100,
            heart_rate=70.0,
            amplitude=0.5,
        )

        # Process signal in chunks
        chunk_size = 10
        all_peaks = []

        for i in range(0, len(signal), chunk_size):
            chunk = signal[i : i + chunk_size]
            timestamp = i / 100.0
            peaks = detector.process(chunk, i, timestamp)
            all_peaks.extend(peaks)

        # Should detect several heartbeats in 5 seconds at 70 BPM
        # Expected: ~5 beats
        assert len(all_peaks) >= 3

    def test_no_peaks_in_silence(self, detector):
        """Detector finds no peaks in silent signal."""
        signal = np.zeros(500, dtype=np.float32)
        peaks = detector.process(signal, 0, 0.0)

        assert len(peaks) == 0


class TestHeartRateCalculator:
    """Tests for heart rate calculation."""

    @pytest.fixture
    def config(self):
        return BCGProcessorConfig()

    @pytest.fixture
    def calculator(self, config):
        return HeartRateCalculator(config)

    def test_calculates_rate_from_peaks(self, calculator):
        """Calculator determines heart rate from peaks."""
        # Simulate 70 BPM (857ms intervals)
        interval_ms = 857

        for i in range(10):
            peak = JPeak(
                timestamp=i * interval_ms / 1000.0,
                sample_index=i * 86,
                amplitude=0.5,
            )
            calculator.add_peak(peak)

        hr = calculator.get_heart_rate()

        assert hr is not None
        assert 65 <= hr <= 75  # Should be close to 70

    def test_requires_minimum_peaks(self, calculator):
        """Calculator needs minimum peaks for rate."""
        peak = JPeak(timestamp=0.0, sample_index=0, amplitude=0.5)
        calculator.add_peak(peak)

        hr = calculator.get_heart_rate()
        assert hr is None  # Not enough data

    def test_rejects_invalid_intervals(self, calculator):
        """Calculator ignores unrealistic intervals."""
        # Add peaks with invalid interval (50ms = 1200 BPM)
        for i in range(5):
            peak = JPeak(
                timestamp=i * 0.05,  # 50ms
                sample_index=i * 5,
                amplitude=0.5,
            )
            calculator.add_peak(peak)

        hr = calculator.get_heart_rate()
        # Should be None because intervals are invalid
        assert hr is None


class TestBedOccupancyDetector:
    """Tests for bed occupancy detection."""

    @pytest.fixture
    def config(self):
        return BCGProcessorConfig(occupancy_threshold=0.01)

    @pytest.fixture
    def detector(self, config):
        return BedOccupancyDetector(config)

    def test_empty_bed_not_occupied(self, detector):
        """Empty bed (silent signal) is not occupied."""
        silent = np.zeros(100, dtype=np.float32)

        for _ in range(20):
            detector.process(silent)

        assert not detector.is_occupied()

    def test_active_signal_is_occupied(self, detector):
        """Active BCG signal indicates occupancy."""
        active = np.random.randn(100).astype(np.float32) * 0.1

        for _ in range(20):
            detector.process(active)

        assert detector.is_occupied()


class TestMovementDetector:
    """Tests for movement detection."""

    @pytest.fixture
    def config(self):
        return BCGProcessorConfig()

    @pytest.fixture
    def detector(self, config):
        return MovementDetector(config)

    def test_no_movement_in_calm_signal(self, detector):
        """Calm signal has no movement."""
        calm = np.random.randn(100).astype(np.float32) * 0.01

        for _ in range(30):
            detector.process(calm)

        assert not detector.is_moving()

    def test_detects_large_movement(self, detector):
        """Large signal spike indicates movement."""
        calm = np.random.randn(100).astype(np.float32) * 0.01

        # Build baseline
        for _ in range(30):
            detector.process(calm)

        # Large movement
        movement = np.ones(100, dtype=np.float32) * 1.0
        is_moving = detector.process(movement)

        assert is_moving


class TestBCGProcessor:
    """Tests for full BCG processor."""

    @pytest.fixture
    def processor(self):
        config = BCGProcessorConfig(sample_rate=100)
        return BCGProcessor(config)

    def test_process_returns_analysis(self, processor):
        """Processor returns complete analysis."""
        signal = np.random.randn(100).astype(np.float32) * 0.1
        result = processor.process(signal, time.time())

        assert hasattr(result, "heart_rate")
        assert hasattr(result, "respiration_rate")
        assert hasattr(result, "bed_occupied")
        assert hasattr(result, "signal_quality")

    def test_empty_bed_analysis(self, processor):
        """Empty bed has appropriate analysis."""
        silent = np.zeros(100, dtype=np.float32)

        for i in range(30):
            result = processor.process(silent, time.time() + i * 0.1)

        assert not result.bed_occupied
        assert result.signal_quality == 0.0

    def test_reset_clears_state(self, processor):
        """Reset clears processor state."""
        signal = generate_bcg_signal(1.0, 100, 70.0)
        processor.process(signal, time.time())

        processor.reset()

        # Should not raise and should have fresh state
        result = processor.process(signal, time.time())
        assert result is not None


class TestMockBCGDetector:
    """Tests for mock BCG detector."""

    @pytest.mark.asyncio
    async def test_mock_starts_and_stops(self):
        """Mock detector can start and stop."""
        detector = MockBCGDetector()

        await detector.start()
        assert detector.is_running

        await detector.stop()
        assert not detector.is_running

    @pytest.mark.asyncio
    async def test_mock_emits_events(self):
        """Mock detector emits BCG events."""
        detector = MockBCGDetector(update_rate_hz=10.0)
        events = []

        async def capture(event):
            events.append(event)

        detector.set_on_event(capture)

        await detector.start()

        import asyncio
        await asyncio.sleep(0.3)

        await detector.stop()

        assert len(events) > 0
        assert events[0].detector == "bcg"
        assert "heart_rate" in events[0].value

    @pytest.mark.asyncio
    async def test_mock_bed_occupancy(self):
        """Mock can change bed occupancy."""
        detector = MockBCGDetector(update_rate_hz=10.0)
        events = []

        async def capture(event):
            events.append(event)

        detector.set_on_event(capture)

        await detector.start()

        # Start occupied
        import asyncio
        await asyncio.sleep(0.15)

        # Set empty
        detector.set_bed_occupied(False)
        await asyncio.sleep(0.15)

        await detector.stop()

        # Should have both occupied and empty events
        occupied = [e for e in events if e.value.get("bed_occupied")]
        empty = [e for e in events if not e.value.get("bed_occupied")]

        assert len(occupied) > 0
        assert len(empty) > 0

    @pytest.mark.asyncio
    async def test_mock_bradycardia_injection(self):
        """Mock can inject low heart rate."""
        detector = MockBCGDetector(
            update_rate_hz=10.0,
            base_heart_rate=70.0,
        )
        events = []

        async def capture(event):
            events.append(event)

        detector.set_on_event(capture)

        await detector.start()

        # Normal heart rate
        import asyncio
        await asyncio.sleep(0.15)

        # Inject bradycardia
        detector.inject_bradycardia(True)
        await asyncio.sleep(0.15)

        await detector.stop()

        # Should have low heart rate events
        low_hr = [e for e in events if e.value.get("heart_rate") and e.value["heart_rate"] < 40]
        assert len(low_hr) > 0
