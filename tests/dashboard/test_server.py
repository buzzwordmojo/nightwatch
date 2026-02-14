"""
Tests for the dashboard server.

Covers:
- REST API endpoints
- WebSocket connection handling
- Simulator endpoints (mock mode only)
- Event processing and state caching
- ConnectionManager
"""

from __future__ import annotations

import asyncio
import json
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from nightwatch.core.config import DashboardConfig
from nightwatch.core.events import Event, EventState
from nightwatch.dashboard.server import DashboardServer, ConnectionManager


# =============================================================================
# ConnectionManager Tests
# =============================================================================


class TestConnectionManager:
    """Tests for WebSocket connection manager."""

    def test_initial_state(self):
        """Manager starts with no connections."""
        manager = ConnectionManager()
        assert manager.connection_count == 0

    @pytest.mark.asyncio
    async def test_connect_adds_connection(self):
        """Connecting adds to connection list."""
        manager = ConnectionManager()
        mock_ws = AsyncMock()

        await manager.connect(mock_ws)

        assert manager.connection_count == 1
        mock_ws.accept.assert_called_once()

    def test_disconnect_removes_connection(self):
        """Disconnecting removes from connection list."""
        manager = ConnectionManager()
        mock_ws = MagicMock()
        manager._connections.append(mock_ws)

        manager.disconnect(mock_ws)

        assert manager.connection_count == 0

    def test_disconnect_nonexistent_is_safe(self):
        """Disconnecting non-existent connection doesn't crash."""
        manager = ConnectionManager()
        mock_ws = MagicMock()

        # Should not raise
        manager.disconnect(mock_ws)
        assert manager.connection_count == 0

    @pytest.mark.asyncio
    async def test_broadcast_sends_to_all(self):
        """Broadcast sends message to all connections."""
        manager = ConnectionManager()
        ws1 = AsyncMock()
        ws2 = AsyncMock()
        manager._connections = [ws1, ws2]

        await manager.broadcast({"type": "test"})

        ws1.send_json.assert_called_once_with({"type": "test"})
        ws2.send_json.assert_called_once_with({"type": "test"})

    @pytest.mark.asyncio
    async def test_broadcast_removes_dead_connections(self):
        """Broadcast removes connections that fail."""
        manager = ConnectionManager()
        good_ws = AsyncMock()
        bad_ws = AsyncMock()
        bad_ws.send_json.side_effect = Exception("Connection closed")
        manager._connections = [good_ws, bad_ws]

        await manager.broadcast({"type": "test"})

        # Bad connection should be removed
        assert manager.connection_count == 1
        assert bad_ws not in manager._connections


# =============================================================================
# DashboardServer Tests
# =============================================================================


class TestDashboardServer:
    """Tests for DashboardServer."""

    @pytest.fixture
    def server(self):
        """Create dashboard server."""
        return DashboardServer(
            config=DashboardConfig(port=8080),
            mock_mode=False,
        )

    @pytest.fixture
    def mock_server(self):
        """Create dashboard server in mock mode."""
        return DashboardServer(
            config=DashboardConfig(port=8080),
            mock_mode=True,
            detectors={"radar": MagicMock(), "bcg": MagicMock()},
        )

    @pytest.fixture
    def client(self, server):
        """Create test client."""
        return TestClient(server.app)

    @pytest.fixture
    def mock_client(self, mock_server):
        """Create test client for mock server."""
        return TestClient(mock_server.app)

    # Health Check
    def test_health_check(self, client):
        """Health check endpoint returns status."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "running" in data
        assert "connections" in data

    # Index Page
    def test_index_page(self, client):
        """Index page returns HTML."""
        response = client.get("/")

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "Nightwatch" in response.text

    # API Status
    def test_get_status(self, client):
        """Status endpoint returns current state."""
        response = client.get("/api/status")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "data" in data
        assert "timestamp" in data

    # API Alerts
    def test_get_alerts(self, client):
        """Alerts endpoint returns alert lists."""
        response = client.get("/api/alerts")

        assert response.status_code == 200
        data = response.json()
        assert "active" in data
        assert "history" in data

    def test_get_alerts_with_limit(self, client):
        """Alerts endpoint accepts limit parameter."""
        response = client.get("/api/alerts?limit=10")

        assert response.status_code == 200

    # Alert Actions (without engine)
    def test_acknowledge_alert_no_engine(self, client):
        """Acknowledge alert fails without engine."""
        response = client.post("/api/alerts/test-alert-id/acknowledge")

        assert response.status_code == 503
        assert "Engine not available" in response.json()["detail"]

    def test_resolve_alert_no_engine(self, client):
        """Resolve alert fails without engine."""
        response = client.post("/api/alerts/test-alert-id/resolve")

        assert response.status_code == 503

    # History
    def test_get_history(self, client):
        """History endpoint returns data points."""
        response = client.get("/api/history")

        assert response.status_code == 200
        data = response.json()
        assert "signal" in data
        assert "data" in data
        assert "count" in data

    def test_get_history_with_params(self, client):
        """History endpoint accepts parameters."""
        response = client.get("/api/history?signal=heart_rate&minutes=30")

        assert response.status_code == 200
        data = response.json()
        assert data["signal"] == "heart_rate"

    # Pause/Resume
    def test_pause_monitoring(self, client):
        """Pause endpoint pauses monitoring."""
        response = client.post(
            "/api/pause",
            json={"duration_minutes": 30},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "paused"
        assert data["duration_minutes"] == 30
        assert "expires" in data

    def test_resume_monitoring(self, client):
        """Resume endpoint resumes monitoring."""
        response = client.post("/api/resume")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "resumed"

    # Test Alert
    def test_test_alert(self, client):
        """Test alert endpoint sends test."""
        response = client.post("/api/test-alert")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "test_alert_sent"

    # Config
    def test_get_config(self, client):
        """Config endpoint returns dashboard config."""
        response = client.get("/api/config")

        assert response.status_code == 200
        data = response.json()
        assert "dashboard" in data
        assert data["dashboard"]["port"] == 8080


# =============================================================================
# Simulator Tests
# =============================================================================


class TestSimulatorEndpoints:
    """Tests for simulator endpoints (mock mode only)."""

    @pytest.fixture
    def mock_server(self):
        """Create mock mode server."""
        mock_radar = MagicMock()
        mock_radar._base_respiration_rate = 14.0
        mock_bcg = MagicMock()
        mock_bcg._base_heart_rate = 70.0
        mock_bcg._bed_occupied = True

        return DashboardServer(
            config=DashboardConfig(port=8080),
            mock_mode=True,
            detectors={"radar": mock_radar, "bcg": mock_bcg},
        )

    @pytest.fixture
    def mock_client(self, mock_server):
        """Create test client for mock server."""
        return TestClient(mock_server.app)

    @pytest.fixture
    def non_mock_server(self):
        """Create non-mock server."""
        return DashboardServer(
            config=DashboardConfig(port=8080),
            mock_mode=False,
        )

    @pytest.fixture
    def non_mock_client(self, non_mock_server):
        """Create test client for non-mock server."""
        return TestClient(non_mock_server.app)

    # Sim page
    def test_sim_page_mock_mode(self, mock_client):
        """Sim page available in mock mode."""
        response = mock_client.get("/sim")

        assert response.status_code == 200
        assert "Simulator" in response.text

    def test_sim_page_non_mock_mode(self, non_mock_client):
        """Sim page returns 404 in non-mock mode."""
        response = non_mock_client.get("/sim")

        assert response.status_code == 404

    # Sim status
    def test_sim_status(self, mock_client):
        """Sim status returns current state."""
        response = mock_client.get("/api/sim/status")

        assert response.status_code == 200
        data = response.json()
        assert data["mock_mode"] is True
        assert "breathing_rate" in data
        assert "heart_rate" in data
        assert "presence" in data

    def test_sim_status_non_mock(self, non_mock_client):
        """Sim status returns 404 in non-mock mode."""
        response = non_mock_client.get("/api/sim/status")

        assert response.status_code == 404

    # Scenarios
    def test_run_scenario_apnea(self, mock_client):
        """Run apnea scenario."""
        response = mock_client.post(
            "/api/sim/scenario",
            json={"scenario": "apnea", "duration": 10},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "scenario_started"
        assert data["scenario"] == "apnea"
        assert data["auto_reset"] is True

    def test_run_scenario_normal(self, mock_client):
        """Run normal scenario (baseline)."""
        response = mock_client.post(
            "/api/sim/scenario",
            json={"scenario": "normal"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["scenario"] == "normal"
        assert data["auto_reset"] is False

    def test_run_scenario_invalid(self, mock_client):
        """Invalid scenario returns 400."""
        response = mock_client.post(
            "/api/sim/scenario",
            json={"scenario": "invalid_scenario"},
        )

        assert response.status_code == 400
        assert "Unknown scenario" in response.json()["detail"]

    def test_run_scenario_non_mock(self, non_mock_client):
        """Scenarios return 404 in non-mock mode."""
        response = non_mock_client.post(
            "/api/sim/scenario",
            json={"scenario": "apnea"},
        )

        assert response.status_code == 404

    # Individual controls
    def test_set_breathing(self, mock_client):
        """Set breathing rate."""
        response = mock_client.post(
            "/api/sim/breathing",
            json={"rate": 8.0},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["breathing_rate"] == 8.0

    def test_set_breathing_clamped(self, mock_client):
        """Breathing rate is clamped to valid range."""
        response = mock_client.post(
            "/api/sim/breathing",
            json={"rate": 100.0},  # Too high
        )

        assert response.status_code == 200
        data = response.json()
        assert data["breathing_rate"] == 40.0  # Max

    def test_set_heartrate(self, mock_client):
        """Set heart rate."""
        response = mock_client.post(
            "/api/sim/heartrate",
            json={"rate": 50.0},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["heart_rate"] == 50.0

    def test_set_movement(self, mock_client):
        """Set movement level."""
        response = mock_client.post(
            "/api/sim/movement",
            json={"level": 0.8},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["movement"] == 0.8

    def test_set_movement_clamped(self, mock_client):
        """Movement level is clamped to 0-1."""
        response = mock_client.post(
            "/api/sim/movement",
            json={"level": 5.0},  # Too high
        )

        assert response.status_code == 200
        data = response.json()
        assert data["movement"] == 1.0  # Max

    def test_set_presence(self, mock_client):
        """Set bed presence."""
        response = mock_client.post(
            "/api/sim/presence",
            json={"present": False},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["presence"] is False

    # Reset
    def test_reset_sim(self, mock_client):
        """Reset simulator to normal."""
        response = mock_client.post("/api/sim/reset")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "reset"


# =============================================================================
# Event Processing Tests
# =============================================================================


class TestEventProcessing:
    """Tests for event processing."""

    @pytest.fixture
    def server(self):
        """Create server."""
        return DashboardServer(config=DashboardConfig())

    def test_process_radar_event(self, server):
        """Process radar event updates state."""
        event = Event(
            detector="radar",
            timestamp=time.time(),
            confidence=0.9,
            state=EventState.NORMAL,
            value={
                "respiration_rate": 14.0,
                "heart_rate_estimate": 70.0,
                "movement": 0.1,
                "presence": True,
            },
            sequence=1,
            session_id="test",
        )

        server.process_event(event)

        assert server._current_state["respiration_rate"] == 14.0
        assert server._current_state["heart_rate"] == 70.0
        assert server._current_state["movement"] == 0.1
        assert server._current_state["presence"] is True

    def test_process_audio_event(self, server):
        """Process audio event updates state."""
        event = Event(
            detector="audio",
            timestamp=time.time(),
            confidence=0.8,
            state=EventState.NORMAL,
            value={
                "breathing_rate": 13.0,
            },
            sequence=1,
            session_id="test",
        )

        server.process_event(event)

        assert server._current_state["audio_breathing_rate"] == 13.0

    def test_process_bcg_event(self, server):
        """Process BCG event updates state."""
        event = Event(
            detector="bcg",
            timestamp=time.time(),
            confidence=0.95,
            state=EventState.NORMAL,
            value={
                "heart_rate": 72.0,
            },
            sequence=1,
            session_id="test",
        )

        server.process_event(event)

        # BCG heart rate takes precedence
        assert server._current_state["heart_rate"] == 72.0

    def test_events_added_to_buffer(self, server):
        """Events are added to event buffer."""
        initial_count = len(server._event_buffer._buffer)

        event = Event(
            detector="radar",
            timestamp=time.time(),
            confidence=0.9,
            state=EventState.NORMAL,
            value={"respiration_rate": 14.0},
            sequence=1,
            session_id="test",
        )

        server.process_event(event)

        assert len(server._event_buffer._buffer) == initial_count + 1


# =============================================================================
# Server Lifecycle Tests
# =============================================================================


class TestServerLifecycle:
    """Tests for server start/stop."""

    @pytest.mark.asyncio
    async def test_start_creates_update_task(self):
        """Start creates background update task."""
        server = DashboardServer(config=DashboardConfig(port=8099))

        await server.start()

        assert server._running is True
        assert server._update_task is not None

        await server.stop()

    @pytest.mark.asyncio
    async def test_stop_cancels_update_task(self):
        """Stop cancels background update task."""
        server = DashboardServer(config=DashboardConfig(port=8098))

        await server.start()
        await server.stop()

        assert server._running is False


# =============================================================================
# Edge Cases
# =============================================================================


class TestDashboardEdgeCases:
    """Edge case tests for dashboard."""

    @pytest.fixture
    def server(self):
        """Create server."""
        return DashboardServer(config=DashboardConfig())

    @pytest.fixture
    def client(self, server):
        """Create test client."""
        return TestClient(server.app)

    def test_pause_default_duration(self, client):
        """Pause with default duration."""
        response = client.post(
            "/api/pause",
            json={},  # No duration specified
        )

        assert response.status_code == 200
        data = response.json()
        assert data["duration_minutes"] == 30  # Default

    def test_app_property(self, server):
        """App property returns FastAPI instance."""
        assert server.app is not None
        assert server.app == server._app

    def test_initial_state(self, server):
        """Server has sensible initial state."""
        assert server._current_state["respiration_rate"] is None
        assert server._current_state["heart_rate"] is None
        assert server._current_state["movement"] == 0
        assert server._current_state["presence"] is False
        assert server._current_state["alert_level"] == "ok"
        assert server._current_state["active_alerts"] == []

    def test_scenarios_all_valid(self, server):
        """All predefined scenarios are valid."""
        scenarios = ["normal", "apnea", "bradycardia", "tachycardia", "seizure", "empty_bed"]

        for scenario in scenarios:
            # These should not raise
            mock_server = DashboardServer(
                config=DashboardConfig(),
                mock_mode=True,
                detectors={},
            )
            client = TestClient(mock_server.app)

            response = client.post(
                "/api/sim/scenario",
                json={"scenario": scenario},
            )
            assert response.status_code == 200, f"Scenario {scenario} failed"
