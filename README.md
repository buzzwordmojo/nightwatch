# 🌙 Nightwatch

**Open-source, non-contact epilepsy monitoring system for Raspberry Pi**

Nightwatch monitors a sleeping child for signs of seizure activity using multiple non-invasive sensors. No wearables or contact required.

## Features

- **Non-contact monitoring** - nothing attached to the sleeper
- **Measured vitals** - respiration and heart rate from a 60GHz radar
- **Real-time alerts** - push notifications via ntfy (self-hosted or ntfy.sh)
- **Web dashboard** - live waveforms plus stored history
- **Off-device watchdog** - an external service notices if the monitor dies
- **Open source** - build your own, modify as needed

> **What this is not.** It cannot detect seizures directly. It measures
> respiration, heart rate and movement, and alerts on thresholds you
> configure. Subtle or non-convulsive seizure types produce little or no
> movement and may not be visible to any radar. Treat it as an additional set
> of eyes, never as a medical device or a replacement for one.

## Sensors

| Sensor | Detects | Hardware | Status |
|--------|---------|----------|--------|
| **Vitals radar** | Respiration **and heart rate** (measured), presence | HLK-LD6002 (60GHz FMCW) | **Working** — recommended |
| **Presence radar** | Respiration (inferred), movement, position | HLK-LD2450 (24GHz mmWave) | Supported |
| **Audio** | Breathing sounds, seizure sounds, silence | Lavalier / USB microphone | Untested |
| **BCG** | Heart rate, respiration, bed occupancy | Piezo + MCP3008 over SPI | Written, not wired up |
| **Capacitive** | Heart rate, respiration, bed occupancy | FDC1004 + electrode | Planned |

**Which radar to buy:** the **LD6002** measures respiration and heart rate
directly and is the recommended sensor. The LD2450 tracks position and
*infers* breathing from sub-millimetre chest movement — it works, but it
cannot give you a heart rate. Set `detectors.radar.model` to `ld6002` or
`ld2450` to pick.

> ⚠️ **Read [docs/MOUNTING.md](docs/MOUNTING.md) before buying or installing.**
> With a 60GHz vitals radar, *aim decides whether the system works at all* —
> measured lock quality ranged from 26% to 100% on the same hardware purely
> from how it was pointed.

See [docs/SENSORS.md](docs/SENSORS.md) for detailed sensor documentation and [docs/FUSION.md](docs/FUSION.md) for how signals combine.

## Quick Start

### Hardware (~$123 for basic setup)

See [SHOPPING_LIST.md](hardware/SHOPPING_LIST.md) for complete parts list.

**Minimum:**
- Raspberry Pi 5 (4GB)
- HLK-LD6002 vitals radar (recommended) or HLK-LD2450
- USB-to-UART adapter — some LD6002 carrier boards have USB-C built in
- USB extension cable
- Power supply, SD card

### Software Setup

```bash
# Clone the repository
git clone https://github.com/buzzwordmojo/nightwatch.git
cd nightwatch

# Install Python package
pip install -e .

# Run with mock sensors (no hardware)
./bin/mock

# Run with real hardware
./bin/dev
```

### Dashboard

Open **http://localhost:3000** for the dev dashboard or **https://nightwatch.local** in production.

## Project Structure

```
nightwatch/
├── nightwatch/           # Python backend
│   ├── core/             # Event system, config, alert engine, fusion
│   ├── detectors/        # Sensor modules (radar, audio, capacitive)
│   ├── dashboard/        # Built-in web server
│   └── bridge/           # Convex integration
├── dashboard-ui/         # Next.js dashboard
├── docs/                 # Documentation
│   ├── SENSORS.md        # Sensor details, pinouts, build guides
│   └── FUSION.md         # Signal fusion architecture
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
┌──────────────────────────────────────────────────────────────────┐
│                        Raspberry Pi                               │
│                                                                   │
│  ┌──────────┐  ┌──────────┐  ┌────────────┐                      │
│  │  Radar   │  │  Audio   │  │ Capacitive │   Detectors          │
│  │ (LD2450) │  │(Lavalier)│  │ (FDC1004)  │                      │
│  └────┬─────┘  └────┬─────┘  └─────┬──────┘                      │
│       │             │              │                              │
│       └─────────────┼──────────────┘                              │
│                     ▼                                             │
│             ┌──────────────┐                                      │
│             │  Event Bus   │   ZeroMQ pub/sub                     │
│             └──────┬───────┘                                      │
│                    │                                              │
│        ┌───────────┼───────────┐                                  │
│        ▼           ▼           ▼                                  │
│   ┌─────────┐ ┌─────────┐ ┌─────────┐                            │
│   │ Fusion  │ │Dashboard│ │ Convex  │                            │
│   │ Engine  │ │ Server  │ │ Bridge  │                            │
│   └────┬────┘ └─────────┘ └────┬────┘                            │
│        │                       │                                  │
│        ▼                       ▼                                  │
│   ┌─────────┐            ┌───────────┐                           │
│   │  Alert  │            │  Next.js  │                           │
│   │ Engine  │            │ Dashboard │                           │
│   └────┬────┘            └───────────┘                           │
│        │                                                          │
│        ▼                                                          │
│   ┌─────────┐                                                     │
│   │ Speaker │                                                     │
│   │  Alarm  │                                                     │
│   └─────────┘                                                     │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
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

### Local Development

Run the dashboard locally for instant hot-reload while backend services run in Docker:

```bash
# Terminal 1: Start backend services
docker compose up -d convex        # Start Convex database
./scripts/deploy-convex.sh         # Deploy Convex functions (first time only)
docker compose up backend          # Start Python backend with mock sensors

# Terminal 2: Start dashboard with hot-reload
cd dashboard-ui
npm install                        # First time only
npm run dev                        # Next.js dev server
```

**Services:**
- Dashboard: http://localhost:3000 (Next.js with hot-reload)
- Backend: http://localhost:9531 (Python API + mock sensors)
- Production: https://nightwatch.local (HTTPS on port 443)
- Convex: http://localhost:3210 (real-time database)
- Simulator: http://localhost:9531/sim (trigger test scenarios)

### Production / Raspberry Pi

Build and run all services in Docker (for deployment):

```bash
docker compose up -d convex
./scripts/deploy-convex.sh
docker compose --profile prod up
```

This builds optimized production images suitable for Raspberry Pi deployment.

### Convex Self-Hosted Setup

The dashboard uses [Convex](https://convex.dev) for real-time data. For local development, we run a self-hosted Convex backend in Docker.

**How it works:**
1. Python backend pushes sensor data to Convex via HTTP mutations
2. Next.js dashboard subscribes to Convex queries for real-time updates
3. Functions in `dashboard-ui/convex/*.ts` define the database schema and queries

**Manual Convex deployment (if needed):**

```bash
cd dashboard-ui

# Get admin key from running Convex container
docker exec nightwatch-convex /convex/generate_admin_key.sh

# Set environment variables
export CONVEX_SELF_HOSTED_URL=http://localhost:3210
export CONVEX_SELF_HOSTED_ADMIN_KEY="convex-self-hosted|<key-from-above>"

# Deploy functions
npx convex dev --once
```

Or add to `dashboard-ui/.env.local`:
```
CONVEX_SELF_HOSTED_URL=http://localhost:3210
CONVEX_SELF_HOSTED_ADMIN_KEY=convex-self-hosted|<your-key>
```

## Roadmap

**Software (implemented):**
- [x] Radar detector (respiration, movement, presence)
- [x] Audio detector (breathing, seizure sounds, silence)
- [x] Alert engine with configurable rules
- [x] Web dashboard
- [x] Sensor fusion architecture (documented)
- [x] Fusion engine (combines signals from multiple sensors)

**Hardware (in progress):**
- [ ] Radar hardware testing (LD2450 arriving)
- [ ] Audio hardware testing (lavalier mic arriving)
- [ ] Capacitive sensor prototype (FDC1004 + foil electrode)

**Future:**
- [ ] Push notifications (Pushover/Ntfy)
- [ ] Thermal camera integration (MLX90640)
- [ ] ML-based seizure pattern detection

## Safety Notice

⚠️ **This is not a medical device.** Nightwatch is an open-source project for monitoring and alerting. It should supplement, not replace, proper medical supervision. Always consult healthcare providers for medical decisions.

## Contributing

Contributions welcome! This project exists to help families like ours. If you build one, find bugs, or add features, please share back.

## License

MIT License - Use it, modify it, share it.

---

*Built with love for Miles and families like ours.*
