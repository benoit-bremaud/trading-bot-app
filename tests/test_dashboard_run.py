"""The dashboard entry point must stay local and debugger-free unless asked for."""

from __future__ import annotations

import pytest

from dashboard import app as dashboard_app

_ENV_VARS = ("DASHBOARD_HOST", "DASHBOARD_PORT", "DASHBOARD_DEBUG")


@pytest.fixture
def run_calls(monkeypatch: pytest.MonkeyPatch) -> list[dict[str, object]]:
    """Stub `app.run` (the boundary) and clear the DASHBOARD_* variables."""
    calls: list[dict[str, object]] = []
    monkeypatch.setattr(dashboard_app.app, "run", lambda **kwargs: calls.append(kwargs))
    for name in _ENV_VARS:
        monkeypatch.delenv(name, raising=False)
    return calls


def test_defaults_bind_loopback_without_debugger(run_calls: list[dict[str, object]]) -> None:
    dashboard_app.run_dashboard()

    assert run_calls == [{"debug": False, "host": "127.0.0.1", "port": 5000}]


def test_environment_overrides_host_port_and_debug(
    run_calls: list[dict[str, object]], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("DASHBOARD_HOST", "localhost")
    monkeypatch.setenv("DASHBOARD_PORT", "8080")
    monkeypatch.setenv("DASHBOARD_DEBUG", "1")

    dashboard_app.run_dashboard()

    assert run_calls == [{"debug": True, "host": "localhost", "port": 8080}]


@pytest.mark.parametrize("value", ["0", "true", "yes", ""])
def test_debugger_only_enabled_by_exactly_one(
    run_calls: list[dict[str, object]], monkeypatch: pytest.MonkeyPatch, value: str
) -> None:
    monkeypatch.setenv("DASHBOARD_DEBUG", value)

    dashboard_app.run_dashboard()

    assert run_calls[0]["debug"] is False


def test_debugger_refused_on_non_loopback_host(
    run_calls: list[dict[str, object]], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("DASHBOARD_HOST", "0.0.0.0")
    monkeypatch.setenv("DASHBOARD_DEBUG", "1")

    with pytest.raises(SystemExit, match="loopback"):
        dashboard_app.run_dashboard()
    assert run_calls == []


def test_invalid_port_is_a_clear_startup_error(
    run_calls: list[dict[str, object]], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("DASHBOARD_PORT", "abc")

    with pytest.raises(SystemExit, match="DASHBOARD_PORT"):
        dashboard_app.run_dashboard()
    assert run_calls == []
