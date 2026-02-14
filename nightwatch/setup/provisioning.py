"""
WiFi provisioning for Nightwatch.

Handles saving WiFi credentials, connecting to networks, and verifying connectivity.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

# Configuration paths
DEFAULT_CONFIG_DIR = Path("/etc/nightwatch")
WIFI_CONFIG_FILE = "wifi.conf"
WPA_SUPPLICANT_CONF = Path("/etc/wpa_supplicant/wpa_supplicant.conf")


@dataclass
class WiFiProvisioner:
    """
    Manages WiFi credential storage and network connection.

    Handles saving credentials in both Nightwatch config and
    wpa_supplicant format for system-level connectivity.
    """

    config_dir: Path = DEFAULT_CONFIG_DIR
    interface: str = "wlan0"

    async def save_credentials(self, ssid: str, password: str) -> None:
        """
        Save WiFi credentials for network connection.

        Args:
            ssid: Network name
            password: Network password
        """
        logger.info(f"Saving WiFi credentials for: {ssid}")

        # Ensure config directory exists
        self.config_dir.mkdir(parents=True, exist_ok=True)

        # Save to Nightwatch config
        wifi_config = self.config_dir / WIFI_CONFIG_FILE
        wifi_config.write_text(f"ssid={ssid}\npassword={password}\n")
        wifi_config.chmod(0o600)  # Restrict permissions

        # Generate wpa_supplicant config
        await self._update_wpa_supplicant(ssid, password)

        logger.info("WiFi credentials saved")

    async def connect(self) -> bool:
        """
        Connect to the configured WiFi network.

        Returns:
            True if connection successful
        """
        logger.info("Attempting WiFi connection")

        try:
            # Reconfigure wpa_supplicant to use new credentials
            await self._run_command(["wpa_cli", "-i", self.interface, "reconfigure"])

            # Wait for connection
            for _ in range(30):  # 30 second timeout
                if await self._check_connected():
                    logger.info("WiFi connected successfully")
                    return True
                await asyncio.sleep(1)

            logger.warning("WiFi connection timed out")
            return False

        except Exception as e:
            logger.error(f"WiFi connection failed: {e}")
            return False

    async def test_connection(self) -> bool:
        """
        Test if we have internet connectivity.

        Returns:
            True if internet is reachable
        """
        try:
            # Try to ping a reliable host
            result = await asyncio.create_subprocess_exec(
                "ping", "-c", "1", "-W", "5", "8.8.8.8",
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
            await result.wait()
            return result.returncode == 0
        except Exception:
            return False

    async def get_current_ssid(self) -> str | None:
        """Get the SSID of currently connected network."""
        try:
            result = await asyncio.create_subprocess_exec(
                "iwgetid", "-r",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.DEVNULL,
            )
            stdout, _ = await result.communicate()
            ssid = stdout.decode().strip()
            return ssid if ssid else None
        except Exception:
            return None

    async def get_ip_address(self) -> str | None:
        """Get the IP address of the wireless interface."""
        try:
            result = await asyncio.create_subprocess_exec(
                "ip", "-4", "addr", "show", self.interface,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.DEVNULL,
            )
            stdout, _ = await result.communicate()

            for line in stdout.decode().split("\n"):
                if "inet " in line:
                    # Extract IP from "inet 192.168.1.100/24"
                    ip = line.strip().split()[1].split("/")[0]
                    return ip
            return None
        except Exception:
            return None

    async def disconnect(self) -> None:
        """Disconnect from the current WiFi network."""
        try:
            await self._run_command(["wpa_cli", "-i", self.interface, "disconnect"])
            logger.info("Disconnected from WiFi")
        except Exception as e:
            logger.warning(f"Could not disconnect: {e}")

    async def forget_network(self, ssid: str) -> None:
        """
        Remove saved credentials for a network.

        Args:
            ssid: Network name to forget
        """
        # Remove from Nightwatch config
        wifi_config = self.config_dir / WIFI_CONFIG_FILE
        if wifi_config.exists():
            wifi_config.unlink()
            logger.info(f"Removed credentials for: {ssid}")

        # Note: wpa_supplicant config would need manual cleanup
        # to avoid leaving stale network configs

    async def _update_wpa_supplicant(self, ssid: str, password: str) -> None:
        """Update wpa_supplicant.conf with new network."""
        # Generate PSK using wpa_passphrase
        try:
            result = await asyncio.create_subprocess_exec(
                "wpa_passphrase", ssid, password,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await result.communicate()
            network_block = stdout.decode()

            # Read existing config
            if WPA_SUPPLICANT_CONF.exists():
                existing = WPA_SUPPLICANT_CONF.read_text()
            else:
                existing = """ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1
country=US
"""

            # Remove any existing network block for this SSID
            # (Simple approach - full implementation would parse properly)
            lines = existing.split("\n")
            new_lines = []
            skip_until_close = False

            for line in lines:
                if f'ssid="{ssid}"' in line:
                    # Found existing, skip until closing brace
                    skip_until_close = True
                    # Also remove the preceding "network={" line
                    if new_lines and new_lines[-1].strip() == "network={":
                        new_lines.pop()
                elif skip_until_close and line.strip() == "}":
                    skip_until_close = False
                    continue
                elif not skip_until_close:
                    new_lines.append(line)

            # Add new network block
            new_config = "\n".join(new_lines).rstrip() + "\n\n" + network_block

            # Write back
            WPA_SUPPLICANT_CONF.write_text(new_config)
            WPA_SUPPLICANT_CONF.chmod(0o600)

            logger.debug("Updated wpa_supplicant.conf")

        except Exception as e:
            logger.error(f"Failed to update wpa_supplicant: {e}")
            raise

    async def _check_connected(self) -> bool:
        """Check if WiFi is connected."""
        try:
            result = await asyncio.create_subprocess_exec(
                "wpa_cli", "-i", self.interface, "status",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.DEVNULL,
            )
            stdout, _ = await result.communicate()
            return "wpa_state=COMPLETED" in stdout.decode()
        except Exception:
            return False

    async def _run_command(self, cmd: list[str]) -> str:
        """Run a shell command and return output."""
        result = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await result.communicate()

        if result.returncode != 0:
            raise RuntimeError(f"Command failed: {' '.join(cmd)}\n{stderr.decode()}")

        return stdout.decode()


# Convenience function
async def provision_wifi(ssid: str, password: str) -> bool:
    """
    Configure and connect to a WiFi network.

    Args:
        ssid: Network name
        password: Network password

    Returns:
        True if connected successfully
    """
    provisioner = WiFiProvisioner()
    await provisioner.save_credentials(ssid, password)
    return await provisioner.connect()
