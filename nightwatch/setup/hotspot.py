"""
WiFi hotspot management for Nightwatch setup.

Creates a WiFi access point for initial device configuration using
hostapd and dnsmasq on Raspberry Pi.
"""

from __future__ import annotations

import asyncio
import logging
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

logger = logging.getLogger(__name__)

# Default configuration
DEFAULT_SSID_PREFIX = "Nightwatch"
DEFAULT_GATEWAY_IP = "192.168.4.1"
DEFAULT_DHCP_RANGE_START = "192.168.4.10"
DEFAULT_DHCP_RANGE_END = "192.168.4.50"
DEFAULT_INTERFACE = "wlan0"


@dataclass
class HotspotConfig:
    """Configuration for the WiFi hotspot."""

    ssid: str = ""  # Will be generated if empty
    password: str | None = None  # None = open network
    channel: int = 6
    interface: str = DEFAULT_INTERFACE
    gateway_ip: str = DEFAULT_GATEWAY_IP
    dhcp_range_start: str = DEFAULT_DHCP_RANGE_START
    dhcp_range_end: str = DEFAULT_DHCP_RANGE_END
    dhcp_lease_time: str = "12h"

    def __post_init__(self) -> None:
        if not self.ssid:
            self.ssid = self._generate_ssid()

    def _generate_ssid(self) -> str:
        """Generate SSID with last 4 chars of MAC address."""
        try:
            mac = self._get_mac_address()
            suffix = mac.replace(":", "")[-4:].upper()
            return f"{DEFAULT_SSID_PREFIX}-{suffix}"
        except Exception as e:
            logger.warning(f"Could not get MAC address: {e}")
            return f"{DEFAULT_SSID_PREFIX}-XXXX"

    def _get_mac_address(self) -> str:
        """Get MAC address of the wireless interface."""
        mac_path = Path(f"/sys/class/net/{self.interface}/address")
        if mac_path.exists():
            return mac_path.read_text().strip()
        raise FileNotFoundError(f"No MAC address for {self.interface}")


@dataclass
class HotspotManager:
    """
    Manages WiFi hotspot for device setup.

    Creates and controls a WiFi access point using hostapd and dnsmasq,
    allowing users to connect and configure the device.
    """

    config: HotspotConfig = field(default_factory=HotspotConfig)
    _hostapd_process: subprocess.Popen | None = field(default=None, init=False)
    _dnsmasq_process: subprocess.Popen | None = field(default=None, init=False)
    _temp_files: list[Path] = field(default_factory=list, init=False)
    _running: bool = field(default=False, init=False)

    @property
    def is_running(self) -> bool:
        """Check if hotspot is currently active."""
        return self._running

    @property
    def ssid(self) -> str:
        """Get the SSID being broadcast."""
        return self.config.ssid

    async def start(self) -> bool:
        """
        Start the WiFi hotspot.

        Returns:
            True if hotspot started successfully
        """
        if self._running:
            logger.warning("Hotspot already running")
            return True

        logger.info(f"Starting hotspot with SSID: {self.config.ssid}")

        try:
            # Configure network interface
            await self._configure_interface()

            # Generate and write config files
            hostapd_conf = self._write_hostapd_config()
            dnsmasq_conf = self._write_dnsmasq_config()

            # Start hostapd
            self._hostapd_process = await self._start_hostapd(hostapd_conf)

            # Start dnsmasq
            self._dnsmasq_process = await self._start_dnsmasq(dnsmasq_conf)

            self._running = True
            logger.info(f"Hotspot started: {self.config.ssid} on {self.config.gateway_ip}")
            return True

        except Exception as e:
            logger.error(f"Failed to start hotspot: {e}")
            await self.stop()
            return False

    async def stop(self) -> None:
        """Stop the WiFi hotspot and cleanup."""
        logger.info("Stopping hotspot")

        # Kill hostapd
        if self._hostapd_process:
            self._hostapd_process.terminate()
            try:
                self._hostapd_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._hostapd_process.kill()
            self._hostapd_process = None

        # Kill dnsmasq
        if self._dnsmasq_process:
            self._dnsmasq_process.terminate()
            try:
                self._dnsmasq_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._dnsmasq_process.kill()
            self._dnsmasq_process = None

        # Cleanup temp files
        for temp_file in self._temp_files:
            try:
                temp_file.unlink(missing_ok=True)
            except Exception as e:
                logger.warning(f"Could not remove temp file {temp_file}: {e}")
        self._temp_files.clear()

        # Reset interface
        await self._reset_interface()

        self._running = False
        logger.info("Hotspot stopped")

    async def _configure_interface(self) -> None:
        """Configure the wireless interface for AP mode."""
        interface = self.config.interface
        gateway = self.config.gateway_ip

        # First, disconnect from any existing WiFi connection via NetworkManager
        try:
            await self._run_command(["nmcli", "device", "disconnect", interface])
            logger.info(f"Disconnected {interface} from any existing WiFi")
        except Exception:
            pass  # May not be connected

        commands = [
            # Bring interface down
            ["ip", "link", "set", interface, "down"],
            # Set IP address
            ["ip", "addr", "flush", "dev", interface],
            ["ip", "addr", "add", f"{gateway}/24", "dev", interface],
            # Bring interface up
            ["ip", "link", "set", interface, "up"],
        ]

        for cmd in commands:
            await self._run_command(cmd)

    async def _reset_interface(self) -> None:
        """Reset wireless interface to managed mode."""
        interface = self.config.interface

        commands = [
            ["ip", "addr", "flush", "dev", interface],
            ["ip", "link", "set", interface, "down"],
        ]

        for cmd in commands:
            try:
                await self._run_command(cmd)
            except Exception as e:
                logger.warning(f"Could not reset interface: {e}")

    def _write_hostapd_config(self) -> Path:
        """Generate and write hostapd configuration."""
        config_content = f"""# Nightwatch hotspot configuration
interface={self.config.interface}
driver=nl80211
ssid={self.config.ssid}
hw_mode=g
channel={self.config.channel}
wmm_enabled=0
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
"""
        if self.config.password:
            config_content += f"""wpa=2
wpa_passphrase={self.config.password}
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP
"""

        temp_file = Path(tempfile.mktemp(prefix="nightwatch_hostapd_", suffix=".conf"))
        temp_file.write_text(config_content)
        self._temp_files.append(temp_file)
        return temp_file

    def _write_dnsmasq_config(self) -> Path:
        """Generate and write dnsmasq configuration for DHCP and DNS."""
        config_content = f"""# Nightwatch dnsmasq configuration
interface={self.config.interface}
bind-interfaces
dhcp-range={self.config.dhcp_range_start},{self.config.dhcp_range_end},{self.config.dhcp_lease_time}

# Redirect all DNS queries to captive portal
address=/#/{self.config.gateway_ip}

# Android captive portal detection
address=/connectivitycheck.gstatic.com/{self.config.gateway_ip}
address=/clients3.google.com/{self.config.gateway_ip}

# iOS captive portal detection
address=/captive.apple.com/{self.config.gateway_ip}
address=/www.apple.com/{self.config.gateway_ip}

# Windows captive portal detection
address=/www.msftconnecttest.com/{self.config.gateway_ip}
"""
        temp_file = Path(tempfile.mktemp(prefix="nightwatch_dnsmasq_", suffix=".conf"))
        temp_file.write_text(config_content)
        self._temp_files.append(temp_file)
        return temp_file

    async def _start_hostapd(self, config_path: Path) -> subprocess.Popen:
        """Start hostapd process."""
        cmd = ["hostapd", str(config_path)]
        logger.debug(f"Starting hostapd: {' '.join(cmd)}")

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        # Give it a moment to start
        await asyncio.sleep(1)

        if process.poll() is not None:
            _, stderr = process.communicate()
            raise RuntimeError(f"hostapd failed to start: {stderr.decode()}")

        return process

    async def _start_dnsmasq(self, config_path: Path) -> subprocess.Popen:
        """Start dnsmasq process."""
        cmd = ["dnsmasq", "-C", str(config_path), "-d"]  # -d = don't daemonize
        logger.debug(f"Starting dnsmasq: {' '.join(cmd)}")

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        # Give it a moment to start
        await asyncio.sleep(0.5)

        if process.poll() is not None:
            _, stderr = process.communicate()
            raise RuntimeError(f"dnsmasq failed to start: {stderr.decode()}")

        return process

    async def _run_command(self, cmd: list[str]) -> str:
        """Run a shell command and return output."""
        logger.debug(f"Running: {' '.join(cmd)}")
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout


# Convenience function for simple usage
async def create_hotspot(
    ssid: str | None = None,
    password: str | None = None,
) -> HotspotManager:
    """
    Create and start a WiFi hotspot.

    Args:
        ssid: Network name (auto-generated if None)
        password: Network password (open network if None)

    Returns:
        Running HotspotManager instance
    """
    config = HotspotConfig(ssid=ssid or "", password=password)
    manager = HotspotManager(config=config)
    await manager.start()
    return manager
