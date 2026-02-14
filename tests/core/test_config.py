"""
Tests for the configuration system.

Covers:
- Pydantic model validation
- YAML loading with environment variable substitution
- Config file watching and hot reload
- Environment variable overrides
- Config change diffing
"""

from __future__ import annotations

import os
import tempfile
import time
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import yaml

from nightwatch.core.config import (
    RadarConfig,
    AudioConfig,
    BCGConfig,
    DetectorsConfig,
    AlertRuleCondition,
    AlertRule,
    AlertEngineConfig,
    AudioNotifierConfig,
    PushNotifierConfig,
    WebhookNotifierConfig,
    NotifiersConfig,
    DashboardConfig,
    FusionRuleSource,
    FusionRule,
    FusionConfig,
    EventSystemConfig,
    SystemConfig,
    NightwatchConfig,
    ConfigChange,
    ConfigLoader,
    ConfigWatcher,
    Config,
)


# =============================================================================
# Pydantic Model Validation Tests
# =============================================================================


class TestRadarConfig:
    """Tests for RadarConfig validation."""

    def test_default_values(self):
        """Default values are sensible."""
        config = RadarConfig()
        assert config.enabled is True
        assert config.device == "/dev/ttyAMA0"
        assert config.baud_rate == 256000
        assert config.model == "ld2450"
        assert config.sensitivity == 0.8
        assert config.update_rate_hz == 10

    def test_valid_model_ld2450(self):
        """ld2450 is a valid model."""
        config = RadarConfig(model="ld2450")
        assert config.model == "ld2450"

    def test_valid_model_ld2410(self):
        """ld2410 is a valid model."""
        config = RadarConfig(model="ld2410")
        assert config.model == "ld2410"

    def test_invalid_model_raises(self):
        """Invalid model raises validation error."""
        with pytest.raises(ValueError):
            RadarConfig(model="invalid_model")

    def test_sensitivity_bounds(self):
        """Sensitivity must be between 0 and 1."""
        config = RadarConfig(sensitivity=0.0)
        assert config.sensitivity == 0.0

        config = RadarConfig(sensitivity=1.0)
        assert config.sensitivity == 1.0

        with pytest.raises(ValueError):
            RadarConfig(sensitivity=-0.1)

        with pytest.raises(ValueError):
            RadarConfig(sensitivity=1.1)

    def test_update_rate_bounds(self):
        """Update rate must be between 1 and 30."""
        config = RadarConfig(update_rate_hz=1)
        assert config.update_rate_hz == 1

        config = RadarConfig(update_rate_hz=30)
        assert config.update_rate_hz == 30

        with pytest.raises(ValueError):
            RadarConfig(update_rate_hz=0)

        with pytest.raises(ValueError):
            RadarConfig(update_rate_hz=31)


class TestAudioConfig:
    """Tests for AudioConfig validation."""

    def test_default_values(self):
        """Default values are sensible."""
        config = AudioConfig()
        assert config.enabled is True
        assert config.device is None
        assert config.sample_rate == 16000
        assert config.chunk_size == 1024
        assert config.channels == 1

    def test_sample_rate_bounds(self):
        """Sample rate must be between 8000 and 48000."""
        config = AudioConfig(sample_rate=8000)
        assert config.sample_rate == 8000

        config = AudioConfig(sample_rate=48000)
        assert config.sample_rate == 48000

        with pytest.raises(ValueError):
            AudioConfig(sample_rate=7999)

        with pytest.raises(ValueError):
            AudioConfig(sample_rate=48001)

    def test_chunk_size_bounds(self):
        """Chunk size must be between 256 and 4096."""
        with pytest.raises(ValueError):
            AudioConfig(chunk_size=255)

        with pytest.raises(ValueError):
            AudioConfig(chunk_size=4097)


class TestBCGConfig:
    """Tests for BCGConfig validation."""

    def test_default_disabled(self):
        """BCG is disabled by default."""
        config = BCGConfig()
        assert config.enabled is False

    def test_sample_rate_bounds(self):
        """Sample rate must be between 50 and 500."""
        config = BCGConfig(sample_rate=50)
        assert config.sample_rate == 50

        config = BCGConfig(sample_rate=500)
        assert config.sample_rate == 500

        with pytest.raises(ValueError):
            BCGConfig(sample_rate=49)


class TestAlertRuleCondition:
    """Tests for AlertRuleCondition validation."""

    def test_valid_operators(self):
        """Valid comparison operators."""
        for op in ["<", ">", "==", "!=", "<=", ">="]:
            condition = AlertRuleCondition(
                detector="radar",
                field="respiration_rate",
                operator=op,
                value=10,
            )
            assert condition.operator == op

    def test_invalid_operator_raises(self):
        """Invalid operator raises validation error."""
        with pytest.raises(ValueError):
            AlertRuleCondition(
                detector="radar",
                field="respiration_rate",
                operator="~=",
                value=10,
            )


class TestAlertRule:
    """Tests for AlertRule validation."""

    def test_valid_severities(self):
        """Valid severity levels."""
        for severity in ["info", "warning", "critical"]:
            rule = AlertRule(
                name="test",
                conditions=[],
                severity=severity,
            )
            assert rule.severity == severity

    def test_invalid_severity_raises(self):
        """Invalid severity raises validation error."""
        with pytest.raises(ValueError):
            AlertRule(
                name="test",
                conditions=[],
                severity="danger",
            )

    def test_default_values(self):
        """Default rule values."""
        rule = AlertRule(name="test", conditions=[])
        assert rule.severity == "critical"
        assert rule.combine == "all"
        assert rule.duration_seconds == 0.0
        assert rule.cooldown_seconds == 30.0


class TestAudioNotifierConfig:
    """Tests for AudioNotifierConfig validation."""

    def test_default_values(self):
        """Default values are sensible."""
        config = AudioNotifierConfig()
        assert config.enabled is True
        assert config.output_type == "speaker"
        assert config.initial_volume == 60
        assert config.max_volume == 100
        assert config.escalation_enabled is True

    def test_volume_bounds(self):
        """Volume must be between 0 and 100."""
        config = AudioNotifierConfig(initial_volume=0)
        assert config.initial_volume == 0

        config = AudioNotifierConfig(initial_volume=100)
        assert config.initial_volume == 100

        with pytest.raises(ValueError):
            AudioNotifierConfig(initial_volume=-1)

        with pytest.raises(ValueError):
            AudioNotifierConfig(initial_volume=101)


class TestDashboardConfig:
    """Tests for DashboardConfig validation."""

    def test_default_values(self):
        """Default values are sensible."""
        config = DashboardConfig()
        assert config.host == "0.0.0.0"
        assert config.port == 5000
        assert config.debug is False
        assert config.auth_enabled is False

    def test_port_bounds(self):
        """Port must be valid."""
        config = DashboardConfig(port=1)
        assert config.port == 1

        config = DashboardConfig(port=65535)
        assert config.port == 65535

        with pytest.raises(ValueError):
            DashboardConfig(port=0)

        with pytest.raises(ValueError):
            DashboardConfig(port=65536)


class TestNightwatchConfig:
    """Tests for complete NightwatchConfig."""

    def test_default_config(self):
        """Default config creates all subsections."""
        config = NightwatchConfig()
        assert config.system is not None
        assert config.detectors is not None
        assert config.alert_engine is not None
        assert config.notifiers is not None
        assert config.dashboard is not None

    def test_nested_defaults(self):
        """Nested configs have defaults."""
        config = NightwatchConfig()
        assert config.detectors.radar.enabled is True
        assert config.detectors.audio.enabled is True
        assert config.detectors.bcg.enabled is False


# =============================================================================
# ConfigLoader Tests
# =============================================================================


class TestConfigLoader:
    """Tests for ConfigLoader."""

    @pytest.fixture
    def loader(self):
        """Create config loader."""
        return ConfigLoader()

    @pytest.fixture
    def temp_yaml_file(self):
        """Create a temporary YAML file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("system:\n  name: test\n  log_level: DEBUG\n")
            f.flush()
            yield Path(f.name)
        os.unlink(f.name)

    def test_load_yaml_file(self, loader, temp_yaml_file):
        """Load a simple YAML file."""
        data = loader.load_yaml(temp_yaml_file)
        assert data["system"]["name"] == "test"
        assert data["system"]["log_level"] == "DEBUG"

    def test_load_yaml_missing_file(self, loader):
        """Missing file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            loader.load_yaml(Path("/nonexistent/config.yaml"))

    def test_env_var_substitution(self, loader):
        """Environment variable substitution works."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("database:\n  password: ${TEST_DB_PASSWORD}\n")
            f.flush()
            temp_path = Path(f.name)

        try:
            with patch.dict(os.environ, {"TEST_DB_PASSWORD": "secret123"}):
                data = loader.load_yaml(temp_path)
                assert data["database"]["password"] == "secret123"
        finally:
            os.unlink(temp_path)

    def test_env_var_with_default(self, loader):
        """Environment variable with default value."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("database:\n  host: ${DB_HOST:-localhost}\n")
            f.flush()
            temp_path = Path(f.name)

        try:
            # Without env var, should use default
            if "DB_HOST" in os.environ:
                del os.environ["DB_HOST"]
            data = loader.load_yaml(temp_path)
            assert data["database"]["host"] == "localhost"

            # With env var, should use env value
            with patch.dict(os.environ, {"DB_HOST": "db.example.com"}):
                data = loader.load_yaml(temp_path)
                assert data["database"]["host"] == "db.example.com"
        finally:
            os.unlink(temp_path)

    def test_merge_configs(self, loader):
        """Deep merge of config dictionaries."""
        base = {
            "system": {"name": "base", "log_level": "INFO"},
            "detectors": {"radar": {"enabled": True}},
        }
        override = {
            "system": {"log_level": "DEBUG"},
            "detectors": {"radar": {"sensitivity": 0.9}},
        }

        merged = loader.merge(base, override)

        assert merged["system"]["name"] == "base"  # From base
        assert merged["system"]["log_level"] == "DEBUG"  # Overridden
        assert merged["detectors"]["radar"]["enabled"] is True  # From base
        assert merged["detectors"]["radar"]["sensitivity"] == 0.9  # Added

    def test_load_directory(self, loader):
        """Load and merge all YAML files in directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create multiple config files
            (Path(tmpdir) / "01_base.yaml").write_text(
                "system:\n  name: nightwatch\n  log_level: INFO\n"
            )
            (Path(tmpdir) / "02_override.yaml").write_text(
                "system:\n  log_level: DEBUG\n"
            )

            data = loader.load_directory(Path(tmpdir))

            assert data["system"]["name"] == "nightwatch"
            assert data["system"]["log_level"] == "DEBUG"

    def test_apply_env_overrides(self, loader):
        """Environment variable overrides."""
        config = {"detectors": {"radar": {"sensitivity": 0.5}}}

        with patch.dict(os.environ, {"NIGHTWATCH_DETECTORS_RADAR_SENSITIVITY": "0.9"}):
            updated = loader.apply_env_overrides(config)
            assert updated["detectors"]["radar"]["sensitivity"] == 0.9

    def test_parse_value_boolean(self, loader):
        """Parse boolean values from strings."""
        assert loader._parse_value("true") is True
        assert loader._parse_value("True") is True
        assert loader._parse_value("yes") is True
        assert loader._parse_value("1") is True

        assert loader._parse_value("false") is False
        assert loader._parse_value("False") is False
        assert loader._parse_value("no") is False
        assert loader._parse_value("0") is False

    def test_parse_value_numbers(self, loader):
        """Parse numeric values from strings."""
        assert loader._parse_value("42") == 42
        assert loader._parse_value("3.14") == 3.14
        assert loader._parse_value("-10") == -10
        assert loader._parse_value("0.001") == 0.001

    def test_parse_value_string(self, loader):
        """Non-numeric values remain strings."""
        assert loader._parse_value("hello") == "hello"
        assert loader._parse_value("/dev/ttyAMA0") == "/dev/ttyAMA0"


# =============================================================================
# Config Class Tests
# =============================================================================


class TestConfig:
    """Tests for main Config class."""

    @pytest.fixture
    def temp_config_file(self):
        """Create temporary config file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
system:
  name: test_nightwatch
  log_level: DEBUG

detectors:
  radar:
    enabled: true
    sensitivity: 0.75
  audio:
    enabled: false

dashboard:
  port: 8080
""")
            f.flush()
            yield Path(f.name)
        os.unlink(f.name)

    def test_load_from_file(self, temp_config_file):
        """Load config from YAML file."""
        config = Config.load(temp_config_file)

        assert config.system.name == "test_nightwatch"
        assert config.system.log_level == "DEBUG"
        assert config.detectors.radar.enabled is True
        assert config.detectors.radar.sensitivity == 0.75
        assert config.detectors.audio.enabled is False
        assert config.dashboard.port == 8080

    def test_load_from_dict(self):
        """Create config from dictionary."""
        data = {
            "system": {"name": "from_dict"},
            "detectors": {"radar": {"sensitivity": 0.5}},
        }
        config = Config.from_dict(data)

        assert config.system.name == "from_dict"
        assert config.detectors.radar.sensitivity == 0.5

    def test_default_config(self):
        """Create config with all defaults."""
        config = Config.default()

        assert config.system.name == "nightwatch"
        assert config.detectors.radar.enabled is True
        assert config.detectors.bcg.enabled is False

    def test_get_dot_notation(self, temp_config_file):
        """Get values using dot notation."""
        config = Config.load(temp_config_file)

        assert config.get("system.name") == "test_nightwatch"
        assert config.get("detectors.radar.sensitivity") == 0.75
        assert config.get("nonexistent.path", "default") == "default"

    def test_set_value(self):
        """Set values in config."""
        config = Config.default()

        config.set("system.log_level", "ERROR")
        assert config.system.log_level == "ERROR"

        config.set("detectors.radar.sensitivity", 0.3)
        assert config.detectors.radar.sensitivity == 0.3

    def test_to_dict(self):
        """Convert config to dictionary."""
        config = Config.from_dict({"system": {"name": "test"}})
        data = config.to_dict()

        assert data["system"]["name"] == "test"

    def test_save_config(self):
        """Save config to file."""
        config = Config.from_dict({
            "system": {"name": "save_test", "log_level": "INFO"},
        })

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            temp_path = Path(f.name)

        try:
            config.save(temp_path)

            # Verify file contents
            saved_data = yaml.safe_load(temp_path.read_text())
            assert saved_data["system"]["name"] == "save_test"
        finally:
            os.unlink(temp_path)

    def test_reload_config(self, temp_config_file):
        """Reload config from disk."""
        config = Config.load(temp_config_file)
        original_name = config.system.name

        # Modify file
        content = temp_config_file.read_text()
        content = content.replace("test_nightwatch", "modified_nightwatch")
        temp_config_file.write_text(content)

        # Reload
        changes = config.reload()

        assert config.system.name == "modified_nightwatch"
        assert len(changes) > 0

    def test_validate_config(self):
        """Validate config returns errors."""
        config = Config.default()
        errors = config.validate()
        assert errors == []  # Default config should be valid

    def test_config_diff(self):
        """Calculate differences between configs."""
        config = Config.from_dict({
            "system": {"name": "original", "log_level": "INFO"},
        })

        old_data = {"system": {"name": "original", "log_level": "INFO"}}
        new_data = {"system": {"name": "original", "log_level": "DEBUG"}}

        changes = config._diff(old_data, new_data)

        assert len(changes) == 1
        assert changes[0].path == "system.log_level"
        assert changes[0].old_value == "INFO"
        assert changes[0].new_value == "DEBUG"


class TestConfigChange:
    """Tests for ConfigChange dataclass."""

    def test_config_change_attributes(self):
        """ConfigChange has correct attributes."""
        change = ConfigChange(
            path="system.log_level",
            old_value="INFO",
            new_value="DEBUG",
            timestamp=time.time(),
        )

        assert change.path == "system.log_level"
        assert change.old_value == "INFO"
        assert change.new_value == "DEBUG"
        assert change.timestamp > 0


# =============================================================================
# Edge Case Tests
# =============================================================================


class TestConfigEdgeCases:
    """Edge case tests for config system."""

    def test_empty_yaml_file(self):
        """Empty YAML file returns empty dict."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("")
            f.flush()
            temp_path = Path(f.name)

        try:
            loader = ConfigLoader()
            data = loader.load_yaml(temp_path)
            assert data == {}
        finally:
            os.unlink(temp_path)

    def test_yaml_with_only_comments(self):
        """YAML with only comments returns empty dict."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("# This is a comment\n# Another comment\n")
            f.flush()
            temp_path = Path(f.name)

        try:
            loader = ConfigLoader()
            data = loader.load_yaml(temp_path)
            assert data == {}
        finally:
            os.unlink(temp_path)

    def test_nested_env_var_path(self):
        """Deep nested env var override."""
        loader = ConfigLoader()
        config = {}

        with patch.dict(os.environ, {"NIGHTWATCH_A_B_C_D": "deep_value"}):
            updated = loader.apply_env_overrides(config)
            assert updated["a"]["b"]["c"]["d"] == "deep_value"

    def test_config_without_source_path(self):
        """Config from dict has no source path."""
        config = Config.from_dict({"system": {"name": "test"}})

        # Cannot enable hot reload without source path
        with pytest.raises(ValueError):
            config.enable_hot_reload()

        # Reload returns empty list
        changes = config.reload()
        assert changes == []

    def test_env_var_unset_no_default(self):
        """Unset env var without default keeps placeholder."""
        loader = ConfigLoader()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("key: ${NONEXISTENT_VAR_12345}\n")
            f.flush()
            temp_path = Path(f.name)

        try:
            # Remove var if it somehow exists
            if "NONEXISTENT_VAR_12345" in os.environ:
                del os.environ["NONEXISTENT_VAR_12345"]

            data = loader.load_yaml(temp_path)
            # Keeps original ${VAR} syntax if not found and no default
            assert data["key"] == "${NONEXISTENT_VAR_12345}"
        finally:
            os.unlink(temp_path)

    def test_merge_with_none_values(self):
        """Merge handles None values."""
        loader = ConfigLoader()

        base = {"a": 1, "b": None}
        override = {"b": 2, "c": None}

        merged = loader.merge(base, override)
        assert merged["a"] == 1
        assert merged["b"] == 2
        assert merged["c"] is None

    def test_merge_overwrites_non_dict_with_dict(self):
        """Merge can replace scalar with dict."""
        loader = ConfigLoader()

        base = {"config": "simple_string"}
        override = {"config": {"nested": "value"}}

        merged = loader.merge(base, override)
        assert merged["config"]["nested"] == "value"

    def test_typed_accessors(self):
        """Typed property accessors work."""
        config = Config.default()

        assert isinstance(config.system, SystemConfig)
        assert isinstance(config.event_system, EventSystemConfig)
        assert isinstance(config.detectors, DetectorsConfig)
        assert isinstance(config.alert_engine, AlertEngineConfig)
        assert isinstance(config.fusion, FusionConfig)
        assert isinstance(config.notifiers, NotifiersConfig)
        assert isinstance(config.dashboard, DashboardConfig)

    def test_config_with_invalid_data(self):
        """Config with invalid data raises validation error."""
        with pytest.raises(Exception):
            Config.from_dict({
                "detectors": {
                    "radar": {
                        "sensitivity": 999,  # Out of range
                    }
                }
            })

    def test_save_without_path_raises(self):
        """Save without path and no source raises."""
        config = Config.from_dict({"system": {"name": "test"}})

        with pytest.raises(ValueError):
            config.save()


class TestFusionConfig:
    """Tests for FusionConfig."""

    def test_default_values(self):
        """Default fusion config values."""
        config = FusionConfig()
        assert config.signal_max_age_seconds == 5.0
        assert config.cross_validation_enabled is True
        assert config.agreement_bonus == 0.1
        assert config.disagreement_penalty == 0.2

    def test_fusion_rule(self):
        """Create fusion rule."""
        rule = FusionRule(
            signal="respiration_rate",
            sources=[
                FusionRuleSource(detector="radar", field="respiration_rate", weight=1.0),
                FusionRuleSource(detector="audio", field="breathing_rate", weight=0.5),
            ],
            strategy="weighted_average",
            min_sources=1,
        )

        assert rule.signal == "respiration_rate"
        assert len(rule.sources) == 2
        assert rule.strategy == "weighted_average"


class TestEventSystemConfig:
    """Tests for EventSystemConfig."""

    def test_default_values(self):
        """Default event system config values."""
        config = EventSystemConfig()
        assert config.event_endpoint == "ipc:///tmp/nightwatch-events"
        assert config.alert_endpoint == "ipc:///tmp/nightwatch-alerts"
        assert config.buffer_capacity == 5000
        assert config.persist_interval_seconds == 60.0


class TestPushNotifierConfig:
    """Tests for PushNotifierConfig."""

    def test_default_values(self):
        """Default push notifier config."""
        config = PushNotifierConfig()
        assert config.enabled is True
        assert config.provider == "pushover"
        assert config.retry_count == 3


class TestWebhookNotifierConfig:
    """Tests for WebhookNotifierConfig."""

    def test_default_disabled(self):
        """Webhook notifier disabled by default."""
        config = WebhookNotifierConfig()
        assert config.enabled is False
        assert config.method == "POST"
        assert config.timeout_seconds == 30.0
