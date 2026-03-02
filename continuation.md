# Radar Dashboard Integration - Continuation Notes

## What We Did

### 1. Radar Dashboard Integration
Integrated the standalone Python radar visualizer (`scripts/radar_web_viz.py`) into the main Nightwatch Next.js + Convex dashboard.

**Files created/modified:**

- **`dashboard-ui/convex/schema.ts`** - Added `radarSignal` table (timestamp, x, y, distance) with index
- **`dashboard-ui/convex/vitals.ts`** - Added `insertRadarSignal`, `getRadarSignal` (with downsampling), `cleanupRadarSignal` (12hr retention)
- **`nightwatch/bridge/convex.py`** - Added `push_radar_signal()` method to ConvexBridge; updated `ConvexEventHandler` to push x/y/distance from radar events
- **`nightwatch/detectors/radar/detector.py`** - Added `x` and `y` fields to event value (both real and mock detectors)
- **`dashboard-ui/src/components/dashboard/RadarSignalChart.tsx`** - New component: raw + smoothed Y-deviation waveform with time range selector and stats
- **`dashboard-ui/src/components/dashboard/RadarAimingView.tsx`** - New component: canvas top-down radar view with distance zones (yellow 0.5-1m/3-4m, green 1-3m)
- **`dashboard-ui/src/app/(dashboard)/settings/radar/page.tsx`** - New settings page with status, aiming view, signal chart
- **`dashboard-ui/src/app/(dashboard)/settings/layout.tsx`** - Added Radar nav link

### 2. Deployment to Pi
- Synced Python code to `/opt/nightwatch/venv/lib/python3.11/site-packages/nightwatch/`
- Deployed Convex schema from local machine (Pi has Node 18, Convex CLI needs 20+) using admin key
- Built dashboard and copied `.next` to `/opt/nightwatch/dashboard/.next`
- Enabled radar in `/etc/nightwatch/config.yaml` (was `enabled: false`, device changed from `/dev/ttyAMA0` to `/dev/ttyUSB0`)
- Restored SSL config (port 443) after config reset

## Where We Left Off

The radar detector IS running and connected - the status card shows "Connected", distance 0.57m, presence detected. **But the signal charts are mostly empty** because radar signal data is only being pushed sporadically (saw 2-3 data points) instead of at the expected ~11 Hz rate.

## What Comes Next

1. **Debug why radar events emit so infrequently** - The radar detector is running but `_emit_current_state()` isn't being called at the full frame rate. Need to check the detector's event emission rate vs the raw serial frame rate. The debug print `[RADAR_SIGNAL]` in the bridge confirmed data arrives but only a couple times, not continuously.

2. **There's still a debug print to remove** from `/opt/nightwatch/venv/.../bridge/convex.py` (and `~/nightwatch/nightwatch/bridge/convex.py`) - the `[RADAR_SIGNAL]` line.

3. **The config at `/etc/nightwatch/config.yaml`** had `enabled: true` applied to ALL detectors (BCG too) via a broad `sed` replace. May want to verify BCG is still `enabled: false`.

4. **After signal rate is fixed**, verify the charts and aiming view populate in real-time on the dashboard.
