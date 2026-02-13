"""
Configuration system for Nightwatch.

Provides YAML-based configuration with:
- Dot-notation access
- Environment variable overrides
- Hot reload support
- Pydantic validation
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any, TypeVar, Generic, Type, Callable
from dataclasses import dataclass

import yaml
from pydantic import BaseModel, Field, field_validator
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent

T = TypeVar("T")


# ============================================================================
# Typed Configuration Models
# ============================================================================


class RadarConfig(BaseModel):
    """Configuration for radar detector."""

    enabled: bool = True
    device: str = "/dev/ttyAMA0"
    baud_rate: int = 256000
    model: str = "ld2450"  # ld2450 | ld2410
    sensitivity: float = Field(default=0.8, ge=0.0, le=1.0)
    update_rate_hz: int = Field(default=10, ge=1, le=30)
    respiration_threshold: float = Field(default=0.3, ge=0.0, le=1.0)
    movement_threshold: float = Field(default=0.5, ge=0.0, le=1.0)
    detection_distance_min: float = Field(default=0.3, ge=0.0)
    detection_distance_max: float = Field(default=3.0, ge=0.0)

    @field_validator("model")
    @classmethod
    def validate_model(cls, v: str) -> str:
        if v not in ("ld2450", "ld2410"):
            raise ValueError(f"Model must be 'ld2450' or 'ld2410', got '{v}'")
        return v


class AudioConfig(BaseModel):
    """Configuration for audio detector."""

    enabled: bool = True
    device: str | None = None  # None = default device
    sample_rate: int = Field(default=16000, ge=8000, le=48000)
    chunk_size: int = Field(default=1024, ge=256, le=4096)
    channels: int = Field(default=1, ge=1, le=2)
    update_rate_hz: float = Field(default=10.0, ge=1.0, le=30.0)
    silence_threshold: float = Field(default=0.005, ge=0.0, le=1.0)
    breathing_threshold: float = Field(default=0.02, ge=0.0, le=1.0)
    breathing_freq_min_hz: float = Field(default=200.0, ge=50.0)
    breathing_freq_max_hz: float = Field(default=800.0, le=2000.0)


class BCGConfig(BaseModel):
    """Configuration for BCG (bed sensor) detector."""

    enabled: bool = False  # Not installed initially
    sensor_type: str = "piezo"  # piezo | fsr
    adc_type: str = "mcp3008"  # mcp3008 | ads1115
    spi_bus: int = 0
    spi_device: int = 0
    adc_channel: int = 0
    sample_rate: int = Field(default=100, ge=50, le=500)
    update_rate_hz: float = Field(default=10.0, ge=1.0, le=30.0)
    filter_low_hz: float = Field(default=0.5, ge=0.1)
    filter_high_hz: float = Field(default=25.0, le=50.0)
    peak_detection_threshold: float = Field(default=0.6, ge=0.0, le=1.0)


class DetectorsConfig(BaseModel):
    """Configuration for all detectors."""

    radar: RadarConfig = Field(default_factory=RadarConfig)
    audio: AudioConfig = Field(default_factory=AudioConfig)
    bcg: BCGConfig = Field(default_factory=BCGConfig)


class AlertRuleCondition(BaseModel):
    """Single condition in an alert rule."""

    detector: str
    field: str
    operator: str = "<"  # <, >, ==, !=, <=, >=
    value: float | int | bool | str
    duration_seconds: float = 0.0

    @field_validator("operator")
    @classmethod
    def validate_operator(cls, v: str) -> str:
        valid = {"<", ">", "==", "!=", "<=", ">="}
        if v not in valid:
            raise ValueError(f"Operator must be one of {valid}, got '{v}'")
        return v


class AlertRule(BaseModel):
    """Alert rule configuration."""

    name: str
    conditions: list[AlertRuleCondition]
    severity: str = "critical"  # info | warning | critical
    combine: str = "all"  # all | any
    duration_seconds: float = 0.0
    cooldown_seconds: float = 30.0
    message: str = ""

    @field_validator("severity")
    @classmethod
    def validate_severity(cls, v: str) -> str:
        valid = {"info", "warning", "critical"}
        if v not in valid:
            raise ValueError(f"Severity must be one of {valid}, got '{v}'")
        return v


class AlertEngineConfig(BaseModel):
    """Configuration for alert engine."""

    detector_timeout_seconds: float = Field(default=10.0, ge=1.0)
    health_check_interval: float = Field(default=5.0, ge=1.0)
    alert_cooldown_seconds: float = Field(default=30.0, ge=0.0)
    acknowledge_timeout_seconds: float = Field(default=60.0, ge=0.0)
    max_pause_minutes: int = Field(default=60, ge=1, le=480)
    rules: list[AlertRule] = Field(default_factory=list)


class AudioNotifierConfig(BaseModel):
    """Configuration for audio (local alarm) notifier."""

    enabled: bool = True
    output_type: str = "speaker"  # speaker | buzzer | both
    speaker_device: str = "default"
    buzzer_gpio_pin: int = 18
    initial_volume: int = Field(default=60, ge=0, le=100)
    max_volume: int = Field(default=100, ge=0, le=100)
    escalation_enabled: bool = True
    escalation_interval_seconds: float = 15.0
    max_duration_seconds: float = 120.0
    sounds_dir: str = "/usr/share/nightwatch/sounds"


class PushNotifierConfig(BaseModel):
    """Configuration for push notification."""

    enabled: bool = True
    provider: str = "pushover"  # pushover | ntfy
    pushover_user_key: str = ""
    pushover_api_token: str = ""
    ntfy_server: str = "https://ntfy.sh"
    ntfy_topic: str = ""
    retry_count: int = Field(default=3, ge=0, le=10)
    retry_delay_seconds: float = Field(default=5.0, ge=1.0)


class WebhookNotifierConfig(BaseModel):
    """Configuration for webhook notifier."""

    enabled: bool = False
    url: str = ""
    method: str = "POST"
    headers: dict[str, str] = Field(default_factory=dict)
    body_template: str = ""
    timeout_seconds: float = Field(default=30.0, ge=1.0)


class NotifiersConfig(BaseModel):
    """Configuration for all notifiers."""

    audio: AudioNotifierConfig = Field(default_factory=AudioNotifierConfig)
    push: PushNotifierConfig = Field(default_factory=PushNotifierConfig)
    webhook: WebhookNotifierConfig = Field(default_factory=WebhookNotifierConfig)


class DashboardConfig(BaseModel):
    """Configuration for web dashboard."""

    host: str = "0.0.0.0"
    port: int = Field(default=5000, ge=1, le=65535)
    debug: bool = False
    auth_enabled: bool = False
    auth_username: str = "admin"
    auth_password_hash: str = ""
    websocket_update_interval_ms: int = Field(default=1000, ge=100, le=5000)
    history_retention_days: int = Field(default=30, ge=1, le=365)


class FusionRuleSource(BaseModel):
    """Signal source for fusion."""

    detector: str
    field: str
    weight: float = Field(default=1.0, ge=0.0, le=10.0)


class FusionRule(BaseModel):
    """Fusion rule configuration."""

    signal: str
    sources: list[FusionRuleSource]
    strategy: str = "weighted_average"  # weighted_average | best_confidence | voting
    min_sources: int = 1
    agreement_threshold: float = 4.0


class FusionConfig(BaseModel):
    """Configuration for signal fusion."""

    signal_max_age_seconds: float = Field(default=5.0, ge=1.0)
    cross_validation_enabled: bool = True
    agreement_bonus: float = Field(default=0.1, ge=0.0, le=0.5)
    disagreement_penalty: float = Field(default=0.2, ge=0.0, le=0.5)
    rules: list[FusionRule] = Field(default_factory=list)


class EventSystemConfig(BaseModel):
    """Configuration for event system."""

    event_endpoint: str = "ipc:///tmp/nightwatch-events"
    alert_endpoint: str = "ipc:///tmp/nightwatch-alerts"
    buffer_capacity: int = Field(default=5000, ge=100)
    persist_interval_seconds: float = Field(default=60.0, ge=10.0)


class SystemConfig(BaseModel):
    """Top-level system configuration."""

    name: str = "nightwatch"
    log_level: str = "INFO"
    data_dir: str = "/var/lib/nightwatch"


class NightwatchConfig(BaseModel):
    """Complete Nightwatch configuration."""

    system: SystemConfig = Field(default_factory=SystemConfig)
    event_system: EventSystemConfig = Field(default_factory=EventSystemConfig)
    detectors: DetectorsConfig = Field(default_factory=DetectorsConfig)
    alert_engine: AlertEngineConfig = Field(default_factory=AlertEngineConfig)
    fusion: FusionConfig = Field(default_factory=FusionConfig)
    notifiers: NotifiersConfig = Field(default_factory=NotifiersConfig)
    dashboard: DashboardConfig = Field(default_factory=DashboardConfig)


# ============================================================================
# Configuration Change Tracking
# ============================================================================


@dataclass
class ConfigChange:
    """Represents a configuration change."""

    path: str  # Dot-notation path
    old_value: Any
    new_value: Any
    timestamp: float


# ============================================================================
# Configuration Loader
# ============================================================================


class ConfigLoader:
    """Loads and merges configuration from YAML files."""

    # Pattern for environment variable references: ${VAR} or ${VAR:-default}
    ENV_PATTERN = re.compile(r"\$\{([^}:]+)(?::-([^}]*))?\}")

    def load_yaml(self, path: Path) -> dict[str, Any]:
        """Load single YAML file with env var substitution."""
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")

        content = path.read_text()
        content = self._substitute_env_vars(content)

        return yaml.safe_load(content) or {}

    def load_directory(self, dir_path: Path) -> dict[str, Any]:
        """Load and merge all YAML files in directory."""
        if not dir_path.is_dir():
            raise NotADirectoryError(f"Config directory not found: {dir_path}")

        config: dict[str, Any] = {}

        # Load files in sorted order for deterministic merging
        for yaml_file in sorted(dir_path.glob("*.yaml")):
            file_config = self.load_yaml(yaml_file)
            config = self.merge(config, file_config)

        return config

    def merge(self, base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
        """Deep merge override into base."""
        result = base.copy()

        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self.merge(result[key], value)
            else:
                result[key] = value

        return result

    def _substitute_env_vars(self, content: str) -> str:
        """Replace ${VAR} and ${VAR:-default} with environment values."""

        def replacer(match: re.Match) -> str:
            var_name = match.group(1)
            default = match.group(2)
            value = os.environ.get(var_name)

            if value is not None:
                return value
            elif default is not None:
                return default
            else:
                return match.group(0)  # Keep original if no value and no default

        return self.ENV_PATTERN.sub(replacer, content)

    def apply_env_overrides(self, config: dict[str, Any]) -> dict[str, Any]:
        """
        Apply environment variable overrides.

        NIGHTWATCH_RADAR_SENSITIVITY=0.9 -> detectors.radar.sensitivity = 0.9
        """
        prefix = "NIGHTWATCH_"

        for key, value in os.environ.items():
            if not key.startswith(prefix):
                continue

            # Convert NIGHTWATCH_RADAR_SENSITIVITY to detectors.radar.sensitivity
            path_parts = key[len(prefix) :].lower().split("_")
            self._set_nested(config, path_parts, self._parse_value(value))

        return config

    def _set_nested(self, obj: dict[str, Any], path: list[str], value: Any) -> None:
        """Set a nested value using a list of keys."""
        for key in path[:-1]:
            if key not in obj:
                obj[key] = {}
            obj = obj[key]
        obj[path[-1]] = value

    def _parse_value(self, value: str) -> Any:
        """Parse string value to appropriate type."""
        # Boolean
        if value.lower() in ("true", "yes", "1"):
            return True
        if value.lower() in ("false", "no", "0"):
            return False

        # Number
        try:
            if "." in value:
                return float(value)
            return int(value)
        except ValueError:
            pass

        return value


# ============================================================================
# Configuration Watcher
# ============================================================================


class ConfigWatcher:
    """Watches config files for changes."""

    def __init__(self, paths: list[Path]):
        self._paths = paths
        self._observer = Observer()
        self._callbacks: list[Callable[[Path], None]] = []
        self._started = False

    def start(self) -> None:
        """Start watching for changes."""
        if self._started:
            return

        handler = _ConfigFileHandler(self._on_change)

        for path in self._paths:
            watch_path = path.parent if path.is_file() else path
            self._observer.schedule(handler, str(watch_path), recursive=False)

        self._observer.start()
        self._started = True

    def stop(self) -> None:
        """Stop watching."""
        if not self._started:
            return

        self._observer.stop()
        self._observer.join()
        self._started = False

    def add_callback(self, callback: Callable[[Path], None]) -> None:
        """Add callback for file changes."""
        self._callbacks.append(callback)

    def _on_change(self, path: Path) -> None:
        """Called when a config file changes."""
        for callback in self._callbacks:
            callback(path)


class _ConfigFileHandler(FileSystemEventHandler):
    """File system event handler for config changes."""

    def __init__(self, callback: Callable[[Path], None]):
        self._callback = callback

    def on_modified(self, event: FileModifiedEvent) -> None:
        if event.is_directory:
            return
        if event.src_path.endswith(".yaml"):
            self._callback(Path(event.src_path))


# ============================================================================
# Main Configuration Class
# ============================================================================


class Config:
    """
    Main configuration container with hot reload support.

    Usage:
        config = Config.load(Path("/etc/nightwatch/config.yaml"))
        sensitivity = config.get("detectors.radar.sensitivity", 0.8)

        # Or with typed access:
        radar_config = config.detectors.radar
        sensitivity = radar_config.sensitivity
    """

    def __init__(self, data: dict[str, Any], source_path: Path | None = None):
        self._data = data
        self._source_path = source_path
        self._loader = ConfigLoader()
        self._watcher: ConfigWatcher | None = None
        self._change_callbacks: list[Callable[[list[ConfigChange]], None]] = []

        # Parse into typed config
        self._typed = NightwatchConfig.model_validate(data)

    @classmethod
    def load(cls, path: Path) -> Config:
        """Load configuration from YAML file."""
        loader = ConfigLoader()
        data = loader.load_yaml(path)
        data = loader.apply_env_overrides(data)
        return cls(data, source_path=path)

    @classmethod
    def load_directory(cls, dir_path: Path) -> Config:
        """Load and merge all YAML files in directory."""
        loader = ConfigLoader()
        data = loader.load_directory(dir_path)
        data = loader.apply_env_overrides(data)
        return cls(data, source_path=dir_path)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Config:
        """Create configuration from dictionary."""
        return cls(data)

    @classmethod
    def default(cls) -> Config:
        """Create configuration with all defaults."""
        return cls({})

    def get(self, path: str, default: T = None) -> T:
        """
        Get config value by dot-notation path.

        Example: config.get("detectors.radar.sensitivity", 0.8)
        """
        keys = path.split(".")
        value: Any = self._data

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default  # type: ignore

        return value  # type: ignore

    def set(self, path: str, value: Any) -> None:
        """Set config value (in-memory only, call save() to persist)."""
        keys = path.split(".")
        obj = self._data

        for key in keys[:-1]:
            if key not in obj:
                obj[key] = {}
            obj = obj[key]

        obj[keys[-1]] = value

        # Re-validate typed config
        self._typed = NightwatchConfig.model_validate(self._data)

    def save(self, path: Path | None = None) -> None:
        """Save configuration to YAML file."""
        save_path = path or self._source_path
        if not save_path:
            raise ValueError("No path specified and no source path available")

        # Ensure it's a file path
        if save_path.is_dir():
            save_path = save_path / "config.yaml"

        # Write atomically
        temp_path = save_path.with_suffix(".yaml.tmp")
        temp_path.write_text(yaml.dump(self._data, default_flow_style=False, sort_keys=False))
        temp_path.rename(save_path)

    def reload(self) -> list[ConfigChange]:
        """Reload from disk, return list of changes."""
        if not self._source_path:
            return []

        old_data = self._data.copy()

        if self._source_path.is_dir():
            self._data = self._loader.load_directory(self._source_path)
        else:
            self._data = self._loader.load_yaml(self._source_path)

        self._data = self._loader.apply_env_overrides(self._data)
        self._typed = NightwatchConfig.model_validate(self._data)

        # Calculate changes
        changes = self._diff(old_data, self._data)
        return changes

    def enable_hot_reload(
        self, callback: Callable[[list[ConfigChange]], None] | None = None
    ) -> None:
        """Enable file watching for automatic reload."""
        if not self._source_path:
            raise ValueError("Cannot enable hot reload without a source path")

        if callback:
            self._change_callbacks.append(callback)

        if self._watcher:
            return

        paths = [self._source_path]
        self._watcher = ConfigWatcher(paths)
        self._watcher.add_callback(self._on_file_change)
        self._watcher.start()

    def disable_hot_reload(self) -> None:
        """Disable file watching."""
        if self._watcher:
            self._watcher.stop()
            self._watcher = None

    def validate(self) -> list[str]:
        """Validate configuration, return list of errors."""
        errors: list[str] = []

        try:
            NightwatchConfig.model_validate(self._data)
        except Exception as e:
            errors.append(str(e))

        return errors

    def to_dict(self) -> dict[str, Any]:
        """Get configuration as dictionary."""
        return self._data.copy()

    def _on_file_change(self, path: Path) -> None:
        """Called when a config file changes."""
        changes = self.reload()
        for callback in self._change_callbacks:
            callback(changes)

    def _diff(
        self, old: dict[str, Any], new: dict[str, Any], prefix: str = ""
    ) -> list[ConfigChange]:
        """Calculate differences between two config dicts."""
        import time

        changes: list[ConfigChange] = []
        now = time.time()

        all_keys = set(old.keys()) | set(new.keys())

        for key in all_keys:
            path = f"{prefix}.{key}" if prefix else key
            old_val = old.get(key)
            new_val = new.get(key)

            if old_val == new_val:
                continue

            if isinstance(old_val, dict) and isinstance(new_val, dict):
                changes.extend(self._diff(old_val, new_val, path))
            else:
                changes.append(ConfigChange(path, old_val, new_val, now))

        return changes

    # ========================================================================
    # Typed Accessors
    # ========================================================================

    @property
    def system(self) -> SystemConfig:
        return self._typed.system

    @property
    def event_system(self) -> EventSystemConfig:
        return self._typed.event_system

    @property
    def detectors(self) -> DetectorsConfig:
        return self._typed.detectors

    @property
    def alert_engine(self) -> AlertEngineConfig:
        return self._typed.alert_engine

    @property
    def fusion(self) -> FusionConfig:
        return self._typed.fusion

    @property
    def notifiers(self) -> NotifiersConfig:
        return self._typed.notifiers

    @property
    def dashboard(self) -> DashboardConfig:
        return self._typed.dashboard
