"""Tests for captive portal server and dashboard setup endpoints."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient

from nightwatch.setup.portal import CaptivePortal, WiFiCredentials
from nightwatch.setup.first_boot import detect_setup_state, SetupState
from nightwatch.dashboard.server import DashboardServer


@pytest.fixture
def portal():
    """Create a CaptivePortal instance for testing."""
    return CaptivePortal(gateway_ip="192.168.4.1")


@pytest.fixture
def client(portal: CaptivePortal):
    """Create a test client for the portal."""
    return TestClient(portal._app)


class TestCaptivePortalDetection:
    """Test captive portal detection endpoints."""

    def test_android_generate_204_redirects(self, client: TestClient):
        """Android /generate_204 should redirect to setup."""
        response = client.get("/generate_204", follow_redirects=False)
        assert response.status_code == 302
        assert "192.168.4.1/setup" in response.headers["location"]

    def test_ios_hotspot_detect_returns_html(self, client: TestClient):
        """iOS /hotspot-detect.html should return redirect HTML."""
        response = client.get("/hotspot-detect.html")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        # Should contain redirect to setup
        assert "192.168.4.1/setup" in response.text

    def test_windows_connecttest_redirects(self, client: TestClient):
        """Windows connect test should redirect to setup."""
        response = client.get(
            "/www.msftconnecttest.com/connecttest.txt",
            follow_redirects=False,
        )
        assert response.status_code == 302

    def test_apple_captive_endpoint(self, client: TestClient):
        """Apple captive portal detection endpoint."""
        response = client.get("/captive.apple.com/hotspot-detect.html")
        assert response.status_code == 200
        assert "192.168.4.1/setup" in response.text


class TestSetupWizardEndpoints:
    """Test setup wizard API endpoints."""

    def test_root_redirects_to_setup(self, client: TestClient):
        """Root URL should redirect to /setup."""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307  # Temporary redirect
        assert "/setup" in response.headers["location"]

    def test_setup_page_returns_html(self, client: TestClient):
        """Setup page should return HTML."""
        response = client.get("/setup")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "Nightwatch" in response.text

    def test_setup_page_contains_wifi_form(self, client: TestClient):
        """Setup page should contain WiFi configuration form."""
        response = client.get("/setup")
        assert "Connect to WiFi" in response.text or "WiFi" in response.text

    def test_wifi_scan_returns_networks(self, client: TestClient, portal: CaptivePortal):
        """WiFi scan should return list of networks."""
        with patch.object(portal, "_scan_wifi", new_callable=AsyncMock) as mock_scan:
            mock_scan.return_value = [
                {"ssid": "TestNetwork", "signal": 85},
                {"ssid": "Neighbor", "signal": 45},
            ]

            response = client.get("/api/setup/wifi/scan")

            assert response.status_code == 200
            data = response.json()
            assert "networks" in data
            assert len(data["networks"]) == 2
            assert data["networks"][0]["ssid"] == "TestNetwork"

    def test_wifi_configure_saves_credentials(self, client: TestClient, portal: CaptivePortal):
        """WiFi configuration should save credentials."""
        with patch.object(portal, "_save_wifi_credentials", new_callable=AsyncMock):
            response = client.post(
                "/api/setup/wifi",
                json={"ssid": "TestNetwork", "password": "testpass123"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True

    def test_wifi_configure_returns_redirect_url(self, client: TestClient, portal: CaptivePortal):
        """WiFi configuration should return redirect URL."""
        with patch.object(portal, "_save_wifi_credentials", new_callable=AsyncMock):
            response = client.post(
                "/api/setup/wifi",
                json={"ssid": "TestNetwork", "password": "testpass123"},
            )

            data = response.json()
            assert "redirect_url" in data

    def test_wifi_configure_calls_callback(self, client: TestClient):
        """WiFi configuration should trigger callback."""
        callback_called = False
        callback_ssid = None

        async def on_wifi_configured(ssid: str):
            nonlocal callback_called, callback_ssid
            callback_called = True
            callback_ssid = ssid

        portal = CaptivePortal(
            gateway_ip="192.168.4.1",
            on_wifi_configured=on_wifi_configured,
        )
        test_client = TestClient(portal._app)

        with patch.object(portal, "_save_wifi_credentials", new_callable=AsyncMock):
            test_client.post(
                "/api/setup/wifi",
                json={"ssid": "CallbackTest", "password": "pass12345"},  # 8+ chars
            )

        assert callback_called is True
        assert callback_ssid == "CallbackTest"

    def test_progress_endpoint(self, client: TestClient):
        """Progress endpoint should return current state."""
        response = client.get("/api/setup/progress")
        assert response.status_code == 200

        data = response.json()
        assert "step" in data
        assert "total_steps" in data
        assert "wifi_configured" in data


class TestWiFiCredentialsModel:
    """Test WiFiCredentials pydantic model."""

    def test_valid_credentials(self):
        """Valid credentials should be accepted."""
        creds = WiFiCredentials(ssid="TestNet", password="pass12345")
        assert creds.ssid == "TestNet"
        assert creds.password == "pass12345"

    def test_empty_password_allowed(self):
        """Empty password should be allowed (open networks)."""
        creds = WiFiCredentials(ssid="OpenNetwork", password="")
        assert creds.password == ""


class TestSetupPageContent:
    """Test setup page HTML content."""

    def test_page_is_mobile_friendly(self, client: TestClient):
        """Setup page should have mobile viewport meta tag."""
        response = client.get("/setup")
        assert 'viewport' in response.text

    def test_page_has_network_list(self, client: TestClient):
        """Setup page should have network list element."""
        response = client.get("/setup")
        assert 'network-list' in response.text

    def test_page_has_password_input(self, client: TestClient):
        """Setup page should have password input."""
        response = client.get("/setup")
        assert 'type="password"' in response.text

    def test_page_has_connect_button(self, client: TestClient):
        """Setup page should have connect button."""
        response = client.get("/setup")
        assert 'Connect' in response.text


class TestCaptivePortalLifecycle:
    """Test portal start/stop lifecycle."""

    @pytest.mark.asyncio
    async def test_start_creates_server(self, portal: CaptivePortal):
        """Start should create uvicorn server."""
        with patch("uvicorn.Server") as mock_server_class:
            mock_server = AsyncMock()
            mock_server_class.return_value = mock_server

            await portal.start()

            mock_server_class.assert_called_once()

    @pytest.mark.asyncio
    async def test_stop_signals_exit(self, portal: CaptivePortal):
        """Stop should signal server to exit."""
        mock_server = AsyncMock()
        portal._server = mock_server

        await portal.stop()

        assert mock_server.should_exit is True


# ======================================================================
# Dashboard Setup Endpoint Tests
# ======================================================================


@pytest.fixture
def temp_config_dir():
    """Create temporary config directory for dashboard tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def dashboard(temp_config_dir: Path):
    """Create a DashboardServer in mock mode with temp config dir."""
    server = DashboardServer(mock_mode=True)
    server._config_dir = temp_config_dir
    return server


@pytest.fixture
def dashboard_client(dashboard: DashboardServer):
    """Create a test client for the dashboard."""
    return TestClient(dashboard._app)


class TestDashboardSensorPreview:
    """Test /api/setup/sensor-preview endpoint."""

    def test_returns_expected_shape(self, dashboard_client: TestClient):
        """Sensor preview should return radar, audio, bcg."""
        response = dashboard_client.get("/api/setup/sensor-preview")
        assert response.status_code == 200
        data = response.json()
        assert "radar" in data
        assert "audio" in data
        assert "bcg" in data

    def test_mock_mode_returns_defaults(self, dashboard_client: TestClient):
        """Mock mode should return known default values."""
        data = dashboard_client.get("/api/setup/sensor-preview").json()
        assert data["radar"]["detected"] is True
        assert data["radar"]["signal"] == 85
        assert data["audio"]["detected"] is True
        assert data["bcg"]["detected"] is False


class TestDashboardTestAlert:
    """Test /api/setup/test-alert endpoint."""

    def test_returns_success(self, dashboard_client: TestClient):
        """Test alert should return success."""
        response = dashboard_client.post("/api/setup/test-alert")
        assert response.status_code == 200
        assert response.json()["success"] is True


class TestDashboardSetupComplete:
    """Test /api/setup/complete endpoint."""

    def test_creates_configured_flag(self, dashboard_client: TestClient, temp_config_dir: Path):
        """Complete should create .configured flag."""
        # Need wifi.conf for FULLY_CONFIGURED state
        (temp_config_dir / "wifi.conf").write_text("ssid=TestNet\npassword=pass1234")

        response = dashboard_client.post(
            "/api/setup/complete",
            json={
                "monitorName": "Test Room",
                "sensorsConfirmed": True,
                "notifications": {"audioAlarm": True},
                "testCompleted": True,
            },
        )
        assert response.status_code == 200
        assert (temp_config_dir / ".configured").exists()
        assert detect_setup_state(temp_config_dir) == SetupState.FULLY_CONFIGURED

    def test_saves_monitor_name(self, dashboard_client: TestClient, temp_config_dir: Path):
        """Complete should save monitor name."""
        dashboard_client.post(
            "/api/setup/complete",
            json={"monitorName": "Nursery", "sensorsConfirmed": True,
                  "notifications": {}, "testCompleted": True},
        )
        assert (temp_config_dir / "monitor_name").read_text() == "Nursery"

    def test_saves_notifications(self, dashboard_client: TestClient, temp_config_dir: Path):
        """Complete should save notifications config."""
        dashboard_client.post(
            "/api/setup/complete",
            json={"monitorName": "Room", "sensorsConfirmed": True,
                  "notifications": {"audioAlarm": True, "pushNotifications": False},
                  "testCompleted": True},
        )
        data = json.loads((temp_config_dir / "notifications.json").read_text())
        assert data["audioAlarm"] is True
        assert data["pushNotifications"] is False

    def test_saves_setup_summary(self, dashboard_client: TestClient, temp_config_dir: Path):
        """Complete should save a setup summary."""
        dashboard_client.post(
            "/api/setup/complete",
            json={"monitorName": "Room", "sensorsConfirmed": True,
                  "notifications": {}, "testCompleted": True},
        )
        summary = json.loads((temp_config_dir / "setup_summary.json").read_text())
        assert summary["monitorName"] == "Room"
        assert "completedAt" in summary


class TestDashboardSetupName:
    """Test /api/setup/name endpoint."""

    def test_saves_name(self, dashboard_client: TestClient, temp_config_dir: Path):
        """Name endpoint should save to monitor_name file."""
        response = dashboard_client.post(
            "/api/setup/name",
            json={"name": "Kids Room"},
        )
        assert response.status_code == 200
        assert (temp_config_dir / "monitor_name").read_text() == "Kids Room"

    def test_rejects_short_name(self, dashboard_client: TestClient):
        """Name shorter than 2 chars should be rejected."""
        response = dashboard_client.post(
            "/api/setup/name",
            json={"name": "A"},
        )
        assert response.status_code == 422

    def test_rejects_empty_name(self, dashboard_client: TestClient):
        """Empty name should be rejected."""
        response = dashboard_client.post(
            "/api/setup/name",
            json={"name": ""},
        )
        assert response.status_code == 422

    def test_strips_whitespace(self, dashboard_client: TestClient, temp_config_dir: Path):
        """Name should be stripped of whitespace."""
        dashboard_client.post(
            "/api/setup/name",
            json={"name": "  Nursery  "},
        )
        assert (temp_config_dir / "monitor_name").read_text() == "Nursery"


class TestDashboardSetupNotifications:
    """Test /api/setup/notifications endpoint."""

    def test_saves_preferences(self, dashboard_client: TestClient, temp_config_dir: Path):
        """Notifications should be saved to JSON file."""
        response = dashboard_client.post(
            "/api/setup/notifications",
            json={"audio_alarm": True, "push_notifications": False},
        )
        assert response.status_code == 200

        data = json.loads((temp_config_dir / "notifications.json").read_text())
        assert data["audio_alarm"] is True
        assert data["push_notifications"] is False


# ======================================================================
# Enhanced run_setup_portal Tests
# ======================================================================


class TestSetupPortalHotspot:
    """Test hotspot management in run_setup_portal."""

    @pytest.mark.asyncio
    async def test_hotspot_started_in_production(self):
        """HotspotManager.start() should be called when not in dev mode."""
        from nightwatch.core.config import Config
        from nightwatch.__main__ import run_setup_portal

        config = Config.default()

        mock_hotspot = AsyncMock()
        mock_hotspot.is_running = True
        mock_hotspot.ssid = "Nightwatch-XXXX"

        with patch("nightwatch.__main__.HotspotManager", return_value=mock_hotspot) as mock_cls, \
             patch("nightwatch.__main__.DashboardServer") as mock_dash_cls, \
             patch("nightwatch.__main__.CaptivePortal") as mock_portal_cls, \
             patch("nightwatch.__main__.detect_setup_state", return_value=SetupState.UNCONFIGURED):

            mock_dash_cls.return_value = AsyncMock()
            mock_portal_cls.return_value = AsyncMock()

            # Simulate immediate shutdown
            with patch("asyncio.wait", new_callable=AsyncMock) as mock_wait:
                mock_wait.return_value = ({MagicMock()}, set())

                try:
                    await run_setup_portal(config, dev_mode=False, setup_only=True)
                except Exception:
                    pass  # May error on signal handling; that's fine

            mock_cls.assert_called_once()
            mock_hotspot.start.assert_called_once()

    @pytest.mark.asyncio
    async def test_hotspot_skipped_in_dev_mode(self):
        """Hotspot should NOT be started in dev mode."""
        from nightwatch.core.config import Config
        from nightwatch.__main__ import run_setup_portal

        config = Config.default()

        with patch("nightwatch.__main__.HotspotManager") as mock_cls, \
             patch("nightwatch.__main__.DashboardServer") as mock_dash_cls, \
             patch("nightwatch.__main__.CaptivePortal") as mock_portal_cls, \
             patch("nightwatch.__main__.detect_setup_state", return_value=SetupState.UNCONFIGURED):

            mock_dash_cls.return_value = AsyncMock()
            mock_portal_cls.return_value = AsyncMock()

            with patch("asyncio.wait", new_callable=AsyncMock) as mock_wait:
                mock_wait.return_value = ({MagicMock()}, set())

                try:
                    await run_setup_portal(config, dev_mode=True, setup_only=True)
                except Exception:
                    pass

            mock_cls.assert_not_called()

    @pytest.mark.asyncio
    async def test_dashboard_started_during_setup(self):
        """DashboardServer should be created and started during setup."""
        from nightwatch.core.config import Config
        from nightwatch.__main__ import run_setup_portal

        config = Config.default()

        mock_dashboard = AsyncMock()

        with patch("nightwatch.__main__.HotspotManager") as mock_hotspot_cls, \
             patch("nightwatch.__main__.DashboardServer", return_value=mock_dashboard) as mock_dash_cls, \
             patch("nightwatch.__main__.CaptivePortal") as mock_portal_cls, \
             patch("nightwatch.__main__.detect_setup_state", return_value=SetupState.UNCONFIGURED):

            mock_hotspot_cls.return_value = AsyncMock(is_running=False, ssid="test")
            mock_portal_cls.return_value = AsyncMock()

            with patch("asyncio.wait", new_callable=AsyncMock) as mock_wait:
                mock_wait.return_value = ({MagicMock()}, set())

                try:
                    await run_setup_portal(config, dev_mode=True, setup_only=True)
                except Exception:
                    pass

            mock_dash_cls.assert_called_once_with(
                config=config.dashboard,
                mock_mode=True,
            )
            mock_dashboard.start.assert_called_once()

    @pytest.mark.asyncio
    async def test_hotspot_stopped_after_wifi(self):
        """Hotspot should be stopped when WiFi callback fires."""
        from nightwatch.__main__ import run_setup_portal
        from nightwatch.core.config import Config

        config = Config.default()

        mock_hotspot = AsyncMock()
        mock_hotspot.is_running = True
        mock_hotspot.ssid = "Nightwatch-XXXX"

        captured_callback = None

        def capture_portal_init(**kwargs):
            nonlocal captured_callback
            captured_callback = kwargs.get("on_wifi_configured")
            mock_portal = AsyncMock()
            return mock_portal

        with patch("nightwatch.__main__.HotspotManager", return_value=mock_hotspot), \
             patch("nightwatch.__main__.DashboardServer", return_value=AsyncMock()), \
             patch("nightwatch.__main__.CaptivePortal", side_effect=capture_portal_init), \
             patch("nightwatch.__main__.detect_setup_state", return_value=SetupState.UNCONFIGURED):

            with patch("asyncio.wait", new_callable=AsyncMock) as mock_wait:
                mock_wait.return_value = ({MagicMock()}, set())

                try:
                    await run_setup_portal(config, dev_mode=False, setup_only=True)
                except Exception:
                    pass

        # The callback should have been captured from CaptivePortal kwargs
        assert captured_callback is not None

        # Simulate calling the wifi callback
        mock_hotspot.reset_mock()
        with patch("asyncio.sleep", new_callable=AsyncMock):
            await captured_callback("TestNetwork")

        mock_hotspot.stop.assert_called_once()
