"""
Setup and onboarding module for Nightwatch.

Handles first-boot detection, WiFi provisioning, and the setup wizard.
"""

from nightwatch.setup.first_boot import SetupState, detect_setup_state
from nightwatch.setup.hotspot import HotspotManager
from nightwatch.setup.portal import CaptivePortal
from nightwatch.setup.provisioning import WiFiProvisioner

__all__ = [
    "SetupState",
    "detect_setup_state",
    "HotspotManager",
    "CaptivePortal",
    "WiFiProvisioner",
]
