"""
Audio detector module for Nightwatch.

Detects breathing sounds, silence (potential apnea), and vocalizations
using a USB microphone.
"""

from nightwatch.detectors.audio.detector import AudioDetector, MockAudioDetector

__all__ = ["AudioDetector", "MockAudioDetector"]
