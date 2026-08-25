"""Radar detector module."""

from nightwatch.detectors.radar.detector import (
    RadarDetector,
    MockRadarDetector,
    LD6002Detector,
)
from nightwatch.detectors.radar.ld2450 import LD2450Driver, LD2450Frame, LD2450Target
from nightwatch.detectors.radar.ld6002 import LD6002Driver, LD6002Frame, LD6002Reading

__all__ = [
    "RadarDetector", "MockRadarDetector", "LD6002Detector",
    "LD2450Driver", "LD2450Frame", "LD2450Target",
    "LD6002Driver", "LD6002Frame", "LD6002Reading",
]
