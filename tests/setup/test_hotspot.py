"""Tests for WiFi hotspot module."""

from __future__ import annotations

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from pathlib import Path

from nightwatch.setup.hotspot import (
    HotspotConfig,
    HotspotManager,
    DEFAULT_SSID_PREFIX,
    DEFAULT_GATEWAY_IP,
)


class TestHotspotConfig:
    """Test HotspotConfig dataclass."""

    def test_default_values(self):
        """Config should have sensible defaults."""
        config = HotspotConfig()

        assert config.channel == 6
        assert config.interface == "wlan0"
        assert config.gateway_ip == DEFAULT_GATEWAY_IP
        assert config.password is None  # Open network by default

    def test_ssid_auto_generation(self):
        """SSID should be auto-generated if not provided."""
        with patch.object(HotspotConfig, "_get_mac_address", return_value="aa:bb:cc:dd:ee:ff"):
            config = HotspotConfig()
            assert config.ssid == f"{DEFAULT_SSID_PREFIX}-EEFF"

    def test_ssid_fallback_on_error(self):
        """SSID should fallback to XXXX if MAC address unavailable."""
        with patch.object(HotspotConfig, "_get_mac_address", side_effect=FileNotFoundError):
            config = HotspotConfig()
            assert config.ssid == f"{DEFAULT_SSID_PREFIX}-XXXX"

    def test_explicit_ssid(self):
        """Explicit SSID should be used as-is."""
        config = HotspotConfig(ssid="MyCustomSSID")
        assert config.ssid == "MyCustomSSID"

    def test_password_setting(self):
        """Password should be settable."""
        config = HotspotConfig(password="secretpass")
        assert config.password == "secretpass"


class TestHotspotManager:
    """Test HotspotManager class."""

    @pytest.fixture
    def manager(self):
        """Create a HotspotManager with mocked config."""
        config = HotspotConfig(ssid="TestHotspot", password=None)
        return HotspotManager(config=config)

    def test_initial_state(self, manager: HotspotManager):
        """Manager should start in stopped state."""
        assert manager.is_running is False

    def test_ssid_property(self, manager: HotspotManager):
        """SSID property should return config SSID."""
        assert manager.ssid == "TestHotspot"

    @pytest.mark.asyncio
    async def test_start_configures_interface(self, manager: HotspotManager):
        """Start should configure network interface."""
        with patch.object(manager, "_configure_interface", new_callable=AsyncMock) as mock_configure:
            with patch.object(manager, "_write_hostapd_config", return_value=Path("/tmp/test")):
                with patch.object(manager, "_write_dnsmasq_config", return_value=Path("/tmp/test")):
                    with patch.object(manager, "_start_hostapd", new_callable=AsyncMock, return_value=MagicMock()):
                        with patch.object(manager, "_start_dnsmasq", new_callable=AsyncMock, return_value=MagicMock()):
                            await manager.start()
                            mock_configure.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_sets_running_flag(self, manager: HotspotManager):
        """Successful start should set is_running to True."""
        with patch.object(manager, "_configure_interface", new_callable=AsyncMock):
            with patch.object(manager, "_write_hostapd_config", return_value=Path("/tmp/test")):
                with patch.object(manager, "_write_dnsmasq_config", return_value=Path("/tmp/test")):
                    with patch.object(manager, "_start_hostapd", new_callable=AsyncMock, return_value=MagicMock()):
                        with patch.object(manager, "_start_dnsmasq", new_callable=AsyncMock, return_value=MagicMock()):
                            await manager.start()
                            assert manager.is_running is True

    @pytest.mark.asyncio
    async def test_stop_clears_running_flag(self, manager: HotspotManager):
        """Stop should clear is_running flag."""
        manager._running = True
        with patch.object(manager, "_reset_interface", new_callable=AsyncMock):
            await manager.stop()
            assert manager.is_running is False

    @pytest.mark.asyncio
    async def test_stop_terminates_processes(self, manager: HotspotManager):
        """Stop should terminate hostapd and dnsmasq."""
        mock_hostapd = MagicMock()
        mock_dnsmasq = MagicMock()
        manager._hostapd_process = mock_hostapd
        manager._dnsmasq_process = mock_dnsmasq
        manager._running = True

        with patch.object(manager, "_reset_interface", new_callable=AsyncMock):
            await manager.stop()

        mock_hostapd.terminate.assert_called_once()
        mock_dnsmasq.terminate.assert_called_once()

    def test_hostapd_config_content(self, manager: HotspotManager):
        """Generated hostapd config should have correct content."""
        config_path = manager._write_hostapd_config()

        content = config_path.read_text()
        assert "interface=wlan0" in content
        assert "ssid=TestHotspot" in content
        assert "channel=6" in content
        # Open network should not have WPA settings
        assert "wpa=" not in content

        # Cleanup
        config_path.unlink()

    def test_hostapd_config_with_password(self):
        """Hostapd config with password should include WPA settings."""
        config = HotspotConfig(ssid="SecureNetwork", password="mypassword")
        manager = HotspotManager(config=config)

        config_path = manager._write_hostapd_config()

        content = config_path.read_text()
        assert "wpa=2" in content
        assert "wpa_passphrase=mypassword" in content

        # Cleanup
        config_path.unlink()

    def test_dnsmasq_config_content(self, manager: HotspotManager):
        """Generated dnsmasq config should have correct content."""
        config_path = manager._write_dnsmasq_config()

        content = config_path.read_text()
        assert "interface=wlan0" in content
        assert "dhcp-range=" in content
        # Should redirect captive portal detection URLs
        assert "connectivitycheck.gstatic.com" in content
        assert "captive.apple.com" in content

        # Cleanup
        config_path.unlink()

    @pytest.mark.asyncio
    async def test_cleanup_removes_temp_files(self, manager: HotspotManager):
        """Stop should clean up temp config files."""
        # Create temp files
        hostapd_conf = manager._write_hostapd_config()
        dnsmasq_conf = manager._write_dnsmasq_config()

        assert hostapd_conf.exists()
        assert dnsmasq_conf.exists()

        with patch.object(manager, "_reset_interface", new_callable=AsyncMock):
            await manager.stop()

        assert not hostapd_conf.exists()
        assert not dnsmasq_conf.exists()
