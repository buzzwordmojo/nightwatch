"""
Alert Engine for Nightwatch.

The central coordinator that:
- Receives events from all detectors
- Evaluates configurable alert rules
- Manages alert lifecycle (trigger, acknowledge, resolve)
- Triggers notifications
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Awaitable

from nightwatch.core.config import AlertEngineConfig, AlertRule as AlertRuleConfig
from nightwatch.core.events import (
    Event,
    Alert,
    EventState,
    EventSeverity,
    EventBus,
    EventBuffer,
    Publisher,
    Subscriber,
)


class AlertLevel(str, Enum):
    """System-wide alert level."""

    OK = "ok"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class AlertState:
    """Current system alert state."""

    level: AlertLevel
    active_alerts: list[Alert]
    detector_states: dict[str, EventState]
    last_update: float
    paused: bool = False
    pause_expires: float | None = None


@dataclass
class RuleState:
    """Tracking state for a single rule."""

    condition_start_times: dict[int, float] = field(default_factory=dict)
    last_triggered: float | None = None


class Condition:
    """Single condition in an alert rule."""

    def __init__(
        self,
        detector: str,
        field_path: str,
        operator: str,
        threshold: Any,
        duration_seconds: float = 0,
    ):
        self.detector = detector
        self.field_path = field_path
        self.operator = operator
        self.threshold = threshold
        self.duration_seconds = duration_seconds

    def evaluate(self, event: Event) -> bool:
        """Evaluate condition against an event."""
        if event.detector != self.detector:
            return False

        # Get value from event using field path
        value = self._get_field_value(event, self.field_path)
        if value is None:
            return False

        # Compare using operator
        return self._compare(value, self.operator, self.threshold)

    def _get_field_value(self, event: Event, path: str) -> Any:
        """Get value from event using dot-notation path."""
        parts = path.split(".")
        obj: Any = event

        for part in parts:
            if hasattr(obj, part):
                obj = getattr(obj, part)
            elif isinstance(obj, dict) and part in obj:
                obj = obj[part]
            else:
                return None

        return obj

    def _compare(self, value: Any, operator: str, threshold: Any) -> bool:
        """Compare value to threshold using operator."""
        try:
            if operator == "<":
                return value < threshold
            elif operator == ">":
                return value > threshold
            elif operator == "<=":
                return value <= threshold
            elif operator == ">=":
                return value >= threshold
            elif operator == "==":
                return value == threshold
            elif operator == "!=":
                return value != threshold
            else:
                return False
        except (TypeError, ValueError):
            return False


class Rule:
    """Alert rule with conditions and actions."""

    def __init__(
        self,
        name: str,
        conditions: list[Condition],
        severity: EventSeverity,
        combine: str = "all",  # "all" or "any"
        duration_seconds: float = 0,
        cooldown_seconds: float = 30,
        message_template: str = "",
    ):
        self.name = name
        self.conditions = conditions
        self.severity = severity
        self.combine = combine
        self.duration_seconds = duration_seconds
        self.cooldown_seconds = cooldown_seconds
        self.message_template = message_template

        self._state = RuleState()

    @classmethod
    def from_config(cls, config: AlertRuleConfig) -> Rule:
        """Create rule from configuration."""
        conditions = [
            Condition(
                detector=c.detector,
                field_path=c.field,
                operator=c.operator,
                threshold=c.value,
                duration_seconds=c.duration_seconds,
            )
            for c in config.conditions
        ]

        return cls(
            name=config.name,
            conditions=conditions,
            severity=EventSeverity(config.severity),
            combine=config.combine,
            duration_seconds=config.duration_seconds,
            cooldown_seconds=config.cooldown_seconds,
            message_template=config.message,
        )

    def evaluate(
        self,
        current_events: dict[str, Event],
        history: EventBuffer,
    ) -> Alert | None:
        """
        Evaluate rule against current detector states.

        Returns an Alert if the rule triggers, None otherwise.
        """
        now = time.time()

        # Check cooldown
        if self._state.last_triggered:
            if now - self._state.last_triggered < self.cooldown_seconds:
                return None

        # Evaluate conditions
        condition_results: list[bool] = []

        for i, condition in enumerate(self.conditions):
            # Get relevant event
            event = current_events.get(condition.detector)
            if not event:
                condition_results.append(False)
                continue

            # Evaluate condition
            result = condition.evaluate(event)

            # Handle duration requirement
            if condition.duration_seconds > 0:
                if result:
                    if i not in self._state.condition_start_times:
                        self._state.condition_start_times[i] = now
                    elapsed = now - self._state.condition_start_times[i]
                    result = elapsed >= condition.duration_seconds
                else:
                    self._state.condition_start_times.pop(i, None)

            condition_results.append(result)

        # Combine results
        if self.combine == "all":
            triggered = all(condition_results) if condition_results else False
        else:  # "any"
            triggered = any(condition_results)

        # Handle rule-level duration
        if self.duration_seconds > 0 and triggered:
            if "rule" not in self._state.condition_start_times:
                self._state.condition_start_times["rule"] = now
            elapsed = now - self._state.condition_start_times["rule"]
            triggered = elapsed >= self.duration_seconds
        elif not triggered:
            self._state.condition_start_times.pop("rule", None)

        if not triggered:
            return None

        # Create alert
        self._state.last_triggered = now
        self._state.condition_start_times.clear()

        # Build message
        message = self.message_template or f"Alert: {self.name}"
        # Substitute values in message
        for detector, event in current_events.items():
            for key, value in event.value.items():
                message = message.replace(f"{{{key}}}", str(value))

        contributing_events = [e for e in current_events.values()]

        return Alert.create(
            severity=self.severity,
            rule_name=self.name,
            message=message,
            contributing_events=contributing_events,
        )

    def reset(self) -> None:
        """Reset rule state."""
        self._state = RuleState()


class AlertManager:
    """Manages active alerts and their lifecycle."""

    def __init__(self):
        self._active: dict[str, Alert] = {}
        self._history: list[Alert] = []
        self._max_history = 1000

    def add(self, alert: Alert) -> bool:
        """Add new alert. Returns True if added."""
        if alert.id in self._active:
            return False
        self._active[alert.id] = alert
        return True

    def acknowledge(self, alert_id: str) -> Alert | None:
        """Acknowledge an alert. Returns updated alert."""
        if alert_id not in self._active:
            return None

        alert = self._active[alert_id].acknowledge()
        self._active[alert_id] = alert
        return alert

    def resolve(self, alert_id: str) -> Alert | None:
        """Resolve an alert. Returns updated alert."""
        if alert_id not in self._active:
            return None

        alert = self._active[alert_id].resolve()
        del self._active[alert_id]

        self._history.append(alert)
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history :]

        return alert

    def get_active(self) -> list[Alert]:
        """Get all active alerts."""
        return list(self._active.values())

    def get_by_id(self, alert_id: str) -> Alert | None:
        """Get alert by ID."""
        return self._active.get(alert_id)

    def get_history(self, limit: int = 50) -> list[Alert]:
        """Get recent alert history."""
        return self._history[-limit:]

    def clear_all(self) -> None:
        """Clear all active alerts."""
        for alert in self._active.values():
            self._history.append(alert.resolve())
        self._active.clear()


class DetectorHealthMonitor:
    """Monitors detector connectivity and health."""

    def __init__(self, timeout_seconds: float = 10.0):
        self._last_seen: dict[str, float] = {}
        self._timeout = timeout_seconds

    def update(self, detector: str) -> None:
        """Record event from detector."""
        self._last_seen[detector] = time.time()

    def get_status(self, detector: str) -> str:
        """Get detector status."""
        if detector not in self._last_seen:
            return "unknown"

        elapsed = time.time() - self._last_seen[detector]
        if elapsed > self._timeout:
            return "offline"
        return "online"

    def get_offline_detectors(self) -> list[str]:
        """Get list of offline detectors."""
        now = time.time()
        return [
            d for d, t in self._last_seen.items() if now - t > self._timeout
        ]

    def get_all_status(self) -> dict[str, str]:
        """Get status of all known detectors."""
        return {d: self.get_status(d) for d in self._last_seen}


class AlertEngine:
    """
    Main alert processing engine.

    Receives events from detectors, evaluates rules, manages alerts,
    and triggers notifications.
    """

    def __init__(
        self,
        config: AlertEngineConfig,
        event_bus: EventBus | None = None,
        notifiers: list[Any] | None = None,
    ):
        self._config = config
        self._event_bus = event_bus
        self._notifiers = notifiers or []

        # Create rules from config
        self._rules = [Rule.from_config(r) for r in config.rules]

        # Event buffer for recent events
        self._buffer = EventBuffer(capacity=5000)

        # Current event per detector
        self._current_events: dict[str, Event] = {}

        # Alert management
        self._alert_manager = AlertManager()
        self._health_monitor = DetectorHealthMonitor(config.detector_timeout_seconds)

        # State
        self._running = False
        self._paused = False
        self._pause_expires: float | None = None
        self._subscriber: Subscriber | None = None

        # Callbacks
        self.on_alert: Callable[[Alert], Awaitable[None]] | None = None
        self.on_state_change: Callable[[AlertState], Awaitable[None]] | None = None
        self.on_detector_offline: Callable[[str], Awaitable[None]] | None = None

    async def start(self) -> None:
        """Start the alert engine."""
        if self._running:
            return

        self._running = True

        # Subscribe to events if event bus provided
        if self._event_bus:
            self._subscriber = self._event_bus.create_subscriber()
            self._subscriber.set_callback(self._on_event)
            asyncio.create_task(self._subscriber.run())

        # Start health check task
        asyncio.create_task(self._health_check_loop())

    async def stop(self) -> None:
        """Stop the alert engine."""
        self._running = False

        if self._subscriber:
            self._subscriber.stop()
            self._subscriber.close()
            self._subscriber = None

    async def process_event(self, event: Event) -> None:
        """
        Process an incoming event.

        This is the main entry point for event processing.
        Can be called directly or via event bus subscription.
        """
        # Store event
        self._buffer.append(event)
        self._current_events[event.detector] = event

        # Update health monitor
        self._health_monitor.update(event.detector)

        # Check if paused
        if self._paused:
            if self._pause_expires and time.time() >= self._pause_expires:
                self._paused = False
                self._pause_expires = None
            else:
                return

        # Evaluate rules
        for rule in self._rules:
            alert = rule.evaluate(self._current_events, self._buffer)
            if alert:
                await self._trigger_alert(alert)

    async def _on_event(self, topic: str, event: Event) -> None:
        """Callback for events from event bus."""
        await self.process_event(event)

    async def _trigger_alert(self, alert: Alert) -> None:
        """Trigger an alert and send notifications."""
        if not self._alert_manager.add(alert):
            return  # Duplicate

        # Callback
        if self.on_alert:
            await self.on_alert(alert)

        # State change callback
        if self.on_state_change:
            await self.on_state_change(self.get_state())

        # Send to notifiers
        for notifier in self._notifiers:
            try:
                await notifier.notify(alert)
            except Exception as e:
                print(f"Notifier error: {e}")

    async def _health_check_loop(self) -> None:
        """Periodically check detector health."""
        while self._running:
            await asyncio.sleep(self._config.health_check_interval)

            offline = self._health_monitor.get_offline_detectors()
            for detector in offline:
                if self.on_detector_offline:
                    await self.on_detector_offline(detector)

    def get_state(self) -> AlertState:
        """Get current alert state."""
        active = self._alert_manager.get_active()

        # Determine overall level
        if any(a.severity == EventSeverity.CRITICAL for a in active):
            level = AlertLevel.CRITICAL
        elif any(a.severity == EventSeverity.WARNING for a in active):
            level = AlertLevel.WARNING
        else:
            level = AlertLevel.OK

        # Get detector states
        detector_states = {
            detector: event.state
            for detector, event in self._current_events.items()
        }

        return AlertState(
            level=level,
            active_alerts=active,
            detector_states=detector_states,
            last_update=time.time(),
            paused=self._paused,
            pause_expires=self._pause_expires,
        )

    def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge an alert."""
        result = self._alert_manager.acknowledge(alert_id)
        return result is not None

    def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an alert."""
        result = self._alert_manager.resolve(alert_id)
        return result is not None

    def pause(self, duration_seconds: int) -> None:
        """Pause alerting for the specified duration."""
        max_pause = self._config.max_pause_minutes * 60
        duration_seconds = min(duration_seconds, max_pause)

        self._paused = True
        self._pause_expires = time.time() + duration_seconds

    def resume(self) -> None:
        """Resume alerting."""
        self._paused = False
        self._pause_expires = None

    def get_recent_events(self, detector: str | None = None, seconds: float = 60) -> list[Event]:
        """Get recent events, optionally filtered by detector."""
        events = self._buffer.get_recent(seconds)
        if detector:
            events = [e for e in events if e.detector == detector]
        return events

    def get_current_event(self, detector: str) -> Event | None:
        """Get the most recent event from a detector."""
        return self._current_events.get(detector)

    def add_rule(self, rule: Rule) -> None:
        """Add a new rule."""
        self._rules.append(rule)

    def remove_rule(self, rule_name: str) -> bool:
        """Remove a rule by name."""
        for i, rule in enumerate(self._rules):
            if rule.name == rule_name:
                del self._rules[i]
                return True
        return False
