"""
Tests for audio notifier.

Covers:
- Alert notification
- Volume escalation
- Sound playback
- Buzzer patterns
- MockAudioNotifier
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from nightwatch.core.config import AudioNotifierConfig
from nightwatch.core.events import Alert, EventSeverity
from nightwatch.core.notifiers.audio import AudioNotifier, MockAudioNotifier


# =============================================================================
# AudioNotifier Tests
# =============================================================================


class TestAudioNotifier:
    """Tests for AudioNotifier."""

    @pytest.fixture
    def notifier(self):
        """Create audio notifier."""
        return AudioNotifier(AudioNotifierConfig())

    @pytest.fixture
    def disabled_notifier(self):
        """Create disabled audio notifier."""
        return AudioNotifier(AudioNotifierConfig(enabled=False))

    def test_default_config(self, notifier):
        """Default configuration values."""
        assert notifier._config.enabled is True
        assert notifier._config.output_type == "speaker"
        assert notifier._config.initial_volume == 60
        assert notifier._config.max_volume == 100
        assert notifier._config.escalation_enabled is True

    def test_name_property(self, notifier):
        """Name property returns 'audio'."""
        assert notifier.name == "audio"

    def test_enabled_property(self, notifier):
        """Enabled property reflects config."""
        assert notifier.enabled is True

    def test_disabled_notifier(self, disabled_notifier):
        """Disabled notifier reports disabled."""
        assert disabled_notifier.enabled is False

    @pytest.mark.asyncio
    async def test_notify_disabled_returns_false(self, disabled_notifier):
        """Notify on disabled notifier returns False."""
        alert = Alert(
            id="test-1",
            severity=EventSeverity.WARNING,
            rule_name="test",
            message="Test alert",
            timestamp=0,
        )

        result = await disabled_notifier.notify(alert)

        assert result is False

    @pytest.mark.asyncio
    async def test_notify_critical_uses_critical_sound(self, notifier):
        """Critical alert uses critical sound."""
        alert = Alert(
            id="test-1",
            severity=EventSeverity.CRITICAL,
            rule_name="test",
            message="Critical alert",
            timestamp=0,
        )

        with patch.object(notifier, "_play_alarm", new_callable=AsyncMock) as mock_play:
            await notifier.notify(alert)
            mock_play.assert_called_once()
            # Check severity was passed
            call_args = mock_play.call_args
            assert call_args[0][1] == EventSeverity.CRITICAL

    @pytest.mark.asyncio
    async def test_notify_warning_uses_warning_sound(self, notifier):
        """Warning alert uses warning sound."""
        alert = Alert(
            id="test-1",
            severity=EventSeverity.WARNING,
            rule_name="test",
            message="Warning alert",
            timestamp=0,
        )

        with patch.object(notifier, "_play_alarm", new_callable=AsyncMock) as mock_play:
            await notifier.notify(alert)
            mock_play.assert_called_once()
            call_args = mock_play.call_args
            assert call_args[0][1] == EventSeverity.WARNING

    @pytest.mark.asyncio
    async def test_notify_info_uses_info_sound(self, notifier):
        """Info alert uses info sound."""
        alert = Alert(
            id="test-1",
            severity=EventSeverity.INFO,
            rule_name="test",
            message="Info alert",
            timestamp=0,
        )

        with patch.object(notifier, "_play_alarm", new_callable=AsyncMock) as mock_play:
            await notifier.notify(alert)
            mock_play.assert_called_once()
            call_args = mock_play.call_args
            assert call_args[0][1] == EventSeverity.INFO

    @pytest.mark.asyncio
    async def test_test_plays_test_sound(self, notifier):
        """Test method plays test sound."""
        with patch.object(notifier, "_play_sound", new_callable=AsyncMock) as mock_play:
            result = await notifier.test()

            assert result is True
            mock_play.assert_called_once()

    @pytest.mark.asyncio
    async def test_stop_sets_stop_event(self, notifier):
        """Stop sets stop event."""
        await notifier.stop()

        assert notifier._stop_event.is_set()
        assert notifier._playing is False

    @pytest.mark.asyncio
    async def test_stop_cancels_escalation_task(self, notifier):
        """Stop cancels escalation task."""
        # Create a mock task
        notifier._escalation_task = asyncio.create_task(asyncio.sleep(100))

        await notifier.stop()

        assert notifier._escalation_task is None

    def test_set_volume(self, notifier):
        """Set volume changes current volume."""
        notifier.set_volume(80)
        assert notifier._current_volume == 80

    def test_set_volume_clamped_low(self, notifier):
        """Volume is clamped at 0."""
        notifier.set_volume(-10)
        assert notifier._current_volume == 0

    def test_set_volume_clamped_high(self, notifier):
        """Volume is clamped at 100."""
        notifier.set_volume(150)
        assert notifier._current_volume == 100

    def test_get_sound_file_nonexistent(self, notifier):
        """Get sound file returns None for nonexistent."""
        result = notifier._get_sound_file("nonexistent_sound")
        assert result is None

    def test_get_sound_file_with_existing(self, notifier, tmp_path):
        """Get sound file returns path for existing file."""
        notifier._config.sounds_dir = str(tmp_path)

        # Create test sound file
        (tmp_path / "test.wav").write_text("fake wav")

        result = notifier._get_sound_file("test")
        assert result == tmp_path / "test.wav"

    def test_get_sound_file_tries_extensions(self, notifier, tmp_path):
        """Get sound file tries multiple extensions."""
        notifier._config.sounds_dir = str(tmp_path)

        # Create mp3 file
        (tmp_path / "alert.mp3").write_text("fake mp3")

        result = notifier._get_sound_file("alert")
        assert result == tmp_path / "alert.mp3"


class TestAudioNotifierEscalation:
    """Tests for volume escalation."""

    @pytest.fixture
    def notifier(self):
        """Create notifier with escalation."""
        return AudioNotifier(AudioNotifierConfig(
            initial_volume=50,
            max_volume=100,
            escalation_enabled=True,
            escalation_interval_seconds=0.1,
        ))

    @pytest.mark.asyncio
    async def test_escalation_increases_volume(self, notifier):
        """Escalation increases volume over time."""
        initial_volume = notifier._current_volume
        notifier._playing = True

        # Start escalation
        task = asyncio.create_task(notifier._escalate_volume())

        await asyncio.sleep(0.25)  # Let it escalate a few times
        notifier._playing = False  # Stop
        task.cancel()

        try:
            await task
        except asyncio.CancelledError:
            pass

        assert notifier._current_volume > initial_volume

    @pytest.mark.asyncio
    async def test_escalation_stops_at_max(self, notifier):
        """Escalation stops at max volume."""
        notifier._current_volume = 95
        notifier._playing = True

        task = asyncio.create_task(notifier._escalate_volume())

        await asyncio.sleep(0.25)
        notifier._playing = False
        task.cancel()

        try:
            await task
        except asyncio.CancelledError:
            pass

        assert notifier._current_volume <= 100


class TestBuzzerPatterns:
    """Tests for buzzer patterns."""

    @pytest.fixture
    def notifier(self):
        """Create notifier."""
        return AudioNotifier(AudioNotifierConfig())

    @pytest.mark.asyncio
    async def test_play_buzzer_pattern_critical(self, notifier):
        """Critical pattern is played."""
        with patch.object(
            notifier, "_play_gpio_pattern", new_callable=AsyncMock
        ) as mock_gpio:
            mock_gpio.side_effect = ImportError("No RPi.GPIO")

            with patch.object(
                notifier, "_play_software_beep", new_callable=AsyncMock
            ) as mock_beep:
                await notifier._play_buzzer_pattern(EventSeverity.CRITICAL)

                mock_beep.assert_called_once()
                pattern = mock_beep.call_args[0][0]
                # Critical has multiple beeps
                assert len(pattern) == 3

    @pytest.mark.asyncio
    async def test_play_buzzer_pattern_warning(self, notifier):
        """Warning pattern is played."""
        with patch.object(
            notifier, "_play_gpio_pattern", new_callable=AsyncMock
        ) as mock_gpio:
            mock_gpio.side_effect = ImportError("No RPi.GPIO")

            with patch.object(
                notifier, "_play_software_beep", new_callable=AsyncMock
            ) as mock_beep:
                await notifier._play_buzzer_pattern(EventSeverity.WARNING)

                mock_beep.assert_called_once()
                pattern = mock_beep.call_args[0][0]
                assert len(pattern) == 1


# =============================================================================
# MockAudioNotifier Tests
# =============================================================================


class TestMockAudioNotifier:
    """Tests for MockAudioNotifier."""

    @pytest.fixture
    def notifier(self):
        """Create mock notifier."""
        return MockAudioNotifier()

    def test_initial_state(self, notifier):
        """Initial state is empty."""
        assert notifier.notifications == []
        assert notifier.test_called is False

    @pytest.mark.asyncio
    async def test_notify_records_alert(self, notifier):
        """Notify records alert without playing."""
        alert = Alert(
            id="test-1",
            severity=EventSeverity.WARNING,
            rule_name="test",
            message="Test alert",
            timestamp=0,
        )

        result = await notifier.notify(alert)

        assert result is True
        assert len(notifier.notifications) == 1
        assert notifier.notifications[0] == alert

    @pytest.mark.asyncio
    async def test_notify_multiple(self, notifier):
        """Multiple notifications are recorded."""
        for i in range(3):
            alert = Alert(
                id=f"test-{i}",
                severity=EventSeverity.INFO,
                rule_name="test",
                message=f"Alert {i}",
                timestamp=0,
            )
            await notifier.notify(alert)

        assert len(notifier.notifications) == 3

    @pytest.mark.asyncio
    async def test_test_records_call(self, notifier):
        """Test method records call."""
        result = await notifier.test()

        assert result is True
        assert notifier.test_called is True

    @pytest.mark.asyncio
    async def test_play_sound_is_noop(self, notifier):
        """Play sound does nothing."""
        # Should not raise
        await notifier._play_sound(Path("/fake/path.wav"), 50)

    @pytest.mark.asyncio
    async def test_play_buzzer_is_noop(self, notifier):
        """Play buzzer does nothing."""
        # Should not raise
        await notifier._play_buzzer_pattern(EventSeverity.CRITICAL)


# =============================================================================
# Edge Cases
# =============================================================================


class TestNotifierEdgeCases:
    """Edge case tests for notifiers."""

    @pytest.fixture
    def notifier(self):
        """Create notifier."""
        return AudioNotifier(AudioNotifierConfig())

    @pytest.mark.asyncio
    async def test_notify_exception_returns_false(self, notifier):
        """Notify returns False on exception."""
        alert = Alert(
            id="test-1",
            severity=EventSeverity.CRITICAL,
            rule_name="test",
            message="Test",
            timestamp=0,
        )

        with patch.object(notifier, "_play_alarm", new_callable=AsyncMock) as mock:
            mock.side_effect = Exception("Audio error")
            result = await notifier.notify(alert)

            assert result is False

    @pytest.mark.asyncio
    async def test_test_exception_returns_false(self, notifier):
        """Test returns False on exception."""
        with patch.object(notifier, "_play_sound", new_callable=AsyncMock) as mock:
            mock.side_effect = Exception("Audio error")
            result = await notifier.test()

            assert result is False

    @pytest.mark.asyncio
    async def test_stop_without_playing(self, notifier):
        """Stop when not playing doesn't crash."""
        await notifier.stop()

        assert notifier._playing is False

    @pytest.mark.asyncio
    async def test_play_alarm_respects_stop_event(self, notifier):
        """Play alarm stops when stop event is set."""
        notifier._stop_event.set()

        # Mock sound file
        with patch.object(notifier, "_get_sound_file") as mock_get:
            mock_get.return_value = None

            with patch.object(
                notifier, "_play_buzzer_pattern", new_callable=AsyncMock
            ) as mock_buzz:
                await notifier._play_alarm(None, EventSeverity.INFO)

                # Should exit quickly due to stop event
                assert not notifier._playing

    @pytest.mark.asyncio
    async def test_play_with_aplay_fallback(self, notifier):
        """Play sound falls back to aplay."""
        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
            mock_proc = AsyncMock()
            mock_proc.wait = AsyncMock()
            mock_exec.return_value = mock_proc

            await notifier._play_with_aplay(Path("/test/sound.wav"), 50)

            mock_exec.assert_called_once()

    def test_custom_config_values(self):
        """Custom config values are used."""
        config = AudioNotifierConfig(
            enabled=True,
            output_type="buzzer",
            buzzer_gpio_pin=23,
            initial_volume=80,
            max_volume=90,
            escalation_enabled=False,
            max_duration_seconds=60.0,
        )

        notifier = AudioNotifier(config)

        assert notifier._config.output_type == "buzzer"
        assert notifier._config.buzzer_gpio_pin == 23
        assert notifier._config.initial_volume == 80
        assert notifier._config.max_volume == 90
        assert notifier._config.escalation_enabled is False
        assert notifier._config.max_duration_seconds == 60.0
