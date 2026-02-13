"""
Audio notifier for local alarm output.

Supports:
- Speaker output (WAV files)
- GPIO buzzer output
- Escalating volume
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

from nightwatch.core.config import AudioNotifierConfig
from nightwatch.core.events import Alert, EventSeverity
from nightwatch.core.notifiers.base import BaseNotifier


class AudioNotifier(BaseNotifier):
    """
    Local audio alarm notification.

    Plays sounds through the system speaker or triggers a GPIO buzzer
    when alerts are triggered. Supports escalating volume over time.
    """

    def __init__(self, config: AudioNotifierConfig | None = None):
        self._config = config or AudioNotifierConfig()
        self._playing = False
        self._current_volume = self._config.initial_volume
        self._escalation_task: asyncio.Task | None = None
        self._stop_event = asyncio.Event()

    @property
    def name(self) -> str:
        return "audio"

    @property
    def enabled(self) -> bool:
        return self._config.enabled

    async def notify(self, alert: Alert) -> bool:
        """Play alarm sound for alert."""
        if not self._config.enabled:
            return False

        # Select sound based on severity
        if alert.severity == EventSeverity.CRITICAL:
            sound_name = "critical"
        elif alert.severity == EventSeverity.WARNING:
            sound_name = "warning"
        else:
            sound_name = "info"

        # Get sound file path
        sound_file = self._get_sound_file(sound_name)

        try:
            await self._play_alarm(sound_file, alert.severity)
            return True
        except Exception as e:
            print(f"Audio notifier error: {e}")
            return False

    async def test(self) -> bool:
        """Play test sound."""
        try:
            sound_file = self._get_sound_file("test")
            await self._play_sound(sound_file, self._config.initial_volume)
            return True
        except Exception as e:
            print(f"Audio test error: {e}")
            return False

    async def stop(self) -> None:
        """Stop any playing alarm."""
        self._stop_event.set()

        if self._escalation_task:
            self._escalation_task.cancel()
            try:
                await self._escalation_task
            except asyncio.CancelledError:
                pass
            self._escalation_task = None

        self._playing = False
        self._current_volume = self._config.initial_volume

    async def _play_alarm(self, sound_file: Path | None, severity: EventSeverity) -> None:
        """Play alarm with optional escalation."""
        self._stop_event.clear()
        self._playing = True
        self._current_volume = self._config.initial_volume

        # Start escalation task for critical alerts
        if severity == EventSeverity.CRITICAL and self._config.escalation_enabled:
            self._escalation_task = asyncio.create_task(self._escalate_volume())

        # Play sound (or buzzer pattern)
        start_time = asyncio.get_event_loop().time()
        max_duration = self._config.max_duration_seconds

        while self._playing:
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed >= max_duration:
                break

            if self._stop_event.is_set():
                break

            if sound_file and sound_file.exists():
                await self._play_sound(sound_file, self._current_volume)
            else:
                await self._play_buzzer_pattern(severity)

            # Brief pause between repeats
            try:
                await asyncio.wait_for(self._stop_event.wait(), timeout=1.0)
                break  # Stop event was set
            except asyncio.TimeoutError:
                pass  # Continue playing

        self._playing = False

    async def _escalate_volume(self) -> None:
        """Gradually increase volume over time."""
        interval = self._config.escalation_interval_seconds

        while self._playing and self._current_volume < self._config.max_volume:
            await asyncio.sleep(interval)

            if not self._playing:
                break

            # Increase volume by 10%
            self._current_volume = min(
                self._config.max_volume,
                self._current_volume + 10,
            )

    async def _play_sound(self, sound_file: Path, volume: int) -> None:
        """Play a sound file using system audio."""
        try:
            import sounddevice as sd
            import numpy as np

            # For now, generate a simple tone if we can't load the file
            # In production, use scipy.io.wavfile or similar to load WAV
            sample_rate = 44100
            duration = 0.5  # seconds
            frequency = 880  # Hz (A5)

            t = np.linspace(0, duration, int(sample_rate * duration), False)
            tone = np.sin(2 * np.pi * frequency * t) * (volume / 100.0)

            # Play tone
            sd.play(tone.astype(np.float32), sample_rate)
            sd.wait()

        except ImportError:
            # Fallback: try using aplay on Linux
            await self._play_with_aplay(sound_file, volume)
        except Exception as e:
            print(f"Sound playback error: {e}")

    async def _play_with_aplay(self, sound_file: Path, volume: int) -> None:
        """Play sound using aplay (Linux ALSA)."""
        try:
            proc = await asyncio.create_subprocess_exec(
                "aplay",
                "-q",  # Quiet
                str(sound_file),
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
            await proc.wait()
        except Exception as e:
            print(f"aplay error: {e}")

    async def _play_buzzer_pattern(self, severity: EventSeverity) -> None:
        """Play pattern on GPIO buzzer."""
        # Define patterns: list of (on_seconds, off_seconds)
        patterns = {
            EventSeverity.CRITICAL: [(0.3, 0.1), (0.3, 0.1), (0.3, 0.5)],
            EventSeverity.WARNING: [(0.5, 0.5)],
            EventSeverity.INFO: [(0.2, 0.8)],
        }

        pattern = patterns.get(severity, [(0.5, 0.5)])

        try:
            # Try to use RPi.GPIO for hardware buzzer
            await self._play_gpio_pattern(pattern)
        except Exception:
            # Fallback to software beep
            await self._play_software_beep(pattern)

    async def _play_gpio_pattern(self, pattern: list[tuple[float, float]]) -> None:
        """Play pattern using GPIO buzzer."""
        try:
            import RPi.GPIO as GPIO

            pin = self._config.buzzer_gpio_pin
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(pin, GPIO.OUT)

            for on_time, off_time in pattern:
                if self._stop_event.is_set():
                    break

                GPIO.output(pin, GPIO.HIGH)
                await asyncio.sleep(on_time)
                GPIO.output(pin, GPIO.LOW)
                await asyncio.sleep(off_time)

        except ImportError:
            raise  # Let caller handle
        except Exception as e:
            print(f"GPIO error: {e}")

    async def _play_software_beep(self, pattern: list[tuple[float, float]]) -> None:
        """Play pattern using software beep (for development)."""
        try:
            import sounddevice as sd
            import numpy as np

            sample_rate = 44100
            frequency = 2000  # Hz

            for on_time, off_time in pattern:
                if self._stop_event.is_set():
                    break

                # Generate tone
                t = np.linspace(0, on_time, int(sample_rate * on_time), False)
                volume = self._current_volume / 100.0
                tone = np.sin(2 * np.pi * frequency * t) * volume

                sd.play(tone.astype(np.float32), sample_rate)
                sd.wait()

                await asyncio.sleep(off_time)

        except Exception as e:
            print(f"Software beep error: {e}")

    def _get_sound_file(self, sound_name: str) -> Path | None:
        """Get path to sound file."""
        sounds_dir = Path(self._config.sounds_dir)

        # Try common audio formats
        for ext in [".wav", ".mp3", ".ogg"]:
            path = sounds_dir / f"{sound_name}{ext}"
            if path.exists():
                return path

        return None

    def set_volume(self, volume: int) -> None:
        """Set current volume (0-100)."""
        self._current_volume = max(0, min(100, volume))


class MockAudioNotifier(AudioNotifier):
    """Mock audio notifier for testing."""

    def __init__(self, config: AudioNotifierConfig | None = None):
        super().__init__(config)
        self.notifications: list[Alert] = []
        self.test_called = False

    async def notify(self, alert: Alert) -> bool:
        """Record notification without playing sound."""
        self.notifications.append(alert)
        return True

    async def test(self) -> bool:
        """Record test call."""
        self.test_called = True
        return True

    async def _play_sound(self, sound_file: Path, volume: int) -> None:
        """Don't actually play sound in mock."""
        pass

    async def _play_buzzer_pattern(self, severity: EventSeverity) -> None:
        """Don't actually buzz in mock."""
        pass
