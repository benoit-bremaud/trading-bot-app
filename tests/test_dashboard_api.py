"""Tests for dashboard API endpoints."""

from __future__ import annotations

import pytest

from dashboard.app import app


@pytest.fixture
def client():
    """Create test client."""
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_index_page(client):
    """Test index page loads."""
    response = client.get("/")
    assert response.status_code == 200
    assert b"Trading Bot Dashboard" in response.data


def test_health_endpoint(client):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "ok"


def test_get_candles_endpoint_no_data(client):
    """Test candles endpoint with no data."""
    response = client.get("/api/candles/BTC-USDT/1h")
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)


def test_get_signals_endpoint_no_data(client):
    """Test signals endpoint with no data."""
    response = client.get("/api/signals/BTC-USDT/1h")
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)


def test_backtest_endpoint(client):
    """Test backtest endpoint."""
    response = client.post(
        "/api/backtest",
        json={
            "symbol": "BTC-USDT",
            "timeframe": "1h",
            "initial_cash": 10000,
            "risk_per_trade": 0.02,
        },
    )
    # May return 404 if no data, or 200 with results
    assert response.status_code in [200, 404]
