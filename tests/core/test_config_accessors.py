"""
Every NightwatchConfig field must be reachable through the Config wrapper.

`Config` exposes the typed config through hand-written properties, so adding a
field to `NightwatchConfig` without adding its accessor leaves the field
invisible - and any code reading it dies with AttributeError at startup.

That is not hypothetical: `heartbeat` was added with the off-device dead man's
switch, the accessor was not, and `__main__` crashed on `config.heartbeat`
before it could start monitoring. This test fails the moment that recurs.
"""

from __future__ import annotations

from nightwatch.core.config import Config, NightwatchConfig


def test_every_typed_field_has_a_config_accessor():
    config = Config.default()
    missing = [
        name for name in NightwatchConfig.model_fields
        if not hasattr(config, name)
    ]
    assert not missing, (
        f"NightwatchConfig field(s) {missing} have no accessor on Config. "
        f"Add a @property for each, or code reading them dies at startup."
    )


def test_accessors_return_the_typed_objects():
    config = Config.default()
    for name in NightwatchConfig.model_fields:
        assert getattr(config, name) is getattr(config._typed, name)


def test_heartbeat_is_reachable():
    """The specific regression: __main__ reads config.heartbeat at startup."""
    assert Config.default().heartbeat is not None
