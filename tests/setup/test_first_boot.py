"""Tests for first-boot detection logic."""

from __future__ import annotations

import pytest
from pathlib import Path
import tempfile

from nightwatch.setup.first_boot import (
    SetupState,
    SetupStatus,
    detect_setup_state,
    get_setup_status,
    mark_configured,
    reset_configuration,
    CONFIGURED_FLAG,
    WIFI_CONFIG_FILE,
    MONITOR_NAME_FILE,
)


@pytest.fixture
def temp_config_dir():
    """Create a temporary config directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


class TestSetupState:
    """Test SetupState enum values."""

    def test_unconfigured_state_exists(self):
        assert SetupState.UNCONFIGURED is not None

    def test_wifi_only_state_exists(self):
        assert SetupState.WIFI_ONLY is not None

    def test_fully_configured_state_exists(self):
        assert SetupState.FULLY_CONFIGURED is not None


class TestDetectSetupState:
    """Test detect_setup_state function."""

    def test_nonexistent_dir_returns_unconfigured(self, temp_config_dir: Path):
        """Missing config directory should return UNCONFIGURED."""
        nonexistent = temp_config_dir / "does-not-exist"
        state = detect_setup_state(nonexistent)
        assert state == SetupState.UNCONFIGURED

    def test_empty_dir_returns_unconfigured(self, temp_config_dir: Path):
        """Empty config directory should return UNCONFIGURED."""
        state = detect_setup_state(temp_config_dir)
        assert state == SetupState.UNCONFIGURED

    def test_wifi_only_returns_wifi_only(self, temp_config_dir: Path):
        """WiFi configured but no .configured flag should return WIFI_ONLY."""
        wifi_file = temp_config_dir / WIFI_CONFIG_FILE
        wifi_file.write_text("ssid=TestNetwork\npassword=testpass123")

        state = detect_setup_state(temp_config_dir)
        assert state == SetupState.WIFI_ONLY

    def test_configured_flag_returns_fully_configured(self, temp_config_dir: Path):
        """Both WiFi and .configured flag should return FULLY_CONFIGURED."""
        # Create WiFi config
        wifi_file = temp_config_dir / WIFI_CONFIG_FILE
        wifi_file.write_text("ssid=TestNetwork\npassword=testpass123")

        # Create configured flag
        flag_file = temp_config_dir / CONFIGURED_FLAG
        flag_file.touch()

        state = detect_setup_state(temp_config_dir)
        assert state == SetupState.FULLY_CONFIGURED

    def test_configured_flag_without_wifi_is_unconfigured(self, temp_config_dir: Path):
        """Configured flag alone without WiFi should still be UNCONFIGURED."""
        flag_file = temp_config_dir / CONFIGURED_FLAG
        flag_file.touch()

        state = detect_setup_state(temp_config_dir)
        assert state == SetupState.UNCONFIGURED


class TestGetSetupStatus:
    """Test get_setup_status function for detailed status."""

    def test_returns_setup_status_object(self, temp_config_dir: Path):
        """Should return a SetupStatus namedtuple."""
        status = get_setup_status(temp_config_dir)
        assert isinstance(status, SetupStatus)

    def test_status_contains_all_fields(self, temp_config_dir: Path):
        """SetupStatus should have all expected fields."""
        status = get_setup_status(temp_config_dir)

        assert hasattr(status, "state")
        assert hasattr(status, "has_wifi")
        assert hasattr(status, "has_name")
        assert hasattr(status, "has_configured_flag")
        assert hasattr(status, "config_dir_exists")
        assert hasattr(status, "message")

    def test_empty_dir_status(self, temp_config_dir: Path):
        """Empty directory should report correct status."""
        status = get_setup_status(temp_config_dir)

        assert status.state == SetupState.UNCONFIGURED
        assert status.has_wifi is False
        assert status.has_name is False
        assert status.has_configured_flag is False
        assert status.config_dir_exists is True

    def test_wifi_configured_status(self, temp_config_dir: Path):
        """WiFi config should be reflected in status."""
        wifi_file = temp_config_dir / WIFI_CONFIG_FILE
        wifi_file.write_text("ssid=TestNetwork\npassword=testpass123")

        status = get_setup_status(temp_config_dir)

        assert status.has_wifi is True
        assert status.state == SetupState.WIFI_ONLY

    def test_name_configured_status(self, temp_config_dir: Path):
        """Monitor name should be reflected in status."""
        name_file = temp_config_dir / MONITOR_NAME_FILE
        name_file.write_text("Kids Room")

        status = get_setup_status(temp_config_dir)

        assert status.has_name is True

    def test_fully_configured_status(self, temp_config_dir: Path):
        """Full configuration should be reflected in status."""
        # Create all config files
        (temp_config_dir / WIFI_CONFIG_FILE).write_text("ssid=TestNet\npassword=pass123")
        (temp_config_dir / MONITOR_NAME_FILE).write_text("Kids Room")
        (temp_config_dir / CONFIGURED_FLAG).touch()

        status = get_setup_status(temp_config_dir)

        assert status.state == SetupState.FULLY_CONFIGURED
        assert status.has_wifi is True
        assert status.has_name is True
        assert status.has_configured_flag is True


class TestWiFiConfigValidation:
    """Test WiFi configuration file validation."""

    def test_empty_wifi_file_is_invalid(self, temp_config_dir: Path):
        """Empty WiFi config file should not count as configured."""
        wifi_file = temp_config_dir / WIFI_CONFIG_FILE
        wifi_file.write_text("")

        status = get_setup_status(temp_config_dir)
        assert status.has_wifi is False

    def test_wifi_file_without_ssid_is_invalid(self, temp_config_dir: Path):
        """WiFi config without SSID should not count as configured."""
        wifi_file = temp_config_dir / WIFI_CONFIG_FILE
        wifi_file.write_text("password=testpass123")

        status = get_setup_status(temp_config_dir)
        assert status.has_wifi is False

    def test_wifi_file_with_ssid_is_valid(self, temp_config_dir: Path):
        """WiFi config with SSID should be valid."""
        wifi_file = temp_config_dir / WIFI_CONFIG_FILE
        wifi_file.write_text("ssid=MyNetwork\npassword=pass")

        status = get_setup_status(temp_config_dir)
        assert status.has_wifi is True

    def test_wifi_file_ssid_case_insensitive(self, temp_config_dir: Path):
        """SSID key should be case-insensitive."""
        wifi_file = temp_config_dir / WIFI_CONFIG_FILE
        wifi_file.write_text("SSID=MyNetwork\npassword=pass")

        status = get_setup_status(temp_config_dir)
        assert status.has_wifi is True


class TestMarkConfigured:
    """Test mark_configured function."""

    def test_creates_flag_file(self, temp_config_dir: Path):
        """Should create .configured flag file."""
        mark_configured(temp_config_dir)

        flag_path = temp_config_dir / CONFIGURED_FLAG
        assert flag_path.exists()

    def test_creates_directory_if_needed(self):
        """Should create config directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            new_config_dir = Path(tmpdir) / "new" / "config" / "dir"
            mark_configured(new_config_dir)

            assert new_config_dir.exists()
            assert (new_config_dir / CONFIGURED_FLAG).exists()

    def test_idempotent(self, temp_config_dir: Path):
        """Calling multiple times should not fail."""
        mark_configured(temp_config_dir)
        mark_configured(temp_config_dir)

        flag_path = temp_config_dir / CONFIGURED_FLAG
        assert flag_path.exists()


class TestResetConfiguration:
    """Test reset_configuration function."""

    def test_removes_flag_file(self, temp_config_dir: Path):
        """Should remove .configured flag file."""
        flag_path = temp_config_dir / CONFIGURED_FLAG
        flag_path.touch()
        assert flag_path.exists()

        reset_configuration(temp_config_dir)

        assert not flag_path.exists()

    def test_handles_missing_flag(self, temp_config_dir: Path):
        """Should not fail if flag doesn't exist."""
        reset_configuration(temp_config_dir)  # Should not raise

    def test_preserves_other_files(self, temp_config_dir: Path):
        """Should not remove WiFi config or other files."""
        wifi_file = temp_config_dir / WIFI_CONFIG_FILE
        wifi_file.write_text("ssid=Test\npassword=pass")

        flag_path = temp_config_dir / CONFIGURED_FLAG
        flag_path.touch()

        reset_configuration(temp_config_dir)

        assert wifi_file.exists()  # WiFi config preserved
        assert not flag_path.exists()  # Flag removed
