"""
Tests for WiFi provisioning.

Covers:
- Credential saving
- NetworkManager (nmcli) connection flow
- IP address retrieval
- Network scanning
"""

from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from nightwatch.setup.provisioning import WiFiProvisioner, provision_wifi


# =============================================================================
# WiFiProvisioner Tests
# =============================================================================


class TestWiFiProvisioner:
    """Tests for WiFiProvisioner."""

    @pytest.fixture
    def temp_config_dir(self, tmp_path):
        """Create temporary config directory."""
        return tmp_path

    @pytest.fixture
    def provisioner(self, temp_config_dir):
        """Create provisioner with temp directory."""
        return WiFiProvisioner(
            config_dir=temp_config_dir,
            interface="wlan0",
        )

    @pytest.mark.asyncio
    async def test_save_credentials_creates_file(self, provisioner, temp_config_dir):
        """Save credentials creates wifi.conf file."""
        await provisioner.save_credentials("TestNetwork", "password123")

        wifi_conf = temp_config_dir / "wifi.conf"
        assert wifi_conf.exists()

    @pytest.mark.asyncio
    async def test_save_credentials_content(self, provisioner, temp_config_dir):
        """Save credentials writes correct content."""
        await provisioner.save_credentials("MyWiFi", "secretpass")

        wifi_conf = temp_config_dir / "wifi.conf"
        content = wifi_conf.read_text()

        assert "ssid=MyWiFi" in content
        assert "password=secretpass" in content

    @pytest.mark.asyncio
    async def test_save_credentials_restricted_permissions(
        self, provisioner, temp_config_dir
    ):
        """Save credentials sets restricted permissions."""
        await provisioner.save_credentials("TestNet", "pass123")

        wifi_conf = temp_config_dir / "wifi.conf"
        mode = wifi_conf.stat().st_mode & 0o777

        assert mode == 0o600

    @pytest.mark.asyncio
    async def test_save_credentials_creates_directory(self, tmp_path):
        """Save credentials creates config directory if missing."""
        new_dir = tmp_path / "subdir" / "config"
        provisioner = WiFiProvisioner(config_dir=new_dir)

        await provisioner.save_credentials("TestNet", "pass123")

        assert new_dir.exists()

    @pytest.mark.asyncio
    async def test_connect_calls_nmcli(self, provisioner, temp_config_dir):
        """Connect calls nmcli to connect to network."""
        # Save credentials first
        await provisioner.save_credentials("TestNetwork", "password123")

        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
            mock_proc = AsyncMock()
            mock_proc.communicate = AsyncMock(return_value=(b"", b""))
            mock_proc.returncode = 0
            mock_exec.return_value = mock_proc

            result = await provisioner.connect("TestNetwork", "password123")

        assert result is True
        # Verify nmcli was called with correct args
        mock_exec.assert_called_once()
        call_args = mock_exec.call_args[0]
        assert "nmcli" in call_args
        assert "wifi" in call_args
        assert "connect" in call_args
        assert "TestNetwork" in call_args

    @pytest.mark.asyncio
    async def test_connect_failure_returns_false(self, provisioner, temp_config_dir):
        """Connect returns False on nmcli failure."""
        await provisioner.save_credentials("TestNetwork", "wrongpass")

        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
            mock_proc = AsyncMock()
            mock_proc.communicate = AsyncMock(
                return_value=(b"", b"Error: Secrets were required, but not provided")
            )
            mock_proc.returncode = 1
            mock_exec.return_value = mock_proc

            result = await provisioner.connect("TestNetwork", "wrongpass")

        assert result is False

    @pytest.mark.asyncio
    async def test_connect_loads_saved_credentials(self, provisioner, temp_config_dir):
        """Connect loads credentials from saved file if not provided."""
        await provisioner.save_credentials("SavedNetwork", "savedpass")

        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
            mock_proc = AsyncMock()
            mock_proc.communicate = AsyncMock(return_value=(b"", b""))
            mock_proc.returncode = 0
            mock_exec.return_value = mock_proc

            result = await provisioner.connect()

        assert result is True
        call_args = mock_exec.call_args[0]
        assert "SavedNetwork" in call_args

    @pytest.mark.asyncio
    async def test_connect_error_returns_false(self, provisioner):
        """Connect returns False on exception."""
        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
            mock_exec.side_effect = Exception("nmcli failed")

            result = await provisioner.connect("TestNet", "pass")

        assert result is False

    @pytest.mark.asyncio
    async def test_test_connection_success(self, provisioner):
        """Test connection returns True on ping success."""
        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
            mock_proc = AsyncMock()
            mock_proc.wait = AsyncMock()
            mock_proc.returncode = 0
            mock_exec.return_value = mock_proc

            result = await provisioner.test_connection()

        assert result is True

    @pytest.mark.asyncio
    async def test_test_connection_failure(self, provisioner):
        """Test connection returns False on ping failure."""
        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
            mock_proc = AsyncMock()
            mock_proc.wait = AsyncMock()
            mock_proc.returncode = 1
            mock_exec.return_value = mock_proc

            result = await provisioner.test_connection()

        assert result is False

    @pytest.mark.asyncio
    async def test_test_connection_exception(self, provisioner):
        """Test connection returns False on exception."""
        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
            mock_exec.side_effect = Exception("Ping failed")

            result = await provisioner.test_connection()

        assert result is False

    @pytest.mark.asyncio
    async def test_get_current_ssid(self, provisioner):
        """Get current SSID returns connected network."""
        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
            mock_proc = AsyncMock()
            mock_proc.communicate = AsyncMock(return_value=(b"MyNetwork\n", b""))
            mock_exec.return_value = mock_proc

            result = await provisioner.get_current_ssid()

        assert result == "MyNetwork"

    @pytest.mark.asyncio
    async def test_get_current_ssid_not_connected(self, provisioner):
        """Get current SSID returns None when not connected."""
        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
            mock_proc = AsyncMock()
            mock_proc.communicate = AsyncMock(return_value=(b"", b""))
            mock_exec.return_value = mock_proc

            result = await provisioner.get_current_ssid()

        assert result is None

    @pytest.mark.asyncio
    async def test_get_current_ssid_exception(self, provisioner):
        """Get current SSID returns None on exception."""
        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
            mock_exec.side_effect = Exception("Command failed")

            result = await provisioner.get_current_ssid()

        assert result is None

    @pytest.mark.asyncio
    async def test_get_ip_address(self, provisioner):
        """Get IP address returns interface IP."""
        ip_output = b"""2: wlan0: <BROADCAST,MULTICAST,UP,LOWER_UP>
    link/ether 12:34:56:78:9a:bc
    inet 192.168.1.100/24 brd 192.168.1.255 scope global wlan0
       valid_lft forever preferred_lft forever
"""
        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
            mock_proc = AsyncMock()
            mock_proc.communicate = AsyncMock(return_value=(ip_output, b""))
            mock_exec.return_value = mock_proc

            result = await provisioner.get_ip_address()

        assert result == "192.168.1.100"

    @pytest.mark.asyncio
    async def test_get_ip_address_no_ip(self, provisioner):
        """Get IP address returns None when no IP assigned."""
        ip_output = b"""2: wlan0: <BROADCAST,MULTICAST>
    link/ether 12:34:56:78:9a:bc
"""
        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
            mock_proc = AsyncMock()
            mock_proc.communicate = AsyncMock(return_value=(ip_output, b""))
            mock_exec.return_value = mock_proc

            result = await provisioner.get_ip_address()

        assert result is None

    @pytest.mark.asyncio
    async def test_get_ip_address_exception(self, provisioner):
        """Get IP address returns None on exception."""
        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
            mock_exec.side_effect = Exception("Command failed")

            result = await provisioner.get_ip_address()

        assert result is None

    @pytest.mark.asyncio
    async def test_disconnect(self, provisioner):
        """Disconnect calls nmcli disconnect."""
        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
            mock_proc = AsyncMock()
            mock_proc.returncode = 0
            mock_exec.return_value = mock_proc

            await provisioner.disconnect()

        mock_exec.assert_called_once()
        call_args = mock_exec.call_args[0]
        assert "nmcli" in call_args
        assert "disconnect" in call_args

    @pytest.mark.asyncio
    async def test_disconnect_error_handled(self, provisioner):
        """Disconnect handles errors gracefully."""
        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
            mock_exec.side_effect = Exception("Command failed")

            # Should not raise
            await provisioner.disconnect()

    @pytest.mark.asyncio
    async def test_forget_network_removes_config(self, provisioner, temp_config_dir):
        """Forget network removes credentials file."""
        # Create wifi.conf
        wifi_conf = temp_config_dir / "wifi.conf"
        wifi_conf.write_text("ssid=OldNetwork\npassword=oldpass\n")

        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
            mock_proc = AsyncMock()
            mock_exec.return_value = mock_proc

            await provisioner.forget_network("OldNetwork")

        assert not wifi_conf.exists()

    @pytest.mark.asyncio
    async def test_forget_network_calls_nmcli(self, provisioner, temp_config_dir):
        """Forget network calls nmcli to delete connection."""
        wifi_conf = temp_config_dir / "wifi.conf"
        wifi_conf.write_text("ssid=OldNetwork\npassword=oldpass\n")

        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
            mock_proc = AsyncMock()
            mock_exec.return_value = mock_proc

            await provisioner.forget_network("OldNetwork")

        mock_exec.assert_called_once()
        call_args = mock_exec.call_args[0]
        assert "nmcli" in call_args
        assert "delete" in call_args
        assert "OldNetwork" in call_args

    @pytest.mark.asyncio
    async def test_forget_network_missing_file(self, provisioner):
        """Forget network handles missing file."""
        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
            mock_proc = AsyncMock()
            mock_exec.return_value = mock_proc

            # Should not raise
            await provisioner.forget_network("NonExistent")

    @pytest.mark.asyncio
    async def test_is_connected_true(self, provisioner):
        """Is connected returns True when connected."""
        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
            mock_proc = AsyncMock()
            mock_proc.communicate = AsyncMock(
                return_value=(b"STATE:connected\n", b"")
            )
            mock_exec.return_value = mock_proc

            result = await provisioner.is_connected()

        assert result is True

    @pytest.mark.asyncio
    async def test_is_connected_false(self, provisioner):
        """Is connected returns False when not connected."""
        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
            mock_proc = AsyncMock()
            mock_proc.communicate = AsyncMock(
                return_value=(b"STATE:disconnected\n", b"")
            )
            mock_exec.return_value = mock_proc

            result = await provisioner.is_connected()

        assert result is False


class TestWiFiProvisionerScanning:
    """Tests for WiFi network scanning."""

    @pytest.fixture
    def provisioner(self, tmp_path):
        """Create provisioner."""
        return WiFiProvisioner(config_dir=tmp_path)

    @pytest.mark.asyncio
    async def test_scan_networks_parses_output(self, provisioner):
        """Scan networks parses nmcli output correctly."""
        nmcli_output = b"HomeNetwork:85:WPA2\nGuestWiFi:72:WPA2\nOpenNet:45:\n"

        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
            # Mock rescan (first call)
            rescan_proc = AsyncMock()
            rescan_proc.returncode = 0

            # Mock list (second call)
            list_proc = AsyncMock()
            list_proc.communicate = AsyncMock(return_value=(nmcli_output, b""))

            mock_exec.side_effect = [rescan_proc, list_proc]

            with patch("asyncio.sleep", new_callable=AsyncMock):
                networks = await provisioner.scan_networks()

        assert len(networks) == 3
        assert networks[0]["ssid"] == "HomeNetwork"
        assert networks[0]["signal"] == 85
        assert networks[1]["ssid"] == "GuestWiFi"
        assert networks[1]["signal"] == 72

    @pytest.mark.asyncio
    async def test_scan_networks_sorted_by_signal(self, provisioner):
        """Scan networks returns results sorted by signal strength."""
        nmcli_output = b"WeakNet:25:WPA2\nStrongNet:95:WPA2\nMediumNet:60:WPA2\n"

        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
            rescan_proc = AsyncMock()
            rescan_proc.returncode = 0

            list_proc = AsyncMock()
            list_proc.communicate = AsyncMock(return_value=(nmcli_output, b""))

            mock_exec.side_effect = [rescan_proc, list_proc]

            with patch("asyncio.sleep", new_callable=AsyncMock):
                networks = await provisioner.scan_networks()

        assert networks[0]["ssid"] == "StrongNet"
        assert networks[1]["ssid"] == "MediumNet"
        assert networks[2]["ssid"] == "WeakNet"

    @pytest.mark.asyncio
    async def test_scan_networks_deduplicates(self, provisioner):
        """Scan networks removes duplicate SSIDs."""
        nmcli_output = b"HomeNetwork:85:WPA2\nHomeNetwork:72:WPA2\nHomeNetwork:60:WPA2\n"

        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
            rescan_proc = AsyncMock()
            rescan_proc.returncode = 0

            list_proc = AsyncMock()
            list_proc.communicate = AsyncMock(return_value=(nmcli_output, b""))

            mock_exec.side_effect = [rescan_proc, list_proc]

            with patch("asyncio.sleep", new_callable=AsyncMock):
                networks = await provisioner.scan_networks()

        assert len(networks) == 1
        assert networks[0]["ssid"] == "HomeNetwork"

    @pytest.mark.asyncio
    async def test_scan_networks_error_returns_empty(self, provisioner):
        """Scan networks returns empty list on error."""
        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
            mock_exec.side_effect = Exception("nmcli failed")

            networks = await provisioner.scan_networks()

        assert networks == []


# =============================================================================
# provision_wifi Function Tests
# =============================================================================


class TestProvisionWifiFunction:
    """Tests for provision_wifi convenience function."""

    @pytest.mark.asyncio
    async def test_provision_wifi_success(self, tmp_path):
        """Provision wifi returns True on success."""
        with patch(
            "nightwatch.setup.provisioning.WiFiProvisioner"
        ) as mock_class:
            mock_provisioner = AsyncMock()
            mock_provisioner.save_credentials = AsyncMock()
            mock_provisioner.connect = AsyncMock(return_value=True)
            mock_class.return_value = mock_provisioner

            result = await provision_wifi("TestNet", "password")

        assert result is True
        mock_provisioner.save_credentials.assert_called_once_with("TestNet", "password")
        mock_provisioner.connect.assert_called_once_with("TestNet", "password")

    @pytest.mark.asyncio
    async def test_provision_wifi_failure(self, tmp_path):
        """Provision wifi returns False on connection failure."""
        with patch(
            "nightwatch.setup.provisioning.WiFiProvisioner"
        ) as mock_class:
            mock_provisioner = AsyncMock()
            mock_provisioner.save_credentials = AsyncMock()
            mock_provisioner.connect = AsyncMock(return_value=False)
            mock_class.return_value = mock_provisioner

            result = await provision_wifi("TestNet", "wrongpass")

        assert result is False


# =============================================================================
# Edge Cases
# =============================================================================


class TestProvisioningEdgeCases:
    """Edge case tests for provisioning."""

    @pytest.fixture
    def provisioner(self, tmp_path):
        """Create provisioner."""
        return WiFiProvisioner(config_dir=tmp_path)

    @pytest.mark.asyncio
    async def test_ssid_with_special_characters(self, provisioner):
        """SSID with special characters is handled."""
        await provisioner.save_credentials('My "Weird" Network!', "pass123")

        wifi_conf = provisioner.config_dir / "wifi.conf"
        content = wifi_conf.read_text()

        assert 'My "Weird" Network!' in content

    @pytest.mark.asyncio
    async def test_password_with_special_characters(self, provisioner):
        """Password with special characters is handled."""
        await provisioner.save_credentials("TestNet", 'P@$$w0rd!"#$%')

        wifi_conf = provisioner.config_dir / "wifi.conf"
        content = wifi_conf.read_text()

        assert 'P@$$w0rd!"#$%' in content

    @pytest.mark.asyncio
    async def test_empty_ssid(self, provisioner):
        """Empty SSID is saved (validation should be elsewhere)."""
        await provisioner.save_credentials("", "password")

        wifi_conf = provisioner.config_dir / "wifi.conf"
        assert wifi_conf.exists()

    @pytest.mark.asyncio
    async def test_empty_password(self, provisioner):
        """Empty password is saved (for open networks)."""
        await provisioner.save_credentials("OpenNetwork", "")

        wifi_conf = provisioner.config_dir / "wifi.conf"
        content = wifi_conf.read_text()

        assert "password=" in content

    def test_custom_interface(self, tmp_path):
        """Custom interface is used."""
        provisioner = WiFiProvisioner(config_dir=tmp_path, interface="wlan1")
        assert provisioner.interface == "wlan1"

    @pytest.mark.asyncio
    async def test_multiple_ip_addresses(self, provisioner):
        """Get IP address returns first IPv4 address."""
        ip_output = b"""2: wlan0: <BROADCAST,MULTICAST,UP,LOWER_UP>
    inet 192.168.1.100/24 brd 192.168.1.255 scope global wlan0
    inet 192.168.1.101/24 brd 192.168.1.255 scope global secondary wlan0
"""
        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
            mock_proc = AsyncMock()
            mock_proc.communicate = AsyncMock(return_value=(ip_output, b""))
            mock_exec.return_value = mock_proc

            result = await provisioner.get_ip_address()

        assert result == "192.168.1.100"

    @pytest.mark.asyncio
    async def test_connect_without_saved_credentials_fails(self, provisioner):
        """Connect without saved credentials returns False."""
        result = await provisioner.connect()
        assert result is False

    @pytest.mark.asyncio
    async def test_load_credentials(self, provisioner, tmp_path):
        """Load credentials reads from wifi.conf."""
        wifi_conf = tmp_path / "wifi.conf"
        wifi_conf.write_text("ssid=SavedNet\npassword=savedpass\n")

        result = await provisioner._load_credentials()

        assert result == ("SavedNet", "savedpass")

    @pytest.mark.asyncio
    async def test_load_credentials_missing_file(self, provisioner):
        """Load credentials returns None when file missing."""
        result = await provisioner._load_credentials()
        assert result is None

    @pytest.mark.asyncio
    async def test_load_credentials_invalid_format(self, provisioner, tmp_path):
        """Load credentials returns None for invalid format."""
        wifi_conf = tmp_path / "wifi.conf"
        wifi_conf.write_text("invalid content\n")

        result = await provisioner._load_credentials()

        assert result is None
