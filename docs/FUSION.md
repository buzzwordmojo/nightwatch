# Nightwatch Fusion Layer Architecture

This document describes the sensor fusion architecture that combines multiple sensor inputs into unified signal channels for reliable health monitoring.

## Why Fusion?

### The Problem

Without fusion, alert rules must reference specific sensors:

```yaml
# Current: Pick ONE sensor, no fallback
rules:
  - name: "Low respiration"
    conditions:
      - detector: radar
        field: value.respiration_rate
        operator: "<"
        value: 6
```

**Issues**:
1. If radar loses signal, no fallback to audio's breathing rate
2. No cross-validation between sensors
3. Rules must know about sensor implementation details
4. Adding new sensors requires updating all rules

### The Solution

Fusion layer creates **channels** that abstract away individual sensors:

```yaml
# Future: Reference fused channel
rules:
  - name: "Low respiration"
    conditions:
      - channel: respiration_rate  # Fused from multiple sensors
        operator: "<"
        value: 6
```

**Benefits**:
1. Automatic fallback when sensors degrade
2. Cross-validation boosts confidence when sensors agree
3. Rules reference logical signals, not hardware
4. New sensors automatically contribute to channels

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           SENSOR LAYER                                   │
│                                                                          │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐              │
│  │  Radar   │   │  Audio   │   │   BCG    │   │ [Future] │              │
│  │ LD2450   │   │ USB Mic  │   │  Piezo   │   │ Thermal  │              │
│  └────┬─────┘   └────┬─────┘   └────┬─────┘   └────┬─────┘              │
│       │              │              │              │                     │
│       │ Events       │ Events       │ Events       │ Events              │
│       ▼              ▼              ▼              ▼                     │
└───────┼──────────────┼──────────────┼──────────────┼─────────────────────┘
        │              │              │              │
        └──────────────┴──────────────┴──────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          FUSION ENGINE                                   │
│                                                                          │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │                    Latest Value Buffer                           │   │
│   │  radar.respiration_rate = 14.2 @ t-0.3s, confidence=0.85        │   │
│   │  audio.breathing_rate = 13.8 @ t-0.5s, confidence=0.72          │   │
│   │  bcg.respiration_rate = 15.1 @ t-0.2s, confidence=0.60          │   │
│   │  bcg.heart_rate = 72 @ t-0.2s, confidence=0.91                  │   │
│   │  radar.heart_rate_estimate = 68 @ t-0.3s, confidence=0.45       │   │
│   └─────────────────────────────────────────────────────────────────┘   │
│                              │                                           │
│                              ▼                                           │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │                    Fusion Rules                                  │   │
│   │                                                                  │   │
│   │  respiration_rate:                                               │   │
│   │    sources: [radar(1.0), audio(0.8), bcg(0.5)]                  │   │
│   │    strategy: weighted_average                                    │   │
│   │                                                                  │   │
│   │  heart_rate:                                                     │   │
│   │    sources: [bcg(1.0), radar(0.3)]                              │   │
│   │    strategy: weighted_average                                    │   │
│   │                                                                  │   │
│   │  seizure:                                                        │   │
│   │    sources: [audio, radar, bcg]                                 │   │
│   │    strategy: any                                                 │   │
│   └─────────────────────────────────────────────────────────────────┘   │
│                              │                                           │
│                              ▼                                           │
└──────────────────────────────┼──────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        FUSED CHANNELS                                    │
│                                                                          │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐             │
│  │ respiration    │  │ heart_rate     │  │ seizure        │             │
│  │ rate: 14.1     │  │ rate: 71       │  │ detected: no   │             │
│  │ conf: 0.89     │  │ conf: 0.88     │  │ conf: 0.0      │             │
│  │ sources: 3     │  │ sources: 2     │  │ sources: 0     │             │
│  │ agreement: 0.92│  │ agreement: 0.85│  │ agreement: 1.0 │             │
│  └────────────────┘  └────────────────┘  └────────────────┘             │
│                                                                          │
└──────────────────────────────┬──────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         ALERT ENGINE                                     │
│              Rules reference channels instead of sensors                 │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Fused Channels

### Channel: `respiration_rate`

**Purpose**: Unified breathing rate from all capable sensors

| Source | Field | Weight | Notes |
|--------|-------|--------|-------|
| radar | `value.respiration_rate` | 1.0 | Primary - chest movement |
| audio | `value.breathing_rate` | 0.8 | Secondary - breath sounds |
| capacitive | `value.respiration_rate` | 0.7 | From capacitance envelope |
| thermal | `value.respiration_rate` | 0.6 | Future - thermal plume |

**Strategy**: `weighted_average`

**Cross-validation**: If radar and audio agree within 2 BPM, confidence boosted by 0.1

---

### Channel: `heart_rate`

**Purpose**: Unified heart rate with graceful degradation

| Source | Field | Weight | Notes |
|--------|-------|--------|-------|
| capacitive | `value.heart_rate` | 1.0 | **Primary** - planned main source |
| radar | `value.heart_rate_estimate` | 0.3 | Rough estimate, backup |
| thermal | `value.heart_rate` | 0.5 | Future - FLIR-based |
| rppg | `value.heart_rate` | 0.6 | Future - camera-based |

**Strategy**: `weighted_average`

**Cross-validation**: Capacitive + radar agreement (within 10 BPM) boosts confidence

**Fallback**: If capacitive unavailable (movement/unoccupied), use radar estimate with low confidence flag

---

### Channel: `presence`

**Purpose**: Is the subject in the monitored area?

| Source | Field | Notes |
|--------|-------|-------|
| radar | `value.presence` | Distance-based detection |
| capacitive | `value.bed_occupied` | Capacitance change detection |
| thermal | `value.presence` | Heat signature detection (future) |

**Strategy**: `voting` (majority wins)

**Output**: Boolean + confidence (unanimous = 1.0, 2/3 = 0.7, 1/3 = 0.3)

---

### Channel: `movement`

**Purpose**: Is the subject moving significantly?

| Source | Field | Notes |
|--------|-------|-------|
| radar | `value.movement` | 0.0-1.0 intensity |
| capacitive | `value.movement_detected` | Boolean, converted to 0/1 |

**Strategy**: `max` (highest reading wins)

**Rationale**: Movement from any sensor is relevant; conservative approach

---

### Channel: `seizure`

**Purpose**: Seizure detection from any available indicator

| Source | Field | Detection Method |
|--------|-------|-----------------|
| audio | `value.seizure_detected` | Rhythmic sounds (1.5-8 Hz) |
| radar | `value.seizure_detected` | Rhythmic position changes (future) |
| capacitive | `value.seizure_detected` | Rhythmic capacitance pattern (future) |

**Strategy**: `any` (any positive triggers alert)

**Rationale**: Seizures are critical events; prefer false positives over missed events

**Confidence**: Increases with number of confirming sensors

---

### Channel: `apnea_risk`

**Purpose**: Computed score indicating apnea likelihood

**Inputs**:
- `respiration_rate` channel (fused)
- `audio.silence_duration` (direct)
- `capacitive.bed_occupied` (direct)

**Computation**:
```
IF bed_occupied AND silence_duration > 10s:
    apnea_risk = 0.5 + (silence_duration - 10) * 0.05

IF bed_occupied AND respiration_rate < 6:
    apnea_risk += (6 - respiration_rate) * 0.1

apnea_risk = clamp(0.0, 1.0)
```

**Strategy**: `computed` (custom logic, not simple fusion)

---

## Fusion Strategies

### `weighted_average`

Combines numeric values weighted by source reliability and current confidence.

**Formula**:
```
fused_value = sum(value[i] * weight[i] * confidence[i]) / sum(weight[i] * confidence[i])
fused_confidence = average(confidence[i]) * agreement_factor
```

**Use case**: Continuous physiological signals (respiration, heart rate)

**Example**:
```
radar.respiration = 14.0, weight=1.0, conf=0.9
audio.breathing = 13.5, weight=0.8, conf=0.7

fused = (14.0 * 1.0 * 0.9 + 13.5 * 0.8 * 0.7) / (1.0 * 0.9 + 0.8 * 0.7)
      = (12.6 + 7.56) / (0.9 + 0.56)
      = 20.16 / 1.46
      = 13.8 BPM
```

---

### `best_confidence`

Uses the reading from whichever source has highest confidence.

**Formula**:
```
fused_value = value[argmax(confidence)]
fused_confidence = max(confidence)
```

**Use case**: When one source is clearly better situationally

**Example**:
```
bcg.heart_rate = 72, conf=0.9
radar.heart_rate = 65, conf=0.3

fused = 72, conf = 0.9  (BCG wins)
```

---

### `voting`

For boolean signals, uses majority vote.

**Formula**:
```
votes_true = count(value == True)
votes_false = count(value == False)
fused_value = votes_true > votes_false

fused_confidence = |votes_true - votes_false| / total_votes
```

**Use case**: Binary signals (presence, occupancy)

**Example**:
```
radar.presence = True
bcg.occupied = True
thermal.presence = False  (malfunction?)

fused = True, conf = 0.67 (2/3 agree)
```

---

### `any`

Alert triggers if ANY source indicates positive.

**Formula**:
```
fused_value = any(values)
fused_confidence = max(confidence where value == True), or 0 if none
```

**Use case**: Critical alerts where missing event is worse than false positive

**Example** (seizure):
```
audio.seizure = False, conf=0.9
radar.seizure = True, conf=0.6

fused = True, conf = 0.6  (radar detection triggers alert)
```

---

### `all`

Only positive if ALL sources agree.

**Formula**:
```
fused_value = all(values)
fused_confidence = min(confidence) if all true, else 0
```

**Use case**: High-stakes decisions requiring confirmation

**Example**:
```
# "All clear" signal
radar.normal = True, conf=0.9
audio.normal = True, conf=0.8
capacitive.normal = True, conf=0.7

fused = True, conf = 0.7  (minimum confidence)
```

---

### `computed`

Custom logic for derived channels.

**Use case**: Complex relationships between multiple channels/signals

**Example**: `apnea_risk` combines silence duration + respiration rate + occupancy

---

## Cross-Validation

When multiple sensors report the same underlying signal, their agreement (or disagreement) provides valuable information.

### Agreement Detection

**Threshold**: Configurable per channel (e.g., 2 BPM for respiration)

```
agreement = 1.0 - (std_dev(values) / max_expected_deviation)
agreement = clamp(0.0, 1.0)
```

### Confidence Adjustments

| Scenario | Adjustment | Rationale |
|----------|------------|-----------|
| All sources agree | +0.1 confidence | High reliability |
| Partial agreement | No change | Normal operation |
| Significant disagreement | -0.2 confidence | Uncertainty flag |
| Single source only | -0.1 confidence | No validation possible |

### Disagreement Handling

When sensors disagree significantly:

1. **Flag uncertainty**: Set `degraded: true` on fused signal
2. **Use conservative value**: For safety-critical signals, use worst-case
3. **Alert on sustained disagreement**: May indicate sensor malfunction
4. **Log for debugging**: Record raw values for analysis

**Example**:
```
radar.respiration = 14
audio.breathing = 28  # Suspicious!

# Disagreement detected (>5 BPM threshold)
fused.respiration = 14  # Use radar (higher weight)
fused.confidence = 0.5  # Penalized
fused.degraded = True   # Flag issue
# Consider: Log warning, check audio calibration
```

---

## Configuration

### Fusion Rules in YAML

```yaml
fusion:
  # Global settings
  signal_max_age_seconds: 5.0     # Discard stale signals
  cross_validation_enabled: true
  agreement_bonus: 0.1            # Confidence boost when sensors agree
  disagreement_penalty: 0.2       # Confidence penalty when sensors disagree

  rules:
    # Respiration rate fusion
    - signal: respiration_rate
      sources:
        - detector: radar
          field: value.respiration_rate
          weight: 1.0
        - detector: audio
          field: value.breathing_rate
          weight: 0.8
        - detector: capacitive
          field: value.respiration_rate
          weight: 0.7
      strategy: weighted_average
      min_sources: 1              # Minimum sources for valid output
      agreement_threshold: 2.0    # BPM difference for "agreement"

    # Heart rate fusion
    - signal: heart_rate
      sources:
        - detector: capacitive
          field: value.heart_rate
          weight: 1.0
        - detector: radar
          field: value.heart_rate_estimate
          weight: 0.3
      strategy: weighted_average
      min_sources: 1
      agreement_threshold: 10.0   # BPM

    # Presence voting
    - signal: presence
      sources:
        - detector: radar
          field: value.presence
        - detector: capacitive
          field: value.bed_occupied
      strategy: voting
      min_sources: 1

    # Seizure detection (any trigger)
    - signal: seizure
      sources:
        - detector: audio
          field: value.seizure_detected
        # Future: radar, capacitive movement patterns
      strategy: any
```

### Alert Rules Using Channels

```yaml
rules:
  # Rule using fused channel (future syntax)
  - name: "Low respiration"
    conditions:
      - channel: respiration_rate    # References fused channel
        operator: "<"
        value: 6
        duration_seconds: 10
    severity: critical
    message: "Respiration rate critically low"

  # Rule still using direct detector (current syntax)
  - name: "Seizure detected"
    conditions:
      - detector: audio
        field: value.seizure_detected
        operator: "=="
        value: true
        duration_seconds: 5
    severity: critical
```

---

## Implementation Status

### Current State

| Component | Status | Notes |
|-----------|--------|-------|
| FusionConfig schema | Defined | In `config.py` |
| Fusion rules in YAML | Configured | In `default.yaml` |
| FusionEngine class | **Not implemented** | Placeholder |
| Channel-based rules | **Not implemented** | Rules use detector directly |
| Cross-validation logic | **Not implemented** | Config exists |

### Future Implementation

#### FusionEngine Class

```python
# nightwatch/core/fusion.py

@dataclass
class SignalValue:
    """A single signal reading from a detector."""
    value: float | bool
    confidence: float
    timestamp: float
    detector: str
    field: str

@dataclass
class FusedSignal:
    """Result of fusing multiple sources."""
    channel: str
    value: float | bool
    confidence: float
    timestamp: float
    sources: list[str]      # Which detectors contributed
    agreement: float        # How much sources agreed (0-1)
    degraded: bool          # True if fewer than ideal sources

class FusionEngine:
    """Combines signals from multiple detectors into fused channels."""

    def __init__(self, config: FusionConfig):
        self.config = config
        self._latest: dict[str, dict[str, SignalValue]] = {}
        self._channels: dict[str, FusedSignal] = {}

    def update(self, event: Event) -> None:
        """Process incoming detector event, update latest values."""
        detector = event.detector
        for field, value in event.value.items():
            self._latest[detector][field] = SignalValue(
                value=value,
                confidence=event.confidence,
                timestamp=event.timestamp,
                detector=detector,
                field=field
            )
        self._recalculate_channels()

    def get_channel(self, channel: str) -> FusedSignal | None:
        """Get current fused value for a channel."""
        return self._channels.get(channel)

    def _recalculate_channels(self) -> None:
        """Apply fusion rules to update all channels."""
        for rule in self.config.rules:
            sources = self._gather_sources(rule)
            if len(sources) >= rule.min_sources:
                self._channels[rule.signal] = self._apply_strategy(rule, sources)
```

#### Integration Point

```python
# In AlertEngine.process_event()

async def process_event(self, event: Event) -> None:
    # Update fusion engine
    self._fusion_engine.update(event)

    # Evaluate rules (future: support channel references)
    for rule in self._rules:
        if rule.uses_channel:
            fused = self._fusion_engine.get_channel(rule.channel)
            matched = self._evaluate_channel_rule(rule, fused)
        else:
            matched = self._evaluate_detector_rule(rule, event)
```

---

## Testing Considerations

### Unit Tests

1. **Weighted average calculation**: Verify formula with known inputs
2. **Strategy selection**: Each strategy produces expected output
3. **Confidence adjustments**: Agreement/disagreement properly applied
4. **Stale signal handling**: Old values excluded
5. **Edge cases**: Single source, all sources offline, extreme disagreement

### Integration Tests

1. **Multi-detector scenarios**: Events from multiple detectors properly fused
2. **Fallback behavior**: Graceful degradation when sensors drop
3. **Alert triggering**: Fused channels correctly trigger rules

### Simulation Tests

1. **Agreement scenarios**: All sensors report similar values
2. **Disagreement scenarios**: One sensor reports outlier
3. **Degraded scenarios**: Sensors going offline mid-session

---

## Revision History

| Date | Version | Changes |
|------|---------|---------|
| 2024-XX-XX | 1.0 | Initial documentation |
