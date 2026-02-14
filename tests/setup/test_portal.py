"""Tests for captive portal server."""

from __future__ import annotations

import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient

from nightwatch.setup.portal import CaptivePortal, WiFiCredentials


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
                json={"ssid": "CallbackTest", "password": "pass123"},
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
        creds = WiFiCredentials(ssid="TestNet", password="pass123")
        assert creds.ssid == "TestNet"
        assert creds.password == "pass123"

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
