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


class _RecordingNotifier:
    """Notifier double that records lifecycle calls and delivery attempts."""

    def __init__(self, *, deliver: bool = True, raise_on_notify: bool = False):
        self.started = False
        self.stopped = False
        self.delivered: list[object] = []
        self._deliver = deliver
        self._raise_on_notify = raise_on_notify

    @property
    def name(self) -> str:
        return "recording"

    async def start(self) -> None:
        self.started = True

    async def stop(self) -> None:
        self.stopped = True

    async def notify(self, alert) -> bool:
        if self._raise_on_notify:
            raise RuntimeError("delivery exploded")
        self.delivered.append(alert)
        return self._deliver


class TestNotifierDelivery:
    """Alerts must actually reach a notifier, and failures must be visible."""

    def _engine(self, notifiers):
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
        return AlertEngine(config=config, notifiers=notifiers)

    def _low_respiration_event(self) -> Event:
        return Event(
            detector="radar",
            timestamp=time.time(),
            confidence=0.9,
            state=EventState.WARNING,
            value={"respiration_rate": 4},
        )

    @pytest.mark.asyncio
    async def test_engine_starts_and_stops_notifiers(self):
        """PushNotifier builds its HTTP client in start(); skipping it loses alerts."""
        notifier = _RecordingNotifier()
        engine = self._engine([notifier])

        await engine.start()
        assert notifier.started is True

        await engine.stop()
        assert notifier.stopped is True

    @pytest.mark.asyncio
    async def test_alert_is_delivered_to_notifier(self):
        notifier = _RecordingNotifier()
        engine = self._engine([notifier])

        await engine.start()
        await engine.process_event(self._low_respiration_event())
        await engine.stop()

        assert len(notifier.delivered) == 1
        assert engine.undelivered_alerts == 0

    @pytest.mark.asyncio
    async def test_raising_notifier_is_counted_not_swallowed(self):
        notifier = _RecordingNotifier(raise_on_notify=True)
        engine = self._engine([notifier])

        await engine.start()
        await engine.process_event(self._low_respiration_event())
        await engine.stop()

        assert engine.undelivered_alerts == 1
        assert engine.last_alert_delivered is False

    @pytest.mark.asyncio
    async def test_one_working_notifier_is_enough(self):
        broken = _RecordingNotifier(raise_on_notify=True)
        working = _RecordingNotifier()
        engine = self._engine([broken, working])

        await engine.start()
        await engine.process_event(self._low_respiration_event())
        await engine.stop()

        assert len(working.delivered) == 1
        assert engine.undelivered_alerts == 0
        assert engine.last_alert_delivered is True
