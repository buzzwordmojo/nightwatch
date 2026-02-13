"""
Bridge module for pushing Nightwatch events to Convex.

Provides real-time synchronization between Python detectors
and the Convex-powered Next.js dashboard.
"""

from nightwatch.bridge.convex import ConvexBridge

__all__ = ["ConvexBridge"]
