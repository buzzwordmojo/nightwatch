"""
Tests for Convex bridge.

Covers:
- Event batching and flushing
- HTTP mutation calls
- State caching
- Error handling
"""

from __future__ import annotations

import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from nightwatch.core.events import Event, EventState
from nightwatch.bridge.convex import ConvexConfig, ConvexBridge, ConvexEventHandler


# =============================================================================
# ConvexConfig Tests
# =============================================================================


class TestConvexConfig:
    """Tests for ConvexConfig."""

    def test_default_values(self):
        """Default configuration values."""
        config = ConvexConfig()

        assert config.url == "http://localhost:3210"
        assert config.timeout == 5.0
        assert config.batch_interval == 1.0
        assert config.retry_attempts == 3

    def test_custom_values(self):
        """Custom configuration values."""
        config = ConvexConfig(
            url="http://convex.example.com:4000",
            timeout=10.0,
            batch_interval=2.0,
            retry_attempts=5,
        )

        assert config.url == "http://convex.example.com:4000"
        assert config.timeout == 10.0
        assert config.batch_interval == 2.0
        assert config.retry_attempts == 5


# =============================================================================
# ConvexBridge Tests
# =============================================================================


class TestConvexBridge:
    """Tests for ConvexBridge."""

    @pytest.fixture
    def bridge(self):
        """Create bridge instance."""
        return ConvexBridge(ConvexConfig())

    @pytest.fixture
    def sample_event(self):
        """Create sample event."""
        return Event(
            detector="radar",
            timestamp=time.time(),
            confidence=0.9,
            state=EventState.NORMAL,
            value={
                "respiration_rate": 14.0,
                "presence": True,
            },
            sequence=1,
            session_id="test",
        )

    def test_initial_state(self, bridge):
        """Initial state is not running."""
        assert bridge._running is False
        assert bridge._client is None
        assert bridge._pending_readings == []

    @pytest.mark.asyncio
    async def test_start_creates_client(self, bridge):
        """Start creates HTTP client."""
        await bridge.start()

        assert bridge._running is True
        assert bridge._client is not None

        await bridge.stop()

    @pytest.mark.asyncio
    async def test_stop_closes_client(self, bridge):
        """Stop closes HTTP client."""
        await bridge.start()
        await bridge.stop()

        assert bridge._running is False
        assert bridge._client is None

    @pytest.mark.asyncio
    async def test_push_event_not_running(self, bridge, sample_event):
        """Push event when not running returns False."""
        result = await bridge.push_event(sample_event)

        assert result is False

    @pytest.mark.asyncio
    async def test_push_event_updates_detector_state(self, bridge, sample_event):
        """Push event updates detector state."""
        await bridge.start()

        with patch.object(bridge, "_mutation", new_callable=AsyncMock) as mock_mut:
            await bridge.push_event(sample_event)

            # Should have called mutation for detector update
            mock_mut.assert_called()

        await bridge.stop()

    @pytest.mark.asyncio
    async def test_push_event_adds_to_pending_readings(self, bridge, sample_event):
        """Push event adds to pending readings."""
        await bridge.start()

        with patch.object(bridge, "_mutation", new_callable=AsyncMock):
            await bridge.push_event(sample_event)

            # Should have pending readings
            assert len(bridge._pending_readings) > 0

        await bridge.stop()

    @pytest.mark.asyncio
    async def test_push_event_flushes_on_interval(self, bridge, sample_event):
        """Push event flushes after interval."""
        bridge._config.batch_interval = 0.0  # Immediate flush
        await bridge.start()

        with patch.object(bridge, "_mutation", new_callable=AsyncMock) as mock_mut:
            # Set last flush to past
            bridge._last_flush = time.time() - 10

            await bridge.push_event(sample_event)

            # Should have flushed (multiple mutations)
            assert mock_mut.call_count >= 2

        await bridge.stop()

    @pytest.mark.asyncio
    async def test_push_alert_not_running(self, bridge):
        """Push alert when not running returns False."""
        result = await bridge.push_alert(
            alert_id="test-1",
            level="warning",
            source="radar",
            message="Test alert",
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_push_alert_calls_mutation(self, bridge):
        """Push alert calls mutation."""
        await bridge.start()

        with patch.object(bridge, "_mutation", new_callable=AsyncMock) as mock_mut:
            result = await bridge.push_alert(
                alert_id="test-1",
                level="critical",
                source="radar",
                message="Critical alert",
            )

            assert result is True
            mock_mut.assert_called_with(
                "alerts:create",
                {
                    "alertId": "test-1",
                    "level": "critical",
                    "source": "radar",
                    "message": "Critical alert",
                },
            )

        await bridge.stop()

    @pytest.mark.asyncio
    async def test_update_system_status(self, bridge):
        """Update system status calls mutation."""
        await bridge.start()

        with patch.object(bridge, "_mutation", new_callable=AsyncMock) as mock_mut:
            result = await bridge.update_system_status(
                component="radar",
                status="online",
                message="Connected",
            )

            assert result is True
            mock_mut.assert_called_with(
                "system:updateStatus",
                {
                    "component": "radar",
                    "status": "online",
                    "message": "Connected",
                    "mock": False,
                },
            )

        await bridge.stop()

    @pytest.mark.asyncio
    async def test_update_system_status_not_running(self, bridge):
        """Update system status when not running returns False."""
        result = await bridge.update_system_status(
            component="radar",
            status="online",
        )

        assert result is False


class TestConvexBridgeReadings:
    """Tests for reading extraction and batching."""

    @pytest.fixture
    def bridge(self):
        """Create bridge instance."""
        return ConvexBridge(ConvexConfig())

    def test_add_reading_radar(self, bridge):
        # Collection is gated on presence; these tests model a detector
        # reporting while someone is in the room.
        bridge._last_present_at = time.time()
        """Radar event extracts respiration rate."""
        event = Event(
            detector="radar",
            timestamp=time.time(),
            confidence=0.9,
            state=EventState.NORMAL,
            value={"respiration_rate": 14.0},
            sequence=1,
            session_id="test",
        )

        bridge._add_reading(event)

        assert len(bridge._pending_readings) == 1
        assert bridge._pending_readings[0]["respirationRate"] == 14.0

    def test_add_reading_audio(self, bridge):
        # Collection is gated on presence; these tests model a detector
        # reporting while someone is in the room.
        bridge._last_present_at = time.time()
        """Audio event extracts breathing rate and amplitude."""
        event = Event(
            detector="audio",
            timestamp=time.time(),
            confidence=0.8,
            state=EventState.NORMAL,
            value={
                "breathing_rate": 13.0,
                "breathing_amplitude": 0.5,
            },
            sequence=1,
            session_id="test",
        )

        bridge._add_reading(event)

        assert len(bridge._pending_readings) == 1
        assert bridge._pending_readings[0]["respirationRate"] == 13.0
        assert bridge._pending_readings[0]["breathingAmplitude"] == 0.5

    def test_add_reading_bcg(self, bridge):
        """BCG event extracts heart rate and bed status."""
        event = Event(
            detector="bcg",
            timestamp=time.time(),
            confidence=0.95,
            state=EventState.NORMAL,
            value={
                "heart_rate": 72.0,
                "bed_occupied": True,
                "signal_quality": 0.85,
            },
            sequence=1,
            session_id="test",
        )

        bridge._add_reading(event)

        assert len(bridge._pending_readings) == 1
        assert bridge._pending_readings[0]["heartRate"] == 72.0
        assert bridge._pending_readings[0]["bedOccupied"] is True
        assert bridge._pending_readings[0]["signalQuality"] == 0.85

    def test_add_reading_empty_value(self, bridge):
        """Event with no relevant values doesn't add reading."""
        event = Event(
            detector="unknown",
            timestamp=time.time(),
            confidence=0.5,
            state=EventState.NORMAL,
            value={},
            sequence=1,
            session_id="test",
        )

        bridge._add_reading(event)

        assert len(bridge._pending_readings) == 0

    def test_merge_readings(self, bridge):
        """Merge multiple readings."""
        readings = [
            {"respirationRate": 14.0},
            {"heartRate": 70.0},
            {"respirationRate": 15.0},  # Later value wins
        ]

        merged = bridge._merge_readings(readings)

        assert merged["respirationRate"] == 15.0
        assert merged["heartRate"] == 70.0

    def test_merge_readings_ignores_none(self, bridge):
        """Merge ignores None values."""
        readings = [
            {"respirationRate": 14.0, "heartRate": None},
            {"heartRate": 70.0},
        ]

        merged = bridge._merge_readings(readings)

        assert merged["respirationRate"] == 14.0
        assert merged["heartRate"] == 70.0


class TestConvexBridgeStateConversion:
    """Tests for event state conversion."""

    def test_state_normal(self):
        """Normal state converts to 'normal'."""
        result = ConvexBridge._event_state_to_string(EventState.NORMAL)
        assert result == "normal"

    def test_state_warning(self):
        """Warning state converts to 'warning'."""
        result = ConvexBridge._event_state_to_string(EventState.WARNING)
        assert result == "warning"

    def test_state_alert(self):
        """Alert state converts to 'alert'."""
        result = ConvexBridge._event_state_to_string(EventState.ALERT)
        assert result == "alert"

    def test_state_uncertain(self):
        """Uncertain state converts to 'uncertain'."""
        result = ConvexBridge._event_state_to_string(EventState.UNCERTAIN)
        assert result == "uncertain"


# =============================================================================
# ConvexEventHandler Tests
# =============================================================================


class TestConvexEventHandler:
    """Tests for ConvexEventHandler."""

    @pytest.fixture
    def bridge(self):
        """Create mock bridge."""
        return MagicMock(spec=ConvexBridge)

    @pytest.fixture
    def handler(self, bridge):
        """Create event handler."""
        return ConvexEventHandler(bridge)

    @pytest.mark.asyncio
    async def test_call_pushes_event(self, handler, bridge):
        """Calling handler pushes event to bridge."""
        bridge.push_event = AsyncMock()

        event = Event(
            detector="radar",
            timestamp=time.time(),
            confidence=0.9,
            state=EventState.NORMAL,
            value={"respiration_rate": 14.0},
            sequence=1,
            session_id="test",
        )

        await handler(event)

        bridge.push_event.assert_called_once_with(event)


# =============================================================================
# Error Handling Tests
# =============================================================================


class TestConvexBridgeErrors:
    """Tests for error handling."""

    @pytest.fixture
    def bridge(self):
        """Create bridge instance."""
        return ConvexBridge(ConvexConfig())

    @pytest.mark.asyncio
    async def test_push_event_handles_error(self, bridge):
        """Push event handles errors gracefully."""
        await bridge.start()

        with patch.object(bridge, "_mutation", new_callable=AsyncMock) as mock_mut:
            mock_mut.side_effect = Exception("Network error")

            event = Event(
                detector="radar",
                timestamp=time.time(),
                confidence=0.9,
                state=EventState.NORMAL,
                value={"respiration_rate": 14.0},
                sequence=1,
                session_id="test",
            )

            result = await bridge.push_event(event)

            assert result is False

        await bridge.stop()

    @pytest.mark.asyncio
    async def test_push_alert_handles_error(self, bridge):
        """Push alert handles errors gracefully."""
        await bridge.start()

        with patch.object(bridge, "_mutation", new_callable=AsyncMock) as mock_mut:
            mock_mut.side_effect = Exception("Network error")

            result = await bridge.push_alert(
                alert_id="test",
                level="warning",
                source="test",
                message="Test",
            )

            assert result is False

        await bridge.stop()

    @pytest.mark.asyncio
    async def test_update_status_handles_error(self, bridge):
        """Update status handles errors gracefully."""
        await bridge.start()

        with patch.object(bridge, "_mutation", new_callable=AsyncMock) as mock_mut:
            mock_mut.side_effect = Exception("Network error")

            result = await bridge.update_system_status(
                component="test",
                status="online",
            )

            assert result is False

        await bridge.stop()

    @pytest.mark.asyncio
    async def test_mutation_without_client_raises(self, bridge):
        """Mutation without client raises RuntimeError."""
        with pytest.raises(RuntimeError, match="Client not initialized"):
            await bridge._mutation("test:path", {})

    @pytest.mark.asyncio
    async def test_flush_handles_error(self, bridge):
        """Flush handles errors gracefully."""
        await bridge.start()

        bridge._pending_readings = [{"respirationRate": 14.0}]

        with patch.object(bridge, "_mutation", new_callable=AsyncMock) as mock_mut:
            mock_mut.side_effect = Exception("Network error")

            # Should not raise
            await bridge._flush_readings()

            # Readings should be cleared anyway
            assert bridge._pending_readings == []

        await bridge.stop()


# =============================================================================
# Edge Cases
# =============================================================================


class TestConvexBridgeEdgeCases:
    """Edge case tests for Convex bridge."""

    @pytest.fixture
    def bridge(self):
        """Create bridge instance."""
        return ConvexBridge(ConvexConfig())

    @pytest.mark.asyncio
    async def test_stop_flushes_pending(self, bridge):
        """Stop flushes pending readings."""
        await bridge.start()

        bridge._pending_readings = [{"respirationRate": 14.0}]

        with patch.object(bridge, "_mutation", new_callable=AsyncMock):
            await bridge.stop()

            # Pending should be flushed (cleared)
            assert bridge._pending_readings == []

    @pytest.mark.asyncio
    async def test_flush_empty_is_noop(self, bridge):
        """Flush with no pending readings is no-op."""
        await bridge.start()

        with patch.object(bridge, "_mutation", new_callable=AsyncMock) as mock_mut:
            await bridge._flush_readings()

            # Should not call mutation for empty flush
            mock_mut.assert_not_called()

        await bridge.stop()

    @pytest.mark.asyncio
    async def test_detector_state_cached(self, bridge):
        """Detector state is cached locally."""
        await bridge.start()

        event = Event(
            detector="radar",
            timestamp=time.time(),
            confidence=0.9,
            state=EventState.NORMAL,
            value={"respiration_rate": 14.0},
            sequence=1,
            session_id="test",
        )

        with patch.object(bridge, "_mutation", new_callable=AsyncMock):
            await bridge._update_detector_state(event)

        assert "radar" in bridge._detector_states
        assert bridge._detector_states["radar"]["state"] == "normal"
        assert bridge._detector_states["radar"]["confidence"] == 0.9

        await bridge.stop()

    @pytest.mark.asyncio
    async def test_multiple_events_batch(self, bridge):
        bridge._last_present_at = time.time()  # collection gated on presence
        """Multiple events batch before flush."""
        await bridge.start()

        # Prevent auto-flush by setting last_flush to now
        bridge._last_flush = time.time()

        with patch.object(bridge, "_mutation", new_callable=AsyncMock):
            for i in range(5):
                event = Event(
                    detector="radar",
                    timestamp=time.time(),
                    confidence=0.9,
                    state=EventState.NORMAL,
                    value={"respiration_rate": 14.0 + i},
                    sequence=i + 1,
                    session_id="test",
                )
                await bridge.push_event(event)

        assert len(bridge._pending_readings) == 5

        await bridge.stop()


class TestRadarHeartRateIsStored:
    """
    The LD6002 measures heart rate directly, so it must reach the database.

    Regression: _add_reading extracted only respiration_rate for the radar
    detector, which was correct while the LD2450's heart rate was a weak
    inference. With the LD6002 the radar is the only real HR source on the
    device, and dropping it here meant no historical pulse at all.
    """

    def _reading_for(self, value):
        import time

        from nightwatch.bridge.convex import ConvexBridge
        from nightwatch.core.events import Event, EventState

        bridge = ConvexBridge()
        bridge._add_reading(Event(
            detector="radar", timestamp=time.time(), confidence=0.9,
            state=EventState.NORMAL, value=value,
        ))
        return bridge._pending_readings[0] if bridge._pending_readings else {}

    def test_measured_heart_rate_is_captured(self):
        r = self._reading_for({"respiration_rate": 18.0, "heart_rate": 72.0, "presence": True})
        assert r.get("heartRate") == 72.0, "radar heart rate was dropped"
        assert r.get("respirationRate") == 18.0
        assert r.get("bedOccupied") is True

    def test_absent_heart_rate_is_not_written_as_null(self):
        r = self._reading_for({"respiration_rate": 18.0, "heart_rate": None})
        assert "heartRate" not in r


class TestMockDataNeverPersisted:
    """Simulated detectors must not write vitals history."""

    def test_mock_detector_readings_are_dropped(self):
        import time

        from nightwatch.bridge.convex import ConvexBridge
        from nightwatch.core.events import Event, EventState

        bridge = ConvexBridge(mock_detectors={"bcg"})
        bridge._add_reading(Event(
            detector="bcg", timestamp=time.time(), confidence=0.9,
            state=EventState.NORMAL,
            value={"heart_rate": 62.0, "bed_occupied": True},
        ))
        assert bridge._pending_readings == [], "mock vitals reached the readings batch"


class TestCollectionGatedOnPresence:
    """
    Vitals history is written only while someone is present, plus a linger.

    An empty room produces placeholder rates and absence rows; a night of that
    is noise in the child's history and write wear on the SD card. Alerting is
    unaffected - it runs off the event bus, not this bridge.
    """

    def _event(self, detector="radar", **value):
        import time

        from nightwatch.core.events import Event, EventState

        return Event(detector=detector, timestamp=time.time(), confidence=0.9,
                     state=EventState.NORMAL, value=value)

    def _bridge(self, monkeypatch, now):
        import nightwatch.bridge.convex as mod

        monkeypatch.setattr(mod.time, "time", lambda: now[0])
        return mod.ConvexBridge(mock_detectors={"bcg"})

    def test_nothing_collected_before_first_presence(self, monkeypatch):
        now = [1000.0]
        b = self._bridge(monkeypatch, now)
        b._add_reading(self._event(respiration_rate=18.0, presence=False))
        assert b._pending_readings == []

    def test_presence_opens_collection(self, monkeypatch):
        now = [1000.0]
        b = self._bridge(monkeypatch, now)
        b._add_reading(self._event(respiration_rate=18.0, presence=True))
        assert len(b._pending_readings) == 1

    def test_collection_lingers_after_departure(self, monkeypatch):
        import nightwatch.bridge.convex as mod

        now = [1000.0]
        b = self._bridge(monkeypatch, now)
        b._add_reading(self._event(respiration_rate=18.0, presence=True))
        now[0] += b._config.presence_linger_seconds - 5
        b._add_reading(self._event(respiration_rate=17.0, presence=False))
        assert len(b._pending_readings) == 2, "linger window should still collect"

    def test_collection_stops_after_linger_expires(self, monkeypatch):
        import nightwatch.bridge.convex as mod

        now = [1000.0]
        b = self._bridge(monkeypatch, now)
        b._add_reading(self._event(respiration_rate=18.0, presence=True))
        now[0] += b._config.presence_linger_seconds + 5
        b._add_reading(self._event(respiration_rate=17.0, presence=False))
        assert len(b._pending_readings) == 1, "collection should stop after the linger"

    def test_mock_presence_does_not_arm_collection(self, monkeypatch):
        now = [1000.0]
        b = self._bridge(monkeypatch, now)
        # The mock BCG always reports the bed occupied; that must not count.
        b._add_reading(self._event(detector="bcg", bed_occupied=True))
        b._add_reading(self._event(respiration_rate=18.0, presence=False))
        assert b._pending_readings == []

    def test_null_respiration_is_not_written(self, monkeypatch):
        now = [1000.0]
        b = self._bridge(monkeypatch, now)
        b._add_reading(self._event(respiration_rate=None, presence=True))
        assert all("respirationRate" not in r for r in b._pending_readings)


    def test_linger_is_configurable(self, monkeypatch):
        """The linger comes from config - testing uses seconds, production minutes."""
        import nightwatch.bridge.convex as mod

        now = [1000.0]
        monkeypatch.setattr(mod.time, "time", lambda: now[0])
        b = mod.ConvexBridge(config=mod.ConvexConfig(presence_linger_seconds=30.0))
        b._add_reading(self._event(respiration_rate=18.0, presence=True))
        now[0] += 31
        b._add_reading(self._event(respiration_rate=17.0, presence=False))
        assert len(b._pending_readings) == 1
