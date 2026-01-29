from __future__ import annotations

from dataclasses import dataclass

from trading_bot.application.ports import RiskManager
from trading_bot.domain.entities import PairProfile


def _clamp(value: float, min_value: float, max_value: float) -> float:
    return max(min_value, min(max_value, value))


@dataclass(frozen=True, slots=True)
class BaselineRiskManager(RiskManager):
    max_position_pct: float
    volatility_target: float | None = None

    def __post_init__(self) -> None:
        if not 0 < self.max_position_pct <= 1:
            raise ValueError("max_position_pct must be within (0, 1]")
        if self.volatility_target is not None and self.volatility_target <= 0:
            raise ValueError("volatility_target must be positive")

    def position_size(self, profile: PairProfile, portfolio_value: float, score: float) -> float:
        if portfolio_value < 0:
            raise ValueError("portfolio_value must be >= 0")
        if portfolio_value == 0:
            return 0.0

        scaled_score = _clamp(score, 0.0, 1.0)
        position_pct = self.max_position_pct * scaled_score

        if self.volatility_target is not None and profile.volatility > 0:
            scale = min(1.0, self.volatility_target / profile.volatility)
            position_pct *= scale

        return portfolio_value * position_pct
