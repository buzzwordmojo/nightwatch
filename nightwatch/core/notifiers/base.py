"""
Base notifier interface for Nightwatch.

All notifiers implement this interface for consistency.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from nightwatch.core.events import Alert


class BaseNotifier(ABC):
    """
    Abstract base class for all notifiers.

    Notifiers are responsible for alerting users when something
    requires attention. They can send notifications via various
    channels: local audio, push notifications, webhooks, etc.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique notifier identifier."""
        pass

    @property
    @abstractmethod
    def enabled(self) -> bool:
        """Whether this notifier is enabled."""
        pass

    @abstractmethod
    async def notify(self, alert: Alert) -> bool:
        """
        Send notification for an alert.

        Args:
            alert: The alert to notify about

        Returns:
            True if notification was sent successfully
        """
        pass

    @abstractmethod
    async def test(self) -> bool:
        """
        Send a test notification.

        Returns:
            True if test was successful
        """
        pass

    async def start(self) -> None:
        """Start the notifier (optional setup)."""
        pass

    async def stop(self) -> None:
        """Stop the notifier (optional cleanup)."""
        pass
