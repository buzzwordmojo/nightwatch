"""
BCG signal processing for heart rate detection.

Processes ballistocardiography signals from a piezoelectric sensor
under the mattress to detect:
- Heart rate from J-peaks
- Heart rate variability (HRV)
- Respiration from low-frequency oscillations
- Bed occupancy
"""

from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, field

import numpy as np
from scipy import signal as scipy_signal


@dataclass
class BCGAnalysis:
    """Result of BCG signal analysis."""

    heart_rate: float | None  # BPM
    heart_rate_variability: float | None  # RMSSD in ms
    respiration_rate: float | None  # BPM
    bed_occupied: bool
    signal_quality: float  # 0.0 - 1.0
    movement_detected: bool


@dataclass
class BCGProcessorConfig:
    """Configuration for BCG processing."""

    sample_rate: int = 100  # Hz

    # Heart rate filtering (0.5-25 Hz)
    hr_low_hz: float = 0.5
    hr_high_hz: float = 25.0

    # Respiration filtering (0.1-0.5 Hz = 6-30 BPM)
    resp_low_hz: float = 0.1
    resp_high_hz: float = 0.5

    # J-peak detection
    min_peak_distance_ms: int = 400  # 150 BPM max
    max_peak_distance_ms: int = 2000  # 30 BPM min

    # Bed occupancy
    occupancy_threshold: float = 0.01
    occupancy_window_seconds: float = 5.0

    # HRV calculation
    hrv_window_beats: int = 20


class BandpassFilter:
    """Butterworth bandpass filter."""

    def __init__(
        self,
        low_hz: float,
        high_hz: float,
        sample_rate: int,
        order: int = 4,
    ):
        nyquist = sample_rate / 2
        low = max(0.001, min(0.999, low_hz / nyquist))
        high = max(low + 0.001, min(0.999, high_hz / nyquist))

        self._sos = scipy_signal.butter(order, [low, high], btype="band", output="sos")
        self._zi = scipy_signal.sosfilt_zi(self._sos)

    def filter(self, signal: np.ndarray) -> np.ndarray:
        """Apply bandpass filter."""
        if len(signal) == 0:
            return signal
        filtered, self._zi = scipy_signal.sosfilt(
            self._sos, signal, zi=self._zi * signal[0]
        )
        return filtered

    def reset(self) -> None:
        """Reset filter state."""
        self._zi = scipy_signal.sosfilt_zi(self._sos)


@dataclass
class JPeak:
    """Detected J-peak (heartbeat)."""

    timestamp: float
    sample_index: int
    amplitude: float


class JPeakDetector:
    """
    Detect J-peaks (heartbeats) in BCG signal.

    The J-wave is the largest component of the BCG waveform,
    corresponding to blood ejection from the heart.
    """

    def __init__(self, config: BCGProcessorConfig):
        """
        Initialize J-peak detector.

        Args:
            config: BCG processing configuration
        """
        self._config = config

        # Bandpass filter for heart rate frequencies
        self._filter = BandpassFilter(
            config.hr_low_hz,
            config.hr_high_hz,
            config.sample_rate,
        )

        # Peak detection state
        self._peaks: deque[JPeak] = deque(maxlen=100)
        self._last_peak_sample = 0
        self._min_samples_between = int(
            config.min_peak_distance_ms * config.sample_rate / 1000
        )

        # Adaptive threshold
        self._amplitude_history: deque[float] = deque(maxlen=200)
        self._threshold = 0.0

    def process(
        self,
        signal: np.ndarray,
        start_sample: int,
        timestamp: float,
    ) -> list[JPeak]:
        """
        Process BCG signal to detect J-peaks.

        Args:
            signal: Raw BCG signal samples
            start_sample: Global sample index of first sample
            timestamp: Timestamp of first sample

        Returns:
            List of newly detected J-peaks
        """
        # Filter signal
        filtered = self._filter.filter(signal)

        # Update amplitude history for adaptive threshold
        self._amplitude_history.extend(np.abs(filtered))

        # Calculate adaptive threshold (75th percentile)
        if len(self._amplitude_history) >= 50:
            self._threshold = np.percentile(list(self._amplitude_history), 75)

        # Find peaks above threshold
        min_height = max(self._threshold, 0.001)

        # Use scipy for peak detection
        peak_indices, properties = scipy_signal.find_peaks(
            filtered,
            height=min_height,
            distance=self._min_samples_between,
        )

        # Convert to JPeak objects
        new_peaks = []
        sample_period = 1.0 / self._config.sample_rate

        for idx in peak_indices:
            global_sample = start_sample + idx

            # Skip if too close to last peak
            if global_sample - self._last_peak_sample < self._min_samples_between:
                continue

            peak = JPeak(
                timestamp=timestamp + idx * sample_period,
                sample_index=global_sample,
                amplitude=float(filtered[idx]),
            )
            self._peaks.append(peak)
            new_peaks.append(peak)
            self._last_peak_sample = global_sample

        return new_peaks

    def get_recent_peaks(self, n: int = 20) -> list[JPeak]:
        """Get most recent N peaks."""
        peaks = list(self._peaks)
        return peaks[-n:] if len(peaks) >= n else peaks

    def reset(self) -> None:
        """Reset detector state."""
        self._filter.reset()
        self._peaks.clear()
        self._last_peak_sample = 0
        self._amplitude_history.clear()


class HeartRateCalculator:
    """
    Calculate heart rate from inter-beat intervals.

    Uses median of recent intervals for robustness against
    occasional missed or false peaks.
    """

    def __init__(self, config: BCGProcessorConfig):
        """
        Initialize heart rate calculator.

        Args:
            config: BCG processing configuration
        """
        self._config = config
        self._intervals_ms: deque[float] = deque(maxlen=30)
        self._last_peak_time: float | None = None

    def add_peak(self, peak: JPeak) -> None:
        """
        Add a detected peak.

        Args:
            peak: Detected J-peak
        """
        if self._last_peak_time is not None:
            interval = (peak.timestamp - self._last_peak_time) * 1000  # ms

            # Only accept physiologically valid intervals (30-150 BPM)
            if 400 <= interval <= 2000:
                self._intervals_ms.append(interval)

        self._last_peak_time = peak.timestamp

    def get_heart_rate(self) -> float | None:
        """
        Calculate heart rate from recent intervals.

        Returns:
            Heart rate in BPM, or None if insufficient data
        """
        if len(self._intervals_ms) < 3:
            return None

        # Use median for robustness
        median_interval = np.median(list(self._intervals_ms))
        heart_rate = 60000.0 / median_interval

        # Clamp to valid range
        return max(30.0, min(200.0, heart_rate))

    def get_hrv(self) -> float | None:
        """
        Calculate heart rate variability (RMSSD).

        Returns:
            RMSSD in milliseconds, or None if insufficient data
        """
        if len(self._intervals_ms) < self._config.hrv_window_beats:
            return None

        intervals = list(self._intervals_ms)[-self._config.hrv_window_beats:]

        # RMSSD: Root Mean Square of Successive Differences
        diffs = np.diff(intervals)
        rmssd = float(np.sqrt(np.mean(diffs ** 2)))

        return rmssd

    def reset(self) -> None:
        """Reset calculator state."""
        self._intervals_ms.clear()
        self._last_peak_time = None


class RespirationExtractor:
    """
    Extract respiration rate from BCG signal.

    Respiration modulates the BCG signal amplitude, creating
    a low-frequency oscillation (0.1-0.5 Hz = 6-30 BPM).
    """

    def __init__(self, config: BCGProcessorConfig):
        """
        Initialize respiration extractor.

        Args:
            config: BCG processing configuration
        """
        self._config = config

        # Bandpass filter for respiration frequencies
        self._filter = BandpassFilter(
            config.resp_low_hz,
            config.resp_high_hz,
            config.sample_rate,
            order=2,  # Lower order for smoother response
        )

        # Respiration envelope history
        self._envelope: deque[tuple[float, float]] = deque(
            maxlen=int(config.sample_rate * 60)  # 1 minute
        )

    def process(self, signal: np.ndarray, timestamp: float) -> None:
        """
        Process BCG signal for respiration.

        Args:
            signal: BCG signal samples
            timestamp: Current timestamp
        """
        # Extract respiration envelope
        filtered = self._filter.filter(signal)
        envelope = np.abs(filtered)

        # Downsample to ~2 Hz for rate calculation
        step = max(1, len(envelope) // 2)
        for i in range(0, len(envelope), step):
            sample_time = timestamp + i / self._config.sample_rate
            self._envelope.append((sample_time, float(envelope[i])))

    def get_respiration_rate(self) -> float | None:
        """
        Calculate respiration rate from envelope.

        Returns:
            Respiration rate in BPM, or None if insufficient data
        """
        if len(self._envelope) < 100:
            return None

        # Extract values for analysis
        times = np.array([t for t, _ in self._envelope])
        values = np.array([v for _, v in self._envelope])

        # Use autocorrelation to find period
        values_normalized = values - np.mean(values)
        autocorr = np.correlate(values_normalized, values_normalized, mode="full")
        autocorr = autocorr[len(autocorr) // 2:]

        # Find first peak after zero lag
        min_lag = int(2.0 * len(self._envelope) / (times[-1] - times[0] + 0.001))  # 2 sec min
        max_lag = int(15.0 * len(self._envelope) / (times[-1] - times[0] + 0.001))  # 15 sec max

        if max_lag <= min_lag or max_lag >= len(autocorr):
            return None

        search_region = autocorr[min_lag:max_lag]
        if len(search_region) == 0:
            return None

        peak_idx = np.argmax(search_region) + min_lag

        # Convert lag to period
        duration = times[-1] - times[0]
        if duration <= 0:
            return None

        samples_per_sec = len(self._envelope) / duration
        period_seconds = peak_idx / samples_per_sec

        if period_seconds <= 0:
            return None

        rate = 60.0 / period_seconds

        # Clamp to valid range (6-30 BPM)
        return max(6.0, min(30.0, rate))

    def reset(self) -> None:
        """Reset extractor state."""
        self._filter.reset()
        self._envelope.clear()


class BedOccupancyDetector:
    """
    Detect whether the bed is occupied.

    Uses signal energy to determine if someone is in the bed.
    An occupied bed has consistent low-level vibrations from
    breathing and heartbeat.
    """

    def __init__(self, config: BCGProcessorConfig):
        """
        Initialize bed occupancy detector.

        Args:
            config: BCG processing configuration
        """
        self._config = config
        self._energy_history: deque[float] = deque(
            maxlen=int(config.occupancy_window_seconds * 10)  # 10 samples/sec
        )
        self._occupied = False

    def process(self, signal: np.ndarray) -> bool:
        """
        Process signal to detect bed occupancy.

        Args:
            signal: BCG signal samples

        Returns:
            True if bed is occupied
        """
        # Calculate RMS energy
        energy = float(np.sqrt(np.mean(signal ** 2)))
        self._energy_history.append(energy)

        if len(self._energy_history) < 10:
            return False

        # Occupied if median energy above threshold
        median_energy = np.median(list(self._energy_history))
        self._occupied = median_energy > self._config.occupancy_threshold

        return self._occupied

    def is_occupied(self) -> bool:
        """Check if bed is currently occupied."""
        return self._occupied

    def reset(self) -> None:
        """Reset detector state."""
        self._energy_history.clear()
        self._occupied = False


class MovementDetector:
    """
    Detect large movements (turning over, getting up).

    Large movements saturate the BCG signal and disrupt
    heart rate detection temporarily.
    """

    def __init__(self, config: BCGProcessorConfig):
        """
        Initialize movement detector.

        Args:
            config: BCG processing configuration
        """
        self._config = config
        self._baseline_energy = 0.01
        self._energy_history: deque[float] = deque(maxlen=50)
        self._movement_detected = False

    def process(self, signal: np.ndarray) -> bool:
        """
        Process signal to detect movement.

        Args:
            signal: BCG signal samples

        Returns:
            True if large movement detected
        """
        # Calculate peak-to-peak amplitude
        amplitude = float(np.max(signal) - np.min(signal))
        self._energy_history.append(amplitude)

        if len(self._energy_history) >= 20:
            # Update baseline (25th percentile)
            self._baseline_energy = np.percentile(list(self._energy_history), 25)

        # Movement = amplitude > 5x baseline
        self._movement_detected = amplitude > self._baseline_energy * 5

        return self._movement_detected

    def is_moving(self) -> bool:
        """Check if movement is detected."""
        return self._movement_detected

    def reset(self) -> None:
        """Reset detector state."""
        self._energy_history.clear()
        self._movement_detected = False


class BCGProcessor:
    """
    Main BCG processing pipeline.

    Combines J-peak detection, heart rate calculation,
    respiration extraction, and bed occupancy detection.
    """

    def __init__(self, config: BCGProcessorConfig | None = None):
        """
        Initialize BCG processor.

        Args:
            config: Processing configuration, or None for defaults
        """
        self._config = config or BCGProcessorConfig()

        self._jpeak = JPeakDetector(self._config)
        self._hr = HeartRateCalculator(self._config)
        self._resp = RespirationExtractor(self._config)
        self._occupancy = BedOccupancyDetector(self._config)
        self._movement = MovementDetector(self._config)

        self._sample_count = 0
        self._start_time: float | None = None

    @property
    def sample_rate(self) -> int:
        """Expected sample rate."""
        return self._config.sample_rate

    def process(self, signal: np.ndarray, timestamp: float) -> BCGAnalysis:
        """
        Process BCG signal through full pipeline.

        Args:
            signal: BCG signal samples (ADC values normalized to -1 to 1)
            timestamp: Current timestamp

        Returns:
            BCGAnalysis with all detection results
        """
        if self._start_time is None:
            self._start_time = timestamp

        # Convert to float if needed
        if signal.dtype != np.float32 and signal.dtype != np.float64:
            if signal.dtype == np.int16:
                signal = signal.astype(np.float32) / 32768.0
            elif signal.dtype == np.uint16:
                signal = (signal.astype(np.float32) - 32768.0) / 32768.0
            else:
                signal = signal.astype(np.float32)

        # Run all detectors
        bed_occupied = self._occupancy.process(signal)
        movement = self._movement.process(signal)

        # Only detect heartbeats if occupied and not moving
        if bed_occupied and not movement:
            peaks = self._jpeak.process(signal, self._sample_count, timestamp)
            for peak in peaks:
                self._hr.add_peak(peak)

            self._resp.process(signal, timestamp)

        self._sample_count += len(signal)

        # Get results
        heart_rate = self._hr.get_heart_rate()
        hrv = self._hr.get_hrv()
        resp_rate = self._resp.get_respiration_rate()

        # Calculate signal quality
        signal_quality = self._calculate_quality(bed_occupied, movement, heart_rate)

        return BCGAnalysis(
            heart_rate=heart_rate,
            heart_rate_variability=hrv,
            respiration_rate=resp_rate,
            bed_occupied=bed_occupied,
            signal_quality=signal_quality,
            movement_detected=movement,
        )

    def _calculate_quality(
        self,
        occupied: bool,
        moving: bool,
        heart_rate: float | None,
    ) -> float:
        """Calculate signal quality score."""
        if not occupied:
            return 0.0
        if moving:
            return 0.2
        if heart_rate is None:
            return 0.4

        # Check heart rate validity
        if 40 <= heart_rate <= 120:
            return 0.9
        elif 30 <= heart_rate <= 150:
            return 0.7
        else:
            return 0.5

    def reset(self) -> None:
        """Reset all processor state."""
        self._jpeak.reset()
        self._hr.reset()
        self._resp.reset()
        self._occupancy.reset()
        self._movement.reset()
        self._sample_count = 0
        self._start_time = None
