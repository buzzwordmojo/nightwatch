# 🌙 Nightwatch

**Open-source, non-contact epilepsy monitoring system for Raspberry Pi**

Nightwatch monitors a sleeping child for signs of seizure activity using multiple non-invasive sensors. No wearables or contact required.

## Features

- **Non-contact monitoring** - Nothing attached to the child
- **Multiple sensors** - Radar, audio, and bed vibration (BCG)
- **Real-time alerts** - Audio alarms + push notifications
- **Web dashboard** - Monitor from any device
- **Remote access** - Check on things while out (via Tailscale)
- **Open source** - Build your own, modify as needed

## Sensors

| Sensor | Detects | Hardware |
|--------|---------|----------|
| **Radar** | Respiration rate, movement | HLK-LD2450 (24GHz mmWave) |
| **Audio** | Breathing sounds, vocalizations | USB microphone |
| **BCG** | Heart rate, bed occupancy | Piezo sensor under mattress |

## Quick Start

### Hardware (~$130 for basic setup)

See [SHOPPING_LIST.md](hardware/SHOPPING_LIST.md) for complete parts list.

**Minimum:**
- Raspberry Pi 5 (4GB)
- HLK-LD2450 radar module
- CP2102 USB-to-UART adapter
- USB extension cable
- Power supply, SD card

### Software Setup

```bash
# Clone the repository
git clone https://github.com/yourrepo/nightwatch.git
cd nightwatch

# Install Python package
pip install -e .

# Run with mock sensors (no hardware)
./bin/mock

# Run with real hardware
./bin/dev
```

### Dashboard

Open **http://localhost:3000** for the web dashboard.

## Project Structure

```
nightwatch/
├── nightwatch/           # Python backend
│   ├── core/             # Event system, config, alert engine
│   ├── detectors/        # Sensor modules (radar, audio, bcg)
│   ├── dashboard/        # Built-in web server
│   └── bridge/           # Convex integration
├── dashboard-ui/         # Next.js dashboard
├── hardware/             # Hardware docs & 3D prints
│   ├── SHOPPING_LIST.md  # Parts to buy
│   ├── SENSOR_SPECS.md   # Technical specs
│   └── 3d_prints/        # Enclosure designs
├── config/               # Configuration files
├── tests/                # Test suite
└── bin/                  # Run scripts
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Raspberry Pi                            │
│                                                              │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐                      │
│  │  Radar  │  │  Audio  │  │   BCG   │   Detectors          │
│  └────┬────┘  └────┬────┘  └────┬────┘                      │
│       │            │            │                            │
│       └────────────┼────────────┘                            │
│                    ▼                                         │
│            ┌──────────────┐                                  │
│            │  Event Bus   │   ZeroMQ pub/sub                 │
│            └──────┬───────┘                                  │
│                   │                                          │
│       ┌───────────┼───────────┐                              │
│       ▼           ▼           ▼                              │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐                        │
│  │  Alert  │ │Dashboard│ │ Convex  │                        │
│  │ Engine  │ │ Server  │ │ Bridge  │                        │
│  └────┬────┘ └─────────┘ └────┬────┘                        │
│       │                       │                              │
│       ▼                       ▼                              │
│  ┌─────────┐           ┌───────────┐                        │
│  │ Speaker │           │  Next.js  │                        │
│  │  Alarm  │           │ Dashboard │                        │
│  └─────────┘           └───────────┘                        │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Configuration

Default config is in `config/default.yaml`. Key settings:

```yaml
detectors:
  radar:
    enabled: true
    device: /dev/ttyUSB0   # CP2102 adapter

alert_engine:
  rules:
    - name: respiration_low
      detector: radar
      condition: respiration_rate < 8
      duration_seconds: 15
      level: warning
```

## Hardware Setup

### Wall-Mount Radar

The radar needs to look down at the bed. Use the 3D printed enclosure:

```
    WALL (3-4 ft up)
      │
      └──[Radar enclosure]   ← 45° angle built-in
              ↘
               ↘  USB cable to Pi
                ↘
    ┌──────────────┐
    │  NIGHTSTAND  │
    │    [ Pi ]    │◄── USB mic, BCG wires
    └──────────────┘

    ══════════════════
    ║   MATTRESS     ║
    ══════════════════
```

See [3D print designs](hardware/3d_prints/DESIGN_SPECS.md).

## Remote Monitoring

For checking on things while out (dinner, etc):

1. Install [Tailscale](https://tailscale.com) on Pi and your phone
2. Access dashboard via Tailscale IP

No port forwarding or cloud service needed.

## Development

```bash
# Run tests
pytest

# Run with mock sensors
python -m nightwatch --mock-sensors

# Just the dashboard
cd dashboard-ui && npm run dev
```

## Roadmap

- [x] Radar respiration detection
- [x] Audio breathing detection
- [x] BCG heart rate detection
- [x] Alert engine with rules
- [x] Web dashboard
- [ ] Push notifications (Pushover/Ntfy)
- [ ] Setup wizard (WiFi captive portal)
- [ ] Recording/playback for debugging
- [ ] ML-based seizure pattern detection

## Safety Notice

⚠️ **This is not a medical device.** Nightwatch is an open-source project for monitoring and alerting. It should supplement, not replace, proper medical supervision. Always consult healthcare providers for medical decisions.

## Contributing

Contributions welcome! This project exists to help families like ours. If you build one, find bugs, or add features, please share back.

## License

MIT License - Use it, modify it, share it.

---

*Built with love for Miles and families like ours.*
