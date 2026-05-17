"""Tests for genealogy.observability."""

from __future__ import annotations

from unittest.mock import patch

from genealogy.observability import init_sentry


def test_init_sentry_returns_false_when_dsn_missing(monkeypatch):
    monkeypatch.delenv("GENEALOGY_SENTRY_DSN", raising=False)
    assert init_sentry() is False


def test_init_sentry_returns_false_when_dsn_empty(monkeypatch):
    monkeypatch.setenv("GENEALOGY_SENTRY_DSN", "")
    assert init_sentry() is False


def test_init_sentry_returns_false_when_dsn_whitespace(monkeypatch):
    monkeypatch.setenv("GENEALOGY_SENTRY_DSN", "   ")
    assert init_sentry() is False


def test_init_sentry_calls_sdk_when_dsn_set(monkeypatch):
    monkeypatch.setenv("GENEALOGY_SENTRY_DSN", "https://test@example.com/1")
    monkeypatch.setenv("GENEALOGY_ENV", "test-env")

    with patch("genealogy.observability.sentry_sdk.init") as mock_init:
        result = init_sentry()

    assert result is True
    mock_init.assert_called_once()
    kwargs = mock_init.call_args.kwargs
    assert kwargs["dsn"] == "https://test@example.com/1"
    assert kwargs["environment"] == "test-env"
    assert kwargs["send_default_pii"] is False
    assert kwargs["traces_sample_rate"] == 0.0


def test_init_sentry_explicit_args_win_over_env(monkeypatch):
    monkeypatch.setenv("GENEALOGY_SENTRY_DSN", "https://test@example.com/1")
    monkeypatch.setenv("GENEALOGY_ENV", "should-be-overridden")

    with patch("genealogy.observability.sentry_sdk.init") as mock_init:
        init_sentry(environment="explicit", release="v1.2.3")

    kwargs = mock_init.call_args.kwargs
    assert kwargs["environment"] == "explicit"
    assert kwargs["release"] == "v1.2.3"
