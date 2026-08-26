"""
Tests for authenticating to a self-hosted ntfy server.

A private ntfy server (auth-default-access: deny-all) answers an unauthenticated
publish with 403. Without credentials the monitor would look configured, start
cleanly, and drop every alert - the exact silent failure this project keeps
producing. These tests pin both the header construction and the refusal to start
misconfigured.
"""

from __future__ import annotations

import base64

from nightwatch.__main__ import _missing_push_settings, _ntfy_is_public
from nightwatch.core.notifiers.push import PushConfig, PushNotifier, PushProvider


def cfg(**kw) -> PushConfig:
    base = dict(
        enabled=True,
        provider=PushProvider.NTFY,
        ntfy_server="https://ntfy.example.com",
        ntfy_topic="alerts",
    )
    base.update(kw)
    return PushConfig(**base)


# --- header construction ---------------------------------------------------


def test_basic_auth_header_is_built_from_user_and_password():
    n = PushNotifier(cfg(ntfy_username="pi", ntfy_password="s3cret"))
    expected = "Basic " + base64.b64encode(b"pi:s3cret").decode()
    assert n._ntfy_auth_header() == expected


def test_token_produces_bearer_header():
    n = PushNotifier(cfg(ntfy_token="tk_abc123"))
    assert n._ntfy_auth_header() == "Bearer tk_abc123"


def test_token_wins_over_password():
    """The token is the more narrowly scoped credential, so prefer it."""
    n = PushNotifier(cfg(ntfy_token="tk_abc123", ntfy_username="pi", ntfy_password="s3cret"))
    assert n._ntfy_auth_header() == "Bearer tk_abc123"


def test_no_credentials_means_no_header():
    assert PushNotifier(cfg())._ntfy_auth_header() is None


def test_username_without_password_is_not_half_sent():
    assert PushNotifier(cfg(ntfy_username="pi"))._ntfy_auth_header() is None


# --- refusing to start misconfigured ---------------------------------------


def test_private_server_without_credentials_is_reported_missing():
    missing = _missing_push_settings(cfg())
    assert any("ntfy_token" in m for m in missing), missing


def test_private_server_with_credentials_is_complete():
    assert _missing_push_settings(cfg(ntfy_username="pi", ntfy_password="s3cret")) == []
    assert _missing_push_settings(cfg(ntfy_token="tk_abc")) == []


def test_public_ntfy_sh_does_not_require_credentials():
    """ntfy.sh accepts anonymous publishes, so credentials are genuinely optional."""
    assert _ntfy_is_public("https://ntfy.sh")
    assert not _ntfy_is_public("https://ntfy.example.com")
    assert _missing_push_settings(cfg(ntfy_server="https://ntfy.sh")) == []


def test_missing_topic_still_reported():
    assert "ntfy_topic" in _missing_push_settings(cfg(ntfy_topic="", ntfy_token="tk"))
