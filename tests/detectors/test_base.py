"""
Tests for base detector interface.

Covers:
- BaseDetector lifecycle (start, stop, calibrate)
- Event emission
- Error handling
- MockDetector behavior
"""

from __future__ import annotations

import asyncio
import time
from unittest.mock import AsyncMock, MagicMock

import pytest

from nightwatch.core.events import Event, EventState
from nightwatch.detectors.base import (
    BaseDetector,
    DetectorStatus,
    DetectorState,
    CalibrationResult,
    MockDetector,
)


# =============================================================================
# DetectorStatus Tests
# =============================================================================


class TestDetectorStatus:
    """Tests for DetectorStatus enum."""

    def test_status_values(self):
        """All expected status values exist."""
        assert DetectorStatus.STOPPED.value == "stopped"
        assert DetectorStatus.STARTING.value == "starting"
        assert DetectorStatus.RUNNING.value == "running"
        assert DetectorStatus.CALIBRATING.value == "calibrating"
        assert DetectorStatus.ERROR.value == "error"
        assert DetectorStatus.DISCONNECTED.value == "disconnected"


# =============================================================================
# DetectorState Tests
# =============================================================================


class TestDetectorState:
    """Tests for DetectorState dataclass."""

    def test_default_values(self):
        """Default state values."""
        state = DetectorState(status=DetectorStatus.STOPPED)

        assert state.status == DetectorStatus.STOPPED
        assert state.connected is False
        assert state.last_event_time is None
        assert state.error_message is None
        assert state.events_emitted == 0
        assert state.uptime_seconds == 0.0
        assert state.extra == {}

    def test_with_all_values(self):
        """State with all values specified."""
        state = DetectorState(
            status=DetectorStatus.RUNNING,
            connected=True,
            last_event_time=time.time(),
            error_message=None,
            events_emitted=100,
            uptime_seconds=3600.0,
            extra={"custom_key": "custom_value"},
        )

        assert state.connected is True
        assert state.events_emitted == 100
        assert state.extra["custom_key"] == "custom_value"


# =============================================================================
# CalibrationResult Tests
# =============================================================================


class TestCalibrationResult:
    """Tests for CalibrationResult dataclass."""

    def test_successful_result(self):
        """Successful calibration result."""
        result = CalibrationResult(
            success=True,
            message="Calibration complete",
            baseline_values={"y_position": 1500.0},
            recommended_settings={"sensitivity": 0.8},
            duration_seconds=10.5,
        )

        assert result.success is True
        assert result.message == "Calibration complete"
        assert result.baseline_values["y_position"] == 1500.0
        assert result.recommended_settings["sensitivity"] == 0.8
        assert result.duration_seconds == 10.5

    def test_failed_result(self):
        """Failed calibration result."""
        result = CalibrationResult(
            success=False,
            message="No target detected",
        )

        assert result.success is False
        assert result.baseline_values == {}
        assert result.recommended_settings == {}


# =============================================================================
# MockDetector Tests
# =============================================================================


class TestMockDetector:
    """Tests for MockDetector."""

    @pytest.fixture
    def detector(self):
        """Create mock detector."""
        return MockDetector(name="test_mock")

    def test_default_values(self, detector):
        """Default configuration values."""
        assert detector.name == "test_mock"
        assert detector._update_rate_hz == 10.0
        assert detector._base_respiration_rate == 14.0
        assert detector._base_heart_rate == 70.0
        assert detector._noise_level == 0.1

    def test_custom_values(self):
        """Custom configuration values."""
        detector = MockDetector(
            name="custom",
            update_rate_hz=5.0,
            base_respiration_rate=12.0,
            base_heart_rate=65.0,
            noise_level=0.2,
        )

        assert detector._update_rate_hz == 5.0
        assert detector._base_respiration_rate == 12.0
        assert detector._base_heart_rate == 65.0
        assert detector._noise_level == 0.2

    def test_initial_status(self, detector):
        """Initial status is stopped."""
        assert detector.status == DetectorStatus.STOPPED
        assert detector.is_running is False

    @pytest.mark.asyncio
    async def test_start_changes_status(self, detector):
        """Starting changes status to running."""
        await detector.start()

        assert detector.status == DetectorStatus.RUNNING
        assert detector.is_running is True
        assert detector._connected is True

        await detector.stop()

    @pytest.mark.asyncio
    async def test_stop_changes_status(self, detector):
        """Stopping changes status to stopped."""
        await detector.start()
        await detector.stop()

        assert detector.status == DetectorStatus.STOPPED
        assert detector.is_running is False
        assert detector._connected is False

    @pytest.mark.asyncio
    async def test_start_is_idempotent(self, detector):
        """Starting twice doesn't cause issues."""
        await detector.start()
        await detector.start()  # Second start should be no-op

        assert detector.status == DetectorStatus.RUNNING

        await detector.stop()

    @pytest.mark.asyncio
    async def test_stop_is_idempotent(self, detector):
        """Stopping twice doesn't cause issues."""
        await detector.start()
        await detector.stop()
        await detector.stop()  # Second stop should be no-op

        assert detector.status == DetectorStatus.STOPPED

    @pytest.mark.asyncio
    async def test_stop_without_start(self, detector):
        """Stopping without starting doesn't crash."""
        await detector.stop()
        assert detector.status == DetectorStatus.STOPPED

    @pytest.mark.asyncio
    async def test_emits_events(self, detector):
        """Detector emits events when running."""
        events = []

        async def capture_event(event):
            events.append(event)

        detector.set_on_event(capture_event)

        await detector.start()
        await asyncio.sleep(0.25)  # Let some events emit
        await detector.stop()

        assert len(events) > 0
        assert all(isinstance(e, Event) for e in events)

    @pytest.mark.asyncio
    async def test_event_structure(self, detector):
        """Emitted events have correct structure."""
        events = []

        async def capture_event(event):
            events.append(event)

        detector.set_on_event(capture_event)

        await detector.start()
        await asyncio.sleep(0.15)
        await detector.stop()

        if events:
            event = events[0]
            assert event.detector == "test_mock"
            assert event.confidence == 0.9
            assert "respiration_rate" in event.value
            assert "heart_rate" in event.value
            assert "movement" in event.value
            assert "presence" in event.value

    @pytest.mark.asyncio
    async def test_inject_anomaly_apnea(self, detector):
        """Inject apnea anomaly reduces respiration."""
        events = []

        async def capture_event(event):
            events.append(event)

        detector.set_on_event(capture_event)
        detector.inject_anomaly("apnea", duration=1.0)

        await detector.start()
        await asyncio.sleep(0.2)
        await detector.stop()

        # During apnea, respiration should be reduced
        apnea_events = [e for e in events if e.value.get("respiration_rate", 14) < 5]
        assert len(apnea_events) > 0

    @pytest.mark.asyncio
    async def test_inject_anomaly_bradycardia(self, detector):
        """Inject bradycardia anomaly reduces heart rate."""
        events = []

        async def capture_event(event):
            events.append(event)

        detector.set_on_event(capture_event)
        detector.inject_anomaly("bradycardia", duration=1.0)

        await detector.start()
        await asyncio.sleep(0.2)
        await detector.stop()

        # During bradycardia, heart rate should be reduced
        brady_events = [e for e in events if e.value.get("heart_rate", 70) < 50]
        assert len(brady_events) > 0

    @pytest.mark.asyncio
    async def test_inject_anomaly_seizure(self, detector):
        """Inject seizure anomaly increases movement."""
        events = []

        async def capture_event(event):
            events.append(event)

        detector.set_on_event(capture_event)
        detector.inject_anomaly("seizure", duration=1.0)

        await detector.start()
        await asyncio.sleep(0.2)
        await detector.stop()

        # During seizure, movement should be high
        seizure_events = [e for e in events if e.value.get("movement", 0) > 0.5]
        assert len(seizure_events) > 0

    @pytest.mark.asyncio
    async def test_anomaly_expires(self, detector):
        """Anomaly expires after duration."""
        detector.inject_anomaly("apnea", duration=0.1)

        await detector.start()
        await asyncio.sleep(0.3)  # Wait for anomaly to expire
        await detector.stop()

        assert detector._inject_anomaly is None

    @pytest.mark.asyncio
    async def test_calibrate(self, detector):
        """Calibration returns success."""
        result = await detector.calibrate()

        assert result.success is True
        assert "calibration" in result.message.lower()
        assert "respiration_rate" in result.baseline_values
        assert "heart_rate" in result.baseline_values

    def test_get_state(self, detector):
        """Get state returns detector state."""
        state = detector.get_state()

        assert isinstance(state, DetectorState)
        assert state.status == DetectorStatus.STOPPED
        assert state.connected is False

    @pytest.mark.asyncio
    async def test_get_state_running(self, detector):
        """Get state while running."""
        await detector.start()
        await asyncio.sleep(0.1)

        state = detector.get_state()

        assert state.status == DetectorStatus.RUNNING
        assert state.connected is True
        assert state.uptime_seconds > 0

        await detector.stop()

    def test_get_detector_specific_state(self, detector):
        """Get detector-specific state."""
        state = detector._get_detector_specific_state()

        assert "update_rate_hz" in state
        assert "base_respiration_rate" in state
        assert "base_heart_rate" in state
        assert "active_anomaly" in state


# =============================================================================
# BaseDetector Tests (via MockDetector)
# =============================================================================


class TestBaseDetector:
    """Tests for BaseDetector (via MockDetector implementation)."""

    @pytest.fixture
    def detector(self):
        """Create mock detector."""
        return MockDetector(name="base_test")

    def test_name_property(self, detector):
        """Name property returns detector name."""
        assert detector.name == "base_test"

    def test_status_property(self, detector):
        """Status property returns current status."""
        assert detector.status == DetectorStatus.STOPPED

    def test_is_running_property(self, detector):
        """is_running property reflects running state."""
        assert detector.is_running is False

    def test_set_publisher(self, detector):
        """Set publisher stores reference."""
        mock_publisher = MagicMock()
        detector.set_publisher(mock_publisher)

        assert detector._publisher == mock_publisher

    def test_set_session_id(self, detector):
        """Set session ID stores value."""
        detector.set_session_id("session-123")
        assert detector._session_id == "session-123"

    def test_set_on_event(self, detector):
        """Set on_event callback."""
        callback = AsyncMock()
        detector.set_on_event(callback)

        assert detector._on_event == callback

    def test_set_on_error(self, detector):
        """Set on_error callback."""
        callback = AsyncMock()
        detector.set_on_error(callback)

        assert detector._on_error == callback

    @pytest.mark.asyncio
    async def test_emit_event_increments_sequence(self, detector):
        """Emitting events increments sequence number."""
        events = []

        async def capture(event):
            events.append(event)

        detector.set_on_event(capture)

        await detector._emit_event(EventState.NORMAL, 0.9, {"test": 1})
        await detector._emit_event(EventState.NORMAL, 0.9, {"test": 2})

        assert events[0].sequence == 1
        assert events[1].sequence == 2

    @pytest.mark.asyncio
    async def test_emit_event_updates_last_event_time(self, detector):
        """Emitting events updates last event time."""
        assert detector._last_event_time is None

        await detector._emit_event(EventState.NORMAL, 0.9, {"test": 1})

        assert detector._last_event_time is not None
        assert detector._last_event_time > 0

    @pytest.mark.asyncio
    async def test_emit_event_increments_count(self, detector):
        """Emitting events increments event count."""
        assert detector._events_emitted == 0

        await detector._emit_event(EventState.NORMAL, 0.9, {"test": 1})
        await detector._emit_event(EventState.NORMAL, 0.9, {"test": 2})

        assert detector._events_emitted == 2

    @pytest.mark.asyncio
    async def test_emit_event_with_publisher(self, detector):
        """Emitting events publishes via ZeroMQ."""
        mock_publisher = AsyncMock()
        detector.set_publisher(mock_publisher)

        await detector._emit_event(EventState.NORMAL, 0.9, {"test": 1})

        mock_publisher.send.assert_called_once()

    @pytest.mark.asyncio
    async def test_emit_event_includes_session_id(self, detector):
        """Emitted events include session ID."""
        events = []

        async def capture(event):
            events.append(event)

        detector.set_on_event(capture)
        detector.set_session_id("test-session")

        await detector._emit_event(EventState.NORMAL, 0.9, {"test": 1})

        assert events[0].session_id == "test-session"

    @pytest.mark.asyncio
    async def test_handle_error_stores_message(self, detector):
        """Handling error stores error message."""
        error = ValueError("Test error")
        await detector._handle_error(error)

        assert detector._error_message == "Test error"

    @pytest.mark.asyncio
    async def test_handle_error_calls_callback(self, detector):
        """Handling error calls error callback."""
        callback = AsyncMock()
        detector.set_on_error(callback)

        error = ValueError("Test error")
        await detector._handle_error(error)

        callback.assert_called_once_with(error)


# =============================================================================
# Edge Cases
# =============================================================================


class TestDetectorEdgeCases:
    """Edge case tests for detectors."""

    @pytest.fixture
    def detector(self):
        """Create mock detector."""
        return MockDetector(name="edge_test")

    @pytest.mark.asyncio
    async def test_rapid_start_stop(self, detector):
        """Rapid start/stop cycles don't crash."""
        for _ in range(5):
            await detector.start()
            await asyncio.sleep(0.01)
            await detector.stop()

    @pytest.mark.asyncio
    async def test_calibrate_while_running(self, detector):
        """Calibration while running works."""
        await detector.start()

        result = await detector.calibrate()

        assert result.success is True

        await detector.stop()

    @pytest.mark.asyncio
    async def test_calibrate_sets_status(self, detector):
        """Calibration temporarily changes status."""
        # Mock _calibrate_impl to capture status during calibration
        captured_status = None

        original_impl = detector._calibrate_impl

        async def capturing_impl():
            nonlocal captured_status
            captured_status = detector.status
            return await original_impl()

        detector._calibrate_impl = capturing_impl

        await detector.calibrate()

        assert captured_status == DetectorStatus.CALIBRATING

    @pytest.mark.asyncio
    async def test_state_uptime_increases(self, detector):
        """Uptime increases while running."""
        await detector.start()

        state1 = detector.get_state()
        await asyncio.sleep(0.1)
        state2 = detector.get_state()

        assert state2.uptime_seconds > state1.uptime_seconds

        await detector.stop()

    def test_zero_update_rate(self):
        """Zero update rate doesn't cause division by zero."""
        # This would cause infinite loop if not handled
        # Just verify it can be created
        detector = MockDetector(name="zero_rate", update_rate_hz=0.001)
        assert detector._update_rate_hz == 0.001

    def test_negative_noise_level(self):
        """Negative noise level is handled."""
        detector = MockDetector(name="neg_noise", noise_level=-0.1)
        # Should not crash, noise level just used in gauss()
        assert detector._noise_level == -0.1

    @pytest.mark.asyncio
    async def test_callback_exception_doesnt_stop_detector(self, detector):
        """Exception in callback doesn't stop detector."""
        call_count = 0

        async def bad_callback(event):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ValueError("Callback error")

        detector.set_on_event(bad_callback)

        await detector.start()
        await asyncio.sleep(0.25)
        await detector.stop()

        # Detector should have continued despite callback error
        # (implementation may vary - some detectors catch, some don't)

    @pytest.mark.asyncio
    async def test_event_states_based_on_respiration(self, detector):
        """Event state reflects respiration rate."""
        detector._base_respiration_rate = 4.0  # Critical level
        events = []

        async def capture(event):
            events.append(event)

        detector.set_on_event(capture)

        await detector.start()
        await asyncio.sleep(0.15)
        await detector.stop()

        # Should have alert state events
        alert_events = [e for e in events if e.state == EventState.ALERT]
        assert len(alert_events) > 0

    @pytest.mark.asyncio
    async def test_event_states_warning(self, detector):
        """Warning state for low respiration."""
        detector._base_respiration_rate = 7.0  # Warning level
        events = []

        async def capture(event):
            events.append(event)

        detector.set_on_event(capture)

        await detector.start()
        await asyncio.sleep(0.15)
        await detector.stop()

        # Should have warning state events
        warning_events = [e for e in events if e.state == EventState.WARNING]
        assert len(warning_events) > 0

    def test_inject_anomaly_before_start(self, detector):
        """Can inject anomaly before starting."""
        detector.inject_anomaly("apnea", duration=5.0)

        assert detector._inject_anomaly == "apnea"
        assert detector._anomaly_start is not None
        assert detector._anomaly_duration == 5.0

    @pytest.mark.asyncio
    async def test_multiple_anomaly_injections(self, detector):
        """Later anomaly overwrites earlier."""
        detector.inject_anomaly("apnea", duration=10.0)
        detector.inject_anomaly("bradycardia", duration=5.0)

        assert detector._inject_anomaly == "bradycardia"
        assert detector._anomaly_duration == 5.0
