"""Tests for alert engine."""

import time
import pytest

from nightwatch.core.config import (
    AlertEngineConfig,
    AlertRule as AlertRuleConfig,
    AlertRuleCondition,
)
from nightwatch.core.events import Event, EventState, EventSeverity
from nightwatch.core.engine import AlertEngine, Rule, Condition, AlertLevel


class TestCondition:
    """Tests for alert conditions."""

    def test_less_than_condition(self):
        """Less than operator works correctly."""
        condition = Condition(
            detector="radar",
            field_path="value.respiration_rate",
            operator="<",
            threshold=8,
        )

        event_low = Event(
            detector="radar",
            timestamp=time.time(),
            confidence=0.9,
            state=EventState.NORMAL,
            value={"respiration_rate": 5},
        )
        event_normal = Event(
            detector="radar",
            timestamp=time.time(),
            confidence=0.9,
            state=EventState.NORMAL,
            value={"respiration_rate": 14},
        )

        assert condition.evaluate(event_low) is True
        assert condition.evaluate(event_normal) is False

    def test_equals_condition(self):
        """Equals operator works correctly."""
        condition = Condition(
            detector="radar",
            field_path="value.presence",
            operator="==",
            threshold=False,
        )

        event_present = Event(
            detector="radar",
            timestamp=time.time(),
            confidence=0.9,
            state=EventState.NORMAL,
            value={"presence": True},
        )
        event_absent = Event(
            detector="radar",
            timestamp=time.time(),
            confidence=0.9,
            state=EventState.NORMAL,
            value={"presence": False},
        )

        assert condition.evaluate(event_present) is False
        assert condition.evaluate(event_absent) is True

    def test_wrong_detector_returns_false(self):
        """Condition returns False for wrong detector."""
        condition = Condition(
            detector="radar",
            field_path="value.respiration_rate",
            operator="<",
            threshold=8,
        )

        event = Event(
            detector="audio",  # Wrong detector
            timestamp=time.time(),
            confidence=0.9,
            state=EventState.NORMAL,
            value={"respiration_rate": 5},
        )

        assert condition.evaluate(event) is False


class TestRule:
    """Tests for alert rules."""

    def test_simple_rule_triggers(self):
        """Simple rule triggers on matching event."""
        rule = Rule(
            name="Low respiration",
            conditions=[
                Condition(
                    detector="radar",
                    field_path="value.respiration_rate",
                    operator="<",
                    threshold=6,
                )
            ],
            severity=EventSeverity.CRITICAL,
        )

        event = Event(
            detector="radar",
            timestamp=time.time(),
            confidence=0.9,
            state=EventState.WARNING,
            value={"respiration_rate": 4},
        )

        from nightwatch.core.events import EventBuffer
        buffer = EventBuffer()

        alert = rule.evaluate({"radar": event}, buffer)

        assert alert is not None
        assert alert.severity == EventSeverity.CRITICAL

    def test_rule_respects_cooldown(self):
        """Rule doesn't trigger again within cooldown period."""
        rule = Rule(
            name="Test rule",
            conditions=[
                Condition(
                    detector="radar",
                    field_path="value.respiration_rate",
                    operator="<",
                    threshold=10,
                )
            ],
            severity=EventSeverity.WARNING,
            cooldown_seconds=60,
        )

        event = Event(
            detector="radar",
            timestamp=time.time(),
            confidence=0.9,
            state=EventState.WARNING,
            value={"respiration_rate": 5},
        )

        from nightwatch.core.events import EventBuffer
        buffer = EventBuffer()

        # First trigger
        alert1 = rule.evaluate({"radar": event}, buffer)
        assert alert1 is not None

        # Second trigger (within cooldown)
        alert2 = rule.evaluate({"radar": event}, buffer)
        assert alert2 is None

    def test_all_conditions_required(self):
        """With combine='all', all conditions must match."""
        rule = Rule(
            name="Multi-condition",
            conditions=[
                Condition(
                    detector="radar",
                    field_path="value.respiration_rate",
                    operator="<",
                    threshold=10,
                ),
                Condition(
                    detector="radar",
                    field_path="value.presence",
                    operator="==",
                    threshold=True,
                ),
            ],
            severity=EventSeverity.WARNING,
            combine="all",
        )

        # Only one condition met
        event_partial = Event(
            detector="radar",
            timestamp=time.time(),
            confidence=0.9,
            state=EventState.WARNING,
            value={"respiration_rate": 5, "presence": False},
        )

        # Both conditions met
        event_full = Event(
            detector="radar",
            timestamp=time.time(),
            confidence=0.9,
            state=EventState.WARNING,
            value={"respiration_rate": 5, "presence": True},
        )

        from nightwatch.core.events import EventBuffer
        buffer = EventBuffer()

        assert rule.evaluate({"radar": event_partial}, buffer) is None
        assert rule.evaluate({"radar": event_full}, buffer) is not None


class TestAlertEngine:
    """Tests for AlertEngine."""

    @pytest.fixture
    def engine(self):
        """Create engine with test configuration."""
        config = AlertEngineConfig(
            rules=[
                AlertRuleConfig(
                    name="Low respiration",
                    conditions=[
                        AlertRuleCondition(
                            detector="radar",
                            field="value.respiration_rate",
                            operator="<",
                            value=6,
                        )
                    ],
                    severity="critical",
                    cooldown_seconds=1,
                )
            ]
        )
        return AlertEngine(config=config)

    @pytest.mark.asyncio
    async def test_process_event_triggers_alert(self, engine):
        """Processing low respiration triggers alert."""
        await engine.start()

        alerts_received = []

        async def capture_alert(a):
            alerts_received.append(a)

        engine.on_alert = capture_alert

        event = Event(
            detector="radar",
            timestamp=time.time(),
            confidence=0.9,
            state=EventState.WARNING,
            value={"respiration_rate": 4},
        )

        await engine.process_event(event)
        await engine.stop()

        state = engine.get_state()
        assert state.level == AlertLevel.CRITICAL
        assert len(state.active_alerts) == 1

    @pytest.mark.asyncio
    async def test_normal_event_no_alert(self, engine):
        """Normal respiration doesn't trigger alert."""
        await engine.start()

        event = Event(
            detector="radar",
            timestamp=time.time(),
            confidence=0.9,
            state=EventState.NORMAL,
            value={"respiration_rate": 14},
        )

        await engine.process_event(event)
        await engine.stop()

        state = engine.get_state()
        assert state.level == AlertLevel.OK
        assert len(state.active_alerts) == 0

    @pytest.mark.asyncio
    async def test_pause_suppresses_alerts(self, engine):
        """Paused engine doesn't trigger alerts."""
        await engine.start()
        engine.pause(60)

        event = Event(
            detector="radar",
            timestamp=time.time(),
            confidence=0.9,
            state=EventState.WARNING,
            value={"respiration_rate": 4},
        )

        await engine.process_event(event)
        await engine.stop()

        state = engine.get_state()
        assert state.paused is True
        assert len(state.active_alerts) == 0

    @pytest.mark.asyncio
    async def test_acknowledge_alert(self, engine):
        """Alerts can be acknowledged."""
        await engine.start()

        event = Event(
            detector="radar",
            timestamp=time.time(),
            confidence=0.9,
            state=EventState.WARNING,
            value={"respiration_rate": 4},
        )

        await engine.process_event(event)

        state = engine.get_state()
        alert_id = state.active_alerts[0].id

        result = engine.acknowledge_alert(alert_id)
        assert result is True

        state = engine.get_state()
        assert state.active_alerts[0].acknowledged is True

        await engine.stop()
