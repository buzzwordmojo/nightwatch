"""
Tests for syncing alert rules from Convex into the running engine.

The behaviour under test is safety-critical: this device monitors a child for
seizures, so the interesting cases are all the ways a sync could quietly leave
the engine unable to alert.
"""

from __future__ import annotations

import time

from nightwatch.bridge.convex import ConvexUnavailableError
from nightwatch.core.alert_rules import AlertRulesSync, config_to_row, row_to_config
from nightwatch.core.config import (
    AlertEngineConfig,
    AlertRuleCondition,
)
from nightwatch.core.config import (
    AlertRule as AlertRuleConfig,
)
from nightwatch.core.engine import AlertEngine


def yaml_rule(name="Respiration critical", value=4, duration=10.0, cooldown=60.0):
    return AlertRuleConfig(
        name=name,
        conditions=[
            AlertRuleCondition(
                detector="radar",
                field="value.respiration_rate",
                operator="<",
                value=value,
                duration_seconds=duration,
            )
        ],
        severity="critical",
        message="Respiration critically low",
        cooldown_seconds=cooldown,
    )


def convex_row(name="Respiration critical", value=4.0, enabled=True, duration=10.0):
    return {
        "_id": f"id_{name}",
        "name": name,
        "enabled": enabled,
        "detector": "radar",
        "field": "value.respiration_rate",
        "operator": "<",
        "value": value,
        "durationSeconds": duration,
        "severity": "critical",
        "message": "Respiration critically low",
        "cooldownSeconds": 60.0,
    }


class FakeBridge:
    """Stands in for ConvexBridge. `rows` None means Convex is unreachable."""

    def __init__(self, rows=None, unavailable=False):
        self.rows = rows if rows is not None else []
        self.unavailable = unavailable
        self.upserts: list[dict] = []
        self.query_count = 0

    async def query(self, path, args=None):
        self.query_count += 1
        if self.unavailable:
            raise ConvexUnavailableError("connection refused")
        return self.rows

    async def mutation(self, path, args):
        self.upserts.append(args)
        self.rows.append({**args, "_id": f"id_{args['name']}"})
        return None


def make_engine(rules):
    return AlertEngine(config=AlertEngineConfig(rules=rules))


# --- the core promise: dashboard edits reach the engine --------------------


async def test_convex_rules_replace_yaml_rules():
    engine = make_engine([yaml_rule(value=4)])
    bridge = FakeBridge([convex_row(value=7.0)])
    sync = AlertRulesSync(engine, bridge, fallback_rules=[yaml_rule(value=4)])

    assert await sync.sync_once() is True
    assert engine.rule_names == ["Respiration critical"]
    # The threshold the engine evaluates is the one from Convex, not YAML.
    assert engine._rules[0].conditions[0].threshold == 7.0


async def test_disabled_rule_is_not_armed():
    engine = make_engine([yaml_rule()])
    bridge = FakeBridge([convex_row(enabled=False)])
    sync = AlertRulesSync(engine, bridge, fallback_rules=[yaml_rule()])

    await sync.sync_once()
    assert engine.rule_names == []


# --- the subtle one: unchanged rules must keep their timers ----------------


async def test_unchanged_rule_keeps_its_duration_timer():
    """
    A rule needing 10s of low respiration must not have its clock reset by a
    routine sync, or it can never reach 10s and never fires.
    """
    engine = make_engine([yaml_rule()])
    bridge = FakeBridge([convex_row()])
    sync = AlertRulesSync(engine, bridge, fallback_rules=[yaml_rule()])
    await sync.sync_once()

    rule = engine._rules[0]
    started_at = time.time() - 8.0
    rule._state.condition_start_times[0] = started_at
    rule._state.last_triggered = started_at

    await sync.sync_once()  # nothing changed in Convex

    assert engine._rules[0] is rule, "unchanged rule was rebuilt"
    assert engine._rules[0]._state.condition_start_times[0] == started_at
    assert engine._rules[0]._state.last_triggered == started_at


async def test_changed_rule_is_rebuilt():
    engine = make_engine([yaml_rule()])
    bridge = FakeBridge([convex_row(value=4.0)])
    sync = AlertRulesSync(engine, bridge, fallback_rules=[yaml_rule()])
    await sync.sync_once()
    original = engine._rules[0]

    bridge.rows = [convex_row(value=5.0)]
    await sync.sync_once()

    assert engine._rules[0] is not original
    assert engine._rules[0].conditions[0].threshold == 5.0


# --- failure paths must never disarm --------------------------------------


async def test_convex_unreachable_keeps_armed_rules():
    engine = make_engine([yaml_rule()])
    bridge = FakeBridge(unavailable=True)
    sync = AlertRulesSync(engine, bridge, fallback_rules=[yaml_rule()])

    assert await sync.sync_once() is False
    assert engine.rule_names == ["Respiration critical"]


async def test_garbage_response_keeps_armed_rules():
    engine = make_engine([yaml_rule()])
    bridge = FakeBridge()
    bridge.rows = {"not": "a list"}
    sync = AlertRulesSync(engine, bridge, fallback_rules=[yaml_rule()])

    assert await sync.sync_once() is False
    assert engine.rule_names == ["Respiration critical"]


async def test_one_malformed_row_does_not_drop_the_others():
    engine = make_engine([])
    good = convex_row(name="Good")
    bad = convex_row(name="Bad")
    del bad["operator"]
    bridge = FakeBridge([good, bad])
    sync = AlertRulesSync(engine, bridge, fallback_rules=[])

    await sync.sync_once()
    assert engine.rule_names == ["Good"]


# --- seeding ---------------------------------------------------------------


async def test_empty_table_seeds_from_yaml_and_arms():
    rule = yaml_rule()
    engine = make_engine([rule])
    bridge = FakeBridge([])
    sync = AlertRulesSync(engine, bridge, fallback_rules=[rule])

    assert await sync.sync_once() is True
    assert [u["name"] for u in bridge.upserts] == ["Respiration critical"]
    assert engine.rule_names == ["Respiration critical"]


async def test_empty_table_that_cannot_seed_keeps_armed_rules():
    """An unseeded, unwritable database must not be read as 'all rules off'."""
    engine = make_engine([yaml_rule()])
    bridge = FakeBridge([])

    async def failing_mutation(path, args):
        raise RuntimeError("read-only")

    bridge.mutation = failing_mutation
    sync = AlertRulesSync(engine, bridge, fallback_rules=[yaml_rule()])

    assert await sync.sync_once() is False
    assert engine.rule_names == ["Respiration critical"]


# --- rules Convex cannot represent ----------------------------------------


def test_multi_condition_rule_is_not_seedable():
    multi = AlertRuleConfig(
        name="Multi",
        conditions=[
            AlertRuleCondition(detector="radar", field="value.a", operator="<", value=1),
            AlertRuleCondition(detector="audio", field="value.b", operator=">", value=2),
        ],
        severity="critical",
    )
    assert config_to_row(multi) is None


async def test_multi_condition_rule_stays_armed_alongside_convex_rules():
    """Adding a multi-condition rule to config.yaml must never silently drop it."""
    multi = AlertRuleConfig(
        name="Multi",
        conditions=[
            AlertRuleCondition(detector="radar", field="value.a", operator="<", value=1),
            AlertRuleCondition(detector="audio", field="value.b", operator=">", value=2),
        ],
        severity="critical",
    )
    engine = make_engine([multi])
    bridge = FakeBridge([convex_row()])
    sync = AlertRulesSync(engine, bridge, fallback_rules=[multi])

    await sync.sync_once()

    assert sorted(engine.rule_names) == ["Multi", "Respiration critical"]
    assert bridge.upserts == []


# --- round trip ------------------------------------------------------------


def test_row_round_trips_through_config():
    original = convex_row(value=6.0)
    config = row_to_config(original)
    assert config_to_row(config)["value"] == 6.0
    assert config.conditions[0].duration_seconds == 10.0


# --- seeding happens once and never fights the caregiver -------------------


async def test_user_edit_survives_later_syncs():
    """
    The dashboard is the only writer after the initial seed. A threshold edited
    there must not be stomped back to config.yaml on the next poll.
    """
    rule = yaml_rule(value=4)
    engine = make_engine([rule])
    bridge = FakeBridge([])
    sync = AlertRulesSync(engine, bridge, fallback_rules=[rule])

    await sync.sync_once()  # seeds config.yaml's value of 4
    assert engine._rules[0].conditions[0].threshold == 4.0
    upserts_after_seed = len(bridge.upserts)

    # Caregiver raises the threshold in the dashboard.
    bridge.rows = [convex_row(value=9.0)]
    await sync.sync_once()

    assert engine._rules[0].conditions[0].threshold == 9.0
    assert len(bridge.upserts) == upserts_after_seed, "sync re-seeded over a user edit"


async def test_emptied_table_does_not_reseed_or_disarm():
    """Deleting every rule must not silently re-create them, nor disarm the engine."""
    rule = yaml_rule()
    engine = make_engine([rule])
    bridge = FakeBridge([])
    sync = AlertRulesSync(engine, bridge, fallback_rules=[rule])
    await sync.sync_once()
    upserts_after_seed = len(bridge.upserts)

    bridge.rows = []
    assert await sync.sync_once() is False
    assert engine.rule_names == ["Respiration critical"]
    assert len(bridge.upserts) == upserts_after_seed
