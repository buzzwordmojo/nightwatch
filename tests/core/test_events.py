"""Tests for event system."""

import time
import pytest

from nightwatch.core.events import (
    Event,
    Alert,
    EventState,
    EventSeverity,
    EventBuffer,
)


class TestEvent:
    """Tests for Event dataclass."""

    def test_event_creation(self):
        """Event can be created with valid data."""
        event = Event(
            detector="radar",
            timestamp=time.time(),
            confidence=0.9,
            state=EventState.NORMAL,
            value={"respiration_rate": 14.0},
        )
        assert event.detector == "radar"
        assert event.state == EventState.NORMAL

    def test_event_immutability(self):
        """Events are immutable."""
        event = Event(
            detector="radar",
            timestamp=time.time(),
            confidence=0.9,
            state=EventState.NORMAL,
            value={},
        )
        with pytest.raises(Exception):  # FrozenInstanceError
            event.detector = "audio"

    def test_confidence_validation(self):
        """Confidence must be 0.0-1.0."""
        with pytest.raises(ValueError):
            Event(
                detector="radar",
                timestamp=time.time(),
                confidence=1.5,  # Invalid
                state=EventState.NORMAL,
                value={},
            )

    def test_serialization_roundtrip(self):
        """Event survives msgpack serialization."""
        original = Event(
            detector="radar",
            timestamp=time.time(),
            confidence=0.85,
            state=EventState.WARNING,
            value={"respiration_rate": 8.5, "presence": True},
            sequence=42,
            session_id="test-session",
        )

        data = original.to_bytes()
        restored = Event.from_bytes(data)

        assert restored.detector == original.detector
        assert restored.confidence == original.confidence
        assert restored.state == original.state
        assert restored.value == original.value
        assert restored.sequence == original.sequence
        assert restored.session_id == original.session_id

    def test_to_dict(self):
        """Event can be converted to dict."""
        event = Event(
            detector="radar",
            timestamp=12345.0,
            confidence=0.9,
            state=EventState.NORMAL,
            value={"test": 1},
        )

        d = event.to_dict()
        assert d["detector"] == "radar"
        assert d["state"] == "normal"
        assert d["value"]["test"] == 1


class TestAlert:
    """Tests for Alert dataclass."""

    def test_alert_creation(self):
        """Alert can be created via factory method."""
        alert = Alert.create(
            severity=EventSeverity.CRITICAL,
            rule_name="test_rule",
            message="Test alert message",
        )

        assert alert.severity == EventSeverity.CRITICAL
        assert alert.rule_name == "test_rule"
        assert len(alert.id) > 0
        assert not alert.acknowledged
        assert not alert.resolved

    def test_alert_acknowledge(self):
        """Alert can be acknowledged."""
        alert = Alert.create(
            severity=EventSeverity.WARNING,
            rule_name="test",
            message="Test",
        )

        acked = alert.acknowledge()

        assert acked.acknowledged is True
        assert acked.acknowledged_at is not None
        assert alert.acknowledged is False  # Original unchanged

    def test_alert_resolve(self):
        """Alert can be resolved."""
        alert = Alert.create(
            severity=EventSeverity.WARNING,
            rule_name="test",
            message="Test",
        )

        resolved = alert.resolve()

        assert resolved.resolved is True
        assert resolved.resolved_at is not None


class TestEventBuffer:
    """Tests for EventBuffer."""

    def test_buffer_append_and_retrieve(self):
        """Events can be added and retrieved."""
        buffer = EventBuffer(capacity=100)

        event = Event(
            detector="radar",
            timestamp=time.time(),
            confidence=0.9,
            state=EventState.NORMAL,
            value={},
        )
        buffer.append(event)

        assert len(buffer) == 1
        assert buffer.get_latest("radar") == event

    def test_buffer_capacity(self):
        """Buffer respects capacity limit."""
        buffer = EventBuffer(capacity=10)

        for i in range(20):
            buffer.append(Event(
                detector="radar",
                timestamp=time.time(),
                confidence=0.9,
                state=EventState.NORMAL,
                value={"i": i},
            ))

        assert len(buffer) == 10

    def test_get_recent(self):
        """Get recent events by time."""
        buffer = EventBuffer()
        now = time.time()

        # Add old event
        buffer.append(Event(
            detector="radar",
            timestamp=now - 100,
            confidence=0.9,
            state=EventState.NORMAL,
            value={},
        ))

        # Add recent event
        buffer.append(Event(
            detector="radar",
            timestamp=now,
            confidence=0.9,
            state=EventState.NORMAL,
            value={},
        ))

        recent = buffer.get_recent(10)  # Last 10 seconds
        assert len(recent) == 1

    def test_get_by_detector(self):
        """Filter events by detector."""
        buffer = EventBuffer()

        buffer.append(Event(
            detector="radar",
            timestamp=time.time(),
            confidence=0.9,
            state=EventState.NORMAL,
            value={},
        ))
        buffer.append(Event(
            detector="audio",
            timestamp=time.time(),
            confidence=0.9,
            state=EventState.NORMAL,
            value={},
        ))

        radar_events = buffer.get_by_detector("radar")
        assert len(radar_events) == 1
        assert radar_events[0].detector == "radar"

    def test_get_all_latest(self):
        """Get latest event from each detector."""
        buffer = EventBuffer()

        buffer.append(Event(
            detector="radar",
            timestamp=time.time(),
            confidence=0.9,
            state=EventState.NORMAL,
            value={"v": 1},
        ))
        buffer.append(Event(
            detector="radar",
            timestamp=time.time(),
            confidence=0.9,
            state=EventState.NORMAL,
            value={"v": 2},
        ))
        buffer.append(Event(
            detector="audio",
            timestamp=time.time(),
            confidence=0.9,
            state=EventState.NORMAL,
            value={"v": 3},
        ))

        latest = buffer.get_all_latest()

        assert len(latest) == 2
        assert latest["radar"].value["v"] == 2
        assert latest["audio"].value["v"] == 3
