"""
Sensor Fusion Engine for Nightwatch.

Combines signals from multiple detectors into unified "channels" that provide:
- Redundancy (multiple sensors for same signal)
- Cross-validation (sensors agreeing boosts confidence)
- Graceful degradation (works with subset of sensors)

See docs/FUSION.md for architecture details.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Awaitable

from nightwatch.core.events import Event, EventState, EventBus, Publisher, Subscriber
from nightwatch.core.config import FusionConfig, FusionRule, FusionRuleSource


@dataclass
class SignalValue:
    """A single signal reading from a detector."""

    value: float | bool | None
    confidence: float
    timestamp: float
    detector: str
    field: str
    weight: float = 1.0


@dataclass
class FusedSignal:
    """Result of fusing multiple signal sources."""

    channel: str
    value: float | bool | None
    confidence: float
    timestamp: float
    sources: list[str] = field(default_factory=list)
    agreement: float = 1.0  # How much sources agreed (0-1)
    degraded: bool = False  # Fewer sources than ideal

    def to_event(self) -> Event:
        """Convert to Event for publishing on EventBus."""
        return Event(
            detector=f"fusion.{self.channel}",
            timestamp=self.timestamp,
            confidence=self.confidence,
            state=EventState.NORMAL,
            value={
                "value": self.value,
                "sources": self.sources,
                "source_count": len(self.sources),
                "agreement": self.agreement,
                "degraded": self.degraded,
            },
        )


class FusionEngine:
    """
    Sensor fusion engine that combines detector signals into unified channels.

    The engine:
    1. Subscribes to all detector events via EventBus
    2. Maintains latest values from each detector
    3. Applies fusion strategies to combine signals
    4. Emits fused channel events

    Fusion strategies:
    - weighted_average: Weighted mean for continuous values (respiration, HR)
    - best_confidence: Use reading with highest confidence
    - voting: Majority vote for boolean signals (presence)
    - any: Boolean OR - any true triggers (seizure detection)
    - all: Boolean AND - all must be true
    - max: Use maximum value (movement intensity)
    """

    def __init__(
        self,
        config: FusionConfig,
        event_bus: EventBus | None = None,
    ):
        self._config = config
        self._event_bus = event_bus
        self._publisher: Publisher | None = None
        self._subscriber: Subscriber | None = None
        self._running = False
        self._receive_task: asyncio.Task | None = None

        # Latest values per detector/field: {detector: {field: SignalValue}}
        self._latest: dict[str, dict[str, SignalValue]] = {}

        # Current fused channel values
        self._channels: dict[str, FusedSignal] = {}

        # Callbacks
        self.on_channel_update: Callable[[FusedSignal], Awaitable[None]] | None = None

    async def start(self) -> None:
        """Start the fusion engine."""
        if self._running:
            return

        self._running = True

        if self._event_bus:
            # Create publisher for emitting fused events
            self._publisher = self._event_bus.create_publisher()

            # Subscribe to all detector events
            self._subscriber = self._event_bus.create_subscriber(topics=None)
            self._subscriber.set_callback(self._on_detector_event)
            self._receive_task = asyncio.create_task(self._subscriber.run())

    async def stop(self) -> None:
        """Stop the fusion engine."""
        self._running = False

        if self._subscriber:
            self._subscriber.stop()

        if self._receive_task:
            self._receive_task.cancel()
            try:
                await self._receive_task
            except asyncio.CancelledError:
                pass

    async def _on_detector_event(self, topic: str, event: Event) -> None:
        """Handle incoming detector event."""
        # Ignore fusion events to prevent feedback loops
        if event.detector.startswith("fusion."):
            return

        await self.process_event(event)

    async def process_event(self, event: Event) -> None:
        """
        Process a detector event and update fused channels.

        Can be called directly (for testing) or via EventBus subscription.
        """
        # Update latest values from this detector
        self._update_latest(event)

        # Recalculate all affected channels
        await self._recalculate_channels()

    def _update_latest(self, event: Event) -> None:
        """Track latest values from detector event."""
        detector = event.detector

        if detector not in self._latest:
            self._latest[detector] = {}

        # Store each field from the event value
        for field_name, value in event.value.items():
            full_field = f"value.{field_name}"
            self._latest[detector][full_field] = SignalValue(
                value=value,
                confidence=event.confidence,
                timestamp=event.timestamp,
                detector=detector,
                field=full_field,
            )

    async def _recalculate_channels(self) -> None:
        """Recalculate all fused channels."""
        now = time.time()

        for rule in self._config.rules:
            fused = self._fuse_rule(rule, now)

            if fused is not None:
                old = self._channels.get(rule.signal)

                # Only emit if value changed or it's been a while
                if old is None or self._should_emit(old, fused):
                    self._channels[rule.signal] = fused
                    await self._emit_fused(fused)

    def _fuse_rule(self, rule: FusionRule, now: float) -> FusedSignal | None:
        """Apply fusion rule to gather and combine sources."""
        sources = self._gather_sources(rule, now)

        if len(sources) < rule.min_sources:
            return None

        # Apply strategy
        strategy = rule.strategy.lower()

        if strategy == "weighted_average":
            return self._fuse_weighted_average(rule.signal, sources)
        elif strategy == "best_confidence":
            return self._fuse_best_confidence(rule.signal, sources)
        elif strategy == "voting":
            return self._fuse_voting(rule.signal, sources)
        elif strategy == "any":
            return self._fuse_any(rule.signal, sources)
        elif strategy == "all":
            return self._fuse_all(rule.signal, sources)
        elif strategy == "max":
            return self._fuse_max(rule.signal, sources)
        else:
            # Default to weighted average
            return self._fuse_weighted_average(rule.signal, sources)

    def _gather_sources(self, rule: FusionRule, now: float) -> list[SignalValue]:
        """Gather current signal values matching fusion rule sources."""
        sources: list[SignalValue] = []
        max_age = self._config.signal_max_age_seconds

        for source in rule.sources:
            detector_data = self._latest.get(source.detector)
            if not detector_data:
                continue

            signal = detector_data.get(source.field)
            if not signal:
                continue

            # Filter stale signals
            if now - signal.timestamp > max_age:
                continue

            # Skip None values
            if signal.value is None:
                continue

            # Apply source weight
            signal.weight = source.weight
            sources.append(signal)

        return sources

    # =========================================================================
    # Fusion Strategies
    # =========================================================================

    def _fuse_weighted_average(
        self, channel: str, sources: list[SignalValue]
    ) -> FusedSignal:
        """
        Weighted average for continuous values.

        fused = sum(value * weight * confidence) / sum(weight * confidence)
        """
        now = time.time()

        # Filter to numeric values only
        numeric = [s for s in sources if isinstance(s.value, (int, float))]

        if not numeric:
            return FusedSignal(
                channel=channel,
                value=None,
                confidence=0.0,
                timestamp=now,
                sources=[],
                degraded=True,
            )

        total_weight = sum(s.weight * s.confidence for s in numeric)

        if total_weight == 0:
            return FusedSignal(
                channel=channel,
                value=None,
                confidence=0.0,
                timestamp=now,
                sources=[s.detector for s in numeric],
                degraded=True,
            )

        weighted_sum = sum(s.value * s.weight * s.confidence for s in numeric)
        fused_value = weighted_sum / total_weight

        # Calculate agreement and confidence
        agreement, confidence = self._calculate_agreement(numeric)

        return FusedSignal(
            channel=channel,
            value=round(fused_value, 2),
            confidence=confidence,
            timestamp=now,
            sources=[s.detector for s in numeric],
            agreement=agreement,
            degraded=len(numeric) == 1,
        )

    def _fuse_best_confidence(
        self, channel: str, sources: list[SignalValue]
    ) -> FusedSignal:
        """Use reading with highest confidence."""
        now = time.time()

        best = max(sources, key=lambda s: s.confidence)

        return FusedSignal(
            channel=channel,
            value=best.value,
            confidence=best.confidence,
            timestamp=now,
            sources=[best.detector],
            agreement=1.0,
            degraded=len(sources) == 1,
        )

    def _fuse_voting(self, channel: str, sources: list[SignalValue]) -> FusedSignal:
        """
        Majority vote for boolean signals.

        confidence = |votes_true - votes_false| / total
        """
        now = time.time()

        # Convert to boolean
        votes_true = sum(1 for s in sources if bool(s.value))
        votes_false = len(sources) - votes_true

        fused_value = votes_true > votes_false

        # Unanimous = 1.0, split = lower
        if len(sources) > 0:
            agreement = abs(votes_true - votes_false) / len(sources)
        else:
            agreement = 0.0

        confidence = sum(s.confidence for s in sources) / len(sources) if sources else 0

        return FusedSignal(
            channel=channel,
            value=fused_value,
            confidence=confidence * agreement,
            timestamp=now,
            sources=[s.detector for s in sources],
            agreement=agreement,
            degraded=len(sources) == 1,
        )

    def _fuse_any(self, channel: str, sources: list[SignalValue]) -> FusedSignal:
        """
        Boolean OR - any true triggers.

        Used for critical alerts like seizure detection.
        """
        now = time.time()

        true_sources = [s for s in sources if bool(s.value)]
        fused_value = len(true_sources) > 0

        if true_sources:
            confidence = max(s.confidence for s in true_sources)
            contributors = [s.detector for s in true_sources]
        else:
            confidence = max(s.confidence for s in sources) if sources else 0
            contributors = [s.detector for s in sources]

        # Agreement bonus for multiple confirming sources
        agreement = min(1.0, len(true_sources) / max(len(sources), 1))

        return FusedSignal(
            channel=channel,
            value=fused_value,
            confidence=confidence,
            timestamp=now,
            sources=contributors,
            agreement=agreement if fused_value else 1.0,
            degraded=len(sources) == 1,
        )

    def _fuse_all(self, channel: str, sources: list[SignalValue]) -> FusedSignal:
        """Boolean AND - all must be true."""
        now = time.time()

        fused_value = all(bool(s.value) for s in sources)

        # Use minimum confidence
        confidence = min(s.confidence for s in sources) if sources else 0

        return FusedSignal(
            channel=channel,
            value=fused_value,
            confidence=confidence,
            timestamp=now,
            sources=[s.detector for s in sources],
            agreement=1.0 if fused_value else 0.0,
            degraded=len(sources) == 1,
        )

    def _fuse_max(self, channel: str, sources: list[SignalValue]) -> FusedSignal:
        """Use maximum value (for movement intensity)."""
        now = time.time()

        # Filter to numeric
        numeric = [s for s in sources if isinstance(s.value, (int, float))]

        if not numeric:
            return FusedSignal(
                channel=channel,
                value=None,
                confidence=0.0,
                timestamp=now,
                sources=[],
                degraded=True,
            )

        best = max(numeric, key=lambda s: s.value)

        return FusedSignal(
            channel=channel,
            value=best.value,
            confidence=best.confidence,
            timestamp=now,
            sources=[best.detector],
            agreement=1.0,
            degraded=len(numeric) == 1,
        )

    # =========================================================================
    # Agreement / Cross-Validation
    # =========================================================================

    def _calculate_agreement(
        self, sources: list[SignalValue]
    ) -> tuple[float, float]:
        """
        Calculate agreement score and adjusted confidence.

        Returns: (agreement_score, adjusted_confidence)
        """
        if len(sources) < 2:
            # Single source - no agreement calculation
            return 1.0, sources[0].confidence if sources else 0.0

        values = [s.value for s in sources]
        mean_val = sum(values) / len(values)

        if mean_val == 0:
            # Avoid division by zero
            variance = sum((v - mean_val) ** 2 for v in values) / len(values)
        else:
            # Coefficient of variation
            variance = sum((v - mean_val) ** 2 for v in values) / len(values)
            cv = (variance ** 0.5) / abs(mean_val) if mean_val != 0 else 0

            # Agreement = 1 - CV (capped at 0-1)
            agreement = max(0.0, min(1.0, 1.0 - cv))

        # For numeric agreement, use standard deviation approach
        if variance == 0:
            agreement = 1.0
        else:
            # Normalize: smaller variance = higher agreement
            std_dev = variance ** 0.5
            # Agreement based on relative spread
            agreement = max(0.0, 1.0 - (std_dev / (abs(mean_val) + 1)))

        # Base confidence = weighted average of source confidences
        total_weight = sum(s.weight for s in sources)
        base_confidence = sum(s.confidence * s.weight for s in sources) / total_weight

        # Apply agreement bonus/penalty
        if self._config.cross_validation_enabled:
            if agreement > 0.8:
                adjusted = base_confidence + self._config.agreement_bonus
            elif agreement < 0.5:
                adjusted = base_confidence - self._config.disagreement_penalty
            else:
                adjusted = base_confidence

            adjusted = max(0.0, min(1.0, adjusted))
        else:
            adjusted = base_confidence

        return round(agreement, 2), round(adjusted, 2)

    # =========================================================================
    # Emission
    # =========================================================================

    def _should_emit(self, old: FusedSignal, new: FusedSignal) -> bool:
        """Determine if we should emit an update."""
        # Always emit if value changed
        if old.value != new.value:
            return True

        # Emit if confidence changed significantly
        if abs(old.confidence - new.confidence) > 0.1:
            return True

        # Emit if sources changed
        if set(old.sources) != set(new.sources):
            return True

        return False

    async def _emit_fused(self, fused: FusedSignal) -> None:
        """Emit fused signal as event."""
        if self._publisher:
            await self._publisher.send(fused.to_event())

        if self.on_channel_update:
            await self.on_channel_update(fused)

    # =========================================================================
    # Public API
    # =========================================================================

    def get_channel(self, name: str) -> FusedSignal | None:
        """Get current value of a fused channel."""
        return self._channels.get(name)

    def get_all_channels(self) -> dict[str, FusedSignal]:
        """Get all current fused channel values."""
        return self._channels.copy()

    def get_latest_detector_values(self) -> dict[str, dict[str, SignalValue]]:
        """Get all latest detector values (for debugging)."""
        return {
            detector: fields.copy()
            for detector, fields in self._latest.items()
        }
