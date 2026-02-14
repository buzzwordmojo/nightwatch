"""
First-boot detection for Nightwatch.

Determines whether the system needs initial setup, has partial configuration,
or is fully configured and ready to monitor.
"""

from __future__ import annotations

import logging
from enum import Enum, auto
from pathlib import Path
from typing import NamedTuple

logger = logging.getLogger(__name__)

# Default paths - can be overridden for testing
DEFAULT_CONFIG_DIR = Path("/etc/nightwatch")
CONFIGURED_FLAG = ".configured"
WIFI_CONFIG_FILE = "wifi.conf"
MONITOR_NAME_FILE = "monitor_name"


class SetupState(Enum):
    """Current setup state of the Nightwatch system."""

    UNCONFIGURED = auto()  # First boot, needs full setup
    WIFI_ONLY = auto()  # WiFi configured but setup incomplete
    FULLY_CONFIGURED = auto()  # Ready to monitor


class SetupStatus(NamedTuple):
    """Detailed setup status with diagnostic info."""

    state: SetupState
    has_wifi: bool
    has_name: bool
    has_configured_flag: bool
    config_dir_exists: bool
    message: str


def detect_setup_state(config_dir: Path | None = None) -> SetupState:
    """
    Detect the current setup state of the system.

    Args:
        config_dir: Override config directory (for testing)

    Returns:
        SetupState indicating what setup is needed
    """
    status = get_setup_status(config_dir)
    return status.state


def get_setup_status(config_dir: Path | None = None) -> SetupStatus:
    """
    Get detailed setup status with diagnostic information.

    Args:
        config_dir: Override config directory (for testing)

    Returns:
        SetupStatus with full details
    """
    config_dir = config_dir or DEFAULT_CONFIG_DIR

    # Check if config directory exists
    config_dir_exists = config_dir.exists() and config_dir.is_dir()
    if not config_dir_exists:
        logger.info(f"Config directory {config_dir} does not exist - unconfigured")
        return SetupStatus(
            state=SetupState.UNCONFIGURED,
            has_wifi=False,
            has_name=False,
            has_configured_flag=False,
            config_dir_exists=False,
            message="First boot - config directory not found",
        )

    # Check individual configuration files
    has_configured_flag = (config_dir / CONFIGURED_FLAG).exists()
    has_wifi = _check_wifi_configured(config_dir / WIFI_CONFIG_FILE)
    has_name = _check_name_configured(config_dir / MONITOR_NAME_FILE)

    # Determine state
    if has_configured_flag and has_wifi:
        logger.info("System is fully configured")
        return SetupStatus(
            state=SetupState.FULLY_CONFIGURED,
            has_wifi=has_wifi,
            has_name=has_name,
            has_configured_flag=has_configured_flag,
            config_dir_exists=True,
            message="System configured and ready",
        )
    elif has_wifi:
        logger.info("WiFi configured but setup incomplete")
        return SetupStatus(
            state=SetupState.WIFI_ONLY,
            has_wifi=has_wifi,
            has_name=has_name,
            has_configured_flag=has_configured_flag,
            config_dir_exists=True,
            message="WiFi connected - continue setup in dashboard",
        )
    else:
        logger.info("System unconfigured - starting setup mode")
        return SetupStatus(
            state=SetupState.UNCONFIGURED,
            has_wifi=False,
            has_name=has_name,
            has_configured_flag=has_configured_flag,
            config_dir_exists=True,
            message="WiFi not configured - starting hotspot",
        )


def _check_wifi_configured(wifi_config_path: Path) -> bool:
    """Check if WiFi credentials are configured."""
    if not wifi_config_path.exists():
        return False

    try:
        content = wifi_config_path.read_text().strip()
        # Must have at least an SSID
        return "ssid=" in content.lower() and len(content) > 10
    except (OSError, IOError) as e:
        logger.warning(f"Could not read WiFi config: {e}")
        return False


def _check_name_configured(name_path: Path) -> bool:
    """Check if monitor name is configured."""
    if not name_path.exists():
        return False

    try:
        name = name_path.read_text().strip()
        return len(name) >= 1
    except (OSError, IOError) as e:
        logger.warning(f"Could not read monitor name: {e}")
        return False


def mark_configured(config_dir: Path | None = None) -> None:
    """
    Mark the system as fully configured.

    Creates the .configured flag file to indicate setup is complete.
    """
    config_dir = config_dir or DEFAULT_CONFIG_DIR
    config_dir.mkdir(parents=True, exist_ok=True)
    flag_path = config_dir / CONFIGURED_FLAG
    flag_path.touch()
    logger.info(f"System marked as configured: {flag_path}")


def reset_configuration(config_dir: Path | None = None) -> None:
    """
    Reset configuration to trigger setup mode on next boot.

    Removes the .configured flag but preserves other settings.
    """
    config_dir = config_dir or DEFAULT_CONFIG_DIR
    flag_path = config_dir / CONFIGURED_FLAG

    if flag_path.exists():
        flag_path.unlink()
        logger.info(f"Configuration reset - removed {flag_path}")
    else:
        logger.info("Configuration was not set - nothing to reset")
