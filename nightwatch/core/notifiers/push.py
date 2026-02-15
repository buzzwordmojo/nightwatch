"""
Push notification notifier for Nightwatch.

Supports Pushover and Ntfy for sending push notifications to mobile devices.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any

import httpx

from nightwatch.core.events import Alert, EventSeverity
from nightwatch.core.notifiers.base import BaseNotifier

logger = logging.getLogger(__name__)


class PushProvider(str, Enum):
    """Supported push notification providers."""

    PUSHOVER = "pushover"
    NTFY = "ntfy"


@dataclass
class PushConfig:
    """Configuration for push notifications."""

    enabled: bool = False
    provider: PushProvider = PushProvider.PUSHOVER

    # Pushover settings
    pushover_user_key: str = ""
    pushover_api_token: str = ""

    # Ntfy settings
    ntfy_server: str = "https://ntfy.sh"
    ntfy_topic: str = ""

    # Alert level filtering
    alert_levels: list[str] | None = None

    @classmethod
    def from_dict(cls, config: dict[str, Any]) -> PushConfig:
        """Create config from dictionary."""
        return cls(
            enabled=config.get("enabled", False),
            provider=PushProvider(config.get("provider", "pushover")),
            pushover_user_key=config.get("pushover_user_key", ""),
            pushover_api_token=config.get("pushover_api_token", ""),
            ntfy_server=config.get("ntfy_server", "https://ntfy.sh"),
            ntfy_topic=config.get("ntfy_topic", ""),
            alert_levels=config.get("alert_levels"),
        )


class PushNotifier(BaseNotifier):
    """
    Push notification notifier supporting Pushover and Ntfy.

    Sends push notifications to mobile devices when alerts are triggered.
    """

    def __init__(self, config: PushConfig):
        self._config = config
        self._client: httpx.AsyncClient | None = None

    @property
    def name(self) -> str:
        return "push"

    @property
    def enabled(self) -> bool:
        return self._config.enabled

    async def start(self) -> None:
        """Initialize HTTP client."""
        self._client = httpx.AsyncClient(timeout=30.0)
        logger.info(
            f"Push notifier started with provider: {self._config.provider.value}"
        )

    async def stop(self) -> None:
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
        logger.info("Push notifier stopped")

    async def notify(self, alert: Alert) -> bool:
        """
        Send push notification for an alert.

        Args:
            alert: The alert to notify about

        Returns:
            True if notification was sent successfully
        """
        if not self._config.enabled:
            return False

        # Check alert level filter
        if self._config.alert_levels:
            if alert.severity.value not in self._config.alert_levels:
                logger.debug(
                    f"Skipping push for {alert.severity.value} alert "
                    f"(not in {self._config.alert_levels})"
                )
                return False

        if self._config.provider == PushProvider.PUSHOVER:
            return await self._send_pushover(alert)
        elif self._config.provider == PushProvider.NTFY:
            return await self._send_ntfy(alert)
        else:
            logger.error(f"Unknown push provider: {self._config.provider}")
            return False

    async def test(self) -> bool:
        """
        Send a test notification.

        Returns:
            True if test was successful
        """
        test_alert = Alert.create(
            severity=EventSeverity.INFO,
            rule_name="Test",
            message="This is a test notification from Nightwatch",
        )

        # Temporarily allow all levels for test
        original_levels = self._config.alert_levels
        self._config.alert_levels = None

        try:
            if self._config.provider == PushProvider.PUSHOVER:
                return await self._send_pushover(test_alert)
            elif self._config.provider == PushProvider.NTFY:
                return await self._send_ntfy(test_alert)
            return False
        finally:
            self._config.alert_levels = original_levels

    async def _send_pushover(self, alert: Alert) -> bool:
        """Send notification via Pushover API."""
        if not self._client:
            logger.error("HTTP client not initialized")
            return False

        if not self._config.pushover_user_key or not self._config.pushover_api_token:
            logger.error("Pushover credentials not configured")
            return False

        # Map severity to Pushover priority
        # -2: lowest, -1: low, 0: normal, 1: high, 2: emergency
        priority_map = {
            EventSeverity.INFO: -1,
            EventSeverity.WARNING: 0,
            EventSeverity.CRITICAL: 1,
        }
        priority = priority_map.get(alert.severity, 0)

        payload = {
            "token": self._config.pushover_api_token,
            "user": self._config.pushover_user_key,
            "message": alert.message,
            "title": f"Nightwatch: {alert.rule_name}",
            "priority": priority,
            "sound": "siren" if alert.severity == EventSeverity.CRITICAL else "pushover",
        }

        # Emergency priority requires retry/expire params
        if priority == 2:
            payload["retry"] = 60  # Retry every 60 seconds
            payload["expire"] = 3600  # Stop after 1 hour

        try:
            response = await self._client.post(
                "https://api.pushover.net/1/messages.json",
                data=payload,
            )

            if response.status_code == 200:
                logger.info(f"Pushover notification sent for alert: {alert.rule_name}")
                return True
            else:
                logger.error(
                    f"Pushover API error: {response.status_code} - {response.text}"
                )
                return False

        except Exception as e:
            logger.error(f"Failed to send Pushover notification: {e}")
            return False

    async def _send_ntfy(self, alert: Alert) -> bool:
        """Send notification via Ntfy."""
        if not self._client:
            logger.error("HTTP client not initialized")
            return False

        if not self._config.ntfy_topic:
            logger.error("Ntfy topic not configured")
            return False

        # Map severity to Ntfy priority
        # 1: min, 2: low, 3: default, 4: high, 5: urgent
        priority_map = {
            EventSeverity.INFO: 2,
            EventSeverity.WARNING: 3,
            EventSeverity.CRITICAL: 5,
        }
        priority = priority_map.get(alert.severity, 3)

        # Build Ntfy URL
        server = self._config.ntfy_server.rstrip("/")
        url = f"{server}/{self._config.ntfy_topic}"

        headers = {
            "Title": f"Nightwatch: {alert.rule_name}",
            "Priority": str(priority),
            "Tags": self._get_ntfy_tags(alert.severity),
        }

        try:
            response = await self._client.post(
                url,
                content=alert.message,
                headers=headers,
            )

            if response.status_code == 200:
                logger.info(f"Ntfy notification sent for alert: {alert.rule_name}")
                return True
            else:
                logger.error(
                    f"Ntfy API error: {response.status_code} - {response.text}"
                )
                return False

        except Exception as e:
            logger.error(f"Failed to send Ntfy notification: {e}")
            return False

    def _get_ntfy_tags(self, severity: EventSeverity) -> str:
        """Get Ntfy tags (emoji) based on severity."""
        tag_map = {
            EventSeverity.INFO: "information_source",
            EventSeverity.WARNING: "warning",
            EventSeverity.CRITICAL: "rotating_light,skull",
        }
        return tag_map.get(severity, "bell")
