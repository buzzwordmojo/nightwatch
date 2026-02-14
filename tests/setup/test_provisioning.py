"""
Tests for WiFi provisioning.

Covers:
- Credential saving
- wpa_supplicant config generation
- Connection flow
- IP address retrieval
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
        with patch.object(
            provisioner, "_update_wpa_supplicant", new_callable=AsyncMock
        ):
            await provisioner.save_credentials("TestNetwork", "password123")

        wifi_conf = temp_config_dir / "wifi.conf"
        assert wifi_conf.exists()

    @pytest.mark.asyncio
    async def test_save_credentials_content(self, provisioner, temp_config_dir):
        """Save credentials writes correct content."""
        with patch.object(
            provisioner, "_update_wpa_supplicant", new_callable=AsyncMock
        ):
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
        with patch.object(
            provisioner, "_update_wpa_supplicant", new_callable=AsyncMock
        ):
            await provisioner.save_credentials("TestNet", "pass123")

        wifi_conf = temp_config_dir / "wifi.conf"
        mode = wifi_conf.stat().st_mode & 0o777

        assert mode == 0o600

    @pytest.mark.asyncio
    async def test_save_credentials_creates_directory(self, tmp_path):
        """Save credentials creates config directory if missing."""
        new_dir = tmp_path / "subdir" / "config"
        provisioner = WiFiProvisioner(config_dir=new_dir)

        with patch.object(
            provisioner, "_update_wpa_supplicant", new_callable=AsyncMock
        ):
            await provisioner.save_credentials("TestNet", "pass123")

        assert new_dir.exists()

    @pytest.mark.asyncio
    async def test_connect_calls_wpa_cli(self, provisioner):
        """Connect calls wpa_cli reconfigure."""
        with patch.object(
            provisioner, "_run_command", new_callable=AsyncMock
        ) as mock_run:
            with patch.object(
                provisioner, "_check_connected", new_callable=AsyncMock
            ) as mock_check:
                mock_check.return_value = True

                result = await provisioner.connect()

        assert result is True
        mock_run.assert_called_with(
            ["wpa_cli", "-i", "wlan0", "reconfigure"]
        )

    @pytest.mark.asyncio
    async def test_connect_timeout_returns_false(self, provisioner):
        """Connect returns False on timeout."""
        with patch.object(
            provisioner, "_run_command", new_callable=AsyncMock
        ):
            with patch.object(
                provisioner, "_check_connected", new_callable=AsyncMock
            ) as mock_check:
                # Never connects
                mock_check.return_value = False

                # Reduce timeout by mocking sleep
                with patch("asyncio.sleep", new_callable=AsyncMock):
                    result = await provisioner.connect()

        assert result is False

    @pytest.mark.asyncio
    async def test_connect_error_returns_false(self, provisioner):
        """Connect returns False on error."""
        with patch.object(
            provisioner, "_run_command", new_callable=AsyncMock
        ) as mock_run:
            mock_run.side_effect = Exception("wpa_cli failed")

            result = await provisioner.connect()

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
        """Disconnect calls wpa_cli disconnect."""
        with patch.object(
            provisioner, "_run_command", new_callable=AsyncMock
        ) as mock_run:
            await provisioner.disconnect()

        mock_run.assert_called_with(
            ["wpa_cli", "-i", "wlan0", "disconnect"]
        )

    @pytest.mark.asyncio
    async def test_disconnect_error_handled(self, provisioner):
        """Disconnect handles errors gracefully."""
        with patch.object(
            provisioner, "_run_command", new_callable=AsyncMock
        ) as mock_run:
            mock_run.side_effect = Exception("Command failed")

            # Should not raise
            await provisioner.disconnect()

    @pytest.mark.asyncio
    async def test_forget_network(self, provisioner, temp_config_dir):
        """Forget network removes credentials file."""
        # Create wifi.conf
        wifi_conf = temp_config_dir / "wifi.conf"
        wifi_conf.write_text("ssid=OldNetwork\npassword=oldpass\n")

        await provisioner.forget_network("OldNetwork")

        assert not wifi_conf.exists()

    @pytest.mark.asyncio
    async def test_forget_network_missing_file(self, provisioner):
        """Forget network handles missing file."""
        # Should not raise
        await provisioner.forget_network("NonExistent")


class TestWiFiProvisionerWpaSupplicant:
    """Tests for wpa_supplicant config generation."""

    @pytest.fixture
    def provisioner(self, tmp_path):
        """Create provisioner."""
        return WiFiProvisioner(config_dir=tmp_path)

    @pytest.mark.asyncio
    async def test_update_wpa_supplicant_creates_config(self, provisioner, tmp_path):
        """Update wpa_supplicant creates config file."""
        wpa_conf = tmp_path / "wpa_supplicant.conf"

        with patch(
            "nightwatch.setup.provisioning.WPA_SUPPLICANT_CONF",
            wpa_conf,
        ):
            with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
                mock_proc = AsyncMock()
                mock_proc.communicate = AsyncMock(
                    return_value=(
                        b'network={\n    ssid="TestNet"\n    psk=abc123\n}\n',
                        b"",
                    )
                )
                mock_exec.return_value = mock_proc

                await provisioner._update_wpa_supplicant("TestNet", "password")

        assert wpa_conf.exists()

    @pytest.mark.asyncio
    async def test_update_wpa_supplicant_preserves_header(self, provisioner, tmp_path):
        """Update wpa_supplicant preserves header."""
        wpa_conf = tmp_path / "wpa_supplicant.conf"
        wpa_conf.write_text(
            "ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev\n"
            "update_config=1\n"
            "country=US\n"
        )

        with patch(
            "nightwatch.setup.provisioning.WPA_SUPPLICANT_CONF",
            wpa_conf,
        ):
            with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
                mock_proc = AsyncMock()
                mock_proc.communicate = AsyncMock(
                    return_value=(
                        b'network={\n    ssid="NewNet"\n    psk=xyz\n}\n',
                        b"",
                    )
                )
                mock_exec.return_value = mock_proc

                await provisioner._update_wpa_supplicant("NewNet", "password")

        content = wpa_conf.read_text()
        assert "ctrl_interface" in content
        assert "country=US" in content

    @pytest.mark.asyncio
    async def test_update_wpa_supplicant_error(self, provisioner):
        """Update wpa_supplicant raises on error."""
        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
            mock_exec.side_effect = Exception("wpa_passphrase failed")

            with pytest.raises(Exception):
                await provisioner._update_wpa_supplicant("TestNet", "password")


class TestWiFiProvisionerHelpers:
    """Tests for helper methods."""

    @pytest.fixture
    def provisioner(self, tmp_path):
        """Create provisioner."""
        return WiFiProvisioner(config_dir=tmp_path)

    @pytest.mark.asyncio
    async def test_check_connected_true(self, provisioner):
        """Check connected returns True when connected."""
        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
            mock_proc = AsyncMock()
            mock_proc.communicate = AsyncMock(
                return_value=(b"wpa_state=COMPLETED\n", b"")
            )
            mock_exec.return_value = mock_proc

            result = await provisioner._check_connected()

        assert result is True

    @pytest.mark.asyncio
    async def test_check_connected_false(self, provisioner):
        """Check connected returns False when not connected."""
        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
            mock_proc = AsyncMock()
            mock_proc.communicate = AsyncMock(
                return_value=(b"wpa_state=SCANNING\n", b"")
            )
            mock_exec.return_value = mock_proc

            result = await provisioner._check_connected()

        assert result is False

    @pytest.mark.asyncio
    async def test_check_connected_exception(self, provisioner):
        """Check connected returns False on exception."""
        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
            mock_exec.side_effect = Exception("Command failed")

            result = await provisioner._check_connected()

        assert result is False

    @pytest.mark.asyncio
    async def test_run_command_success(self, provisioner):
        """Run command returns stdout."""
        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
            mock_proc = AsyncMock()
            mock_proc.communicate = AsyncMock(return_value=(b"output", b""))
            mock_proc.returncode = 0
            mock_exec.return_value = mock_proc

            result = await provisioner._run_command(["echo", "test"])

        assert result == "output"

    @pytest.mark.asyncio
    async def test_run_command_failure(self, provisioner):
        """Run command raises on failure."""
        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
            mock_proc = AsyncMock()
            mock_proc.communicate = AsyncMock(return_value=(b"", b"error"))
            mock_proc.returncode = 1
            mock_exec.return_value = mock_proc

            with pytest.raises(RuntimeError, match="Command failed"):
                await provisioner._run_command(["false"])


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
        mock_provisioner.connect.assert_called_once()

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
        with patch.object(
            provisioner, "_update_wpa_supplicant", new_callable=AsyncMock
        ):
            await provisioner.save_credentials('My "Weird" Network!', "pass123")

        wifi_conf = provisioner.config_dir / "wifi.conf"
        content = wifi_conf.read_text()

        assert 'My "Weird" Network!' in content

    @pytest.mark.asyncio
    async def test_password_with_special_characters(self, provisioner):
        """Password with special characters is handled."""
        with patch.object(
            provisioner, "_update_wpa_supplicant", new_callable=AsyncMock
        ):
            await provisioner.save_credentials("TestNet", 'P@$$w0rd!"#$%')

        wifi_conf = provisioner.config_dir / "wifi.conf"
        content = wifi_conf.read_text()

        assert 'P@$$w0rd!"#$%' in content

    @pytest.mark.asyncio
    async def test_empty_ssid(self, provisioner):
        """Empty SSID is saved (validation should be elsewhere)."""
        with patch.object(
            provisioner, "_update_wpa_supplicant", new_callable=AsyncMock
        ):
            await provisioner.save_credentials("", "password")

        wifi_conf = provisioner.config_dir / "wifi.conf"
        assert wifi_conf.exists()

    @pytest.mark.asyncio
    async def test_empty_password(self, provisioner):
        """Empty password is saved (for open networks)."""
        with patch.object(
            provisioner, "_update_wpa_supplicant", new_callable=AsyncMock
        ):
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
