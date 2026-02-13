# Nightwatch Sensor Specifications

Detailed technical specifications for each sensor module.

---

## Sensor 1: mmWave Radar (HLK-LD2450)

### Overview

The HLK-LD2450 is a 24GHz FMCW (Frequency Modulated Continuous Wave) radar module that detects human presence, position, and micro-movements like breathing.

### Why This Sensor

| Feature | Benefit for Miles |
|---------|-------------------|
| Works through blankets | No line-of-sight needed |
| Complete darkness operation | No IR illumination required |
| Detects micro-movements | Can sense chest rise/fall |
| Position tracking | Knows where he is in bed |
| No contact required | Nothing attached to him |

### Technical Specifications

```
Model:              HLK-LD2450
Frequency:          24GHz ISM band
Detection range:    0.3m - 6m
Field of view:      ±60° horizontal, ±60° vertical
Position accuracy:  ±15mm
Update rate:        10-20 Hz
Interface:          UART (256000 baud)
Voltage:            5V (200mA typical)
Size:               35mm x 32mm x 7mm
```

### Wiring to Raspberry Pi

```
LD2450          Raspberry Pi 5
──────          ──────────────
VCC    ───────► 5V (Pin 2 or 4)
GND    ───────► GND (Pin 6)
TX     ───────► GPIO 15 / RXD (Pin 10)
RX     ───────► GPIO 14 / TXD (Pin 8)
```

**Note:** The Pi's UART must be enabled. Add to `/boot/config.txt`:
```
enable_uart=1
dtoverlay=disable-bt  # Free up primary UART
```

### Mounting

```
SIDE VIEW OF ROOM

        Radar
          │
          │  1-2m distance
          │  aimed at torso
          ▼
    ┌─────────────────┐
    │      Miles      │
    │    (in bed)     │
    └─────────────────┘
    ═══════════════════
          Bed

MOUNTING OPTIONS:
1. Wall mount (1-1.5m high, angled down)
2. Ceiling mount (directly above torso area)
3. Bedside table (angled toward chest)

OPTIMAL: Wall mount at headboard height, 1m from bed
```

### Data Output

The radar outputs target data at ~10 Hz:

```python
{
    "targets": [
        {
            "x": 150,      # mm, horizontal position
            "y": 1200,     # mm, distance from sensor
            "speed": 0,    # cm/s, movement speed
        }
    ]
}
```

### Signal Processing for Respiration

1. **Bandpass filter** Y-position data (0.1-0.5 Hz = 6-30 breaths/min)
2. **Peak detection** on filtered signal to find breath cycles
3. **Rate calculation** from inter-peak intervals
4. **Amplitude** from peak-to-trough distance (~5-15mm for breathing)

### Expected Performance

| Metric | Expected | Notes |
|--------|----------|-------|
| Respiration rate accuracy | ±2 BPM | When stable and still |
| Heart rate accuracy | ±10 BPM | Less reliable, use as backup |
| Movement detection | 100ms latency | Very responsive |
| Presence detection | 99%+ | Rarely misses |

### Limitations

- Multiple targets can confuse (parents checking on child)
- Large movement (turning over) temporarily disrupts respiration tracking
- Heart rate is estimated, not precise like BCG

---

## Sensor 2: Audio (USB Microphone)

### Overview

A USB microphone captures breathing sounds, enabling detection of:
- Breathing rhythm and amplitude
- Silence (potential apnea)
- Vocalizations (sounds during seizure)
- Gasping or irregular breathing

### Why This Sensor

| Feature | Benefit for Miles |
|---------|-------------------|
| Redundant respiration signal | Confirms radar readings |
| Detects sounds | Catches vocalizations radar misses |
| Simple hardware | Just plug into USB |
| Position agnostic | Works regardless of body position |

### Technical Specifications (Recommended Mic)

```
Type:               Omnidirectional condenser
Connection:         USB 2.0
Sample rate:        16000 Hz (minimum)
Bit depth:          16-bit
Frequency response: 20 Hz - 20 kHz
SNR:                >60 dB
Features:           AGC (Automatic Gain Control)
```

### Mounting

```
TOP VIEW OF BED

    ┌─────────────────────┐
    │                     │
    │       Miles         │
    │                     │
    │         ●           │◄── Mic position
    │       (head)        │    0.5-1m from head
    │                     │
    └─────────────────────┘

MOUNTING OPTIONS:
1. Bedside table (simplest)
2. Headboard mount
3. Ceiling mount (requires longer cable)

DISTANCE: 0.5m - 1.5m from head
DIRECTION: Aimed toward head/chest area
```

### Signal Processing Pipeline

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ Raw Audio   │───►│ Bandpass    │───►│  Envelope   │
│ 16kHz       │    │ 200-800 Hz  │    │  Detection  │
└─────────────┘    └─────────────┘    └─────────────┘
                                             │
                         ┌───────────────────┘
                         ▼
               ┌─────────────────┐    ┌─────────────┐
               │ Breathing Rate  │    │  Silence    │
               │   Estimation    │    │  Detection  │
               └─────────────────┘    └─────────────┘
```

### Breathing Sound Characteristics

| Sound | Frequency Range | Pattern |
|-------|-----------------|---------|
| Normal breathing | 200-600 Hz | Rhythmic, 12-20/min |
| Deep breathing | 150-500 Hz | Slower, louder |
| Shallow breathing | 300-800 Hz | Faster, quieter |
| Snoring | 100-300 Hz | Irregular |
| Vocalization | 200-3000 Hz | Non-rhythmic |

### Detection Logic

```python
# Breathing detection
breathing_detected = (
    energy_in_band(200, 800) > threshold
    and is_rhythmic(envelope)
)

# Silence detection
silence_detected = (
    overall_energy < silence_threshold
    for duration > 10 seconds
)

# Vocalization detection
vocalization = (
    energy_in_band(200, 3000) > threshold
    and not is_rhythmic(envelope)
)
```

### Expected Performance

| Metric | Expected | Notes |
|--------|----------|-------|
| Breathing rate accuracy | ±3 BPM | In quiet room |
| Silence detection | 2-3s latency | After breathing stops |
| Vocalization detection | <1s latency | Very responsive |
| False positive rate | <5% | With proper calibration |

### Limitations

- Background noise affects accuracy (fan, AC, traffic)
- Mouth breathing vs nose breathing sound different
- Blanket over face muffles sound
- Works best in quiet room

### Noise Handling

- **Adaptive threshold**: Adjusts to ambient noise level
- **Spectral subtraction**: Remove constant background noise
- **AGC on mic**: Hardware-level gain adjustment

---

## Sensor 3: BCG Bed Sensor (Piezoelectric)

### Overview

BCG (Ballistocardiography) detects the mechanical recoil of the body caused by heartbeats. A piezoelectric sensor under the mattress picks up these micro-vibrations.

### Why This Sensor

| Feature | Benefit for Miles |
|---------|-------------------|
| Most accurate heart rate | ±3-5 BPM, better than radar |
| Heart rate variability | Can detect irregular rhythms |
| Completely hidden | Under mattress, unfelt |
| Also detects breathing | Secondary respiration signal |
| Bed occupancy | Knows when he's in/out of bed |

### Technical Specifications

**Piezo Film Sensor:**
```
Type:               PVDF piezoelectric film
Size:               Large format (200mm x 50mm minimum)
Sensitivity:        ~100 mV/N typical
Frequency response: 0.1 Hz - 100 Hz
Output:             Analog voltage (needs amplification)
```

**Signal Conditioning:**
```
Amplifier:          Instrumentation amp or charge amp
Gain:               100-1000x (adjustable)
Filter:             0.5 Hz - 25 Hz bandpass
ADC:                12-bit minimum (MCP3008)
Sample rate:        100 Hz minimum
```

### System Diagram

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌──────────┐
│   Piezo     │───►│  Amplifier  │───►│   Filter    │───►│   ADC    │
│   Sensor    │    │   (100x)    │    │ 0.5-25 Hz   │    │ MCP3008  │
└─────────────┘    └─────────────┘    └─────────────┘    └────┬─────┘
                                                              │ SPI
                                                              ▼
                                                        ┌──────────┐
                                                        │ Pi GPIO  │
                                                        └──────────┘
```

### Placement Under Mattress

```
SIDE VIEW

    ┌─────────────────────────────────┐
    │░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░│ Sheets
    │                                 │
    │           MATTRESS              │
    │                                 │
    └─────────────────────────────────┘
    ┃▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓┃ ← SENSOR HERE
    ═══════════════════════════════════ Box spring/slats


TOP VIEW (Sensor placement)

    ┌─────────────────────────────────┐
    │                                 │
    │    ┌───────────────────────┐    │
    │    │                       │    │
    │    │  SENSOR STRIP HERE    │    │ ← Under torso/chest
    │    │  (under upper body)   │    │
    │    │                       │    │
    │    └───────────────────────┘    │
    │                                 │
    │                                 │
    └─────────────────────────────────┘
```

### BCG Signal Characteristics

The BCG waveform shows distinct components for each heartbeat:

```
    H
    │\
    │ \    J (main peak - blood ejection)
    │  \  /\
    │   \/  \
────┼────────\────────────
    │         \  /
    │          \/
    │           K

    ◄──────────────►
      ~500-1000ms
      (one heartbeat)
```

- **J-wave**: Largest component, blood ejection into aorta
- **Inter-beat interval**: Time between J-peaks = heart rate
- **Amplitude**: Relates to cardiac output

### Signal Processing

```python
# 1. Bandpass filter (0.5-25 Hz)
filtered = bandpass(raw_signal, 0.5, 25, sample_rate=100)

# 2. J-peak detection
peaks = find_peaks(filtered,
                   min_distance=0.4 * sample_rate,  # 150 BPM max
                   threshold=adaptive_threshold)

# 3. Heart rate from inter-beat intervals
ibis = np.diff(peaks) / sample_rate * 1000  # ms
heart_rate = 60000 / np.mean(ibis)  # BPM

# 4. HRV (Heart Rate Variability)
rmssd = np.sqrt(np.mean(np.diff(ibis)**2))
```

### Wiring to Raspberry Pi (via MCP3008)

```
MCP3008         Raspberry Pi 5
────────        ──────────────
VDD      ─────► 3.3V (Pin 1)
VREF     ─────► 3.3V (Pin 1)
AGND     ─────► GND (Pin 6)
CLK      ─────► GPIO 11 / SCLK (Pin 23)
DOUT     ─────► GPIO 9 / MISO (Pin 21)
DIN      ─────► GPIO 10 / MOSI (Pin 19)
CS       ─────► GPIO 8 / CE0 (Pin 24)
DGND     ─────► GND (Pin 6)

CH0      ◄───── Piezo amplifier output
```

### Expected Performance

| Metric | Expected | Notes |
|--------|----------|-------|
| Heart rate accuracy | ±3-5 BPM | Most accurate of all sensors |
| HRV accuracy | Good | Useful for health monitoring |
| Respiration rate | ±2 BPM | Secondary to radar |
| Bed occupancy | 99%+ | Very reliable |
| Movement detection | 100% | Any movement detected |

### Limitations

- Partner in bed creates interference (if applicable)
- Very active movement saturates sensor
- Requires good signal conditioning
- More complex than radar/audio setup

### Alternative: Load Cells

Instead of piezo, can use 4 load cells under bed legs:

```
        ┌───────────────┐
        │               │
        │    Mattress   │
        │               │
        └───────────────┘
        ┌───────────────┐
        │   Bed Frame   │
        └───┬───────┬───┘
            │       │
           ■         ■ ← Load cells (x4)
        ───┴───────┴───
            Floor

Pros: Very accurate weight/movement
Cons: More complex installation, 4 sensors needed
```

---

## Sensor Fusion Strategy

### Multi-Sensor Confidence Boosting

```
                    ┌─────────────────────────┐
                    │     FUSION ENGINE       │
                    │                         │
    Radar ─────────►│  Respiration: 14 BPM   │
                    │  (confidence: 0.85)     │
                    │                         │
    Audio ─────────►│  + Agrees: 13 BPM      │──► Final: 14 BPM
                    │  (boost: +0.1)          │    Confidence: 0.95
                    │                         │
    BCG   ─────────►│  Heart rate: 68 BPM    │
                    │  (confidence: 0.90)     │
                    └─────────────────────────┘
```

### Redundancy Matrix

| Vital Sign | Primary | Secondary | Backup |
|------------|---------|-----------|--------|
| Respiration | Radar | Audio | BCG |
| Heart Rate | BCG | Radar | - |
| Movement | Radar | BCG | Audio |
| Presence | Radar | BCG | Audio |

### Alert Confidence Levels

| Sensors Agreeing | Confidence | Alert Speed |
|------------------|------------|-------------|
| 1 sensor | 0.7 | Normal (15s) |
| 2 sensors | 0.85 | Faster (10s) |
| 3 sensors | 0.95 | Fastest (5s) |

---

## Calibration Procedures

### Radar Calibration

1. Ensure room is empty
2. Measure background for 30 seconds
3. Subject lies in normal sleeping position
4. Measure baseline Y-position for 60 seconds
5. Measure normal breathing pattern for 2 minutes
6. Store baseline and thresholds

### Audio Calibration

1. Measure ambient noise for 30 seconds
2. Set silence threshold = ambient + 10 dB
3. Subject breathes normally for 60 seconds
4. Detect breathing frequency band
5. Set breathing threshold

### BCG Calibration

1. Empty bed measurement (60 seconds)
2. Subject lies still (60 seconds)
3. Detect baseline amplitude
4. Set J-peak detection threshold
5. Calculate baseline heart rate

---

## Troubleshooting

### Radar Issues

| Problem | Likely Cause | Solution |
|---------|--------------|----------|
| No targets | Too far / wrong angle | Reposition sensor |
| Erratic readings | Multiple people | Single target mode |
| Poor respiration | Too much movement | Wait for stillness |

### Audio Issues

| Problem | Likely Cause | Solution |
|---------|--------------|----------|
| No breathing detected | Too quiet / too far | Move mic closer |
| False positives | Background noise | Adjust threshold |
| Constant detection | AGC too high | Lower sensitivity |

### BCG Issues

| Problem | Likely Cause | Solution |
|---------|--------------|----------|
| No heartbeat | Bad placement | Move under torso |
| Too noisy | Gain too high | Lower amplifier gain |
| Signal clipping | Excessive movement | Add limiter |
