"""
BCG (Ballistocardiography) detector module for Nightwatch.

Detects heart rate and respiration from bed vibrations using
a piezoelectric sensor under the mattress.
"""

from nightwatch.detectors.bcg.detector import BCGDetector, MockBCGDetector

__all__ = ["BCGDetector", "MockBCGDetector"]
