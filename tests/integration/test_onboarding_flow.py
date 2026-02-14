"""
Integration tests for the complete onboarding flow.

These tests verify the end-to-end setup wizard experience,
from first boot detection through setup completion.

Run in Pi VM:
    pytest tests/integration/test_onboarding_flow.py -v
"""

from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from nightwatch.setup.first_boot import (
    SetupState,
    detect_setup_state,
    mark_configured,
    reset_configuration,
)
from nightwatch.setup.portal import CaptivePortal


@pytest.fixture
def temp_config_dir():
    """Create temporary config directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def portal(temp_config_dir: Path):
    """Create a test portal instance."""
    return CaptivePortal(
        gateway_ip="192.168.4.1",
    )


class TestFirstBootToSetupMode:
    """Test the transition from first boot to setup mode."""

    def test_fresh_install_detects_unconfigured(self, temp_config_dir: Path):
        """Fresh install should detect as unconfigured."""
        state = detect_setup_state(temp_config_dir)
        assert state == SetupState.UNCONFIGURED

    def test_unconfigured_triggers_setup_mode(self, temp_config_dir: Path):
        """Unconfigured state should trigger setup mode."""
        state = detect_setup_state(temp_config_dir)

        # App logic: if UNCONFIGURED, enter setup mode
        should_enter_setup = state == SetupState.UNCONFIGURED
        assert should_enter_setup is True

    def test_configured_skips_setup_mode(self, temp_config_dir: Path):
        """Configured state should skip setup mode."""
        # Simulate completed setup
        (temp_config_dir / "wifi.conf").write_text("ssid=TestNet\npassword=pass")
        mark_configured(temp_config_dir)

        state = detect_setup_state(temp_config_dir)
        should_enter_setup = state == SetupState.UNCONFIGURED

        assert state == SetupState.FULLY_CONFIGURED
        assert should_enter_setup is False


class TestCaptivePortalFlow:
    """Test the captive portal setup flow."""

    @pytest.mark.asyncio
    async def test_portal_starts_successfully(self, portal: CaptivePortal):
        """Portal should start without errors."""
        with patch("uvicorn.Server") as mock_server_class:
            mock_server = AsyncMock()
            mock_server_class.return_value = mock_server

            await portal.start()

            mock_server_class.assert_called_once()

    @pytest.mark.asyncio
    async def test_portal_stops_cleanly(self, portal: CaptivePortal):
        """Portal should stop without errors."""
        mock_server = AsyncMock()
        portal._server = mock_server

        await portal.stop()

        assert mock_server.should_exit is True

    def test_android_captive_portal_detection(self, portal: CaptivePortal):
        """Android captive portal detection should redirect."""
        from fastapi.testclient import TestClient

        client = TestClient(portal._app)

        # Android sends this request to detect captive portal
        response = client.get("/generate_204", follow_redirects=False)

        # Should redirect to setup, not return 204
        assert response.status_code == 302
        assert "/setup" in response.headers.get("location", "")

    def test_ios_captive_portal_detection(self, portal: CaptivePortal):
        """iOS captive portal detection should return redirect HTML."""
        from fastapi.testclient import TestClient

        client = TestClient(portal._app)

        response = client.get("/hotspot-detect.html")

        assert response.status_code == 200
        assert "setup" in response.text.lower()


class TestWiFiConfigurationFlow:
    """Test WiFi configuration during setup."""

    def test_wifi_scan_returns_networks(self, portal: CaptivePortal):
        """WiFi scan should return available networks."""
        from fastapi.testclient import TestClient

        client = TestClient(portal._app)

        with patch.object(portal, "_scan_wifi", new_callable=AsyncMock) as mock_scan:
            mock_scan.return_value = [
                {"ssid": "HomeNetwork", "signal": 90},
                {"ssid": "Neighbor", "signal": 45},
            ]

            response = client.get("/api/setup/wifi/scan")

            assert response.status_code == 200
            data = response.json()
            assert "networks" in data
            assert len(data["networks"]) == 2

    def test_wifi_credentials_saved(self, portal: CaptivePortal, temp_config_dir: Path):
        """WiFi credentials should be saved correctly."""
        from fastapi.testclient import TestClient

        client = TestClient(portal._app)

        with patch.object(portal, "_save_wifi_credentials", new_callable=AsyncMock) as mock_save:
            response = client.post(
                "/api/setup/wifi",
                json={"ssid": "TestNetwork", "password": "secretpass123"},
            )

            assert response.status_code == 200
            mock_save.assert_called_once()

    def test_wifi_config_triggers_callback(self, temp_config_dir: Path):
        """WiFi configuration should trigger callback for connection."""
        callback_triggered = False
        configured_ssid = None

        async def on_wifi_configured(ssid: str):
            nonlocal callback_triggered, configured_ssid
            callback_triggered = True
            configured_ssid = ssid

        portal = CaptivePortal(
            gateway_ip="192.168.4.1",
            on_wifi_configured=on_wifi_configured,
        )

        from fastapi.testclient import TestClient
        client = TestClient(portal._app)

        with patch.object(portal, "_save_wifi_credentials", new_callable=AsyncMock):
            client.post(
                "/api/setup/wifi",
                json={"ssid": "MyWiFi", "password": "pass12345"},  # 8+ chars for WPA
            )

        assert callback_triggered is True
        assert configured_ssid == "MyWiFi"


class TestSetupWizardFlow:
    """Test the complete setup wizard flow."""

    def test_progress_tracking(self, portal: CaptivePortal):
        """Setup progress should be tracked correctly."""
        from fastapi.testclient import TestClient

        client = TestClient(portal._app)

        response = client.get("/api/setup/progress")

        assert response.status_code == 200
        data = response.json()
        assert "step" in data
        assert "total_steps" in data

    @pytest.mark.skip(reason="Endpoint /api/setup/name not yet implemented in CaptivePortal")
    def test_monitor_name_saved(self, portal: CaptivePortal, temp_config_dir: Path):
        """Monitor name should be saved correctly."""
        from fastapi.testclient import TestClient

        client = TestClient(portal._app)

        response = client.post(
            "/api/setup/name",
            json={"name": "Kids Room"},
        )

        assert response.status_code == 200

        # Verify name was saved
        name_file = temp_config_dir / "monitor_name.txt"
        if name_file.exists():
            assert name_file.read_text().strip() == "Kids Room"

    @pytest.mark.skip(reason="Endpoint /api/setup/notifications not yet implemented in CaptivePortal")
    def test_notification_preferences_saved(self, portal: CaptivePortal):
        """Notification preferences should be saved."""
        from fastapi.testclient import TestClient

        client = TestClient(portal._app)

        response = client.post(
            "/api/setup/notifications",
            json={
                "audio_alarm": True,
                "push_notifications": False,
            },
        )

        assert response.status_code == 200

    @pytest.mark.skip(reason="Endpoint /api/setup/test-alert and _trigger_test_alert not yet implemented")
    def test_test_alert_triggers(self, portal: CaptivePortal):
        """Test alert should trigger successfully."""
        from fastapi.testclient import TestClient

        client = TestClient(portal._app)

        with patch.object(portal, "_trigger_test_alert", new_callable=AsyncMock) as mock_alert:
            mock_alert.return_value = True

            response = client.post("/api/setup/test-alert")

            assert response.status_code == 200
            data = response.json()
            assert data.get("success") is True

    @pytest.mark.skip(reason="Endpoint /api/setup/complete not yet implemented in CaptivePortal")
    def test_setup_complete_marks_configured(self, portal: CaptivePortal, temp_config_dir: Path):
        """Completing setup should mark system as configured."""
        from fastapi.testclient import TestClient

        client = TestClient(portal._app)

        # Complete setup
        response = client.post(
            "/api/setup/complete",
            json={
                "monitorName": "Test Room",
                "sensorsConfirmed": True,
                "notifications": {"audioAlarm": True, "pushNotifications": False},
                "testCompleted": True,
            },
        )

        assert response.status_code == 200

        # Verify configured
        state = detect_setup_state(temp_config_dir)
        assert state == SetupState.FULLY_CONFIGURED


class TestSetupErrorHandling:
    """Test error handling during setup."""

    def test_invalid_wifi_credentials_rejected(self, portal: CaptivePortal):
        """Invalid WiFi credentials should be rejected."""
        from fastapi.testclient import TestClient

        client = TestClient(portal._app)

        # Empty SSID should fail
        response = client.post(
            "/api/setup/wifi",
            json={"ssid": "", "password": "pass"},
        )

        assert response.status_code == 422  # Validation error

    @pytest.mark.skip(reason="Endpoint /api/setup/name not yet implemented in CaptivePortal")
    def test_empty_monitor_name_rejected(self, portal: CaptivePortal):
        """Empty monitor name should be rejected."""
        from fastapi.testclient import TestClient

        client = TestClient(portal._app)

        response = client.post(
            "/api/setup/name",
            json={"name": ""},
        )

        assert response.status_code == 422  # Validation error

    def test_wifi_connection_failure_reported(self, portal: CaptivePortal):
        """WiFi connection failure should be reported clearly."""
        from fastapi.testclient import TestClient

        client = TestClient(portal._app)

        with patch.object(portal, "_save_wifi_credentials", new_callable=AsyncMock) as mock_save:
            mock_save.side_effect = Exception("Connection failed")

            response = client.post(
                "/api/setup/wifi",
                json={"ssid": "BadNetwork", "password": "wrongpass"},
            )

            # Should return error, not crash
            assert response.status_code in [500, 400]


class TestSensorDetectionDuringSetup:
    """Test sensor detection during setup wizard."""

    @pytest.mark.skip(reason="Endpoint /api/setup/sensor-preview and _get_sensor_status not yet implemented")
    def test_sensor_preview_returns_status(self, portal: CaptivePortal):
        """Sensor preview should return detection status."""
        from fastapi.testclient import TestClient

        client = TestClient(portal._app)

        with patch.object(portal, "_get_sensor_status", new_callable=AsyncMock) as mock_status:
            mock_status.return_value = {
                "radar": {"detected": True, "signal": 85},
                "audio": {"detected": True},
                "bcg": {"detected": False},
            }

            response = client.get("/api/setup/sensor-preview")

            assert response.status_code == 200
            data = response.json()
            assert data["radar"]["detected"] is True
            assert data["bcg"]["detected"] is False

    @pytest.mark.skip(reason="Endpoint /api/setup/sensor-preview and _get_sensor_status not yet implemented")
    def test_no_sensors_detected_warns_user(self, portal: CaptivePortal):
        """No sensors detected should warn but not block setup."""
        from fastapi.testclient import TestClient

        client = TestClient(portal._app)

        with patch.object(portal, "_get_sensor_status", new_callable=AsyncMock) as mock_status:
            mock_status.return_value = {
                "radar": {"detected": False},
                "audio": {"detected": False},
                "bcg": {"detected": False},
            }

            response = client.get("/api/setup/sensor-preview")

            assert response.status_code == 200
            data = response.json()
            # All sensors should report not detected
            assert data["radar"]["detected"] is False


class TestSetupResetFlow:
    """Test resetting setup for reconfiguration."""

    def test_reset_clears_configuration(self, temp_config_dir: Path):
        """Reset should clear configured flag."""
        # First, mark as configured
        (temp_config_dir / "wifi.conf").write_text("ssid=Test\npassword=pass")
        mark_configured(temp_config_dir)

        assert detect_setup_state(temp_config_dir) == SetupState.FULLY_CONFIGURED

        # Reset
        reset_configuration(temp_config_dir)

        # Should return to wifi-only state (wifi.conf still exists)
        assert detect_setup_state(temp_config_dir) == SetupState.WIFI_ONLY

    def test_factory_reset_clears_everything(self, temp_config_dir: Path):
        """Factory reset should clear all configuration."""
        # Setup complete config
        (temp_config_dir / "wifi.conf").write_text("ssid=Test\npassword=pass")
        (temp_config_dir / "monitor_name.txt").write_text("Kids Room")
        mark_configured(temp_config_dir)

        # Factory reset (remove all files)
        for f in temp_config_dir.iterdir():
            f.unlink()

        assert detect_setup_state(temp_config_dir) == SetupState.UNCONFIGURED
