"""
Audio signal processing for breathing and seizure detection.

Processes audio input to detect:
- Breathing sounds (200-800 Hz band)
- Silence periods (potential apnea)
- Vocalizations (non-rhythmic sounds)
- Seizure sounds (rhythmic patterns 1-8 Hz, higher frequencies)
"""

from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, field

import numpy as np
from scipy import signal as scipy_signal


@dataclass
class SeizureAnalysis:
    """Result of seizure sound detection."""

    seizure_detected: bool
    seizure_confidence: float  # 0.0 - 1.0
    rhythmic_rate: float | None  # Rhythmic pattern rate in Hz
    duration: float  # Seconds of continuous seizure-like sounds


@dataclass
class BreathingAnalysis:
    """Result of breathing analysis on an audio chunk."""

    breathing_detected: bool
    breathing_rate: float | None  # BPM, None if not detected
    breathing_amplitude: float  # 0.0 - 1.0
    breathing_confidence: float  # 0.0 - 1.0
    silence_duration: float  # Seconds of continuous silence
    vocalization_detected: bool
    seizure_detected: bool  # Rhythmic seizure sounds detected
    seizure_confidence: float  # 0.0 - 1.0
    energy_level: float  # Overall audio energy


@dataclass
class AudioProcessorConfig:
    """Configuration for audio processing."""

    sample_rate: int = 16000
    chunk_duration: float = 0.1  # 100ms chunks

    # Breathing detection
    breathing_low_hz: float = 200.0
    breathing_high_hz: float = 800.0
    breathing_threshold: float = 0.02

    # Silence detection
    silence_threshold: float = 0.005
    silence_min_duration: float = 2.0  # Seconds before counting as silence

    # Vocalization detection
    vocalization_low_hz: float = 200.0
    vocalization_high_hz: float = 3000.0
    vocalization_threshold: float = 0.1

    # Rate estimation
    rate_window_seconds: float = 30.0
    min_breaths_for_rate: int = 3

    # Seizure sound detection
    # Seizures can produce various rhythmic sounds:
    # - Tonic-clonic: loud vocalizations, grunting
    # - Subtle: quiet mouth sounds, lip smacking, labored breathing
    # - Movement: repetitive rustling from limb movements
    # Key indicator is RHYTHMIC REPETITION at 1-8 Hz, even if quiet
    #
    # IMPORTANT: Must distinguish from breathing/snoring:
    # - Breathing rate: 0.2-0.5 Hz (12-30 BPM)
    # - Snoring: repetitive but modulated by breathing envelope
    # - Seizure: sustained fast rhythm (1-8 Hz) independent of breath cycle
    seizure_low_hz: float = 100.0  # Lower to catch subtle sounds
    seizure_high_hz: float = 3000.0  # Higher to catch rustling
    seizure_rhythm_low_hz: float = 1.5  # Start above breathing harmonics
    seizure_rhythm_high_hz: float = 8.0
    seizure_min_duration: float = 5.0  # Longer duration to avoid snoring bursts
    seizure_energy_threshold: float = 0.005  # Very low - prioritize rhythm over volume

    # Breathing rate range (used to exclude from seizure detection)
    breathing_rate_low_hz: float = 0.15  # ~9 BPM
    breathing_rate_high_hz: float = 0.6  # ~36 BPM


class BandpassFilter:
    """Butterworth bandpass filter for isolating frequency bands."""

    def __init__(
        self,
        low_hz: float,
        high_hz: float,
        sample_rate: int,
        order: int = 4,
    ):
        """
        Create bandpass filter.

        Args:
            low_hz: Lower cutoff frequency
            high_hz: Upper cutoff frequency
            sample_rate: Audio sample rate
            order: Filter order (higher = sharper cutoff)
        """
        nyquist = sample_rate / 2
        low = low_hz / nyquist
        high = high_hz / nyquist

        # Clamp to valid range
        low = max(0.001, min(0.999, low))
        high = max(low + 0.001, min(0.999, high))

        self._sos = scipy_signal.butter(order, [low, high], btype="band", output="sos")
        self._zi = scipy_signal.sosfilt_zi(self._sos)

    def filter(self, audio: np.ndarray) -> np.ndarray:
        """Apply bandpass filter to audio chunk."""
        filtered, self._zi = scipy_signal.sosfilt(self._sos, audio, zi=self._zi * audio[0])
        return filtered

    def reset(self) -> None:
        """Reset filter state."""
        self._zi = scipy_signal.sosfilt_zi(self._sos)


class EnvelopeExtractor:
    """Extract amplitude envelope from audio signal."""

    def __init__(self, sample_rate: int, smoothing_hz: float = 5.0):
        """
        Create envelope extractor.

        Args:
            sample_rate: Audio sample rate
            smoothing_hz: Cutoff frequency for envelope smoothing
        """
        nyquist = sample_rate / 2
        cutoff = min(smoothing_hz / nyquist, 0.99)
        self._sos = scipy_signal.butter(2, cutoff, btype="low", output="sos")
        self._zi = scipy_signal.sosfilt_zi(self._sos)

    def extract(self, audio: np.ndarray) -> np.ndarray:
        """Extract amplitude envelope."""
        # Rectify (absolute value)
        rectified = np.abs(audio)
        # Smooth with lowpass filter
        envelope, self._zi = scipy_signal.sosfilt(
            self._sos, rectified, zi=self._zi * rectified[0]
        )
        return envelope

    def reset(self) -> None:
        """Reset filter state."""
        self._zi = scipy_signal.sosfilt_zi(self._sos)


@dataclass
class BreathCycle:
    """Represents a detected breath cycle."""

    start_time: float
    peak_time: float
    end_time: float | None
    peak_amplitude: float


class BreathingDetector:
    """
    Detect breathing patterns in audio.

    Uses bandpass filtering (200-800 Hz) to isolate breathing sounds,
    then analyzes the envelope for rhythmic patterns.
    """

    def __init__(self, config: AudioProcessorConfig):
        """
        Initialize breathing detector.

        Args:
            config: Audio processing configuration
        """
        self._config = config

        # Filters
        self._bandpass = BandpassFilter(
            config.breathing_low_hz,
            config.breathing_high_hz,
            config.sample_rate,
        )
        self._envelope = EnvelopeExtractor(config.sample_rate)

        # Breathing detection state
        self._envelope_history: deque[tuple[float, float]] = deque(
            maxlen=int(config.rate_window_seconds * 10)  # 10 samples per second
        )
        self._breath_cycles: deque[BreathCycle] = deque(maxlen=30)
        self._in_breath = False
        self._breath_start: float | None = None
        self._last_peak_time: float | None = None
        self._last_peak_amplitude: float = 0.0

        # Adaptive threshold
        self._baseline_energy = config.breathing_threshold
        self._energy_history: deque[float] = deque(maxlen=100)

    def process(self, audio: np.ndarray, timestamp: float) -> tuple[bool, float]:
        """
        Process audio chunk to detect breathing.

        Args:
            audio: Audio samples (normalized -1 to 1)
            timestamp: Current timestamp

        Returns:
            Tuple of (breathing_detected, breathing_amplitude)
        """
        # Apply bandpass filter to isolate breathing frequencies
        filtered = self._bandpass.filter(audio)

        # Extract envelope
        envelope = self._envelope.extract(filtered)

        # Calculate mean envelope energy
        energy = float(np.mean(envelope))
        self._energy_history.append(energy)

        # Update adaptive baseline
        if len(self._energy_history) >= 50:
            self._baseline_energy = np.percentile(list(self._energy_history), 25)

        # Detect breath cycles using threshold crossing
        threshold = max(self._baseline_energy * 2, self._config.breathing_threshold)
        breathing_detected = energy > threshold

        # Track breath cycles
        if breathing_detected and not self._in_breath:
            # Start of breath
            self._in_breath = True
            self._breath_start = timestamp
        elif not breathing_detected and self._in_breath:
            # End of breath
            self._in_breath = False
            if self._breath_start is not None:
                cycle = BreathCycle(
                    start_time=self._breath_start,
                    peak_time=(self._breath_start + timestamp) / 2,
                    end_time=timestamp,
                    peak_amplitude=self._last_peak_amplitude,
                )
                self._breath_cycles.append(cycle)

        # Track peak amplitude during breath
        if self._in_breath:
            self._last_peak_amplitude = max(self._last_peak_amplitude, energy)
        else:
            self._last_peak_amplitude = 0.0

        # Store envelope sample for rate calculation
        self._envelope_history.append((timestamp, energy))

        # Normalize amplitude to 0-1 range
        max_energy = max(e for _, e in self._envelope_history) if self._envelope_history else 1.0
        amplitude = min(1.0, energy / max(max_energy, 0.001))

        return breathing_detected, amplitude

    def get_breathing_rate(self) -> float | None:
        """
        Calculate breathing rate from recent breath cycles.

        Returns:
            Breathing rate in BPM, or None if insufficient data
        """
        if len(self._breath_cycles) < self._config.min_breaths_for_rate:
            return None

        # Calculate inter-breath intervals
        cycles = list(self._breath_cycles)
        intervals = []
        for i in range(1, len(cycles)):
            interval = cycles[i].peak_time - cycles[i - 1].peak_time
            # Filter unrealistic intervals (2-15 seconds per breath)
            if 2.0 <= interval <= 15.0:
                intervals.append(interval)

        if len(intervals) < 2:
            return None

        # Use median for robustness
        median_interval = np.median(intervals)
        rate = 60.0 / median_interval

        # Clamp to realistic range (4-30 BPM)
        return max(4.0, min(30.0, rate))

    def get_confidence(self) -> float:
        """
        Calculate confidence in breathing detection.

        Returns:
            Confidence score 0.0 - 1.0
        """
        if len(self._breath_cycles) < 3:
            return 0.3

        # Check rhythm consistency
        cycles = list(self._breath_cycles)[-10:]
        if len(cycles) < 3:
            return 0.5

        intervals = []
        for i in range(1, len(cycles)):
            intervals.append(cycles[i].peak_time - cycles[i - 1].peak_time)

        if not intervals:
            return 0.5

        # Lower variance = higher confidence
        mean_interval = np.mean(intervals)
        std_interval = np.std(intervals)
        cv = std_interval / mean_interval if mean_interval > 0 else 1.0

        # CV of 0.3 or less is good rhythm
        confidence = max(0.3, min(1.0, 1.0 - cv))
        return confidence

    def reset(self) -> None:
        """Reset detector state."""
        self._bandpass.reset()
        self._envelope.reset()
        self._envelope_history.clear()
        self._breath_cycles.clear()
        self._in_breath = False
        self._breath_start = None


class SilenceDetector:
    """
    Detect periods of silence.

    Tracks how long audio has been below the silence threshold,
    which could indicate apnea when combined with breathing detection.
    """

    def __init__(self, config: AudioProcessorConfig):
        """
        Initialize silence detector.

        Args:
            config: Audio processing configuration
        """
        self._config = config
        self._silence_start: float | None = None
        self._current_silence_duration: float = 0.0
        self._is_silent = False

        # Adaptive threshold
        self._noise_floor = config.silence_threshold
        self._energy_history: deque[float] = deque(maxlen=100)

    def process(self, audio: np.ndarray, timestamp: float) -> float:
        """
        Process audio chunk to detect silence.

        Args:
            audio: Audio samples (normalized -1 to 1)
            timestamp: Current timestamp

        Returns:
            Duration of continuous silence in seconds
        """
        # Calculate RMS energy
        energy = float(np.sqrt(np.mean(audio ** 2)))
        self._energy_history.append(energy)

        # Update noise floor estimate (5th percentile of recent energy)
        if len(self._energy_history) >= 20:
            self._noise_floor = np.percentile(list(self._energy_history), 5)

        # Detect silence
        threshold = max(self._noise_floor * 2, self._config.silence_threshold)
        is_silent = energy < threshold

        if is_silent:
            if not self._is_silent:
                # Transition to silence
                self._silence_start = timestamp
                self._is_silent = True

            if self._silence_start is not None:
                self._current_silence_duration = timestamp - self._silence_start
        else:
            # Not silent
            self._is_silent = False
            self._silence_start = None
            self._current_silence_duration = 0.0

        return self._current_silence_duration

    def get_silence_duration(self) -> float:
        """Get current continuous silence duration."""
        return self._current_silence_duration

    def reset(self) -> None:
        """Reset detector state."""
        self._silence_start = None
        self._current_silence_duration = 0.0
        self._is_silent = False


class VocalizationDetector:
    """
    Detect vocalizations (non-rhythmic sounds).

    Distinguishes between regular breathing sounds and
    vocalizations like cries, gasps, or speech during sleep.
    """

    def __init__(self, config: AudioProcessorConfig):
        """
        Initialize vocalization detector.

        Args:
            config: Audio processing configuration
        """
        self._config = config

        # Bandpass for vocalization frequencies (200-3000 Hz)
        self._bandpass = BandpassFilter(
            config.vocalization_low_hz,
            config.vocalization_high_hz,
            config.sample_rate,
        )

        # Energy history for detecting sudden changes
        self._energy_history: deque[float] = deque(maxlen=20)
        self._vocalization_detected = False

    def process(self, audio: np.ndarray) -> bool:
        """
        Process audio chunk to detect vocalizations.

        Args:
            audio: Audio samples (normalized -1 to 1)

        Returns:
            True if vocalization detected
        """
        # Apply bandpass filter
        filtered = self._bandpass.filter(audio)

        # Calculate energy in vocalization band
        energy = float(np.sqrt(np.mean(filtered ** 2)))

        # Check for sudden energy spike
        if len(self._energy_history) >= 5:
            baseline = np.mean(list(self._energy_history))

            # Vocalization = sudden spike > 3x baseline
            if energy > baseline * 3 and energy > self._config.vocalization_threshold:
                self._vocalization_detected = True
            else:
                self._vocalization_detected = False

        self._energy_history.append(energy)

        return self._vocalization_detected

    def reset(self) -> None:
        """Reset detector state."""
        self._bandpass.reset()
        self._energy_history.clear()
        self._vocalization_detected = False


class SeizureSoundDetector:
    """
    Detect seizure-related sounds.

    Tonic-clonic seizures often produce rhythmic sounds:
    - Tonic phase: sustained vocalization/grunting
    - Clonic phase: rhythmic sounds at 1-8 Hz (muscle contractions)
    - May include teeth grinding, choking sounds

    Detection approach:
    1. Bandpass filter for seizure frequency range (300-2000 Hz)
    2. Extract envelope to find amplitude modulation
    3. Analyze envelope for rhythmic patterns in 1-8 Hz range
    4. Sustained rhythmic pattern = potential seizure
    """

    def __init__(self, config: AudioProcessorConfig):
        """
        Initialize seizure sound detector.

        Args:
            config: Audio processing configuration
        """
        self._config = config

        # Filter for seizure frequency range
        self._bandpass = BandpassFilter(
            config.seizure_low_hz,
            config.seizure_high_hz,
            config.sample_rate,
        )

        # Envelope extractor with faster smoothing for rhythm detection
        self._envelope = EnvelopeExtractor(config.sample_rate, smoothing_hz=15.0)

        # Store envelope samples for rhythm analysis
        # Need enough samples for FFT analysis of 1-8 Hz patterns
        samples_per_second = int(1.0 / config.chunk_duration)
        self._envelope_buffer: deque[float] = deque(
            maxlen=samples_per_second * 10  # 10 seconds of data
        )
        self._timestamps: deque[float] = deque(maxlen=samples_per_second * 10)

        # Detection state
        self._seizure_start: float | None = None
        self._current_duration: float = 0.0
        self._seizure_detected = False
        self._seizure_confidence = 0.0
        self._rhythmic_rate: float | None = None

        # Energy tracking for adaptive threshold
        self._energy_history: deque[float] = deque(maxlen=100)
        self._baseline_energy = config.seizure_energy_threshold

    def process(self, audio: np.ndarray, timestamp: float) -> SeizureAnalysis:
        """
        Process audio chunk to detect seizure sounds.

        Args:
            audio: Audio samples (normalized -1 to 1)
            timestamp: Current timestamp

        Returns:
            SeizureAnalysis with detection results
        """
        # Apply bandpass filter
        filtered = self._bandpass.filter(audio)

        # Extract envelope
        envelope = self._envelope.extract(filtered)
        mean_envelope = float(np.mean(envelope))

        # Update energy history for adaptive threshold
        self._energy_history.append(mean_envelope)
        if len(self._energy_history) >= 50:
            self._baseline_energy = np.percentile(list(self._energy_history), 25)

        # Store envelope sample
        self._envelope_buffer.append(mean_envelope)
        self._timestamps.append(timestamp)

        # Need at least 3 seconds of data for rhythm analysis
        min_samples = int(3.0 / self._config.chunk_duration)
        if len(self._envelope_buffer) < min_samples:
            return SeizureAnalysis(
                seizure_detected=False,
                seizure_confidence=0.0,
                rhythmic_rate=None,
                duration=0.0,
            )

        # Analyze for rhythmic patterns
        rhythmic, rate, confidence = self._analyze_rhythm()

        # For seizure detection, rhythm is the PRIMARY indicator
        # Energy threshold is very low - we care about pattern, not volume
        # Even quiet rhythmic sounds during sleep are suspicious
        energy_threshold = max(
            self._baseline_energy * 1.5,  # Just above noise floor
            self._config.seizure_energy_threshold,
        )
        has_some_energy = mean_envelope > energy_threshold

        # Detect seizure pattern - rhythm is key, energy is secondary
        # Strong rhythm alone is enough; weak rhythm needs some energy
        pattern_detected = (
            (rhythmic and confidence > 0.6) or  # Strong rhythm pattern
            (rhythmic and has_some_energy and confidence > 0.3)  # Weaker rhythm but audible
        )

        if pattern_detected:
            if self._seizure_start is None:
                self._seizure_start = timestamp
            self._current_duration = timestamp - self._seizure_start
            self._rhythmic_rate = rate

            # Only flag as seizure after minimum duration
            if self._current_duration >= self._config.seizure_min_duration:
                self._seizure_detected = True
                # Boost confidence if sustained longer
                duration_boost = min(0.2, (self._current_duration - 3.0) * 0.05)
                self._seizure_confidence = min(1.0, confidence + duration_boost)
        else:
            # Reset if pattern breaks
            self._seizure_start = None
            self._current_duration = 0.0
            self._seizure_detected = False
            self._seizure_confidence = 0.0
            self._rhythmic_rate = None

        return SeizureAnalysis(
            seizure_detected=self._seizure_detected,
            seizure_confidence=self._seizure_confidence,
            rhythmic_rate=self._rhythmic_rate,
            duration=self._current_duration,
        )

    def _analyze_rhythm(self) -> tuple[bool, float | None, float]:
        """
        Analyze envelope buffer for rhythmic patterns.

        Uses FFT to find dominant frequencies in the envelope,
        looking for sustained rhythmic patterns in the 1.5-8 Hz range.

        Key distinction from breathing/snoring:
        - Breathing: 0.2-0.5 Hz base rhythm
        - Snoring: has breathing-rate modulation (loud during exhale)
        - Seizure: sustained fast rhythm WITHOUT breathing modulation

        Returns:
            Tuple of (is_rhythmic, rate_hz, confidence)
        """
        envelope_data = np.array(list(self._envelope_buffer))

        # Calculate sample rate from timestamps
        if len(self._timestamps) < 2:
            return False, None, 0.0

        timestamps = list(self._timestamps)
        dt = (timestamps[-1] - timestamps[0]) / (len(timestamps) - 1)
        if dt <= 0:
            return False, None, 0.0

        # Remove DC component (mean)
        envelope_data = envelope_data - np.mean(envelope_data)

        # Apply window to reduce spectral leakage
        window = np.hanning(len(envelope_data))
        envelope_data = envelope_data * window

        # FFT
        fft_result = np.fft.rfft(envelope_data)
        freqs = np.fft.rfftfreq(len(envelope_data), d=dt)
        magnitudes = np.abs(fft_result)

        # Check for breathing-rate energy (indicates snoring pattern)
        breathing_mask = (freqs >= self._config.breathing_rate_low_hz) & (
            freqs <= self._config.breathing_rate_high_hz
        )
        breathing_energy = np.sum(magnitudes[breathing_mask]) if np.any(breathing_mask) else 0

        # Find frequencies in seizure rhythm range (1.5-8 Hz)
        seizure_mask = (freqs >= self._config.seizure_rhythm_low_hz) & (
            freqs <= self._config.seizure_rhythm_high_hz
        )

        if not np.any(seizure_mask):
            return False, None, 0.0

        seizure_freqs = freqs[seizure_mask]
        seizure_mags = magnitudes[seizure_mask]

        # Find peak frequency
        peak_idx = np.argmax(seizure_mags)
        peak_freq = seizure_freqs[peak_idx]
        peak_mag = seizure_mags[peak_idx]

        # Calculate total energy and peak prominence
        total_mag = np.sum(magnitudes[1:])  # Exclude DC
        if total_mag <= 0:
            return False, None, 0.0

        # Energy in seizure band vs total
        seizure_energy = np.sum(seizure_mags)
        energy_ratio = seizure_energy / total_mag

        # Check if this looks like snoring (breathing-modulated pattern)
        # Snoring has significant energy at breathing rate AND at higher freq
        # Seizure has energy at seizure rate but NOT at breathing rate
        if breathing_energy > 0:
            seizure_to_breathing_ratio = seizure_energy / breathing_energy
            # If breathing energy is dominant, this is likely snoring
            if seizure_to_breathing_ratio < 2.0:
                # Looks like snoring - fast sounds modulated by breath
                return False, None, 0.0

        # Peak should be at least 1.5x the average magnitude in the band
        avg_mag = np.mean(seizure_mags) if len(seizure_mags) > 0 else 0
        peak_prominence = peak_mag / avg_mag if avg_mag > 0 else 0

        # Rhythmic if we have a clear peak and energy concentration
        # Thresholds:
        # - 15% energy concentration in seizure band
        # - 1.5x peak prominence
        is_rhythmic = (energy_ratio > 0.15) and (peak_prominence > 1.5)

        # Confidence based on peak prominence and energy concentration
        # Reduce confidence if there's any breathing-rate energy
        base_confidence = min(1.0, (energy_ratio * 3) * (peak_prominence / 3))

        # Penalize if breathing energy is present (might be snoring)
        if breathing_energy > 0 and seizure_energy > 0:
            snoring_penalty = min(0.3, breathing_energy / seizure_energy * 0.5)
            confidence = max(0.0, base_confidence - snoring_penalty)
        else:
            confidence = base_confidence

        return is_rhythmic, float(peak_freq), confidence

    def reset(self) -> None:
        """Reset detector state."""
        self._bandpass.reset()
        self._envelope.reset()
        self._envelope_buffer.clear()
        self._timestamps.clear()
        self._seizure_start = None
        self._current_duration = 0.0
        self._seizure_detected = False
        self._seizure_confidence = 0.0
        self._rhythmic_rate = None


class AudioProcessor:
    """
    Main audio processing pipeline.

    Combines breathing detection, silence detection, vocalization
    detection, and seizure sound detection into a unified analysis.
    """

    def __init__(self, config: AudioProcessorConfig | None = None):
        """
        Initialize audio processor.

        Args:
            config: Processing configuration, or None for defaults
        """
        self._config = config or AudioProcessorConfig()

        self._breathing = BreathingDetector(self._config)
        self._silence = SilenceDetector(self._config)
        self._vocalization = VocalizationDetector(self._config)
        self._seizure = SeizureSoundDetector(self._config)

        self._chunk_samples = int(self._config.chunk_duration * self._config.sample_rate)

    @property
    def chunk_samples(self) -> int:
        """Number of samples per processing chunk."""
        return self._chunk_samples

    @property
    def sample_rate(self) -> int:
        """Expected sample rate."""
        return self._config.sample_rate

    def process(self, audio: np.ndarray, timestamp: float) -> BreathingAnalysis:
        """
        Process audio chunk through full pipeline.

        Args:
            audio: Audio samples (normalized -1 to 1)
            timestamp: Current timestamp

        Returns:
            BreathingAnalysis with all detection results
        """
        # Normalize audio to -1 to 1 range
        if audio.dtype != np.float32 and audio.dtype != np.float64:
            if audio.dtype == np.int16:
                audio = audio.astype(np.float32) / 32768.0
            elif audio.dtype == np.int32:
                audio = audio.astype(np.float32) / 2147483648.0
            else:
                audio = audio.astype(np.float32)

        # Calculate overall energy
        energy_level = float(np.sqrt(np.mean(audio ** 2)))

        # Run detectors
        breathing_detected, breathing_amplitude = self._breathing.process(audio, timestamp)
        silence_duration = self._silence.process(audio, timestamp)
        vocalization_detected = self._vocalization.process(audio)
        seizure_analysis = self._seizure.process(audio, timestamp)

        # Get breathing rate and confidence
        breathing_rate = self._breathing.get_breathing_rate()
        breathing_confidence = self._breathing.get_confidence()

        return BreathingAnalysis(
            breathing_detected=breathing_detected,
            breathing_rate=breathing_rate,
            breathing_amplitude=breathing_amplitude,
            breathing_confidence=breathing_confidence,
            silence_duration=silence_duration,
            vocalization_detected=vocalization_detected,
            seizure_detected=seizure_analysis.seizure_detected,
            seizure_confidence=seizure_analysis.seizure_confidence,
            energy_level=energy_level,
        )

    def reset(self) -> None:
        """Reset all detector states."""
        self._breathing.reset()
        self._silence.reset()
        self._vocalization.reset()
        self._seizure.reset()
