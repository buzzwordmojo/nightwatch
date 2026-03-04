"""
Audio detector for Nightwatch.

Uses a USB microphone to detect breathing sounds, silence (potential apnea),
vocalizations, and seizure-related rhythmic sounds during sleep.
"""

from __future__ import annotations

import asyncio
import logging
import time
from pathlib import Path
from typing import Any

import numpy as np

from nightwatch.core.config import AudioConfig
from nightwatch.core.events import EventState, Publisher
from nightwatch.detectors.base import BaseDetector, CalibrationResult
from nightwatch.detectors.audio.processing import (
    AudioProcessor,
    AudioProcessorConfig,
    BreathingAnalysis,
)

logger = logging.getLogger(__name__)


class AudioDetector(BaseDetector):
    """
    Detect breathing and vocalizations via USB microphone.

    Uses sounddevice for cross-platform audio capture and processes
    the audio stream to detect:
    - Breathing sounds (rhythmic patterns in 200-800 Hz)
    - Silence periods (potential apnea indicator)
    - Vocalizations (cries, gasps, speech)
    - Seizure sounds (rhythmic patterns at 1-8 Hz, tonic-clonic)

    Event value format:
    {
        "breathing_detected": bool,
        "breathing_rate": float | None,  # BPM
        "breathing_amplitude": float,     # 0-1
        "silence_duration": float,        # seconds
        "vocalization_detected": bool,
        "seizure_detected": bool,
        "seizure_confidence": float,      # 0-1
    }
    """

    def __init__(
        self,
        config: AudioConfig | None = None,
        publisher: Publisher | None = None,
    ):
        """
        Initialize audio detector.

        Args:
            config: Audio configuration, or None for defaults
            publisher: ZeroMQ publisher for events
        """
        super().__init__("audio", publisher)

        self._config = config or AudioConfig()

        # Processing
        proc_config = AudioProcessorConfig(
            sample_rate=self._config.sample_rate,
            chunk_duration=0.1,
            breathing_threshold=self._config.breathing_threshold,
            silence_threshold=self._config.silence_threshold,
        )
        self._processor = AudioProcessor(proc_config)

        # Audio capture
        self._stream = None
        self._audio_buffer: asyncio.Queue[np.ndarray] = asyncio.Queue()

        # Live audio listeners (for dashboard streaming)
        self._audio_listeners: set[asyncio.Queue] = set()

        # Noise reduction
        self._noise_profile_path = Path("/var/lib/nightwatch/noise_profile.npy")

        # State
        self._device_name: str | None = None
        self._last_analysis: BreathingAnalysis | None = None
        self._calibrated = False
        self._baseline_noise = 0.0

    async def _connect(self) -> None:
        """Connect to USB microphone."""
        try:
            import sounddevice as sd
        except ImportError:
            raise ConnectionError(
                "sounddevice not installed. Run: pip install sounddevice"
            )

        # Find device
        device_id = None
        device_name = self._config.device

        if device_name:
            # Search for specified device
            devices = sd.query_devices()
            for i, d in enumerate(devices):
                if device_name.lower() in d["name"].lower():
                    if d["max_input_channels"] > 0:
                        device_id = i
                        self._device_name = d["name"]
                        break

            if device_id is None:
                raise ConnectionError(f"Audio device not found: {device_name}")
        else:
            # Use default input device
            try:
                default = sd.query_devices(kind="input")
                device_id = None  # Let sounddevice use default
                self._device_name = default["name"]
            except Exception as e:
                raise ConnectionError(f"No audio input device available: {e}")

        # Create audio callback
        def audio_callback(indata, frames, time_info, status):
            if status:
                pass  # Ignore buffer warnings for now
            # Copy to avoid buffer reuse issues
            self._audio_buffer.put_nowait(indata.copy().flatten())

        # Load saved noise profile if it exists
        if self._noise_profile_path.exists():
            self._processor.noise_reducer.load(self._noise_profile_path)

        # Open stream
        try:
            self._stream = sd.InputStream(
                device=device_id,
                channels=1,
                samplerate=self._config.sample_rate,
                blocksize=self._processor.chunk_samples,
                dtype=np.float32,
                callback=audio_callback,
            )
            self._stream.start()
        except Exception as e:
            raise ConnectionError(f"Failed to open audio stream: {e}")

    async def _disconnect(self) -> None:
        """Close audio stream."""
        if self._stream is not None:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception:
                pass
            self._stream = None

    def subscribe_audio(self) -> asyncio.Queue:
        """Subscribe to raw audio chunks for live streaming."""
        queue: asyncio.Queue = asyncio.Queue(maxsize=50)
        self._audio_listeners.add(queue)
        return queue

    def unsubscribe_audio(self, queue: asyncio.Queue) -> None:
        """Unsubscribe from raw audio chunks."""
        self._audio_listeners.discard(queue)

    async def _read_loop(self) -> None:
        """Process audio stream and emit events."""
        emit_interval = 1.0 / self._config.update_rate_hz
        last_emit = 0.0

        while self._running:
            try:
                # Get audio chunk with timeout
                audio = await asyncio.wait_for(
                    self._audio_buffer.get(),
                    timeout=1.0,
                )

                # Apply software gain (amplify quiet signals)
                if self._config.gain != 1.0:
                    audio = np.clip(audio * self._config.gain, -1.0, 1.0)

                # Feed noise reducer if sampling
                if self._processor.noise_reducer.is_sampling:
                    self._processor.noise_reducer.add_sample(audio)

                # Apply noise reduction so detectors and listeners see clean audio
                audio = self._processor.noise_reducer.reduce(audio)

                # Fan out to live audio listeners (post noise reduction)
                for listener in list(self._audio_listeners):
                    try:
                        listener.put_nowait(audio)
                    except asyncio.QueueFull:
                        pass  # Drop frames for slow consumers

                # Process audio
                timestamp = time.time()
                analysis = self._processor.process(audio, timestamp)
                self._last_analysis = analysis

                # Emit at configured rate
                if timestamp - last_emit >= emit_interval:
                    await self._emit_analysis(analysis)
                    last_emit = timestamp

            except asyncio.TimeoutError:
                # No audio received, emit warning
                await self._emit_event(
                    state=EventState.UNCERTAIN,
                    confidence=0.0,
                    value={
                        "breathing_detected": False,
                        "breathing_rate": None,
                        "breathing_amplitude": 0.0,
                        "silence_duration": 0.0,
                        "vocalization_detected": False,
                        "seizure_detected": False,
                        "seizure_confidence": 0.0,
                        "error": "No audio input",
                    },
                )

            except Exception as e:
                await self._handle_error(e)
                await asyncio.sleep(0.1)

    async def _emit_analysis(self, analysis: BreathingAnalysis) -> None:
        """Emit event based on breathing analysis."""
        # Determine state
        state = EventState.NORMAL

        # Warning: extended silence or low breathing
        if analysis.silence_duration > 5.0:
            state = EventState.WARNING

        # Alert: very extended silence or vocalization
        if analysis.silence_duration > 10.0:
            state = EventState.ALERT
        elif analysis.vocalization_detected:
            state = EventState.WARNING

        # Seizure detection is highest priority alert
        if analysis.seizure_detected:
            state = EventState.ALERT

        # Confidence based on breathing detection (or seizure if detected)
        if analysis.seizure_detected:
            confidence = analysis.seizure_confidence
        elif analysis.breathing_detected:
            confidence = analysis.breathing_confidence
        else:
            confidence = 0.5

        await self._emit_event(
            state=state,
            confidence=confidence,
            value={
                "breathing_detected": analysis.breathing_detected,
                "breathing_rate": round(analysis.breathing_rate, 1) if analysis.breathing_rate else None,
                "breathing_amplitude": round(analysis.breathing_amplitude, 2),
                "silence_duration": round(analysis.silence_duration, 1),
                "vocalization_detected": analysis.vocalization_detected,
                "seizure_detected": analysis.seizure_detected,
                "seizure_confidence": round(analysis.seizure_confidence, 2),
            },
        )

    async def sample_noise(self, duration: float = 5.0) -> bool:
        """Sample background noise and build a spectral subtraction profile.

        Args:
            duration: Seconds to sample (default 5s)

        Returns:
            True if profile was created successfully.
        """
        reducer = self._processor.noise_reducer
        reducer.start_sampling()
        logger.info("Noise sampling started for %.1fs", duration)
        await asyncio.sleep(duration)
        ok = reducer.finish_sampling()
        if ok:
            reducer.save(self._noise_profile_path)
            logger.info("Noise profile saved")
        else:
            logger.warning("Noise sampling failed — no samples collected")
        return ok

    def set_noise_enabled(self, enabled: bool) -> None:
        """Enable or disable noise reduction without clearing the profile."""
        self._processor.noise_reducer.enabled = enabled

    def clear_noise_profile(self) -> None:
        """Clear the noise reduction profile and delete the saved file."""
        self._processor.noise_reducer.clear()
        if self._noise_profile_path.exists():
            self._noise_profile_path.unlink()
            logger.info("Noise profile deleted")

    async def _calibrate_impl(self) -> CalibrationResult:
        """
        Calibrate audio detection.

        Measures ambient noise level to set appropriate thresholds.
        """
        if self._stream is None:
            return CalibrationResult(
                success=False,
                message="Audio stream not connected",
            )

        start_time = time.time()
        noise_samples = []

        # Collect 5 seconds of ambient audio
        while time.time() - start_time < 5.0:
            try:
                audio = await asyncio.wait_for(
                    self._audio_buffer.get(),
                    timeout=1.0,
                )
                energy = float(np.sqrt(np.mean(audio ** 2)))
                noise_samples.append(energy)
            except asyncio.TimeoutError:
                pass

        if not noise_samples:
            return CalibrationResult(
                success=False,
                message="No audio samples received during calibration",
            )

        # Calculate baseline noise (median of samples)
        self._baseline_noise = float(np.median(noise_samples))
        self._calibrated = True

        # Calculate recommended thresholds
        recommended_silence = self._baseline_noise * 2
        recommended_breathing = self._baseline_noise * 4

        return CalibrationResult(
            success=True,
            message=f"Calibration complete. Baseline noise: {self._baseline_noise:.4f}",
            baseline_values={
                "noise_floor": self._baseline_noise,
            },
            recommended_settings={
                "silence_threshold": recommended_silence,
                "breathing_threshold": recommended_breathing,
            },
            duration_seconds=time.time() - start_time,
        )

    def _get_detector_specific_state(self) -> dict[str, Any]:
        """Get audio detector state."""
        return {
            "device": self._device_name,
            "sample_rate": self._config.sample_rate,
            "calibrated": self._calibrated,
            "baseline_noise": self._baseline_noise,
            "last_analysis": {
                "breathing_detected": self._last_analysis.breathing_detected,
                "breathing_rate": self._last_analysis.breathing_rate,
                "silence_duration": self._last_analysis.silence_duration,
                "seizure_detected": self._last_analysis.seizure_detected,
                "seizure_confidence": self._last_analysis.seizure_confidence,
            } if self._last_analysis else None,
        }


class MockAudioDetector(BaseDetector):
    """
    Mock audio detector for testing.

    Generates synthetic breathing patterns without requiring
    actual audio hardware.
    """

    def __init__(
        self,
        publisher: Publisher | None = None,
        update_rate_hz: float = 10.0,
        base_breathing_rate: float = 14.0,
        noise_level: float = 0.1,
    ):
        """
        Initialize mock audio detector.

        Args:
            publisher: ZeroMQ publisher
            update_rate_hz: Event emission rate
            base_breathing_rate: Simulated breathing rate BPM
            noise_level: Amount of noise to add
        """
        super().__init__("audio", publisher)

        self._update_rate_hz = update_rate_hz
        self._base_breathing_rate = base_breathing_rate
        self._noise_level = noise_level

        # Anomaly injection
        self._inject_silence = False
        self._silence_start: float | None = None
        self._silence_duration = 0.0
        self._inject_vocalization = False
        self._inject_seizure = False
        self._seizure_start: float | None = None

        # Simulated state
        self._breathing_phase = 0.0

        # Live audio listeners (for dashboard streaming)
        self._audio_listeners: set[asyncio.Queue] = set()

        # Synthetic audio params
        self._sample_rate = 16000

    def subscribe_audio(self) -> asyncio.Queue:
        """Subscribe to raw audio chunks for live streaming."""
        queue: asyncio.Queue = asyncio.Queue(maxsize=50)
        self._audio_listeners.add(queue)
        return queue

    def unsubscribe_audio(self, queue: asyncio.Queue) -> None:
        """Unsubscribe from raw audio chunks."""
        self._audio_listeners.discard(queue)

    async def _connect(self) -> None:
        """Mock connection."""
        await asyncio.sleep(0.05)

    async def _disconnect(self) -> None:
        """Mock disconnect."""
        pass

    async def _read_loop(self) -> None:
        """Generate synthetic audio events."""
        import random

        interval = 1.0 / self._update_rate_hz
        chunk_samples = int(self._sample_rate * interval)

        while self._running:
            timestamp = time.time()

            # Simulate breathing cycle
            breath_period = 60.0 / self._base_breathing_rate
            self._breathing_phase += interval / breath_period
            if self._breathing_phase > 1.0:
                self._breathing_phase -= 1.0

            # Breathing amplitude follows sine pattern
            breathing_amplitude = 0.5 + 0.5 * np.sin(2 * np.pi * self._breathing_phase)
            breathing_amplitude += random.gauss(0, self._noise_level * 0.2)
            breathing_amplitude = max(0, min(1, breathing_amplitude))

            # Add noise to rate
            rate_noise = random.gauss(0, self._noise_level * 2)
            breathing_rate = self._base_breathing_rate + rate_noise

            # Handle injected anomalies
            silence_duration = 0.0
            breathing_detected = True
            vocalization = False
            seizure_detected = False
            seizure_confidence = 0.0

            if self._inject_silence:
                if self._silence_start is None:
                    self._silence_start = timestamp
                silence_duration = timestamp - self._silence_start
                breathing_detected = False
                breathing_amplitude = 0.0
            else:
                self._silence_start = None

            if self._inject_vocalization:
                vocalization = True
                self._inject_vocalization = False  # One-shot

            if self._inject_seizure:
                if self._seizure_start is None:
                    self._seizure_start = timestamp
                seizure_duration = timestamp - self._seizure_start
                # Seizure detection requires minimum duration
                if seizure_duration >= 3.0:
                    seizure_detected = True
                    seizure_confidence = min(0.95, 0.5 + seizure_duration * 0.05)

            # Determine state
            state = EventState.NORMAL
            if silence_duration > 5.0:
                state = EventState.WARNING
            if silence_duration > 10.0:
                state = EventState.ALERT
            if vocalization:
                state = EventState.WARNING
            if seizure_detected:
                state = EventState.ALERT

            # Generate synthetic audio for listeners
            if self._audio_listeners:
                t = np.arange(chunk_samples) / self._sample_rate
                # Breathing-like tone modulated by breathing phase
                freq = 400.0  # Hz
                envelope = 0.3 * (0.5 + 0.5 * np.sin(2 * np.pi * self._breathing_phase))
                audio_chunk = (envelope * np.sin(2 * np.pi * freq * t + timestamp)).astype(np.float32)
                audio_chunk += (np.random.randn(chunk_samples) * 0.02).astype(np.float32)
                for listener in list(self._audio_listeners):
                    try:
                        listener.put_nowait(audio_chunk)
                    except asyncio.QueueFull:
                        pass

            await self._emit_event(
                state=state,
                confidence=seizure_confidence if seizure_detected else (0.85 if breathing_detected else 0.5),
                value={
                    "breathing_detected": breathing_detected,
                    "breathing_rate": round(breathing_rate, 1) if breathing_detected else None,
                    "breathing_amplitude": round(breathing_amplitude, 2),
                    "silence_duration": round(silence_duration, 1),
                    "vocalization_detected": vocalization,
                    "seizure_detected": seizure_detected,
                    "seizure_confidence": round(seizure_confidence, 2),
                },
            )

            await asyncio.sleep(interval)

    async def _calibrate_impl(self) -> CalibrationResult:
        """Mock calibration."""
        await asyncio.sleep(1.0)
        return CalibrationResult(
            success=True,
            message="Mock audio calibration complete",
            baseline_values={"noise_floor": 0.01},
            duration_seconds=1.0,
        )

    def _get_detector_specific_state(self) -> dict[str, Any]:
        """Get mock state."""
        return {
            "mock": True,
            "base_breathing_rate": self._base_breathing_rate,
            "inject_silence": self._inject_silence,
            "inject_seizure": self._inject_seizure,
        }

    def inject_silence(self, enable: bool = True) -> None:
        """
        Inject silence anomaly.

        Args:
            enable: True to start silence, False to end
        """
        self._inject_silence = enable
        if not enable:
            self._silence_start = None

    def inject_vocalization(self) -> None:
        """Inject a single vocalization event."""
        self._inject_vocalization = True

    def inject_seizure(self, enable: bool = True) -> None:
        """
        Inject seizure sound anomaly.

        Args:
            enable: True to start seizure sounds, False to end
        """
        self._inject_seizure = enable
        if not enable:
            self._seizure_start = None
