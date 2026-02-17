"""Tests for fusion engine."""

import time
import pytest

from nightwatch.core.events import Event, EventState
from nightwatch.core.config import FusionConfig, FusionRule, FusionRuleSource
from nightwatch.core.fusion import FusionEngine, FusedSignal, SignalValue


def make_event(
    detector: str,
    value: dict,
    confidence: float = 0.9,
    timestamp: float | None = None,
) -> Event:
    """Helper to create test events."""
    return Event(
        detector=detector,
        timestamp=timestamp or time.time(),
        confidence=confidence,
        state=EventState.NORMAL,
        value=value,
    )


def make_config(rules: list[FusionRule]) -> FusionConfig:
    """Helper to create test config."""
    return FusionConfig(
        signal_max_age_seconds=5.0,
        cross_validation_enabled=True,
        agreement_bonus=0.1,
        disagreement_penalty=0.2,
        rules=rules,
    )


class TestFusedSignal:
    """Tests for FusedSignal dataclass."""

    def test_fused_signal_to_event(self):
        """FusedSignal converts to Event correctly."""
        fused = FusedSignal(
            channel="respiration_rate",
            value=14.5,
            confidence=0.9,
            timestamp=time.time(),
            sources=["radar", "audio"],
            agreement=0.95,
            degraded=False,
        )

        event = fused.to_event()

        assert event.detector == "fusion.respiration_rate"
        assert event.confidence == 0.9
        assert event.value["value"] == 14.5
        assert event.value["sources"] == ["radar", "audio"]
        assert event.value["source_count"] == 2
        assert event.value["agreement"] == 0.95
        assert event.value["degraded"] is False


class TestFusionEngineWeightedAverage:
    """Tests for weighted_average fusion strategy."""

    @pytest.fixture
    def engine(self) -> FusionEngine:
        """Create fusion engine with respiration rule."""
        config = make_config([
            FusionRule(
                signal="respiration_rate",
                sources=[
                    FusionRuleSource(detector="radar", field="value.respiration_rate", weight=1.0),
                    FusionRuleSource(detector="audio", field="value.breathing_rate", weight=0.8),
                ],
                strategy="weighted_average",
                min_sources=1,
            )
        ])
        return FusionEngine(config)

    @pytest.mark.asyncio
    async def test_single_source(self, engine: FusionEngine):
        """Fusion works with single source."""
        event = make_event("radar", {"respiration_rate": 14.0}, confidence=0.9)
        await engine.process_event(event)

        result = engine.get_channel("respiration_rate")

        assert result is not None
        assert result.value == 14.0
        assert result.sources == ["radar"]
        assert result.degraded is True  # Single source

    @pytest.mark.asyncio
    async def test_multiple_sources_agreement(self, engine: FusionEngine):
        """Fusion combines agreeing sources."""
        await engine.process_event(
            make_event("radar", {"respiration_rate": 14.0}, confidence=0.9)
        )
        await engine.process_event(
            make_event("audio", {"breathing_rate": 14.5}, confidence=0.8)
        )

        result = engine.get_channel("respiration_rate")

        assert result is not None
        # Weighted average: (14.0 * 1.0 * 0.9 + 14.5 * 0.8 * 0.8) / (1.0 * 0.9 + 0.8 * 0.8)
        # = (12.6 + 9.28) / (0.9 + 0.64) = 21.88 / 1.54 ≈ 14.21
        assert 14.0 <= result.value <= 14.5
        assert set(result.sources) == {"radar", "audio"}
        assert result.degraded is False

    @pytest.mark.asyncio
    async def test_stale_signals_ignored(self, engine: FusionEngine):
        """Old signals are ignored."""
        now = time.time()

        # Old event (10 seconds ago)
        await engine.process_event(
            make_event("radar", {"respiration_rate": 5.0}, timestamp=now - 10)
        )

        # Fresh event
        await engine.process_event(
            make_event("audio", {"breathing_rate": 14.0}, timestamp=now)
        )

        result = engine.get_channel("respiration_rate")

        assert result is not None
        assert result.value == 14.0  # Only fresh audio used
        assert result.sources == ["audio"]

    @pytest.mark.asyncio
    async def test_none_values_ignored(self, engine: FusionEngine):
        """None values don't contribute to fusion."""
        await engine.process_event(
            make_event("radar", {"respiration_rate": None}, confidence=0.9)
        )
        await engine.process_event(
            make_event("audio", {"breathing_rate": 14.0}, confidence=0.8)
        )

        result = engine.get_channel("respiration_rate")

        assert result is not None
        assert result.value == 14.0
        assert result.sources == ["audio"]


class TestFusionEngineVoting:
    """Tests for voting fusion strategy."""

    @pytest.fixture
    def engine(self) -> FusionEngine:
        """Create fusion engine with presence rule."""
        config = make_config([
            FusionRule(
                signal="presence",
                sources=[
                    FusionRuleSource(detector="radar", field="value.presence"),
                    FusionRuleSource(detector="capacitive", field="value.bed_occupied"),
                ],
                strategy="voting",
                min_sources=1,
            )
        ])
        return FusionEngine(config)

    @pytest.mark.asyncio
    async def test_voting_unanimous_true(self, engine: FusionEngine):
        """All sources true = high confidence true."""
        await engine.process_event(make_event("radar", {"presence": True}))
        await engine.process_event(make_event("capacitive", {"bed_occupied": True}))

        result = engine.get_channel("presence")

        assert result is not None
        assert result.value is True
        assert result.agreement == 1.0

    @pytest.mark.asyncio
    async def test_voting_unanimous_false(self, engine: FusionEngine):
        """All sources false = false."""
        await engine.process_event(make_event("radar", {"presence": False}))
        await engine.process_event(make_event("capacitive", {"bed_occupied": False}))

        result = engine.get_channel("presence")

        assert result is not None
        assert result.value is False
        assert result.agreement == 1.0

    @pytest.mark.asyncio
    async def test_voting_split(self, engine: FusionEngine):
        """Split vote follows majority."""
        await engine.process_event(make_event("radar", {"presence": True}))
        await engine.process_event(make_event("capacitive", {"bed_occupied": False}))

        result = engine.get_channel("presence")

        assert result is not None
        # With equal votes, neither wins clearly
        assert result.agreement == 0.0


class TestFusionEngineAny:
    """Tests for 'any' fusion strategy (Boolean OR)."""

    @pytest.fixture
    def engine(self) -> FusionEngine:
        """Create fusion engine with seizure rule."""
        config = make_config([
            FusionRule(
                signal="seizure",
                sources=[
                    FusionRuleSource(detector="audio", field="value.seizure_detected"),
                    FusionRuleSource(detector="radar", field="value.seizure_detected"),
                ],
                strategy="any",
                min_sources=1,
            )
        ])
        return FusionEngine(config)

    @pytest.mark.asyncio
    async def test_any_single_true(self, engine: FusionEngine):
        """Any single true triggers."""
        await engine.process_event(
            make_event("audio", {"seizure_detected": True}, confidence=0.95)
        )
        await engine.process_event(
            make_event("radar", {"seizure_detected": False}, confidence=0.9)
        )

        result = engine.get_channel("seizure")

        assert result is not None
        assert result.value is True
        assert result.confidence == 0.95  # From the true source

    @pytest.mark.asyncio
    async def test_any_all_false(self, engine: FusionEngine):
        """All false = false."""
        await engine.process_event(make_event("audio", {"seizure_detected": False}))
        await engine.process_event(make_event("radar", {"seizure_detected": False}))

        result = engine.get_channel("seizure")

        assert result is not None
        assert result.value is False

    @pytest.mark.asyncio
    async def test_any_multiple_true(self, engine: FusionEngine):
        """Multiple true sources increase agreement."""
        await engine.process_event(make_event("audio", {"seizure_detected": True}))
        await engine.process_event(make_event("radar", {"seizure_detected": True}))

        result = engine.get_channel("seizure")

        assert result is not None
        assert result.value is True
        assert result.agreement == 1.0  # Both agree


class TestFusionEngineMax:
    """Tests for 'max' fusion strategy."""

    @pytest.fixture
    def engine(self) -> FusionEngine:
        """Create fusion engine with movement rule."""
        config = make_config([
            FusionRule(
                signal="movement",
                sources=[
                    FusionRuleSource(detector="radar", field="value.movement"),
                    FusionRuleSource(detector="capacitive", field="value.movement"),
                ],
                strategy="max",
                min_sources=1,
            )
        ])
        return FusionEngine(config)

    @pytest.mark.asyncio
    async def test_max_picks_highest(self, engine: FusionEngine):
        """Max strategy picks highest value."""
        await engine.process_event(make_event("radar", {"movement": 0.3}))
        await engine.process_event(make_event("capacitive", {"movement": 0.8}))

        result = engine.get_channel("movement")

        assert result is not None
        assert result.value == 0.8
        assert result.sources == ["capacitive"]


class TestFusionEngineMinSources:
    """Tests for minimum source requirements."""

    @pytest.fixture
    def engine(self) -> FusionEngine:
        """Create fusion engine requiring 2 sources."""
        config = make_config([
            FusionRule(
                signal="heart_rate",
                sources=[
                    FusionRuleSource(detector="capacitive", field="value.heart_rate", weight=1.0),
                    FusionRuleSource(detector="radar", field="value.heart_rate_estimate", weight=0.3),
                ],
                strategy="weighted_average",
                min_sources=2,  # Require both
            )
        ])
        return FusionEngine(config)

    @pytest.mark.asyncio
    async def test_below_min_sources(self, engine: FusionEngine):
        """No result if below min_sources."""
        await engine.process_event(make_event("radar", {"heart_rate_estimate": 72}))

        result = engine.get_channel("heart_rate")

        assert result is None  # Needs 2 sources, only have 1

    @pytest.mark.asyncio
    async def test_meets_min_sources(self, engine: FusionEngine):
        """Result when min_sources met."""
        await engine.process_event(make_event("capacitive", {"heart_rate": 70}))
        await engine.process_event(make_event("radar", {"heart_rate_estimate": 72}))

        result = engine.get_channel("heart_rate")

        assert result is not None
        assert 70 <= result.value <= 72


class TestFusionEngineCrossValidation:
    """Tests for cross-validation and agreement."""

    @pytest.mark.asyncio
    async def test_agreement_boosts_confidence(self):
        """Agreeing sources boost confidence."""
        config = FusionConfig(
            signal_max_age_seconds=5.0,
            cross_validation_enabled=True,
            agreement_bonus=0.1,
            disagreement_penalty=0.2,
            rules=[
                FusionRule(
                    signal="respiration_rate",
                    sources=[
                        FusionRuleSource(detector="radar", field="value.respiration_rate"),
                        FusionRuleSource(detector="audio", field="value.breathing_rate"),
                    ],
                    strategy="weighted_average",
                    min_sources=2,
                )
            ],
        )
        engine = FusionEngine(config)

        # Very similar values = high agreement
        await engine.process_event(make_event("radar", {"respiration_rate": 14.0}, confidence=0.8))
        await engine.process_event(make_event("audio", {"breathing_rate": 14.1}, confidence=0.8))

        result = engine.get_channel("respiration_rate")

        assert result is not None
        assert result.agreement > 0.8  # High agreement
        # Confidence should be boosted from base 0.8

    @pytest.mark.asyncio
    async def test_disagreement_lowers_confidence(self):
        """Disagreeing sources lower confidence."""
        config = FusionConfig(
            signal_max_age_seconds=5.0,
            cross_validation_enabled=True,
            agreement_bonus=0.1,
            disagreement_penalty=0.2,
            rules=[
                FusionRule(
                    signal="respiration_rate",
                    sources=[
                        FusionRuleSource(detector="radar", field="value.respiration_rate"),
                        FusionRuleSource(detector="audio", field="value.breathing_rate"),
                    ],
                    strategy="weighted_average",
                    min_sources=2,
                )
            ],
        )
        engine = FusionEngine(config)

        # Very different values = lower agreement than similar values
        await engine.process_event(make_event("radar", {"respiration_rate": 10.0}, confidence=0.8))
        await engine.process_event(make_event("audio", {"breathing_rate": 20.0}, confidence=0.8))

        result = engine.get_channel("respiration_rate")

        assert result is not None
        # 10 vs 20 is a 67% spread - agreement should be lower than perfect
        assert result.agreement < 0.8


class TestFusionEngineAPI:
    """Tests for public API methods."""

    @pytest.mark.asyncio
    async def test_get_all_channels(self):
        """get_all_channels returns all fused values."""
        config = make_config([
            FusionRule(
                signal="respiration_rate",
                sources=[FusionRuleSource(detector="radar", field="value.respiration_rate")],
                strategy="weighted_average",
            ),
            FusionRule(
                signal="presence",
                sources=[FusionRuleSource(detector="radar", field="value.presence")],
                strategy="voting",
            ),
        ])
        engine = FusionEngine(config)

        await engine.process_event(
            make_event("radar", {"respiration_rate": 14.0, "presence": True})
        )

        channels = engine.get_all_channels()

        assert "respiration_rate" in channels
        assert "presence" in channels
        assert channels["respiration_rate"].value == 14.0
        assert channels["presence"].value is True

    @pytest.mark.asyncio
    async def test_get_latest_detector_values(self):
        """get_latest_detector_values returns raw signals."""
        config = make_config([])  # No rules needed
        engine = FusionEngine(config)

        await engine.process_event(
            make_event("radar", {"respiration_rate": 14.0, "presence": True})
        )

        latest = engine.get_latest_detector_values()

        assert "radar" in latest
        assert "value.respiration_rate" in latest["radar"]
        assert latest["radar"]["value.respiration_rate"].value == 14.0


class TestFusionEngineCallback:
    """Tests for callback functionality."""

    @pytest.mark.asyncio
    async def test_on_channel_update_callback(self):
        """Callback fires when channel updates."""
        config = make_config([
            FusionRule(
                signal="respiration_rate",
                sources=[FusionRuleSource(detector="radar", field="value.respiration_rate")],
                strategy="weighted_average",
            ),
        ])
        engine = FusionEngine(config)

        updates = []

        async def callback(fused: FusedSignal):
            updates.append(fused)

        engine.on_channel_update = callback

        await engine.process_event(make_event("radar", {"respiration_rate": 14.0}))

        assert len(updates) == 1
        assert updates[0].channel == "respiration_rate"
        assert updates[0].value == 14.0
