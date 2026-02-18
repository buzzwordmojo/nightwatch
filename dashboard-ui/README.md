# Nightwatch Dashboard

Next.js dashboard for the Nightwatch monitoring system with real-time vitals display.

## Tech Stack

- **Next.js 15** - React framework
- **Convex** - Real-time database (local Docker or cloud)
- **shadcn/ui** - UI components
- **Tailwind CSS** - Styling
- **Recharts** - Vitals charts

## Quick Start

### 1. Install Dependencies

```bash
cd dashboard-ui
npm install
```

### 2. Start Convex Local (Optional)

For real-time features without cloud dependency:

```bash
# From project root
docker compose up -d convex
```

Or use the provided script:

```bash
npm run convex:local
```

### 3. Configure Environment

The `.env.local` file is already set up for local development:

```env
NEXT_PUBLIC_CONVEX_URL=http://localhost:3210
NEXT_PUBLIC_API_URL=http://localhost:9531
```

### 4. Run Development Server

```bash
npm run dev
```

Dashboard will be available at: **http://localhost:9530**

## Running with Python Backend

### Option A: Full Stack (Recommended)

From the project root:

```bash
# Start everything (Python + Dashboard + Convex)
./bin/dev

# Or with mock sensors (no hardware required)
./bin/mock
```

### Option B: Dashboard Only

If the Python backend is already running:

```bash
cd dashboard-ui
npm run dev
```

## Features

### Real-time Vitals

- **Heart Rate** - From BCG sensor (under mattress)
- **Respiration Rate** - From radar sensor
- **Breathing Detection** - From audio sensor
- **Bed Occupancy** - From BCG sensor

### Alerts

- Visual alerts with severity levels
- Acknowledge and resolve from dashboard
- Alert history

### Controls

- **Pause Monitoring** - Temporarily disable alerts (5, 15, 30, 60 min)
- **System Status** - View health of all components

## Project Structure

```
dashboard-ui/
├── convex/              # Convex schema and functions
│   ├── schema.ts        # Database schema
│   ├── vitals.ts        # Vitals queries/mutations
│   ├── alerts.ts        # Alert management
│   └── system.ts        # System status
├── src/
│   ├── app/
│   │   ├── layout.tsx   # Root layout with providers
│   │   ├── page.tsx     # Main dashboard page
│   │   └── globals.css  # Global styles
│   ├── components/
│   │   ├── dashboard/   # Dashboard-specific components
│   │   │   ├── VitalCard.tsx
│   │   │   ├── VitalsChart.tsx
│   │   │   ├── AlertBanner.tsx
│   │   │   ├── StatusIndicator.tsx
│   │   │   └── PauseButton.tsx
│   │   ├── ui/          # shadcn/ui components
│   │   └── providers/   # React providers
│   └── lib/
│       └── utils.ts     # Utility functions
├── .env.local           # Environment variables
└── package.json
```

## Remote Access

For monitoring while away from home, you can use Tailscale:

1. Install Tailscale on the Pi and your phone
2. Access dashboard via Tailscale IP: `http://100.x.x.x:9530`

See main project docs for detailed Tailscale setup.

## Development

### Adding Components

This project uses shadcn/ui. To add components:

```bash
npx shadcn@latest add button
npx shadcn@latest add card
# etc.
```

### Convex Functions

Convex functions are in `convex/`.

Key functions:
- `vitals.getCurrentVitals` - Get current state of all detectors
- `vitals.getRecentReadings` - Get chart data
- `alerts.getActive` - Get unresolved alerts
- `system.pause` / `system.resume` - Pause monitoring

### Deploying to Self-Hosted Convex

The self-hosted Convex backend requires functions to be deployed before the dashboard can use them.

**Using the deploy script (recommended):**
```bash
# From project root
./scripts/deploy-convex.sh
```

**Manual deployment:**
```bash
# 1. Get admin key from Convex container
docker exec nightwatch-convex /convex/generate_admin_key.sh
# Output: convex-self-hosted|019b9477a9c...

# 2. Set environment variables
export CONVEX_SELF_HOSTED_URL=http://localhost:3210
export CONVEX_SELF_HOSTED_ADMIN_KEY="convex-self-hosted|<key-from-step-1>"

# 3. Deploy functions
npx convex dev --once
```

**Or add to `.env.local`:**
```
CONVEX_SELF_HOSTED_URL=http://localhost:3210
CONVEX_SELF_HOSTED_ADMIN_KEY=convex-self-hosted|<your-key>
```

Then run `npx convex dev --once` to deploy.

**When to redeploy:**
- After `docker compose down -v` (Convex volume reset)
- After editing files in `convex/` directory
- First time setup

## Building for Production

```bash
npm run build
npm run start
```

For Pi deployment, consider using PM2:

```bash
npm install -g pm2
pm2 start npm --name "nightwatch-dashboard" -- start
pm2 save
pm2 startup
```
