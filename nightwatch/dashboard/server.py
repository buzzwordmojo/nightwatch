"""
Dashboard web server for Nightwatch.

Provides:
- Real-time vital signs display via WebSocket
- REST API for status, history, configuration
- Mobile-responsive web UI
"""

from __future__ import annotations

import asyncio
import json
import tempfile
import time
from pathlib import Path
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn

from nightwatch.core.config import DashboardConfig
from nightwatch.core.events import Event, Alert, EventBuffer
from nightwatch.core.engine import AlertEngine, AlertState, AlertLevel
from nightwatch.setup.first_boot import mark_configured


class ConnectionManager:
    """Manages WebSocket connections."""

    def __init__(self):
        self._connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections.append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self._connections:
            self._connections.remove(websocket)

    async def broadcast(self, message: dict[str, Any]) -> None:
        """Send message to all connected clients."""
        dead_connections = []

        for connection in self._connections:
            try:
                await connection.send_json(message)
            except Exception:
                dead_connections.append(connection)

        # Clean up dead connections
        for conn in dead_connections:
            self.disconnect(conn)

    @property
    def connection_count(self) -> int:
        return len(self._connections)


class DashboardServer:
    """
    Web dashboard server for Nightwatch monitoring.

    Provides real-time monitoring UI, REST API, and WebSocket updates.
    """

    def __init__(
        self,
        config: DashboardConfig | None = None,
        engine: AlertEngine | None = None,
        detectors: dict[str, Any] | None = None,
        mock_mode: bool = False,
    ):
        self._config = config or DashboardConfig()
        self._engine = engine
        self._detectors = detectors or {}
        self._mock_mode = mock_mode
        self._config_dir = (
            Path(tempfile.mkdtemp(prefix="nightwatch-setup-"))
            if mock_mode
            else Path("/etc/nightwatch")
        )
        self._app = FastAPI(
            title="Nightwatch Dashboard",
            description="Epilepsy monitoring system dashboard",
            version="0.1.0",
        )

        # CORS middleware for cloud proctor setup page
        @self._app.middleware("http")
        async def add_cors_headers(request, call_next):
            if request.method == "OPTIONS":
                response = Response()
                response.headers["Access-Control-Allow-Origin"] = "*"
                response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
                response.headers["Access-Control-Allow-Headers"] = "Content-Type"
                return response
            response = await call_next(request)
            response.headers["Access-Control-Allow-Origin"] = "*"
            return response

        self._ws_manager = ConnectionManager()
        self._event_buffer = EventBuffer(capacity=1000)
        self._running = False
        self._update_task: asyncio.Task | None = None

        # Simulator state
        self._sim_state: dict[str, Any] = {
            "active_scenario": None,
            "scenario_end_time": None,
            "breathing_rate": 14.0,
            "heart_rate": 70.0,
            "movement": 0.1,
            "presence": True,
        }
        self._scenario_task: asyncio.Task | None = None

        # Current state cache
        self._current_state: dict[str, Any] = {
            "respiration_rate": None,
            "heart_rate": None,
            "movement": 0,
            "presence": False,
            "alert_level": "ok",
            "active_alerts": [],
            "detector_status": {},
            "timestamp": time.time(),
        }

        self._setup_routes()

    @property
    def app(self) -> FastAPI:
        """Get FastAPI app instance."""
        return self._app

    def _setup_routes(self) -> None:
        """Configure all routes."""
        # Static files and templates
        static_dir = Path(__file__).parent / "static"
        templates_dir = Path(__file__).parent / "templates"

        if static_dir.exists():
            self._app.mount("/static", StaticFiles(directory=static_dir), name="static")

        # Only use templates if index.html exists
        index_template = templates_dir / "index.html"
        if index_template.exists():
            self._templates = Jinja2Templates(directory=templates_dir)
        else:
            self._templates = None

        # Routes
        self._app.get("/health")(self._health_check)
        self._app.get("/", response_class=HTMLResponse)(self._get_index)
        self._app.get("/api/status")(self._get_status)
        self._app.get("/api/alerts")(self._get_alerts)
        self._app.post("/api/alerts/{alert_id}/acknowledge")(self._acknowledge_alert)
        self._app.post("/api/alerts/{alert_id}/resolve")(self._resolve_alert)
        self._app.get("/api/history")(self._get_history)
        self._app.post("/api/pause")(self._pause)
        self._app.post("/api/resume")(self._resume)
        self._app.post("/api/test-alert")(self._test_alert)
        self._app.get("/api/config")(self._get_config)
        self._app.websocket("/ws")(self._websocket_endpoint)

        # Simulator routes (only in mock mode)
        self._app.get("/sim", response_class=HTMLResponse)(self._get_sim_page)
        self._app.get("/api/sim/status")(self._get_sim_status)
        self._app.post("/api/sim/scenario")(self._run_scenario)
        self._app.post("/api/sim/breathing")(self._set_breathing)
        self._app.post("/api/sim/heartrate")(self._set_heartrate)
        self._app.post("/api/sim/movement")(self._set_movement)
        self._app.post("/api/sim/presence")(self._set_presence)
        self._app.post("/api/sim/reset")(self._reset_sim)

        # Setup wizard routes (called by Next.js dashboard /setup pages)
        self._app.get("/api/setup/sensor-preview")(self._setup_sensor_preview)
        self._app.post("/api/setup/test-alert")(self._setup_test_alert)
        self._app.post("/api/setup/complete")(self._setup_complete)
        self._app.post("/api/setup/name")(self._setup_name)
        self._app.post("/api/setup/notifications")(self._setup_notifications)

    # ========================================================================
    # Health Check
    # ========================================================================

    async def _health_check(self) -> dict[str, Any]:
        """Health check endpoint for Docker/Kubernetes."""
        return {
            "status": "healthy",
            "running": self._running,
            "connections": self._ws_manager.connection_count,
        }

    # ========================================================================
    # Page Routes
    # ========================================================================

    async def _get_index(self, request: Request) -> HTMLResponse:
        """Serve main dashboard page."""
        if self._templates:
            return self._templates.TemplateResponse(
                "index.html",
                {"request": request, "state": self._current_state}
            )
        else:
            # Return inline HTML if no templates
            return HTMLResponse(content=self._get_inline_html())

    def _get_inline_html(self) -> str:
        """Generate inline HTML for dashboard."""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Nightwatch Dashboard</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #1a1a2e;
            color: #eee;
            min-height: 100vh;
        }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 20px 0;
            border-bottom: 1px solid #333;
            margin-bottom: 30px;
        }
        h1 { font-size: 24px; font-weight: 600; }
        .status-badge {
            padding: 8px 16px;
            border-radius: 20px;
            font-weight: 600;
            font-size: 14px;
        }
        .status-ok { background: #10b981; color: white; }
        .status-warning { background: #f59e0b; color: white; }
        .status-critical { background: #ef4444; color: white; animation: pulse 1s infinite; }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.7; }
        }
        .cards {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .card {
            background: #16213e;
            border-radius: 12px;
            padding: 24px;
            text-align: center;
            transition: background 0.3s ease, border-color 0.3s ease;
            border: 2px solid transparent;
        }
        .card.warning {
            background: linear-gradient(135deg, #78350f 0%, #16213e 100%);
            border-color: #f59e0b;
        }
        .card.critical {
            background: linear-gradient(135deg, #7f1d1d 0%, #16213e 100%);
            border-color: #ef4444;
            animation: pulse-card 1s infinite;
        }
        @keyframes pulse-card {
            0%, 100% { border-color: #ef4444; }
            50% { border-color: #fca5a5; }
        }
        .card-label {
            font-size: 14px;
            color: #888;
            margin-bottom: 8px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .card-value {
            font-size: 48px;
            font-weight: 700;
            color: #fff;
        }
        .card-unit {
            font-size: 16px;
            color: #888;
            margin-left: 4px;
        }
        .card-status {
            font-size: 14px;
            margin-top: 8px;
            color: #10b981;
        }
        .card-status.warning { color: #f59e0b; }
        .card-status.alert { color: #ef4444; }
        .charts-section {
            background: #16213e;
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 30px;
        }
        .charts-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            flex-wrap: wrap;
            gap: 12px;
        }
        .time-tabs {
            display: flex;
            gap: 4px;
        }
        .time-tab {
            padding: 6px 12px;
            border: none;
            border-radius: 4px;
            background: transparent;
            color: #666;
            font-size: 12px;
            cursor: pointer;
            transition: all 0.2s;
        }
        .time-tab:hover { color: #888; }
        .time-tab.active { background: #374151; color: white; }
        .chart-title {
            font-size: 16px;
            font-weight: 600;
            color: #fff;
        }
        .chart-container {
            position: relative;
            height: 200px;
        }
        .chart-legend {
            display: flex;
            justify-content: center;
            gap: 24px;
            margin-top: 12px;
            font-size: 13px;
            color: #888;
        }
        .legend-item {
            display: flex;
            align-items: center;
            gap: 6px;
        }
        .legend-dot {
            width: 10px;
            height: 10px;
            border-radius: 50%;
        }
        .legend-dot.breathing { background: #3b82f6; }
        .legend-dot.heartrate { background: #8b5cf6; }
        .legend-dot.movement { background: #10b981; }
        .events {
            background: #16213e;
            border-radius: 12px;
            padding: 24px;
        }
        .events-title {
            font-size: 16px;
            color: #888;
            margin-bottom: 16px;
        }
        .event-item {
            display: flex;
            align-items: center;
            padding: 12px 0;
            border-bottom: 1px solid #333;
        }
        .event-item:last-child { border-bottom: none; }
        .event-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #10b981;
            margin-right: 12px;
        }
        .event-dot.warning { background: #f59e0b; }
        .event-dot.alert { background: #ef4444; }
        .event-time {
            color: #888;
            font-size: 14px;
            margin-left: auto;
        }
        .controls {
            display: flex;
            gap: 12px;
            margin-top: 30px;
        }
        button {
            padding: 12px 24px;
            border: none;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: background 0.2s;
        }
        .btn-primary { background: #3b82f6; color: white; }
        .btn-primary:hover { background: #2563eb; }
        .btn-secondary { background: #374151; color: white; }
        .btn-secondary:hover { background: #4b5563; }
        .btn-danger { background: #ef4444; color: white; }
        .btn-danger:hover { background: #dc2626; }
        .connection-status {
            position: fixed;
            bottom: 20px;
            right: 20px;
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 12px;
            background: #10b981;
            color: white;
        }
        .connection-status.disconnected {
            background: #ef4444;
        }
        .no-data { color: #666; font-style: italic; }
    </style>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chartjs-adapter-date-fns"></script>
</head>
<body>
    <div class="container">
        <header>
            <h1>Nightwatch</h1>
            <div id="status-badge" class="status-badge status-ok">All Normal</div>
        </header>

        <div class="cards">
            <div class="card">
                <div class="card-label">Breathing</div>
                <div class="card-value">
                    <span id="respiration-value">--</span>
                    <span class="card-unit">BPM</span>
                </div>
                <div id="respiration-status" class="card-status">normal</div>
            </div>
            <div class="card">
                <div class="card-label">Heart Rate</div>
                <div class="card-value">
                    <span id="heartrate-value">--</span>
                    <span class="card-unit">BPM</span>
                </div>
                <div id="heartrate-status" class="card-status">normal</div>
            </div>
            <div class="card">
                <div class="card-label">Movement</div>
                <div class="card-value">
                    <span id="movement-value">Low</span>
                </div>
                <div id="movement-status" class="card-status">sleeping</div>
            </div>
        </div>

        <div class="charts-section">
            <div class="charts-header">
                <div class="chart-title">Vital Signs</div>
                <div class="time-tabs">
                    <button class="time-tab active" onclick="selectTimeRange(1)">1m</button>
                    <button class="time-tab" onclick="selectTimeRange(5)">5m</button>
                    <button class="time-tab" onclick="selectTimeRange(15)">15m</button>
                    <button class="time-tab" onclick="selectTimeRange(30)">30m</button>
                    <button class="time-tab" onclick="selectTimeRange(60)">60m</button>
                </div>
            </div>
            <div class="chart-container">
                <canvas id="vitals-chart"></canvas>
            </div>
            <div class="chart-legend">
                <span class="legend-item"><span class="legend-dot breathing"></span> Breathing</span>
                <span class="legend-item"><span class="legend-dot heartrate"></span> Heart Rate</span>
                <span class="legend-item"><span class="legend-dot movement"></span> Movement</span>
            </div>
        </div>

        <div class="events">
            <div class="events-title">Recent Events</div>
            <div id="events-list">
                <div class="event-item">
                    <div class="event-dot"></div>
                    <span>Monitoring started</span>
                    <span class="event-time">just now</span>
                </div>
            </div>
        </div>

        <div class="controls">
            <button class="btn-secondary" onclick="testAlert()">Test Alert</button>
            <button class="btn-secondary" onclick="pauseMonitoring()">Pause 30m</button>
        </div>
    </div>

    <div id="connection-status" class="connection-status">Connected</div>

    <script>
        let ws;
        let vitalsChart;

        // Chart data - store with timestamps
        const chartData = {
            breathing: [],
            heartrate: [],
            movement: []
        };
        const maxDataPoints = 3600;  // 1 hour at 1 sample/sec

        // Chart state
        let currentTimeRange = 1;  // minutes

        function initChart() {
            console.log('Initializing chart...');
            const canvas = document.getElementById('vitals-chart');
            console.log('Canvas element:', canvas);
            const ctx = canvas.getContext('2d');
            console.log('Canvas context:', ctx);
            vitalsChart = new Chart(ctx, {
                type: 'line',
                data: {
                    datasets: [
                        {
                            label: 'Breathing (BPM)',
                            data: [],
                            borderColor: '#3b82f6',
                            backgroundColor: 'rgba(59, 130, 246, 0.1)',
                            fill: false,
                            tension: 0.3,
                            pointRadius: 0,
                            borderWidth: 2,
                            yAxisID: 'y'
                        },
                        {
                            label: 'Heart Rate (BPM)',
                            data: [],
                            borderColor: '#8b5cf6',
                            backgroundColor: 'rgba(139, 92, 246, 0.1)',
                            fill: false,
                            tension: 0.3,
                            pointRadius: 0,
                            borderWidth: 2,
                            yAxisID: 'y1'
                        },
                        {
                            label: 'Movement',
                            data: [],
                            borderColor: '#10b981',
                            backgroundColor: 'rgba(16, 185, 129, 0.1)',
                            fill: false,
                            tension: 0.3,
                            pointRadius: 0,
                            borderWidth: 2,
                            yAxisID: 'y2'
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    animation: { duration: 0 },
                    interaction: { intersect: false, mode: 'index' },
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            callbacks: {
                                label: function(ctx) {
                                    const label = ctx.dataset.label;
                                    const val = ctx.parsed.y;
                                    if (label.includes('Movement')) return 'Movement: ' + (val * 100).toFixed(0) + '%';
                                    return label.split(' ')[0] + ': ' + val.toFixed(1) + ' BPM';
                                }
                            }
                        }
                    },
                    scales: {
                        x: {
                            type: 'time',
                            time: { unit: 'second', displayFormats: { second: 'HH:mm:ss' } },
                            grid: { color: '#333' },
                            ticks: { color: '#888', maxTicksLimit: 6 }
                        },
                        y: {
                            type: 'linear',
                            position: 'left',
                            min: 0,
                            max: 30,
                            grid: { color: '#333' },
                            ticks: { color: '#3b82f6', stepSize: 10 },
                            title: { display: false }
                        },
                        y1: {
                            type: 'linear',
                            position: 'right',
                            min: 40,
                            max: 140,
                            grid: { drawOnChartArea: false },
                            ticks: { color: '#8b5cf6', stepSize: 20 },
                            title: { display: false }
                        },
                        y2: {
                            type: 'linear',
                            position: 'right',
                            min: 0,
                            max: 1,
                            display: false  // Hidden - movement uses left scale conceptually
                        }
                    }
                }
            });
        }

        function connect() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            ws = new WebSocket(`${protocol}//${window.location.host}/ws`);

            ws.onopen = () => {
                document.getElementById('connection-status').textContent = 'Connected';
                document.getElementById('connection-status').classList.remove('disconnected');
            };

            ws.onclose = () => {
                document.getElementById('connection-status').textContent = 'Disconnected';
                document.getElementById('connection-status').classList.add('disconnected');
                setTimeout(connect, 3000);
            };

            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                updateDisplay(data);
            };
        }

        function updateDisplay(data) {
            const now = Date.now();
            const resp = data.respiration_rate;
            const hr = data.heart_rate;
            const movement = data.movement;

            // Store data with timestamps
            if (resp !== null && resp !== undefined) {
                chartData.breathing.push({ x: now, y: resp });
                if (chartData.breathing.length > maxDataPoints) chartData.breathing.shift();
            }
            if (hr !== null && hr !== undefined) {
                chartData.heartrate.push({ x: now, y: hr });
                if (chartData.heartrate.length > maxDataPoints) chartData.heartrate.shift();
            }
            if (movement !== null && movement !== undefined) {
                chartData.movement.push({ x: now, y: movement });
                if (chartData.movement.length > maxDataPoints) chartData.movement.shift();
            }

            // Update vital signs display
            document.getElementById('respiration-value').textContent =
                resp !== null && resp !== undefined ? Math.round(resp) : '--';
            document.getElementById('heartrate-value').textContent =
                hr !== null && hr !== undefined ? Math.round(hr) : '--';

            // Movement level
            let movementText = 'Low';
            if (movement > 0.7) movementText = 'High';
            else if (movement > 0.3) movementText = 'Medium';
            document.getElementById('movement-value').textContent = movementText;

            // Status badge
            const badge = document.getElementById('status-badge');
            const level = data.alert_level || 'ok';
            badge.className = 'status-badge status-' + level;
            badge.textContent = level === 'ok' ? 'All Normal' :
                               level === 'warning' ? 'Warning' : 'ALERT';

            // Respiration status
            const respStatus = document.getElementById('respiration-status');
            if (resp === null || resp === undefined) {
                respStatus.textContent = 'no data';
                respStatus.className = 'card-status';
            } else if (resp < 6) {
                respStatus.textContent = 'critical';
                respStatus.className = 'card-status alert';
            } else if (resp < 10) {
                respStatus.textContent = 'low';
                respStatus.className = 'card-status warning';
            } else {
                respStatus.textContent = 'normal';
                respStatus.className = 'card-status';
            }

            // Heart rate status
            const hrStatus = document.getElementById('heartrate-status');
            if (hr === null || hr === undefined) {
                hrStatus.textContent = 'no data';
                hrStatus.className = 'card-status';
            } else if (hr < 40 || hr > 150) {
                hrStatus.textContent = 'critical';
                hrStatus.className = 'card-status alert';
            } else if (hr < 50 || hr > 120) {
                hrStatus.textContent = 'abnormal';
                hrStatus.className = 'card-status warning';
            } else {
                hrStatus.textContent = 'normal';
                hrStatus.className = 'card-status';
            }

            // Movement status
            const movStatus = document.getElementById('movement-status');
            if (movement > 0.8) {
                movStatus.textContent = 'active';
                movStatus.className = 'card-status warning';
            } else {
                movStatus.textContent = 'sleeping';
                movStatus.className = 'card-status';
            }

            // Update chart
            updateChart();

            // Update events
            if (data.recent_events && data.recent_events.length > 0) {
                updateEvents(data.recent_events);
            }
        }

        function selectTimeRange(minutes) {
            currentTimeRange = minutes;
            document.querySelectorAll('.time-tab').forEach(tab => {
                tab.classList.toggle('active', tab.textContent === minutes + 'm');
            });
            updateChart();
        }

        function updateChart() {
            if (!vitalsChart) return;

            const now = Date.now();
            const cutoff = now - (currentTimeRange * 60 * 1000);

            // Filter data for each dataset
            vitalsChart.data.datasets[0].data = chartData.breathing.filter(d => d.x >= cutoff);
            vitalsChart.data.datasets[1].data = chartData.heartrate.filter(d => d.x >= cutoff);
            vitalsChart.data.datasets[2].data = chartData.movement.filter(d => d.x >= cutoff);

            vitalsChart.options.scales.x.min = cutoff;
            vitalsChart.options.scales.x.max = now;

            // Adjust time unit based on range
            if (currentTimeRange <= 1) {
                vitalsChart.options.scales.x.time.unit = 'second';
            } else {
                vitalsChart.options.scales.x.time.unit = 'minute';
            }

            vitalsChart.update('none');
        }

        function updateEvents(events) {
            const list = document.getElementById('events-list');
            list.innerHTML = events.slice(0, 5).map(e => {
                const dotClass = e.state === 'alert' ? 'alert' :
                                e.state === 'warning' ? 'warning' : '';
                const time = new Date(e.timestamp * 1000).toLocaleTimeString();
                return `
                    <div class="event-item">
                        <div class="event-dot ${dotClass}"></div>
                        <span>${e.message || e.detector + ': ' + e.state}</span>
                        <span class="event-time">${time}</span>
                    </div>
                `;
            }).join('');
        }

        async function testAlert() {
            await fetch('/api/test-alert', { method: 'POST' });
        }

        async function pauseMonitoring() {
            await fetch('/api/pause', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ duration_minutes: 30 })
            });
        }

        // Initialize on page load
        initChart();
        connect();
    </script>
</body>
</html>
"""

    # ========================================================================
    # API Routes
    # ========================================================================

    async def _get_status(self) -> dict[str, Any]:
        """Get current monitoring status."""
        return {
            "status": "ok",
            "data": self._current_state,
            "timestamp": time.time(),
        }

    async def _get_alerts(self, limit: int = 50) -> dict[str, Any]:
        """Get active and recent alerts."""
        active = []
        history = []

        if self._engine:
            state = self._engine.get_state()
            active = [a.to_dict() for a in state.active_alerts]
            # history would come from AlertManager

        return {
            "active": active,
            "history": history,
        }

    async def _acknowledge_alert(self, alert_id: str) -> dict[str, Any]:
        """Acknowledge an alert."""
        if not self._engine:
            raise HTTPException(status_code=503, detail="Engine not available")

        success = self._engine.acknowledge_alert(alert_id)
        if not success:
            raise HTTPException(status_code=404, detail="Alert not found")

        return {"status": "acknowledged", "alert_id": alert_id}

    async def _resolve_alert(self, alert_id: str) -> dict[str, Any]:
        """Resolve an alert."""
        if not self._engine:
            raise HTTPException(status_code=503, detail="Engine not available")

        success = self._engine.resolve_alert(alert_id)
        if not success:
            raise HTTPException(status_code=404, detail="Alert not found")

        return {"status": "resolved", "alert_id": alert_id}

    async def _get_history(
        self,
        signal: str = "respiration_rate",
        minutes: int = 60,
    ) -> dict[str, Any]:
        """Get historical data for a signal."""
        # Get recent events from buffer
        events = self._event_buffer.get_recent(minutes * 60)

        data_points = []
        for event in events:
            value = event.value.get(signal)
            if value is not None:
                data_points.append({
                    "timestamp": event.timestamp,
                    "value": value,
                })

        return {
            "signal": signal,
            "data": data_points,
            "count": len(data_points),
        }

    async def _pause(self, request: Request) -> dict[str, Any]:
        """Pause monitoring for specified duration."""
        body = await request.json()
        duration_minutes = body.get("duration_minutes", 30)

        if self._engine:
            self._engine.pause(duration_minutes * 60)

        return {
            "status": "paused",
            "duration_minutes": duration_minutes,
            "expires": time.time() + (duration_minutes * 60),
        }

    async def _resume(self) -> dict[str, Any]:
        """Resume monitoring."""
        if self._engine:
            self._engine.resume()

        return {"status": "resumed"}

    async def _test_alert(self) -> dict[str, Any]:
        """Trigger a test alert."""
        # Broadcast test alert via WebSocket
        await self._ws_manager.broadcast({
            "type": "test_alert",
            "message": "This is a test alert",
            "timestamp": time.time(),
        })

        return {"status": "test_alert_sent"}

    async def _get_config(self) -> dict[str, Any]:
        """Get current configuration."""
        return {
            "dashboard": {
                "host": self._config.host,
                "port": self._config.port,
                "websocket_update_interval_ms": self._config.websocket_update_interval_ms,
            }
        }

    # ========================================================================
    # Setup Wizard Endpoints
    # ========================================================================

    async def _setup_sensor_preview(self) -> dict[str, Any]:
        """Return sensor detection status for the setup wizard."""
        if self._mock_mode:
            return {
                "radar": {"detected": True, "signal": 85},
                "audio": {"detected": True},
                "bcg": {"detected": False},
            }

        # In production, check actual detectors
        result = {}
        for name, detector in self._detectors.items():
            detected = hasattr(detector, "is_running") and detector.is_running
            entry: dict[str, Any] = {"detected": detected}
            if name == "radar" and hasattr(detector, "signal_strength"):
                entry["signal"] = detector.signal_strength
            result[name] = entry
        return result

    async def _setup_test_alert(self) -> dict[str, Any]:
        """Simulate a test alert during setup."""
        if self._mock_mode:
            await asyncio.sleep(2)
            return {"success": True}

        # In production, trigger real alert through existing logic
        await self._ws_manager.broadcast({
            "type": "test_alert",
            "message": "This is a test alert",
            "timestamp": time.time(),
        })
        return {"success": True}

    async def _setup_complete(self, request: Request) -> dict[str, Any]:
        """Mark setup as complete and save all config."""
        body = await request.json()

        self._config_dir.mkdir(parents=True, exist_ok=True)

        # Save monitor name
        monitor_name = body.get("monitorName", "")
        if monitor_name:
            (self._config_dir / "monitor_name").write_text(monitor_name)

        # Save notifications config
        notifications = body.get("notifications", {})
        (self._config_dir / "notifications.json").write_text(
            json.dumps(notifications)
        )

        # Save setup summary
        (self._config_dir / "setup_summary.json").write_text(
            json.dumps({
                "monitorName": monitor_name,
                "sensorsConfirmed": body.get("sensorsConfirmed", False),
                "notifications": notifications,
                "testCompleted": body.get("testCompleted", False),
                "completedAt": time.time(),
            })
        )

        # Mark as configured
        mark_configured(self._config_dir)

        return {"success": True}

    async def _setup_name(self, request: Request) -> dict[str, Any]:
        """Save monitor name."""
        body = await request.json()
        name = body.get("name", "").strip()

        if len(name) < 2:
            raise HTTPException(status_code=422, detail="Name must be at least 2 characters")

        self._config_dir.mkdir(parents=True, exist_ok=True)
        (self._config_dir / "monitor_name").write_text(name)

        return {"success": True, "name": name}

    async def _setup_notifications(self, request: Request) -> dict[str, Any]:
        """Save notification preferences."""
        body = await request.json()

        self._config_dir.mkdir(parents=True, exist_ok=True)
        (self._config_dir / "notifications.json").write_text(json.dumps(body))

        return {"success": True}

    # ========================================================================
    # Simulator
    # ========================================================================

    def _check_mock_mode(self) -> None:
        """Raise 404 if not in mock mode."""
        if not self._mock_mode:
            raise HTTPException(
                status_code=404,
                detail="Simulator only available in mock mode (--mock-sensors)"
            )

    async def _get_sim_page(self, request: Request) -> HTMLResponse:
        """Serve the simulator control page."""
        self._check_mock_mode()
        return HTMLResponse(content=self._get_sim_html())

    async def _get_sim_status(self) -> dict[str, Any]:
        """Get current simulator state."""
        self._check_mock_mode()
        return {
            "mock_mode": self._mock_mode,
            "detectors": list(self._detectors.keys()),
            **self._sim_state,
        }

    async def _run_scenario(self, request: Request) -> dict[str, Any]:
        """Run a predefined scenario."""
        self._check_mock_mode()
        body = await request.json()
        scenario = body.get("scenario", "normal")
        duration = body.get("duration")

        # Cancel any existing scenario
        if self._scenario_task and not self._scenario_task.done():
            self._scenario_task.cancel()

        scenarios = {
            "normal": {"breathing": 14, "heart_rate": 70, "movement": 0.1, "presence": True, "duration": 0},
            "apnea": {"breathing": 0, "heart_rate": 70, "movement": 0, "presence": True, "duration": duration or 10},
            "bradycardia": {"breathing": 14, "heart_rate": 40, "movement": 0.1, "presence": True, "duration": duration or 30},
            "tachycardia": {"breathing": 14, "heart_rate": 140, "movement": 0.3, "presence": True, "duration": duration or 30},
            "seizure": {"breathing": 20, "heart_rate": 150, "movement": 0.95, "presence": True, "duration": duration or 15},
            "empty_bed": {"breathing": 0, "heart_rate": 0, "movement": 0, "presence": False, "duration": 0},
        }

        if scenario not in scenarios:
            raise HTTPException(status_code=400, detail=f"Unknown scenario: {scenario}")

        params = scenarios[scenario]
        self._apply_sim_values(
            breathing=params["breathing"],
            heart_rate=params["heart_rate"],
            movement=params["movement"],
            presence=params["presence"],
        )

        self._sim_state["active_scenario"] = scenario
        scenario_duration = params["duration"]

        if scenario_duration > 0:
            self._sim_state["scenario_end_time"] = time.time() + scenario_duration
            self._scenario_task = asyncio.create_task(
                self._scenario_auto_reset(scenario_duration)
            )
        else:
            self._sim_state["scenario_end_time"] = None

        return {
            "status": "scenario_started",
            "scenario": scenario,
            "duration": scenario_duration,
            "auto_reset": scenario_duration > 0,
        }

    async def _scenario_auto_reset(self, duration: float) -> None:
        """Auto-reset to normal after scenario duration."""
        await asyncio.sleep(duration)
        self._apply_sim_values(breathing=14, heart_rate=70, movement=0.1, presence=True)
        self._sim_state["active_scenario"] = None
        self._sim_state["scenario_end_time"] = None

    def _apply_sim_values(
        self,
        breathing: float | None = None,
        heart_rate: float | None = None,
        movement: float | None = None,
        presence: bool | None = None,
    ) -> None:
        """Apply simulation values to mock detectors."""
        if breathing is not None:
            self._sim_state["breathing_rate"] = breathing
            # MockRadarDetector uses _base_respiration_rate
            if "radar" in self._detectors:
                radar = self._detectors["radar"]
                if hasattr(radar, "_base_respiration_rate"):
                    radar._base_respiration_rate = breathing
                # Use inject_anomaly for apnea (reduces amplitude)
                if breathing == 0 and hasattr(radar, "inject_anomaly"):
                    radar.inject_anomaly("apnea", duration=9999)
                elif breathing > 0 and hasattr(radar, "_anomaly_type"):
                    radar._anomaly_type = None
            # MockBCGDetector also has respiration
            if "bcg" in self._detectors:
                bcg = self._detectors["bcg"]
                if hasattr(bcg, "_base_respiration_rate"):
                    bcg._base_respiration_rate = breathing

        if heart_rate is not None:
            self._sim_state["heart_rate"] = heart_rate
            # MockBCGDetector uses _base_heart_rate
            if "bcg" in self._detectors:
                bcg = self._detectors["bcg"]
                if hasattr(bcg, "_base_heart_rate"):
                    bcg._base_heart_rate = heart_rate
                # Reset injection flags when setting direct value
                if hasattr(bcg, "_inject_bradycardia"):
                    bcg._inject_bradycardia = False
                if hasattr(bcg, "_inject_tachycardia"):
                    bcg._inject_tachycardia = False

        if movement is not None:
            self._sim_state["movement"] = movement
            if "bcg" in self._detectors:
                bcg = self._detectors["bcg"]
                if hasattr(bcg, "_movement"):
                    bcg._movement = movement > 0.5

        if presence is not None:
            self._sim_state["presence"] = presence
            if "bcg" in self._detectors:
                bcg = self._detectors["bcg"]
                if hasattr(bcg, "_bed_occupied"):
                    bcg._bed_occupied = presence

    async def _set_breathing(self, request: Request) -> dict[str, Any]:
        """Set breathing rate."""
        self._check_mock_mode()
        body = await request.json()
        rate = float(body.get("rate", 14))
        rate = max(0, min(40, rate))
        self._apply_sim_values(breathing=rate)
        self._sim_state["active_scenario"] = None
        return {"status": "ok", "breathing_rate": rate}

    async def _set_heartrate(self, request: Request) -> dict[str, Any]:
        """Set heart rate."""
        self._check_mock_mode()
        body = await request.json()
        rate = float(body.get("rate", 70))
        rate = max(0, min(200, rate))
        self._apply_sim_values(heart_rate=rate)
        self._sim_state["active_scenario"] = None
        return {"status": "ok", "heart_rate": rate}

    async def _set_movement(self, request: Request) -> dict[str, Any]:
        """Set movement level."""
        self._check_mock_mode()
        body = await request.json()
        level = float(body.get("level", 0.1))
        level = max(0, min(1, level))
        self._apply_sim_values(movement=level)
        self._sim_state["active_scenario"] = None
        return {"status": "ok", "movement": level}

    async def _set_presence(self, request: Request) -> dict[str, Any]:
        """Set bed presence."""
        self._check_mock_mode()
        body = await request.json()
        present = bool(body.get("present", True))
        self._apply_sim_values(presence=present)
        self._sim_state["active_scenario"] = None
        return {"status": "ok", "presence": present}

    async def _reset_sim(self) -> dict[str, Any]:
        """Reset simulator to normal values."""
        self._check_mock_mode()
        if self._scenario_task and not self._scenario_task.done():
            self._scenario_task.cancel()
        self._apply_sim_values(breathing=14, heart_rate=70, movement=0.1, presence=True)
        self._sim_state["active_scenario"] = None
        self._sim_state["scenario_end_time"] = None
        return {"status": "reset"}

    def _get_sim_html(self) -> str:
        """Generate inline HTML for simulator page."""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Nightwatch Simulator</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #1a1a2e;
            color: #eee;
            min-height: 100vh;
            padding: 20px;
        }
        .container { max-width: 600px; margin: 0 auto; }
        header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 20px 0;
            border-bottom: 1px solid #333;
            margin-bottom: 30px;
        }
        h1 { font-size: 24px; font-weight: 600; }
        .mock-badge {
            background: #8b5cf6;
            color: white;
            padding: 6px 12px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 600;
        }
        .section {
            background: #16213e;
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 20px;
        }
        .section-title {
            font-size: 14px;
            color: #888;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 20px;
        }
        .slider-group {
            margin-bottom: 24px;
        }
        .slider-group:last-child { margin-bottom: 0; }
        .slider-label {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
        }
        .slider-name { font-weight: 500; }
        .slider-value {
            font-weight: 700;
            color: #3b82f6;
            min-width: 80px;
            text-align: right;
        }
        input[type="range"] {
            width: 100%;
            height: 8px;
            border-radius: 4px;
            background: #333;
            outline: none;
            -webkit-appearance: none;
        }
        input[type="range"]::-webkit-slider-thumb {
            -webkit-appearance: none;
            width: 20px;
            height: 20px;
            border-radius: 50%;
            background: #3b82f6;
            cursor: pointer;
        }
        .checkbox-group {
            display: flex;
            align-items: center;
            gap: 12px;
        }
        .checkbox-group input {
            width: 20px;
            height: 20px;
            accent-color: #3b82f6;
        }
        .scenarios {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 12px;
        }
        .scenario-btn {
            padding: 16px 12px;
            border: none;
            border-radius: 8px;
            font-size: 13px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
            text-align: center;
        }
        .scenario-btn.normal { background: #10b981; color: white; }
        .scenario-btn.normal:hover { background: #059669; }
        .scenario-btn.warning { background: #f59e0b; color: white; }
        .scenario-btn.warning:hover { background: #d97706; }
        .scenario-btn.danger { background: #ef4444; color: white; }
        .scenario-btn.danger:hover { background: #dc2626; }
        .scenario-btn.neutral { background: #6b7280; color: white; }
        .scenario-btn.neutral:hover { background: #4b5563; }
        .scenario-btn.active {
            box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.5);
        }
        .scenario-duration {
            font-size: 11px;
            opacity: 0.8;
            margin-top: 4px;
        }
        .reset-btn {
            width: 100%;
            padding: 16px;
            border: 2px solid #3b82f6;
            border-radius: 8px;
            background: transparent;
            color: #3b82f6;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
            margin-top: 20px;
        }
        .reset-btn:hover {
            background: #3b82f6;
            color: white;
        }
        .status-bar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 16px 20px;
            background: #16213e;
            border-radius: 12px;
            margin-top: 20px;
        }
        .status-label { color: #888; }
        .status-value { font-weight: 600; }
        .status-value.active { color: #f59e0b; }
        .status-value.normal { color: #10b981; }
        .countdown { color: #f59e0b; font-weight: 600; }
        .dashboard-link {
            display: block;
            text-align: center;
            color: #3b82f6;
            text-decoration: none;
            margin-top: 20px;
            font-weight: 500;
        }
        .dashboard-link:hover { text-decoration: underline; }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Nightwatch Simulator</h1>
            <span class="mock-badge">Mock Mode</span>
        </header>

        <div class="section">
            <div class="section-title">Vital Signs</div>

            <div class="slider-group">
                <div class="slider-label">
                    <span class="slider-name">Breathing Rate</span>
                    <span class="slider-value" id="breathing-value">14 BPM</span>
                </div>
                <input type="range" id="breathing-slider" min="0" max="40" value="14" step="1">
            </div>

            <div class="slider-group">
                <div class="slider-label">
                    <span class="slider-name">Heart Rate</span>
                    <span class="slider-value" id="heartrate-value">70 BPM</span>
                </div>
                <input type="range" id="heartrate-slider" min="0" max="200" value="70" step="1">
            </div>

            <div class="slider-group">
                <div class="slider-label">
                    <span class="slider-name">Movement</span>
                    <span class="slider-value" id="movement-value">Low</span>
                </div>
                <input type="range" id="movement-slider" min="0" max="100" value="10" step="1">
            </div>

            <div class="checkbox-group">
                <input type="checkbox" id="presence-checkbox" checked>
                <label for="presence-checkbox">Person in bed</label>
            </div>
        </div>

        <div class="section">
            <div class="section-title">Quick Scenarios</div>
            <div class="scenarios">
                <button class="scenario-btn warning" onclick="runScenario('apnea')">
                    Apnea
                    <div class="scenario-duration">10 sec</div>
                </button>
                <button class="scenario-btn danger" onclick="runScenario('bradycardia')">
                    Bradycardia
                    <div class="scenario-duration">30 sec</div>
                </button>
                <button class="scenario-btn danger" onclick="runScenario('tachycardia')">
                    Tachycardia
                    <div class="scenario-duration">30 sec</div>
                </button>
                <button class="scenario-btn danger" onclick="runScenario('seizure')">
                    Seizure
                    <div class="scenario-duration">15 sec</div>
                </button>
                <button class="scenario-btn neutral" onclick="runScenario('empty_bed')">
                    Empty Bed
                    <div class="scenario-duration">manual</div>
                </button>
                <button class="scenario-btn normal" onclick="runScenario('normal')">
                    Normal
                    <div class="scenario-duration">baseline</div>
                </button>
            </div>
            <button class="reset-btn" onclick="resetSim()">Reset to Normal</button>
        </div>

        <div class="status-bar">
            <div>
                <span class="status-label">Status: </span>
                <span class="status-value" id="status-text">Normal</span>
            </div>
            <div>
                <span class="status-label">Scenario: </span>
                <span class="status-value" id="scenario-text">None</span>
                <span class="countdown" id="countdown"></span>
            </div>
        </div>

        <a href="/" class="dashboard-link" target="_blank">Open Dashboard in New Window</a>
    </div>

    <script>
        let countdownInterval = null;

        // Slider handlers
        document.getElementById('breathing-slider').addEventListener('input', async (e) => {
            const val = e.target.value;
            document.getElementById('breathing-value').textContent = val + ' BPM';
            await fetch('/api/sim/breathing', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ rate: parseFloat(val) })
            });
            updateStatus();
        });

        document.getElementById('heartrate-slider').addEventListener('input', async (e) => {
            const val = e.target.value;
            document.getElementById('heartrate-value').textContent = val + ' BPM';
            await fetch('/api/sim/heartrate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ rate: parseFloat(val) })
            });
            updateStatus();
        });

        document.getElementById('movement-slider').addEventListener('input', async (e) => {
            const val = e.target.value;
            const level = val / 100;
            let text = 'Low';
            if (level > 0.7) text = 'High';
            else if (level > 0.3) text = 'Medium';
            document.getElementById('movement-value').textContent = text;
            await fetch('/api/sim/movement', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ level: level })
            });
            updateStatus();
        });

        document.getElementById('presence-checkbox').addEventListener('change', async (e) => {
            await fetch('/api/sim/presence', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ present: e.target.checked })
            });
            updateStatus();
        });

        async function runScenario(scenario) {
            const resp = await fetch('/api/sim/scenario', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ scenario: scenario })
            });
            const data = await resp.json();

            document.getElementById('scenario-text').textContent = scenario;
            document.getElementById('scenario-text').className = 'status-value active';

            // Update sliders to match scenario
            await refreshState();

            // Start countdown if auto-reset
            if (data.auto_reset && data.duration > 0) {
                startCountdown(data.duration);
            } else {
                clearCountdown();
            }
        }

        async function resetSim() {
            await fetch('/api/sim/reset', { method: 'POST' });
            clearCountdown();
            await refreshState();
        }

        async function refreshState() {
            const resp = await fetch('/api/sim/status');
            const data = await resp.json();

            document.getElementById('breathing-slider').value = data.breathing_rate;
            document.getElementById('breathing-value').textContent = data.breathing_rate + ' BPM';

            document.getElementById('heartrate-slider').value = data.heart_rate;
            document.getElementById('heartrate-value').textContent = data.heart_rate + ' BPM';

            const movement = data.movement * 100;
            document.getElementById('movement-slider').value = movement;
            let movementText = 'Low';
            if (data.movement > 0.7) movementText = 'High';
            else if (data.movement > 0.3) movementText = 'Medium';
            document.getElementById('movement-value').textContent = movementText;

            document.getElementById('presence-checkbox').checked = data.presence;

            updateStatus();

            if (data.active_scenario) {
                document.getElementById('scenario-text').textContent = data.active_scenario;
                document.getElementById('scenario-text').className = 'status-value active';
            } else {
                document.getElementById('scenario-text').textContent = 'None';
                document.getElementById('scenario-text').className = 'status-value';
            }
        }

        function updateStatus() {
            const breathing = parseFloat(document.getElementById('breathing-slider').value);
            const heartrate = parseFloat(document.getElementById('heartrate-slider').value);
            const presence = document.getElementById('presence-checkbox').checked;

            let status = 'Normal';
            let statusClass = 'normal';

            if (!presence) {
                status = 'Empty Bed';
                statusClass = '';
            } else if (breathing < 6 || heartrate < 40 || heartrate > 150) {
                status = 'Critical';
                statusClass = 'active';
            } else if (breathing < 10 || heartrate < 50 || heartrate > 120) {
                status = 'Warning';
                statusClass = 'active';
            }

            document.getElementById('status-text').textContent = status;
            document.getElementById('status-text').className = 'status-value ' + statusClass;
        }

        function startCountdown(seconds) {
            clearCountdown();
            let remaining = seconds;
            const el = document.getElementById('countdown');
            el.textContent = ' (' + remaining + 's)';

            countdownInterval = setInterval(() => {
                remaining--;
                if (remaining <= 0) {
                    clearCountdown();
                    refreshState();
                } else {
                    el.textContent = ' (' + remaining + 's)';
                }
            }, 1000);
        }

        function clearCountdown() {
            if (countdownInterval) {
                clearInterval(countdownInterval);
                countdownInterval = null;
            }
            document.getElementById('countdown').textContent = '';
        }

        // Initial state
        refreshState();
    </script>
</body>
</html>
"""

    # ========================================================================
    # WebSocket
    # ========================================================================

    async def _websocket_endpoint(self, websocket: WebSocket) -> None:
        """Handle WebSocket connections."""
        await self._ws_manager.connect(websocket)

        try:
            # Send initial state
            await websocket.send_json(self._current_state)

            # Keep connection alive and handle incoming messages
            while True:
                try:
                    data = await asyncio.wait_for(
                        websocket.receive_text(),
                        timeout=30.0
                    )
                    # Handle any incoming commands
                    await self._handle_ws_message(websocket, data)
                except asyncio.TimeoutError:
                    # Send ping to keep alive
                    await websocket.send_json({"type": "ping"})

        except WebSocketDisconnect:
            pass
        finally:
            self._ws_manager.disconnect(websocket)

    async def _handle_ws_message(self, websocket: WebSocket, data: str) -> None:
        """Handle incoming WebSocket message."""
        try:
            message = json.loads(data)
            msg_type = message.get("type")

            if msg_type == "pong":
                pass  # Keepalive response
            elif msg_type == "subscribe":
                pass  # Handle subscriptions
        except json.JSONDecodeError:
            pass

    # ========================================================================
    # Event Processing
    # ========================================================================

    def process_event(self, event: Event) -> None:
        """Process incoming event and update state."""
        self._event_buffer.append(event)

        # Update current state
        if event.detector == "radar":
            self._current_state["respiration_rate"] = event.value.get("respiration_rate")
            self._current_state["heart_rate"] = event.value.get("heart_rate_estimate")
            self._current_state["movement"] = event.value.get("movement", 0)
            self._current_state["presence"] = event.value.get("presence", False)
        elif event.detector == "audio":
            # Audio can provide breathing rate too
            if "breathing_rate" in event.value:
                self._current_state["audio_breathing_rate"] = event.value["breathing_rate"]
        elif event.detector == "bcg":
            # BCG provides more accurate heart rate
            if "heart_rate" in event.value:
                self._current_state["heart_rate"] = event.value["heart_rate"]

        self._current_state["timestamp"] = event.timestamp

        # Update alert level from engine
        if self._engine:
            state = self._engine.get_state()
            self._current_state["alert_level"] = state.level.value
            self._current_state["active_alerts"] = [
                a.to_dict() for a in state.active_alerts
            ]
            self._current_state["paused"] = state.paused

    async def _broadcast_state(self) -> None:
        """Broadcast current state to all WebSocket clients."""
        # Add recent events for display
        recent = self._event_buffer.get_recent(60)  # Last minute
        recent_dicts = [
            {
                "detector": e.detector,
                "state": e.state.value,
                "timestamp": e.timestamp,
                "value": e.value,
            }
            for e in recent[-10:]  # Last 10 events
        ]

        message = {
            **self._current_state,
            "recent_events": recent_dicts,
        }

        await self._ws_manager.broadcast(message)

    async def _update_loop(self) -> None:
        """Periodically broadcast state updates."""
        interval = self._config.websocket_update_interval_ms / 1000.0

        while self._running:
            await self._broadcast_state()
            await asyncio.sleep(interval)

    # ========================================================================
    # Server Control
    # ========================================================================

    async def start(self) -> None:
        """Start the dashboard server in background."""
        self._running = True

        # Start update broadcast task
        self._update_task = asyncio.create_task(self._update_loop())

        # Start uvicorn server in background
        config = uvicorn.Config(
            self._app,
            host=self._config.host,
            port=self._config.port,
            log_level="info",
        )
        self._server = uvicorn.Server(config)
        self._server_task = asyncio.create_task(self._server.serve())

    async def stop(self) -> None:
        """Stop the dashboard server."""
        self._running = False

        if self._update_task:
            self._update_task.cancel()
            try:
                await self._update_task
            except asyncio.CancelledError:
                pass

        # Stop uvicorn server
        if hasattr(self, "_server") and self._server:
            self._server.should_exit = True
            if hasattr(self, "_server_task") and self._server_task:
                try:
                    await asyncio.wait_for(self._server_task, timeout=5.0)
                except asyncio.TimeoutError:
                    self._server_task.cancel()
                except asyncio.CancelledError:
                    pass

    def run(self) -> None:
        """Run server synchronously (for standalone use)."""
        uvicorn.run(
            self._app,
            host=self._config.host,
            port=self._config.port,
        )
