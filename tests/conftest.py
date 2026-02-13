"""Pytest configuration and fixtures."""

import pytest
import asyncio
from pathlib import Path

from nightwatch.core.config import Config
from nightwatch.core.events import Event, EventState


@pytest.fixture
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def default_config():
    """Default configuration for testing."""
    return Config.default()


@pytest.fixture
def sample_event():
    """Sample radar event for testing."""
    import time
    return Event(
        detector="radar",
        timestamp=time.time(),
        confidence=0.9,
        state=EventState.NORMAL,
        value={
            "respiration_rate": 14.0,
            "heart_rate_estimate": 70.0,
            "movement": 0.1,
            "presence": True,
        },
    )


@pytest.fixture
def low_respiration_event():
    """Event with low respiration for alert testing."""
    import time
    return Event(
        detector="radar",
        timestamp=time.time(),
        confidence=0.9,
        state=EventState.WARNING,
        value={
            "respiration_rate": 5.0,
            "heart_rate_estimate": 70.0,
            "movement": 0.1,
            "presence": True,
        },
    )
