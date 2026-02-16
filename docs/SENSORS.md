# Nightwatch Sensor Documentation

This document describes all sensors in the Nightwatch sleep monitoring system, the physiological signals they measure, and future sensor options being explored.

## Hardware Status

| Sensor | Hardware | Software | Status |
|--------|----------|----------|--------|
| **Radar** (LD2450) | Ordered, arriving soon | Detector implemented | Testing soon |
| **Audio** (Lavalier mic) | Ordered, arriving soon | Detector implemented | Testing soon |
| **Capacitive** (FDC1004) | Not yet ordered | Not yet implemented | **Planned for pulse** |
| **BCG** (Piezo) | Sourcing difficult | Detector implemented | On hold |
| **Thermal** (MLX90640) | Not yet ordered | Not yet implemented | Future option |

**Priority**: Capacitive sensing is the planned solution for reliable heart rate monitoring.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           SENSOR LAYER                                   │
├───────────────┬───────────────┬─────────────────┬───────────────────────┤
│    Radar      │    Audio      │   Capacitive    │       [Future]        │
│   (LD2450)    │  (Lavalier)   │   (FDC1004)     │    Thermal/rPPG       │
│               │               │                 │                       │
│  Respiration  │  Breathing    │  Heart Rate     │   Respiration backup  │
│  HR estimate  │  Seizure      │  Respiration    │   Fever detection     │
│  Presence     │  Silence      │  Presence       │                       │
└───────┬───────┴───────┬───────┴────────┬────────┴───────────┬───────────┘
        │               │                │                    │
        ▼               ▼                ▼                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         FUSION LAYER                                     │
│           (Combines signals into unified channels)                       │
│                     See: docs/FUSION.md                                  │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         ALERT ENGINE                                     │
│              (Evaluates rules, triggers notifications)                   │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Planned Sensors

### 1. Radar Detector (HLK-LD2450)

**Type**: Non-contact mmWave radar
**Hardware**: HLK-LD2450 24GHz FMCW radar module (~$15-25)
**Interface**: UART at 256,000 baud (default: `/dev/ttyAMA0`)
**Detection Range**: 0.3m to 3.0m (configurable)

#### Signals Measured

| Signal | Field | Units | Accuracy | Notes |
|--------|-------|-------|----------|-------|
| Respiration Rate | `value.respiration_rate` | BPM | Primary | Chest micro-movement detection |
| Heart Rate | `value.heart_rate_estimate` | BPM | Rough | Less reliable than BCG |
| Movement | `value.movement` | 0.0-1.0 | Good | Macro vs micro classification |
| Presence | `value.presence` | boolean | High | Person in detection zone |
| Target Distance | `value.target_distance` | meters | High | Distance to subject |

#### Processing Pipeline

1. **RespirationExtractor**: Bandpass filter 0.1-0.5 Hz (6-30 BPM range), analyzes Y-axis chest displacement
2. **HeartRateEstimator**: Bandpass filter 0.8-2.0 Hz (48-120 BPM), FFT-based peak detection
3. **MovementDetector**: Variance-based classification of macro (>100mm) vs micro movements

#### Calibration

- **Duration**: ~10 seconds
- **Requirements**: Subject must be in detection zone
- **Outputs**: Baseline Y-position, recommended sensitivity
- **Minimum samples**: 50

#### Limitations

- Heart rate is estimate only (~70-80% correlation potential)
- Requires relatively still subject for accurate respiration
- No seizure detection capability
- Line-of-sight required

---

### 2. Audio Detector (USB Microphone)

**Type**: Non-contact acoustic sensing
**Hardware**: Any USB microphone (~$10-50)
**Interface**: Cross-platform via `sounddevice` library
**Sample Rate**: 16,000 Hz (configurable 8,000-48,000 Hz)

#### Signals Measured

| Signal | Field | Units | Accuracy | Notes |
|--------|-------|-------|----------|-------|
| Breathing Detected | `value.breathing_detected` | boolean | Good | Presence of breath sounds |
| Breathing Rate | `value.breathing_rate` | BPM | Primary | From sound rhythm |
| Breathing Amplitude | `value.breathing_amplitude` | 0.0-1.0 | Good | Relative breath intensity |
| Silence Duration | `value.silence_duration` | seconds | High | Time since last sound (apnea indicator) |
| Vocalization | `value.vocalization_detected` | boolean | Good | Cries, gasps, speech |
| Seizure Detected | `value.seizure_detected` | boolean | Medium | Rhythmic sound patterns |
| Seizure Confidence | `value.seizure_confidence` | 0.0-1.0 | Medium | Detection certainty |

#### Processing Pipeline

1. **BreathingDetector**: Bandpass 200-800 Hz, envelope extraction, adaptive threshold
2. **SilenceDetector**: RMS energy analysis, adaptive noise floor (5th percentile)
3. **VocalizationDetector**: Bandpass 200-3,000 Hz, sudden energy spike detection (>3x baseline)
4. **SeizureSoundDetector**: Envelope analysis, FFT rhythm detection (1.5-8 Hz patterns)

#### Seizure Detection Details

Distinguishes seizure sounds from snoring by checking:
- Energy concentration >15% in seizure band (1.5-8 Hz)
- Peak prominence >1.5x average magnitude
- Breathing energy NOT dominant (seizure-to-breathing ratio >2.0)
- Minimum duration: 5 seconds

#### Calibration

- **Duration**: ~5 seconds
- **Purpose**: Measure ambient noise floor
- **Outputs**: Baseline noise level, recommended silence/breathing thresholds

#### Limitations

- Requires audible breathing (fails if breathing is silent)
- Seizure detection requires sustained rhythmic sounds (may miss short seizures)
- Environmental noise can interfere
- Cannot detect heart rate

---

### 3. Capacitive Detector (FDC1004) - PRIMARY PULSE SOLUTION

**Type**: Under-mattress electric field sensing
**Hardware**: FDC1004 capacitance-to-digital converter + electrode
**Interface**: I2C (address 0x50)
**Sample Rate**: Up to 400 Hz
**Status**: Planned - prototype build instructions below

#### Why Capacitive?

Capacitive sensing is the planned primary solution for heart rate because:
- **Available**: FDC1004 breakouts readily available (~$12)
- **Cheap electrodes**: Aluminum foil or copper tape works
- **Comparable accuracy**: Similar to piezo BCG for heart rate
- **Digital output**: No external ADC or analog conditioning needed

#### How It Works

The sensor creates an electric field that projects through the mattress. Body movements (including heartbeat micro-movements) change the capacitance, which the FDC1004 measures.

```
        ┌─────────────────────────────┐
        │         MATTRESS            │
        │                             │
        │    Body changes the         │
        │    electric field           │
        │         ↕                   │
        └─────────────────────────────┘
        ┌─────────────────────────────┐
        │   Aluminum Foil Electrode   │  ← Simple, cheap
        │   (~12" x 12" or larger)    │
        └──────────────┬──────────────┘
                       │ wire
                ┌──────┴──────┐
                │   FDC1004   │  ← I2C to Pi
                │   Breakout  │
                └─────────────┘
```

#### Signals Measured

| Signal | Field | Units | Accuracy | Notes |
|--------|-------|-------|----------|-------|
| Heart Rate | `value.heart_rate` | BPM | Primary | Peak detection from micro-movements |
| Heart Rate Variability | `value.heart_rate_variability` | ms (RMSSD) | Good | From inter-beat intervals |
| Respiration Rate | `value.respiration_rate` | BPM | Good | From capacitance envelope |
| Bed Occupied | `value.bed_occupied` | boolean | High | Large capacitance change |
| Signal Quality | `value.signal_quality` | 0.0-1.0 | N/A | Confidence indicator |

#### Hardware Required

| Component | Description | Price | Source |
|-----------|-------------|-------|--------|
| FDC1004 Breakout | Capacitance-to-digital converter | ~$12-15 | Adafruit, Amazon |
| Electrode | Aluminum foil, copper tape, or PCB | ~$0-10 | Kitchen, hardware store |
| Wire | Connect electrode to FDC1004 | ~$0 | Any hookup wire |
| (Optional) Shielding | Reduces EMI noise | ~$5 | Aluminum foil |

**Total cost**: ~$15-25

#### Prototype Build: Aluminum Foil Electrode

**Materials**:
- Aluminum foil (standard kitchen foil)
- Cardboard or foam board (backing)
- Tape
- Wire with alligator clip or solder

**Build steps**:

1. **Create electrode backing**
   ```
   Cut cardboard to ~12" x 12" (or larger for more coverage)
   ```

2. **Apply aluminum foil**
   ```
   Smooth foil onto cardboard, fold edges to back
   Ensure no wrinkles in sensing area

   ┌────────────────────────┐
   │ ░░░░░░░░░░░░░░░░░░░░░░ │
   │ ░░░ ALUMINUM FOIL ░░░░ │
   │ ░░░░░░░░░░░░░░░░░░░░░░ │
   │ ░░░░░░░░░░░░░░░░░░░░░░ │
   └────────────────────────┘
   ```

3. **Attach wire**
   ```
   Tape or solder wire to foil
   Route wire to edge for connection to FDC1004
   ```

4. **Optional: Add shielding**
   ```
   Second layer of foil on BACK of cardboard
   Connected to GND (reduces noise from below)

   Cross-section:

   [Mattress above]
        ↓
   ┌─────────────┐ ← Sensing foil (to FDC1004 CH1)
   │  Cardboard  │
   └─────────────┘
   ┌─────────────┐ ← Shield foil (to GND)
   [Bed frame below]
   ```

5. **Placement**
   ```
   Place under mattress, roughly chest area
   Electrode faces UP toward mattress
   Wire routes to Pi
   ```

#### FDC1004 Pinout (10 pins)

From the TI datasheet (SNOSCY5C):

| Pin | Name | Type | Description |
|-----|------|------|-------------|
| 1 | SHLD1 | Analog | Active shield output #1 |
| 2 | CIN1 | Analog | Capacitance input 1 |
| 3 | CIN2 | Analog | Capacitance input 2 |
| 4 | CIN3 | Analog | Capacitance input 3 |
| 5 | CIN4 | Analog | Capacitance input 4 |
| 6 | SHLD2 | Analog | Active shield output #2 |
| 7 | GND | Ground | Ground |
| 8 | VDD | Power | 3.3V supply |
| 9 | SCL | Input | I2C clock |
| 10 | SDA | I/O | I2C data |
| - | DAP | Ground | Die attach pad (connect to GND) |

**Note**: Two shield outputs (SHLD1, SHLD2) allow independent shielding for different electrode zones.

#### FDC1004 Wiring

```
FDC1004                   Raspberry Pi         Electrodes
───────                   ────────────         ──────────
VDD (pin 8)  ──────────── 3.3V (pin 1)
GND (pin 7)  ──────────── GND (pin 6)
SDA (pin 10) ──────────── GPIO 2 (pin 3)
SCL (pin 9)  ──────────── GPIO 3 (pin 5)

CIN1 (pin 2) ─────────────────────────────────  Sensing electrode
SHLD1 (pin 1) ────────────────────────────────  Shield plane (behind sensing)

CIN2-4       ──────────── leave unconnected (for single-electrode prototype)
SHLD2        ──────────── leave unconnected (or tie to SHLD1)
DAP          ──────────── GND (if accessible on breakout)
```

#### Electrode Design Options

**Option A: Aluminum Foil Plate (Recommended for prototype)**
- Maximum surface area = strongest signal
- Easy to make, zero cost
- Use alligator clip or tape wire connection

**Option B: Copper Tape**
- Can be soldered
- Good surface area
- Available at hardware stores

**Option C: Wire Coil/Serpentine Pattern**
- Easier to solder than foil
- Must be densely wound to approximate plate area
- Keep wire spacing <1-2cm for field to "fill in"

```
Wire serpentine pattern (approximates a plate):

    ╭──────────────────────────────╮
    │  ╭────────────────────────╮  │
    ╰──╯  ╭──────────────────╮  ╰──╯
    ╭─────╯  ╭────────────╮  ╰─────╮
    │  ╭─────╯            ╰─────╮  │
    ╰──╯                        ╰──╯
```

**Trade-offs**:

| Electrode Type | Signal Strength | Ease of Build | Solderable |
|----------------|-----------------|---------------|------------|
| Foil plate | Best | Easy | No (clip/tape) |
| Copper tape | Good | Easy | Yes |
| Wire coil | Lower | Medium | Yes |

**Recommendation**: Start with foil to validate signal, then switch to copper tape or wire if you need something more permanent.

#### Software Integration

```python
# Planned: nightwatch/detectors/capacitive/detector.py

class CapacitiveDetector(BaseDetector):
    """Capacitive sensing for heart rate and respiration."""

    def __init__(self, config: CapacitiveConfig):
        self.i2c_address = 0x50  # FDC1004 default
        self.sample_rate = 100   # Hz

    async def _read_impl(self) -> Event:
        # Read capacitance from FDC1004
        # Apply bandpass filter (0.5-25 Hz for HR)
        # Detect peaks
        # Calculate heart rate and respiration
        pass
```

#### Processing Pipeline (Planned)

Same approach as BCG since signal characteristics are similar:

1. **Bandpass filter**: 0.5-25 Hz isolates cardiac signal
2. **Peak detection**: Find heartbeat peaks (adaptive threshold)
3. **HR calculation**: Median of inter-beat intervals
4. **Respiration**: Low-frequency envelope (0.1-0.5 Hz)
5. **Occupancy**: Large capacitance change indicates presence

#### Expected Performance

| Metric | Expected | Notes |
|--------|----------|-------|
| HR accuracy | ±2-5 BPM | Comparable to piezo BCG |
| HR range | 30-150 BPM | Standard range |
| Respiration accuracy | ±1-2 BPM | Good |
| Latency | 3-5 seconds | Time to stable reading |
| Update rate | 1-10 Hz | Configurable |

#### Advantages Over Piezo BCG

| Factor | Piezo BCG | Capacitive |
|--------|-----------|------------|
| Sensor sourcing | Difficult | Easy (any conductive material) |
| Cost | $20-50+ | $15-25 |
| Interface | Analog (needs ADC) | Digital I2C |
| Noise immunity | Good | Good (with shielding) |
| Mattress penetration | Pressure-dependent | Field penetrates well |
| Multi-zone | Hard | Easy (multiple electrodes) |

---

### 4. BCG Detector (Ballistocardiography) - ON HOLD

> **Status**: Software implemented but hardware sourcing has been difficult.
> Capacitive sensing (above) is the planned alternative.

**Type**: Under-mattress pressure sensing
**Hardware**: Piezoelectric film or FSR under mattress (~$20-50)
**ADC**: MCP3008 (10-bit SPI) or ADS1115
**Interface**: SPI bus 0, device 0 (CE0 pin)
**Sample Rate**: 100 Hz (configurable 50-500 Hz)

#### Signals Measured

| Signal | Field | Units | Accuracy | Notes |
|--------|-------|-------|----------|-------|
| Heart Rate | `value.heart_rate` | BPM | Primary | J-peak detection, most reliable |
| Heart Rate Variability | `value.heart_rate_variability` | ms (RMSSD) | Good | Requires 20+ beats |
| Respiration Rate | `value.respiration_rate` | BPM | Secondary | From amplitude envelope |
| Bed Occupied | `value.bed_occupied` | boolean | High | RMS energy threshold |
| Signal Quality | `value.signal_quality` | 0.0-1.0 | N/A | Confidence indicator |
| Movement Detected | `value.movement_detected` | boolean | Good | Large body movements |

#### Processing Pipeline

1. **JPeakDetector**: Butterworth bandpass 0.5-25 Hz, adaptive threshold (75th percentile)
2. **HeartRateCalculator**: Median of inter-beat intervals, valid range 30-150 BPM
3. **RespirationExtractor**: Low-frequency envelope 0.1-0.5 Hz, autocorrelation-based
4. **BedOccupancyDetector**: 5-second RMS energy window, threshold 0.01
5. **MovementDetector**: Peak-to-peak amplitude >5x baseline

#### Signal Quality Scoring

| Condition | Quality Score |
|-----------|---------------|
| Bed unoccupied | 0.0 |
| Occupied + movement | 0.2 |
| Occupied + no HR detected | 0.4 |
| HR outside 40-120 BPM | 0.5-0.7 |
| HR 40-120 BPM, stable | 0.9 |

#### Calibration

- **Duration**: ~12 seconds (5s empty + 2s transition + 5s occupied)
- **Outputs**: Empty noise level, occupied signal level, occupancy threshold

#### Limitations

- Heart rate only available when subject is still (movement disables detection)
- Requires physical contact with bed (under-mattress placement)
- Respiration is secondary signal, less accurate than radar/audio
- No seizure detection capability

---

## Signal Coverage Matrix

| Signal | Radar | Audio | Capacitive | Coverage |
|--------|:-----:|:-----:|:----------:|----------|
| **Respiration Rate** | Primary | Primary | Good | Well covered |
| **Heart Rate** | Rough estimate | - | **Primary** | Capacitive is main source |
| **HRV** | - | - | Yes | Single source |
| **SpO2** | - | - | - | **GAP** |
| **Presence/Occupancy** | Yes | - | Yes | Covered |
| **Movement** | Macro/micro | - | Yes | Covered |
| **Apnea Indicator** | RR drop | Silence duration | RR drop | Partial |
| **Seizure** | - | Sound rhythm | - | Single source (future: movement) |
| **Vocalizations** | - | Yes | - | Single source |
| **Temperature** | - | - | - | **GAP** |

### Key Gaps

1. **SpO2 (Oxygen Saturation)**: Critical for apnea/hypoxia monitoring. Traditionally requires contact sensor. Non-contact options are research-grade only.
2. **Temperature**: No fever detection capability. Thermal camera (MLX90640) is future option.
3. **Movement-based seizure**: Audio detects sound patterns only. Radar/capacitive could add movement-based detection in future.

---

## Future Sensor Options

### Thermal Camera

**Purpose**: Non-contact respiration backup, presence detection, fever monitoring, potential pulse detection

#### Hardware Options

| Model | Resolution | FPS | Price | Interface | Notes |
|-------|------------|-----|-------|-----------|-------|
| MLX90640 | 32x24 | 16 | $50-80 | I2C | Common choice, good value |
| AMG8833 | 8x8 | 10 | $40 | I2C | Lower resolution, cheaper |
| FLIR Lepton 3.5 | 160x120 | 9 | $200+ | SPI | High resolution, best for pulse |

#### Detectable Signals

| Signal | Method | Accuracy Potential |
|--------|--------|-------------------|
| Respiration | Thermal plume oscillation from nose/mouth | High |
| Presence | Body heat signature | High |
| Fever | Elevated body temperature | Medium (relative, not absolute) |
| Pulse | Blood flow causes ~0.1C skin oscillations | Medium (FLIR only, research-grade) |

#### Pros/Cons

**Pros**:
- Works in complete darkness
- Non-contact, no line-of-sight to specific body part needed for presence
- Backup respiration signal independent of sound or chest movement
- Could detect fever/temperature anomalies

**Cons**:
- High-res models expensive ($200+)
- Pulse detection requires high resolution and advanced processing
- Need line-of-sight to face for best respiration/pulse
- Environmental temperature affects readings

---

### IR Camera / Remote PPG (rPPG)

**Purpose**: Non-contact heart rate and potentially SpO2 from skin color changes

#### How It Works

Blood flow causes subtle color changes in skin (visible and near-IR spectrum). These changes can be detected by camera and processed to extract pulse signal.

#### Hardware Options

| Type | Price | Notes |
|------|-------|-------|
| Pi NoIR Camera | $25 | No IR filter, needs IR illumination for darkness |
| USB IR Camera | $30-100 | Various options available |
| Webcam + IR LEDs | $20 | DIY: remove IR filter, add IR illumination |

#### Detectable Signals

| Signal | Accuracy | Conditions |
|--------|----------|------------|
| Heart Rate | 90%+ in ideal conditions | Requires visible skin, stable lighting |
| Respiration | Good | Chest movement or nostril airflow |
| SpO2 (research) | Experimental | Dual-wavelength IR, research-grade |

#### Pros/Cons

**Pros**:
- Potentially non-contact HR + SpO2
- Cheaper than thermal for pulse detection
- Well-researched algorithms available

**Cons**:
- Requires visible skin (face)
- Very sensitive to lighting changes and motion
- Compute intensive (real-time video processing)
- Degrades significantly with movement

---

### Capacitive Sensing (Under-Mattress)

> **Note**: Capacitive sensing has been selected as the primary pulse solution.
> See the detailed **Capacitive Detector (FDC1004)** section above for full documentation including:
> - FDC1004 pinout and wiring
> - Electrode design options (foil, copper tape, wire coil)
> - Prototype build instructions
> - Expected performance

---

### Enhanced Radar HR Algorithm

**Purpose**: Improve heart rate accuracy from existing radar hardware

#### Current State

Radar provides `heart_rate_estimate` marked as "less reliable than BCG". Uses basic FFT on micro-Doppler signal.

#### Potential Improvements

1. **Better micro-Doppler processing**: Advanced filtering, multi-target handling
2. **Longer observation windows**: Trade latency for accuracy
3. **ML-based extraction**: Train model on BCG ground truth
4. **Hardware upgrade**: LD2461 or TI IWR1443 for better sensitivity

#### Expected Outcome

- Current: ~60-70% correlation with ground truth
- Improved: ~75-85% correlation possible
- Limitation: May never match BCG accuracy for technical reasons

---

## Non-Contact Pulse Detection Research

### Radar-Based Approaches

**Principle**: Chest wall micro-movements from heartbeat detected via Doppler shift

**Techniques**:
1. **Harmonic analysis**: Heart rate appears at different harmonics than respiration
2. **Adaptive filtering**: Separate cardiac from respiratory components
3. **Phase-based detection**: More sensitive than amplitude-based

**Research accuracy**: 70-85% correlation with ECG in controlled settings

**References**:
- "Vital Signs Monitoring Using FMCW Radar" (IEEE, 2019)
- "Non-contact Heart Rate Detection Using 24GHz Radar" (Sensors, 2020)

### Thermal-Based Approaches

**Principle**: Blood flow causes periodic temperature changes (~0.1C) on skin surface

**Requirements**:
- High resolution thermal camera (FLIR Lepton or better)
- Visible face/neck region
- Advanced signal processing

**Research accuracy**: 80-90% correlation with ECG using FLIR Lepton + advanced processing

**References**:
- "Thermal Imaging for Heart Rate Estimation" (Biomedical Engineering, 2018)

### Remote PPG (rPPG) Approaches

**Principle**: Blood volume changes cause subtle skin color variations

**Techniques**:
1. **Green channel analysis**: Hemoglobin absorption peaks at green wavelengths
2. **Chrominance-based**: CHROM algorithm uses color channel differences
3. **Plane-Orthogonal-to-Skin (POS)**: Robust to motion artifacts

**Research accuracy**: 90%+ in controlled conditions, 70-80% with motion

**Open-source implementations**:
- `pyrPPG` - Python library for rPPG
- `HeartRateMeasure` - OpenCV-based implementation

---

## Non-Contact SpO2 Research

### The Challenge

Pulse oximetry traditionally requires contact sensor with dual-wavelength LEDs (red + infrared) to measure oxygenated vs deoxygenated hemoglobin.

### Research Approaches

#### Dual-Wavelength rPPG

**Principle**: Use camera with dual-wavelength illumination (red + NIR LEDs) to estimate SpO2 from skin color ratios.

**Hardware**:
- Camera + red LED + NIR LED
- Or: dual-band filter + broadband illumination

**Accuracy**: Research shows 3-5% error vs contact pulse ox in ideal conditions. Degrades significantly with:
- Motion
- Ambient light changes
- Skin tone variations
- Distance

#### Limitations

1. Not FDA-approved for medical use
2. High sensitivity to motion artifacts
3. Requires controlled lighting
4. Accuracy varies significantly by skin tone
5. Not suitable for continuous monitoring without careful setup

#### Current Assessment

Non-contact SpO2 is **research-grade only**. For reliable SpO2 monitoring, contact sensors remain necessary. This is a known gap in the non-contact monitoring space.

**References**:
- "Smartphone-Based SpO2 Estimation" (Nature Scientific Reports, 2021)
- "Camera-Based Vital Signs: Current Challenges" (IEEE Reviews, 2022)

---

## Movement-Based Seizure Detection

### Current State

Audio detector identifies seizure sounds (rhythmic patterns at 1.5-8 Hz). This misses seizures without audible component.

### Proposed Enhancements

#### Radar-Based Seizure Detection

**Method**: Analyze position variance for rhythmic, high-amplitude movements

**Algorithm concept**:
1. Track position over sliding window (5-10 seconds)
2. Calculate movement amplitude and frequency
3. Detect rhythmic pattern in 1-8 Hz range
4. Distinguish from normal repositioning (non-rhythmic)

**Signals to analyze**:
- `value.movement` amplitude over time
- Position variance frequency spectrum
- Movement duration and pattern

#### Capacitive-Based Seizure Detection

**Method**: Analyze capacitance patterns for rhythmic body movements

**Algorithm concept**:
1. Monitor capacitance signal for high-amplitude oscillations
2. Detect sustained rhythmic patterns (>5 seconds)
3. Distinguish from normal movement (non-periodic)

**Advantages**:
- Planned hardware (FDC1004) already supports this
- Bed-wide detection (whole body)
- Works in darkness

### Multi-Sensor Seizure Fusion

**Ideal approach**: Combine audio + radar + capacitive for robust seizure detection

| Indicator | Audio | Radar | Capacitive |
|-----------|:-----:|:-----:|:----------:|
| Rhythmic sounds | Yes | - | - |
| Rhythmic position change | - | Yes | - |
| Rhythmic capacitance pattern | - | - | Yes |
| Sustained duration | Yes | Yes | Yes |

**Fusion rule**: Any 2 of 3 indicators = high confidence seizure alert

---

## Adding New Sensors

### Detector Interface Requirements

All detectors must inherit from `BaseDetector` and implement:

```python
class NewDetector(BaseDetector):
    async def _connect_impl(self) -> None:
        """Connect to hardware."""

    async def _disconnect_impl(self) -> None:
        """Disconnect from hardware."""

    async def _read_impl(self) -> Event:
        """Read sensor and return Event."""

    async def _calibrate_impl(self) -> dict:
        """Run calibration procedure."""
```

### Event Format

All detectors emit standardized `Event` objects:

```python
Event(
    detector="new_sensor",           # Unique detector name
    timestamp=time.time(),           # Unix timestamp
    confidence=0.85,                 # 0.0-1.0 signal quality
    state=EventState.NORMAL,         # NORMAL | WARNING | ALERT | UNCERTAIN
    value={                          # Detector-specific data
        "signal_1": 14.5,
        "signal_2": True,
        # ...
    },
    sequence=self._sequence,         # Monotonic counter
    session_id=self._session_id      # Session identifier
)
```

### Configuration Schema

Add configuration to `nightwatch/core/config.py`:

```python
class NewSensorConfig(BaseModel):
    enabled: bool = False
    # Hardware settings
    device_path: str = "/dev/..."
    sample_rate: int = 100
    # Processing parameters
    threshold: float = 0.5
    # ...
```

### Fusion Integration

Add fusion rules to `config/default.yaml`:

```yaml
fusion:
  rules:
    - signal: respiration_rate
      sources:
        # ... existing sources ...
        - detector: new_sensor
          field: value.respiration_rate
          weight: 0.7
```

See `docs/FUSION.md` for complete fusion layer documentation.

---

## Hardware Reference

### Current Hardware Stack

| Component | Model | Interface | Price |
|-----------|-------|-----------|-------|
| Single-board computer | Raspberry Pi 4/5 | - | $35-80 |
| Radar module | HLK-LD2450 | UART | $15-25 |
| Microphone | Lavalier / USB mic | USB | $10-50 |
| Capacitive sensor | FDC1004 | I2C | $12-15 |
| Electrode | Aluminum foil / copper tape | Wire | $0-10 |

### Expansion Options

| Component | Purpose | Interface | Price |
|-----------|---------|-----------|-------|
| MLX90640 | Thermal imaging | I2C | $50-80 |
| Pi NoIR Camera | rPPG | CSI | $25 |
| FLIR Lepton | High-res thermal | SPI | $200+ |
| BME280 | Environment sensing | I2C | $5 |

---

## DIY Research Resources

### Search Terms for YouTube/Google

**Capacitive vital signs sensing:**
- `FDC1004 heart rate sensor DIY`
- `FDC1004 heartbeat detection`
- `capacitive BCG sensor Arduino`
- `capacitive bed sensor vital signs raspberry pi`
- `non-contact heart rate bed sensor`

**Ballistocardiography (related technique):**
- `ballistocardiography DIY`
- `BCG sensor under mattress Arduino`
- `sleep monitor heart rate DIY`

**Academic/deeper research:**
- `capacitive coupled ECG` (cECG)
- `cECG bed sensor`
- `unobtrusive heart rate monitoring`

**Radar vital signs:**
- `FMCW radar vital signs`
- `LD2450 respiration detection`
- `mmWave radar heart rate`

### Relevant Projects & Papers

- TI FDC1004 datasheet (SNOSCY5C) - Official reference
- "Unobtrusive Heart Rate Monitoring Using Capacitive Sensors" - IEEE papers
- Emfit QS teardowns - Commercial under-mattress sensor analysis
- OpenBCI community - DIY biosensing projects

---

## Revision History

| Date | Version | Changes |
|------|---------|---------|
| 2024-XX-XX | 1.0 | Initial documentation |
