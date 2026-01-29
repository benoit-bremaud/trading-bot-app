import pytest

from trading_bot.application.risk_manager import BaselineRiskManager
from trading_bot.domain.entities import PairProfile


def _profile(volatility: float) -> PairProfile:
    return PairProfile(
        symbol="BTC-USDT",
        timeframe="1h",
        avg_volume=1.0,
        volatility=volatility,
        atr=None,
    )


def test_position_size_scales_with_score():
    manager = BaselineRiskManager(max_position_pct=0.02)

    size = manager.position_size(_profile(0.1), portfolio_value=1000.0, score=0.5)

    assert size == pytest.approx(10.0)


def test_position_size_clamps_score():
    manager = BaselineRiskManager(max_position_pct=0.02)

    high = manager.position_size(_profile(0.1), portfolio_value=1000.0, score=2.0)
    low = manager.position_size(_profile(0.1), portfolio_value=1000.0, score=-0.1)

    assert high == pytest.approx(20.0)
    assert low == 0.0


def test_position_size_validates_inputs():
    with pytest.raises(ValueError):
        BaselineRiskManager(max_position_pct=0.0)
    with pytest.raises(ValueError):
        BaselineRiskManager(max_position_pct=1.2)
    with pytest.raises(ValueError):
        BaselineRiskManager(max_position_pct=0.02, volatility_target=0.0)

    manager = BaselineRiskManager(max_position_pct=0.02)
    with pytest.raises(ValueError):
        manager.position_size(_profile(0.1), portfolio_value=-1.0, score=0.5)


def test_position_size_applies_volatility_target():
    manager = BaselineRiskManager(max_position_pct=0.02, volatility_target=0.05)

    size = manager.position_size(_profile(0.1), portfolio_value=1000.0, score=1.0)

    assert size == pytest.approx(10.0)


def test_position_size_ignores_zero_volatility():
    manager = BaselineRiskManager(max_position_pct=0.02, volatility_target=0.05)

    size = manager.position_size(_profile(0.0), portfolio_value=1000.0, score=1.0)

    assert size == pytest.approx(20.0)
