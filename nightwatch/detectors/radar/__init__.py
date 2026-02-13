"""Radar detector module."""

from nightwatch.detectors.radar.detector import RadarDetector
from nightwatch.detectors.radar.ld2450 import LD2450Driver, LD2450Frame, LD2450Target

__all__ = ["RadarDetector", "LD2450Driver", "LD2450Frame", "LD2450Target"]
