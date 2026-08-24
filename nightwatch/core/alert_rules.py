"""
Keeps the alert engine's rules in step with the dashboard's `alertRules` table.

Before this existed there were two independent sources of truth: the dashboard
wrote thresholds to Convex, and the engine built its rules from `config.yaml`
and never looked at Convex. A caregiver could edit a threshold, watch it save,
and change nothing about whether an alert fires - a control that looks like it
works and does not.

Convex is now authoritative and the YAML rules are the bootstrap seed.

One safety rule governs every decision in this module: **never end up with
fewer rules than we started with because something went wrong.** A monitor that
cannot alert is worse than one that is obviously offline, so every failure path
here keeps the ruleset that is already armed.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from typing import Any

from nightwatch.bridge.convex import ConvexBridge, ConvexUnavailableError
from nightwatch.core.config import AlertRule as AlertRuleConfig
from nightwatch.core.config import AlertRuleCondition
from nightwatch.core.engine import AlertEngine, RuleSyncResult

logger = logging.getLogger(__name__)

LIST_QUERY = "alertRules:list"
UPSERT_MUTATION = "alertRules:upsert"


def config_to_row(config: AlertRuleConfig) -> dict[str, Any] | None:
    """
    Render a YAML rule as an `alertRules` row, or None if it cannot be.

    The Convex table holds exactly one condition per rule. A multi-condition
    rule has no faithful representation, and writing a lossy one would show the
    caregiver a rule that is not the rule being evaluated.
    """
    if len(config.conditions) != 1:
        return None

    condition = config.conditions[0]

    # The table types `value` as a number. Booleans are fine (Python compares
    # False == 0 correctly), but strings cannot cross.
    if isinstance(condition.value, str):
        return None

    return {
        "name": config.name,
        "enabled": True,
        "detector": condition.detector,
        "field": condition.field,
        "operator": condition.operator,
        "value": float(condition.value),
        "durationSeconds": float(condition.duration_seconds),
        "severity": config.severity,
        "message": config.message,
        "cooldownSeconds": float(config.cooldown_seconds),
    }


def row_to_config(row: dict[str, Any]) -> AlertRuleConfig:
    """Convert one `alertRules` row into the engine's rule config."""
    return AlertRuleConfig(
        name=row["name"],
        conditions=[
            AlertRuleCondition(
                detector=row["detector"],
                field=row["field"],
                operator=row["operator"],
                value=row["value"],
                duration_seconds=float(row.get("durationSeconds", 0.0)),
            )
        ],
        severity=row["severity"],
        cooldown_seconds=float(row.get("cooldownSeconds", 30.0)),
        message=row.get("message", ""),
    )


class AlertRulesSync:
    """
    Polls Convex for alert rules and applies them to a running AlertEngine.

    Polling rather than subscribing: the bridge speaks Convex's HTTP API, which
    has no push channel, and a poll that fails is a no-op by construction.
    """

    def __init__(
        self,
        engine: AlertEngine,
        bridge: ConvexBridge,
        fallback_rules: list[AlertRuleConfig],
        poll_interval: float = 10.0,
        on_change: Callable[[RuleSyncResult], Awaitable[None]] | None = None,
    ):
        self._engine = engine
        self._bridge = bridge
        self._poll_interval = poll_interval
        self._on_change = on_change

        # Rules from config.yaml, split by whether Convex can hold them.
        self._seedable: list[AlertRuleConfig] = []
        self._local_only: list[AlertRuleConfig] = []
        for rule in fallback_rules:
            if config_to_row(rule) is None:
                self._local_only.append(rule)
            else:
                self._seedable.append(rule)

        if self._local_only:
            names = ", ".join(r.name for r in self._local_only)
            logger.warning(
                f"Alert rule(s) not representable in the dashboard's schema and so "
                f"NOT editable there: {names}. They stay armed from config.yaml. "
                f"The alertRules table holds a single numeric condition per rule."
            )

        self._task: asyncio.Task | None = None
        self._running = False
        self._seeded = False
        self._last_error_logged = False

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def local_only_rule_names(self) -> list[str]:
        """Rules that stay YAML-driven because Convex cannot express them."""
        return [r.name for r in self._local_only]

    async def start(self) -> None:
        """Sync once, then keep syncing in the background."""
        if self._running:
            return
        self._running = True
        await self.sync_once()
        self._task = asyncio.create_task(self._poll_loop())

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

    async def _poll_loop(self) -> None:
        while self._running:
            await asyncio.sleep(self._poll_interval)
            if not self._running:
                break
            try:
                await self.sync_once()
            except Exception as e:  # never let the loop die
                logger.error(f"Alert rule sync failed unexpectedly: {e}")

    async def sync_once(self) -> bool:
        """
        Fetch rules from Convex and apply them.

        Returns True if the engine's ruleset now reflects Convex, False if we
        kept what was already armed because Convex could not be read.
        """
        try:
            rows = await self._bridge.query(LIST_QUERY)
        except ConvexUnavailableError as e:
            # Keep the current rules. This is the common case during a restart
            # or a brief outage and must not disarm anything.
            if not self._last_error_logged:
                logger.warning(
                    f"Could not read alert rules from Convex ({e}). "
                    f"Keeping the {len(self._engine.rule_names)} rule(s) already armed."
                )
                self._last_error_logged = True
            return False
        except Exception as e:
            if not self._last_error_logged:
                logger.error(
                    f"Alert rule query failed ({e}). "
                    f"Keeping the {len(self._engine.rule_names)} rule(s) already armed."
                )
                self._last_error_logged = True
            return False

        self._last_error_logged = False

        if not isinstance(rows, list):
            logger.error(
                f"Convex returned {type(rows).__name__} for alert rules, expected a list. "
                f"Keeping the rules already armed."
            )
            return False

        # An empty table means nobody has seeded it, NOT that every rule is off.
        # Turning rules off is done per-row with enabled=false, which still
        # returns rows. Conflating the two would let an unseeded database
        # silently disarm the monitor.
        if not rows:
            if self._seedable and not self._seeded:
                logger.info("No alert rules in Convex - seeding from config.yaml")
                if await self._seed():
                    return await self.sync_once()
            logger.warning(
                "Convex holds no alert rules and none could be seeded. "
                "Keeping the rules already armed."
            )
            return False

        self._seeded = True

        configs: list[AlertRuleConfig] = []
        skipped: list[str] = []
        for row in rows:
            name = row.get("name", "<unnamed>") if isinstance(row, dict) else "<malformed>"
            try:
                if not row.get("enabled", True):
                    continue
                configs.append(row_to_config(row))
            except Exception as e:
                # One bad row must not take down every other rule.
                skipped.append(f"{name} ({e})")

        if skipped:
            logger.error(
                f"Ignoring {len(skipped)} malformed alert rule(s) from Convex: "
                f"{'; '.join(skipped)}"
            )

        # Rules Convex cannot represent are always applied on top, so adding a
        # multi-condition rule to config.yaml can never silently drop it.
        configs.extend(self._local_only)

        if not configs:
            logger.warning(
                f"Every alert rule in Convex is disabled ({len(rows)} row(s)). "
                f"No threshold alert can fire."
            )

        result = self._engine.apply_rule_configs(configs)

        if result.changed and self._on_change:
            try:
                await self._on_change(result)
            except Exception as e:
                logger.error(f"Alert rule change callback failed: {e}")

        return True

    async def _seed(self) -> bool:
        """Write the YAML rules into Convex so the dashboard shows what is armed."""
        seeded = 0
        for rule in self._seedable:
            row = config_to_row(rule)
            if row is None:
                continue
            try:
                await self._bridge.mutation(UPSERT_MUTATION, row)
                seeded += 1
            except Exception as e:
                logger.error(f"Could not seed alert rule '{rule.name}': {e}")

        if seeded:
            logger.info(f"Seeded {seeded} alert rule(s) into Convex from config.yaml")
            self._seeded = True
            return True
        return False
