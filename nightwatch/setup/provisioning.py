"""
WiFi provisioning for Nightwatch.

Handles saving WiFi credentials, connecting to networks, and verifying connectivity.
Uses NetworkManager (nmcli) for connection management on Raspberry Pi OS Bookworm+.
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


@dataclass
class WiFiProvisioner:
    """
    Manages WiFi credential storage and network connection.

    Uses NetworkManager (nmcli) for connecting to WiFi networks,
    which is the default on Raspberry Pi OS Bookworm and later.
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

        logger.info("WiFi credentials saved")

    async def connect(self, ssid: str | None = None, password: str | None = None) -> bool:
        """
        Connect to a WiFi network using NetworkManager.

        If ssid/password provided, connects to that network.
        Otherwise, reads from saved credentials.

        Returns:
            True if connection successful
        """
        # Load credentials if not provided
        if ssid is None or password is None:
            creds = await self._load_credentials()
            if creds is None:
                logger.error("No WiFi credentials found")
                return False
            ssid, password = creds

        logger.info(f"Attempting WiFi connection to: {ssid}")

        try:
            # Use nmcli to connect
            result = await asyncio.create_subprocess_exec(
                "nmcli", "device", "wifi", "connect", ssid,
                "password", password,
                "ifname", self.interface,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await result.communicate()

            if result.returncode == 0:
                logger.info(f"WiFi connected successfully to {ssid}")
                return True
            else:
                error_msg = stderr.decode().strip() or stdout.decode().strip()
                logger.error(f"WiFi connection failed: {error_msg}")
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
            await asyncio.create_subprocess_exec(
                "nmcli", "device", "disconnect", self.interface,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
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

        # Remove from NetworkManager
        try:
            await asyncio.create_subprocess_exec(
                "nmcli", "connection", "delete", ssid,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
        except Exception:
            pass  # Connection may not exist

    async def is_connected(self) -> bool:
        """Check if WiFi is currently connected."""
        try:
            result = await asyncio.create_subprocess_exec(
                "nmcli", "-t", "-f", "STATE", "device", "show", self.interface,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.DEVNULL,
            )
            stdout, _ = await result.communicate()
            output = stdout.decode()
            # Look for STATE:connected
            return "STATE:connected" in output
        except Exception:
            return False

    async def scan_networks(self) -> list[dict]:
        """
        Scan for available WiFi networks.

        Returns:
            List of dicts with ssid, signal, security info
        """
        try:
            # Trigger a rescan
            await asyncio.create_subprocess_exec(
                "nmcli", "device", "wifi", "rescan",
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
            await asyncio.sleep(2)

            # Get results
            result = await asyncio.create_subprocess_exec(
                "nmcli", "-t", "-f", "SSID,SIGNAL,SECURITY", "device", "wifi", "list",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.DEVNULL,
            )
            stdout, _ = await result.communicate()

            networks = []
            seen_ssids = set()
            for line in stdout.decode().strip().split("\n"):
                if not line:
                    continue
                parts = line.split(":")
                if len(parts) >= 3:
                    ssid = parts[0]
                    if ssid and ssid not in seen_ssids:
                        seen_ssids.add(ssid)
                        networks.append({
                            "ssid": ssid,
                            "signal": int(parts[1]) if parts[1].isdigit() else 0,
                            "security": parts[2] if len(parts) > 2 else "",
                        })

            # Sort by signal strength
            networks.sort(key=lambda x: x["signal"], reverse=True)
            return networks

        except Exception as e:
            logger.error(f"WiFi scan failed: {e}")
            return []

    async def _load_credentials(self) -> tuple[str, str] | None:
        """Load saved WiFi credentials."""
        wifi_config = self.config_dir / WIFI_CONFIG_FILE
        if not wifi_config.exists():
            return None

        try:
            content = wifi_config.read_text()
            ssid = None
            password = None
            for line in content.split("\n"):
                if line.startswith("ssid="):
                    ssid = line[5:].strip()
                elif line.startswith("password="):
                    password = line[9:].strip()
            if ssid and password:
                return (ssid, password)
            return None
        except Exception:
            return None


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
    return await provisioner.connect(ssid, password)
