# Nightwatch

An open-source, non-contact monitoring system for children with epilepsy. Built on Raspberry Pi with modular, affordable sensors.

## Project Goal

Provide peace of mind for families of children at risk of nocturnal seizures, SUDEP (Sudden Unexpected Death in Epilepsy), or breathing/heart rate complications during sleep. Designed to be:

- **Non-intrusive** - Nothing attached to the child
- **Affordable** - Under $250 for a full system
- **Open source** - Any family can build one
- **Modular** - Start simple, add sensors as needed

---

## Miles' Specific Needs

- **Age:** 13, ~85 lbs
- **Key indicators:**
  - Eyes opening during sleep (sustained)
  - Respiration slowing or stopping
  - Heart rate dropping
  - Risk of hypoxia
- **Alert speed:** Within 15 seconds of detection
- **Environment:** Bedroom, nighttime monitoring

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         ALERT ENGINE                             │
│   • Receives normalized events from all detectors                │
│   • Applies configurable rules and thresholds                    │
│   • Fuses multiple signals for higher confidence                 │
│   • Triggers notifications (sound, phone, lights)                │
└─────────────────────────────────────────────────────────────────┘
                              ▲
                              │ Standardized events
                              │ {detector, timestamp, confidence, state, value}
                              │
        ┌─────────────────────┼─────────────────────┬─────────────────────┐
        │                     │                     │                     │
        ▼                     ▼                     ▼                     ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   DETECTOR   │    │   DETECTOR   │    │   DETECTOR   │    │   DETECTOR   │
│    Radar     │    │    Audio     │    │     BCG      │    │   Future..   │
└──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
```

Each detector:
- Runs as an independent process
- Emits standardized events
- Can be enabled/disabled without affecting others
- Has its own configuration and calibration

---

## Implementation Phases

### Phase 1: Radar Detection (Start Here)
**Hardware: HLK-LD2450 or LD2410C (~$15-20)**

The mmWave radar is the highest-value first sensor. It provides:
- Respiration rate (breaths per minute)
- Respiration amplitude (shallow vs deep breathing)
- Approximate heart rate
- Movement detection (macro and micro)
- Presence detection
- Works through blankets, in complete darkness

**Mounting:** Wall or ceiling mount, 1-3 meters from bed, aimed at torso area. 3D printed enclosure.

**Alerts:**
- Respiration rate below threshold (configurable, e.g., <8 BPM)
- Respiration stops for X seconds
- Sudden movement spike (possible seizure activity)
- Heart rate approximation drops significantly

---

### Phase 2: Audio Detection
**Hardware: USB microphone with AGC (~$15-25)**

Audio provides:
- Breathing sound patterns
- Silence detection (breathing stops)
- Vocalization detection (sounds during seizure)
- Gasping or irregular breathing sounds

**Mounting:** Bedside or ceiling, 1-2 meters from head. 3D printed enclosure with pop filter.

**Processing:**
- Frequency analysis for breath sounds (typically 200-800 Hz range)
- Amplitude envelope for breathing rhythm
- Silence detection with configurable threshold
- Optional: ML model for anomaly detection

**Alerts:**
- Breathing sounds stop for X seconds
- Unusual vocalization detected
- Breathing pattern becomes irregular

**Signal fusion with radar:**
- Radar says respiration dropping + Audio says breathing sounds fading = High confidence alert
- Redundancy if one sensor loses signal

---

### Phase 3: BCG Bed Sensor (Heart Rate Focus)
**Hardware: Piezo film strip or FSR mat (~$20-40)**

BCG (ballistocardiography) provides:
- Accurate heart rate (±3-5 BPM)
- Heart rate variability
- Secondary respiration signal
- Bed movement / position changes
- Bed exit detection

**Mounting:** Under the mattress, positioned under torso area. Thin strip, completely unfelt.

**Alerts:**
- Heart rate below threshold (configurable, e.g., <50 BPM)
- Heart rate drops rapidly (e.g., 20 BPM drop in 30 seconds)
- Heart rate becomes irregular
- Combined: low HR + low respiration = urgent alert

**Signal fusion:**
- BCG heart rate cross-validated with radar heart rate estimate
- Higher confidence when both agree
- Failover if one loses signal

---

## Future Modules (Not for Initial Build)

### Thermal Camera (MLX90640)
- Detects breath plume (warm air from nose/mouth)
- Body temperature changes
- Backup respiration signal
- Cost: ~$70

### IR Camera (Eyes Open Detection)
- Detects sustained eye opening
- Requires ML model, sensitive to positioning
- Could revisit once other sensors are stable
- Cost: ~$35 + IR illuminator

### Environmental Sensors
- Room temperature, humidity
- CO2 levels
- Ambient light
- Cost: ~$15-20

### Pulse Oximeter (Contact)
- If non-contact proves insufficient
- Medical-grade SpO2 reading
- Would require something on Miles
- Last resort option

---

## Hardware Bill of Materials

### Core Platform
| Component | Purpose | Cost | Link/Notes |
|-----------|---------|------|------------|
| Raspberry Pi 5 (4GB) | Main processor | $60 | |
| Power supply (27W USB-C) | Pi power | $12 | Official recommended |
| MicroSD card (32GB+) | Storage | $10 | |
| Case | Pi enclosure | $10 | Or 3D print |

### Phase 1: Radar
| Component | Purpose | Cost | Link/Notes |
|-----------|---------|------|------------|
| HLK-LD2450 | mmWave radar | $18 | UART interface, gives coordinates |
| OR: HLK-LD2410C | mmWave radar | $15 | Simpler, just presence/motion/breath |
| Dupont wires | Connection to Pi | $3 | |
| 3D printed mount | Wall/ceiling mount | -- | Design TBD |

### Phase 2: Audio
| Component | Purpose | Cost | Link/Notes |
|-----------|---------|------|------------|
| USB microphone | Audio capture | $20 | With AGC, omnidirectional |
| 3D printed mount | Positioning | -- | Design TBD |

### Phase 3: BCG
| Component | Purpose | Cost | Link/Notes |
|-----------|---------|------|------------|
| Piezo film sensor | Heart rate / movement | $25 | Large format, under mattress |
| OR: FSR mat | Pressure sensing | $20 | Alternative approach |
| Amplifier board | Signal conditioning | $10 | Piezo signal is weak |
| ADC (if needed) | Analog to digital | $5 | MCP3008 or similar |

### Notifications
| Component | Purpose | Cost | Link/Notes |
|-----------|---------|------|------------|
| Speaker/buzzer | Local alarm | $5 | |
| LED strip (optional) | Visual alert | $10 | |

**Estimated Total:**
- Phase 1 only: ~$115
- Phase 1 + 2: ~$135
- Full system (Phase 1-3): ~$180-200

---

## Software Architecture

```
nightwatch/
├── core/
│   ├── engine.py              # Alert engine - coordinates everything
│   ├── events.py              # Event schema and validation
│   ├── config.py              # System configuration loader
│   ├── fusion.py              # Multi-sensor signal fusion logic
│   └── notifiers/
│       ├── base.py            # Notifier interface
│       ├── audio.py           # Local speaker/buzzer
│       ├── push.py            # Phone notifications (Pushover/Ntfy)
│       └── webhook.py         # Generic webhook for integrations
│
├── detectors/
│   ├── base.py                # Abstract detector interface
│   ├── radar/
│   │   ├── detector.py        # Radar detector implementation
│   │   ├── ld2450.py          # LD2450 protocol driver
│   │   ├── ld2410.py          # LD2410 protocol driver
│   │   └── config.yaml        # Default configuration
│   ├── audio/
│   │   ├── detector.py        # Audio detector implementation
│   │   ├── processing.py      # Audio signal processing
│   │   └── config.yaml
│   └── bcg/
│       ├── detector.py        # BCG detector implementation
│       ├── processing.py      # BCG signal processing
│       └── config.yaml
│
├── setup/
│   ├── hotspot.py             # WiFi hotspot mode
│   ├── bluetooth.py           # BLE advertising for discovery
│   ├── provisioning.py        # WiFi credential handling
│   └── wizard/
│       ├── server.py          # Setup wizard web server
│       ├── templates/         # Wizard step UI
│       └── static/
│
├── dashboard/
│   ├── server.py              # Dashboard web server
│   ├── websocket.py           # Real-time updates via WebSocket
│   ├── api.py                 # REST API for stats/history/config
│   ├── templates/
│   │   ├── index.html         # Main dashboard (vitals at a glance)
│   │   ├── history.html       # Historical data and trends
│   │   └── settings.html      # Configuration UI
│   └── static/
│       ├── css/
│       ├── js/
│       └── icons/
│
├── scripts/
│   ├── setup.sh               # Initial Pi setup
│   ├── calibrate.py           # Sensor calibration wizard
│   └── test_sensors.py        # Hardware verification
│
├── hardware/
│   ├── wiring/                # Wiring diagrams
│   ├── 3d_prints/             # STL files for mounts/enclosures
│   │   ├── radar_mount.stl
│   │   ├── mic_mount.stl
│   │   └── pi_case.stl
│   └── bom.csv                # Bill of materials with links
│
├── config/
│   ├── default.yaml           # Default configuration
│   └── miles.yaml             # Miles-specific config (example)
│
├── logs/                      # Event logs, recordings
├── requirements.txt           # Python dependencies
├── README.md                  # User-facing documentation
└── PLAN.md                    # This file
```

---

## Event Schema

All detectors emit events in this format:

```python
{
    "detector": "radar",           # Source detector name
    "timestamp": 1707782400.123,   # Unix timestamp
    "confidence": 0.92,            # 0.0 - 1.0
    "state": "alert",              # "normal", "warning", "alert", "uncertain"
    "value": {                     # Detector-specific data
        "respiration_rate": 6,
        "heart_rate_estimate": 52,
        "movement": 0.1
    }
}
```

---

## Alert Rules (Configurable)

```yaml
rules:
  - name: "Respiration stopped"
    conditions:
      - detector: radar
        field: respiration_rate
        operator: "<"
        value: 4
        duration_seconds: 10
    severity: critical

  - name: "Heart rate low"
    conditions:
      - detector: bcg
        field: heart_rate
        operator: "<"
        value: 50
        duration_seconds: 15
    severity: critical

  - name: "Breathing sounds stopped"
    conditions:
      - detector: audio
        field: breathing_detected
        operator: "=="
        value: false
        duration_seconds: 12
    severity: warning

  - name: "Multi-signal concern"
    conditions:
      - detector: radar
        field: respiration_rate
        operator: "<"
        value: 8
      - detector: audio
        field: breathing_amplitude
        operator: "<"
        value: 0.3
    combine: "all"  # All conditions must be true
    severity: critical
    alert_delay_seconds: 5  # Faster alert when signals agree
```

---

## Notification Options

1. **Local audio alarm** - Loud enough to wake parents
2. **Phone push notification** - Via Pushover, Ntfy, or similar
3. **Visual alert** - LED strip or smart light
4. **Dashboard alert** - Web UI shows real-time status
5. **Webhook** - Integrate with Home Assistant, etc.

---

## Remote Access

Access the dashboard from anywhere (out to dinner, traveling, etc.) using Tailscale.

### How It Works

```
ANYWHERE                               AT HOME
┌──────────────┐                       ┌──────────────┐
│ Your phone   │◄─────encrypted───────▶│     Pi       │
│ Wife's phone │      Tailscale        │  Nightwatch  │
└──────────────┘                       └──────────────┘
                                       No ports exposed
                                       No configuration
                                       Just works
```

### Setup (One Time)

**On the Pi:**
```bash
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up
```

**On your phones:**
1. Install Tailscale app (iOS/Android)
2. Sign in with same account
3. Access dashboard at `http://nightwatch:5000` from anywhere

### Why Tailscale

- **Free** for personal use (up to 100 devices)
- **Secure** - encrypted, no ports exposed to internet
- **Simple** - no port forwarding, no dynamic DNS, no certificates
- **Reliable** - works through NAT, firewalls, cellular, hotel WiFi
- **Fast** - direct connection when possible, minimal latency

### Alternatives (If Needed)

| Option | Use Case |
|--------|----------|
| Cloudflare Tunnel | If you want a public URL (requires domain) |
| WireGuard | If you want to self-host everything |
| ZeroTier | Similar to Tailscale, also free |

---

## User Experience

### First-Time Setup (Dead Simple)

The goal: A non-technical parent can set this up in 10 minutes.

```
SETUP FLOW:

1. POWER ON
   - Plug in the Pi
   - LED indicates "ready to configure" (pulsing blue)
   - Pi automatically enters setup mode on first boot

2. CONNECT
   - Pi broadcasts WiFi hotspot: "Nightwatch-XXXX"
   - Also advertises via Bluetooth for app discovery
   - Family connects phone/tablet to hotspot
   - Captive portal auto-opens setup wizard

3. WIZARD STEPS
   ┌─────────────────────────────────┐
   │ Step 1: Connect to WiFi        │
   │ Step 2: Name this monitor      │
   │ Step 3: Position sensors       │
   │   └─ Live preview to confirm   │
   │ Step 4: Set up notifications   │
   │   └─ Phone, alarm, both?       │
   │ Step 5: Test alert             │
   │ Step 6: Done!                  │
   └─────────────────────────────────┘

4. MONITORING BEGINS
   - Dashboard available at nightwatch.local
   - Phone notifications configured
   - System running
```

### Dashboard

Clean, glanceable, works on phone or wall-mounted tablet:

```
┌─────────────────────────────────────────────────────────────────┐
│  NIGHTWATCH                                    ● All Normal     │
│  ─────────────────────────────────────────────────────────────  │
│                                                                  │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │   BREATHING     │  │   HEART RATE    │  │    MOVEMENT     │  │
│  │                 │  │                 │  │                 │  │
│  │    14 BPM       │  │     68 BPM      │  │      Low        │  │
│  │    ~~~~~~~~     │  │    ♥♥♥♥♥♥       │  │    ░░▒░░░       │  │
│  │    normal       │  │    normal       │  │    sleeping     │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  RESPIRATION TREND (last 2 hours)                       │    │
│  │  20│      ╭─╮                                           │    │
│  │  15│ ─────╯  ╰──────────────────────────────────────    │    │
│  │  10│                                                    │    │
│  │   5│                                                    │    │
│  │    └────────────────────────────────────────────────    │    │
│  │     11pm            12am            1am          now    │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ RECENT EVENTS                                            │   │
│  │ ○ 1:23am  Movement detected (turned over)                │   │
│  │ ○ 12:45am Brief respiration dip (recovered)              │   │
│  │ ○ 11:30pm Monitoring started                             │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  [Settings]  [History]  [Test Alert]              [Pause 30m]   │
└─────────────────────────────────────────────────────────────────┘
```

**Dashboard features:**
- Big, clear status indicator (green/yellow/red)
- Current vitals at a glance
- Trends over time
- Event log with timestamps
- Mobile-responsive (phone, tablet, desktop)
- Optional: Dedicated wall-mounted tablet as baby monitor style display
- Accessible at `nightwatch.local` (mDNS) or IP address

### Companion App (Future)

- Progressive Web App (PWA) - installable from browser
- Receives push notifications
- Shows live status
- Could go native later if needed

---

## 3D Printing Needs

| Item | Purpose | Priority |
|------|---------|----------|
| Radar enclosure + mount | Wall/ceiling mount for LD2450 | Phase 1 |
| Microphone mount | Bedside or ceiling position | Phase 2 |
| Pi case | Main unit enclosure | Phase 1 |
| Cable management clips | Clean wire routing | Nice to have |

Designs will be parametric (OpenSCAD or FreeCAD) so others can adjust for their specific sensors/hardware.

---

## Development & Testing

### The Challenge

How do you test a system designed to detect seizures without... having seizures?

### Testing Modes

```
┌─────────────────────────────────────────────────────────────────┐
│                     TESTING PYRAMID                              │
└─────────────────────────────────────────────────────────────────┘

     /\
    /  \     REAL-WORLD (Miles, supervised)
   /    \    - Final validation only
  /------\   - Always supervised initially
 /        \  - Gradual trust building
/──────────\
    /\
   /  \      SIMULATION MODE
  /    \     - Replay recorded sessions
 /      \    - Inject synthetic anomalies
/--------\   - Test alert logic without hardware
──────────
    /\
   /  \      SELF-TESTING
  /    \     - You are the subject
 /      \    - Breathe slow, hold breath
/--------\   - Verify sensors respond
──────────
    /\
   /  \      UNIT/INTEGRATION TESTS
  /    \     - Mock sensor data
 /      \    - Test each component
/--------\   - Automated CI
──────────
```

### 1. Unit & Integration Tests (Automated)

```python
# Example: Test alert engine logic
def test_low_respiration_triggers_alert():
    engine = AlertEngine(config)

    # Simulate radar reporting low respiration for 12 seconds
    for i in range(12):
        engine.process_event({
            "detector": "radar",
            "timestamp": time.time() + i,
            "state": "warning",
            "value": {"respiration_rate": 5}
        })

    assert engine.current_alert_level == "critical"
    assert len(engine.triggered_alerts) == 1
```

Run with: `pytest tests/`

### 2. Self-Testing (You're the Subject)

Before putting this in Miles' room, test on yourself:

```
SELF-TEST PROTOCOL:

1. BASELINE
   - Sit/lie in front of radar
   - Verify dashboard shows normal breathing (12-20 BPM)
   - Verify audio detector picks up breath sounds

2. BREATH HOLD TEST
   - Hold breath for 15-20 seconds
   - Verify respiration rate drops toward 0
   - Verify alert triggers at configured threshold
   - Resume breathing, verify recovery detected

3. MOVEMENT TEST
   - Lie still, verify "low movement" state
   - Move around, verify movement spike detected
   - Simulate turning over in bed

4. AUDIO TEST
   - Breathe normally, verify detection
   - Breathe very quietly, verify still detected
   - Make sounds, verify vocalization detection

5. ALERT TEST
   - Trigger each alert type
   - Verify notifications arrive on phone
   - Verify local alarm sounds
   - Verify dashboard shows alert state
```

### 3. Simulation Mode (Synthetic Data)

Record real sessions, replay them for testing:

```
nightwatch/
├── recordings/
│   ├── normal_sleep_8hr.json      # Recorded from real session
│   ├── breath_hold_test.json      # You holding your breath
│   └── simulated_events.json      # Synthetic anomalies
│
├── simulator/
│   ├── playback.py                # Replay recorded sessions
│   ├── generator.py               # Generate synthetic data
│   └── scenarios/
│       ├── gradual_resp_drop.yaml # Respiration slowly decreases
│       ├── sudden_movement.yaml   # Seizure-like movement spike
│       └── sensor_failure.yaml    # Test graceful degradation
```

Run simulation:
```bash
# Replay a recording through the system
./nightwatch --simulate recordings/normal_sleep_8hr.json

# Run a specific scenario
./nightwatch --simulate scenarios/gradual_resp_drop.yaml --speed 10x
```

This lets you:
- Test without hardware connected
- Run accelerated (hours of data in minutes)
- Test edge cases that are hard to produce naturally
- Regression test after code changes

### 4. Real-World Testing (Supervised)

**Phase A: Your bedroom first**
- Run system on yourself for several nights
- Tune thresholds based on your normal patterns
- Verify no false alarms, alerts work

**Phase B: Miles' room, monitoring only**
- Install in Miles' room
- Run in "silent mode" (logging, no alerts)
- Review logs each morning
- Learn his baseline patterns
- Tune thresholds

**Phase C: Miles' room, alerts enabled**
- Enable notifications
- Start with conservative thresholds (fewer false alarms)
- Gradually tune based on real data
- Always have backup monitoring in place initially

### Development Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│  LOCAL DEV           │  PI DEV              │  PRODUCTION       │
│  (your laptop)       │  (Pi on desk)        │  (Miles' room)    │
├──────────────────────┼──────────────────────┼───────────────────┤
│  • Write code        │  • Test with real    │  • Final system   │
│  • Run unit tests    │    sensors           │  • Alerts enabled │
│  • Simulation mode   │  • Self-test         │  • Supervised     │
│  • No hardware       │  • Dashboard dev     │    initially      │
│  • Fast iteration    │  • Integration test  │                   │
└──────────────────────┴──────────────────────┴───────────────────┘
```

### Mock Sensors for Development

When developing on your laptop without hardware:

```python
# Run with mock sensors
./nightwatch --mock-sensors

# Mocks generate realistic fake data:
# - Breathing patterns with natural variation
# - Occasional movement
# - Configurable anomalies for testing
```

### Continuous Integration

```yaml
# .github/workflows/test.yml
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: pytest tests/ -v
      - name: Run simulation tests
        run: ./nightwatch --simulate tests/scenarios/ --verify
```

---

## Development Priorities

### Milestone 1: Proof of Concept
- [ ] Basic radar detector reading respiration
- [ ] Simple threshold alerting
- [ ] Console output / file logging
- [ ] Test on desk with radar pointing at self

### Milestone 2: Core System
- [ ] Full detector framework
- [ ] Alert engine with rules
- [ ] Local audio notification
- [ ] Phone push notification
- [ ] Basic web dashboard

### Milestone 3: Audio Integration
- [ ] Audio detector implementation
- [ ] Breathing sound detection
- [ ] Signal fusion with radar

### Milestone 4: BCG Integration
- [ ] BCG hardware selection and testing
- [ ] Heart rate extraction
- [ ] Integration with alert engine

### Milestone 5: Polish for Others
- [ ] Setup wizard
- [ ] Calibration tools
- [ ] Documentation
- [ ] 3D print files finalized
- [ ] Community release

---

## Future Roadmap (After Core is Working)

Once Miles is being monitored reliably, potential enhancements:

### Additional Detectors
- [ ] **Thermal camera (MLX90640)** - Breath plume detection, backup respiration signal
- [ ] **IR camera + eye detection** - Revisit once other sensors are stable
- [ ] **Environmental sensors** - Room temp, humidity, CO2
- [ ] **Pulse oximetry** - If non-contact proves insufficient (contact sensor, last resort)

### Analytics & Insights
- [ ] **Sleep quality reports** - Nightly summary, trends over time
- [ ] **Pattern detection** - ML to learn Miles' normal patterns, flag anomalies
- [ ] **Export to medical team** - Generate reports for neurologist visits
- [ ] **Seizure logging** - If an event occurs, record full sensor data for review

### Hardware Improvements
- [ ] **Custom PCB** - Consolidate wiring, cleaner build for other families
- [ ] **Battery backup** - UPS or built-in battery for power outages
- [ ] **Enclosure design** - Professional-looking case, less DIY aesthetic
- [ ] **Multiple sensor zones** - Support larger beds or multiple positions

### Platform & Community
- [ ] **GitHub release** - Public repo with documentation
- [ ] **Build guide** - Step-by-step with photos/video
- [ ] **Pre-configured SD card image** - Flash and go
- [ ] **Hardware kit** - Partner with supplier for all-in-one kit
- [ ] **Community forum** - Other families sharing configs, improvements
- [ ] **Multi-child support** - Multiple rooms, single dashboard

### Integrations
- [ ] **Home Assistant** - Native integration
- [ ] **Apple Health / Google Fit** - Export sleep data
- [ ] **IFTTT / Webhooks** - Custom automation triggers
- [ ] **Voice assistants** - "Hey Google, how did Miles sleep?"

### Research Possibilities
- [ ] **Anonymous data contribution** - Opt-in sharing for epilepsy research
- [ ] **Collaboration with researchers** - Help improve seizure detection algorithms
- [ ] **Validation studies** - Compare with clinical monitoring equipment

---

## Safety Considerations

**This system is a supplement, not a replacement for medical care.**

- False negatives are possible - no system is perfect
- Sensors can fail, lose signal, or be miscalibrated
- Always follow your medical team's recommendations
- Consider this one layer of a multi-layer approach

**Reliability measures:**
- Heartbeat/health check for all detectors
- Alert if a detector stops responding
- Battery backup recommended (UPS)
- Test alerts regularly

---

## Open Source Philosophy

This project will be released under a permissive open-source license (MIT or Apache 2.0) so that:

- Any family can build one
- No recurring subscription costs
- Community can improve and extend it
- Medical device companies can't lock it down

Not a medical device. Not FDA approved. A tool for families, by families.

---

## Resources & References

- OpenSeizureDetector - https://openseizuredetector.github.io/
- LD2450 datasheet and protocol documentation
- BCG signal processing papers
- Remote vital signs monitoring research
- Raspberry Pi GPIO documentation

---

## Contact / Contributions

TBD - GitHub repository link once created.
