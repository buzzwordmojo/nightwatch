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
import time
from pathlib import Path
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn

from nightwatch.core.config import DashboardConfig
from nightwatch.core.events import Event, Alert, EventBuffer
from nightwatch.core.engine import AlertEngine, AlertState, AlertLevel


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
    ):
        self._config = config or DashboardConfig()
        self._engine = engine
        self._app = FastAPI(
            title="Nightwatch Dashboard",
            description="Epilepsy monitoring system dashboard",
            version="0.1.0",
        )
        self._ws_manager = ConnectionManager()
        self._event_buffer = EventBuffer(capacity=1000)
        self._running = False
        self._update_task: asyncio.Task | None = None

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
        .chart-container {
            background: #16213e;
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 30px;
        }
        .chart-title {
            font-size: 16px;
            color: #888;
            margin-bottom: 16px;
        }
        .chart {
            height: 150px;
            display: flex;
            align-items: flex-end;
            gap: 2px;
        }
        .chart-bar {
            flex: 1;
            background: #3b82f6;
            border-radius: 2px 2px 0 0;
            min-height: 2px;
            transition: height 0.3s ease;
        }
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

        <div class="chart-container">
            <div class="chart-title">Respiration (last 2 minutes)</div>
            <div id="resp-chart" class="chart"></div>
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
        let respHistory = [];
        const maxHistory = 120;

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
            // Update vital signs
            const resp = data.respiration_rate;
            const hr = data.heart_rate;
            const movement = data.movement;

            document.getElementById('respiration-value').textContent =
                resp !== null ? Math.round(resp) : '--';
            document.getElementById('heartrate-value').textContent =
                hr !== null ? Math.round(hr) : '--';

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
            if (resp === null) {
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

            // Update chart
            if (resp !== null) {
                respHistory.push(resp);
                if (respHistory.length > maxHistory) respHistory.shift();
                updateChart();
            }

            // Update events
            if (data.recent_events && data.recent_events.length > 0) {
                updateEvents(data.recent_events);
            }
        }

        function updateChart() {
            const chart = document.getElementById('resp-chart');
            chart.innerHTML = '';

            const max = Math.max(...respHistory, 20);
            const min = Math.min(...respHistory, 0);
            const range = max - min || 1;

            respHistory.forEach(val => {
                const bar = document.createElement('div');
                bar.className = 'chart-bar';
                const height = ((val - min) / range) * 100;
                bar.style.height = Math.max(2, height) + '%';
                if (val < 6) bar.style.background = '#ef4444';
                else if (val < 10) bar.style.background = '#f59e0b';
                chart.appendChild(bar);
            });
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
