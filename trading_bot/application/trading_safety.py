from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass(frozen=True, slots=True)
class RiskPolicy:
    max_position_pct: float
    max_total_exposure_pct: float
    max_daily_loss_pct: float
    max_open_positions: int

    def __post_init__(self) -> None:
        if not 0 < self.max_position_pct <= 1:
            raise ValueError("max_position_pct must be within (0, 1]")
        if not 0 < self.max_total_exposure_pct <= 1:
            raise ValueError("max_total_exposure_pct must be within (0, 1]")
        if self.max_position_pct > self.max_total_exposure_pct:
            raise ValueError("max_position_pct must be <= max_total_exposure_pct")
        if not 0 < self.max_daily_loss_pct <= 1:
            raise ValueError("max_daily_loss_pct must be within (0, 1]")
        if self.max_open_positions < 1:
            raise ValueError("max_open_positions must be >= 1")


@dataclass(slots=True)
class TradingSafetyState:
    policy: RiskPolicy
    day_start_equity: float = 0.0
    daily_realized_pnl: float = 0.0
    open_positions: int = 0
    current_day: datetime | None = None

    def sync_day(self, timestamp: datetime, current_equity: float) -> None:
        ts_utc = timestamp.astimezone(UTC)
        day = datetime(ts_utc.year, ts_utc.month, ts_utc.day, tzinfo=UTC)
        if self.current_day != day:
            self.current_day = day
            self.day_start_equity = max(current_equity, 0.0)
            self.daily_realized_pnl = 0.0

    def can_open(
        self, portfolio_equity: float, current_exposure_value: float
    ) -> tuple[bool, str]:
        if self.open_positions >= self.policy.max_open_positions:
            return False, "max_open_positions_reached"

        if portfolio_equity <= 0:
            return False, "non_positive_equity"

        exposure_pct = current_exposure_value / portfolio_equity
        if exposure_pct >= self.policy.max_total_exposure_pct:
            return False, "max_total_exposure_reached"

        daily_loss_limit = (
            -self.policy.max_daily_loss_pct * self.day_start_equity
        )
        if self.daily_realized_pnl < daily_loss_limit:
            return False, "max_daily_loss_breached"

        return True, "ok"

    def max_entry_notional(
        self, portfolio_equity: float, current_exposure_value: float
    ) -> float:
        by_position = portfolio_equity * self.policy.max_position_pct
        by_exposure = (
            portfolio_equity * self.policy.max_total_exposure_pct
            - current_exposure_value
        )
        return max(min(by_position, by_exposure), 0.0)

    def on_entry(self) -> None:
        self.open_positions += 1

    def on_exit(self, realized_pnl: float) -> None:
        self.open_positions = max(self.open_positions - 1, 0)
        self.daily_realized_pnl += realized_pnl


@dataclass(slots=True)
class IdempotencyGuard:
    seen_keys: set[str] = field(default_factory=set)

    def make_key(
        self, symbol: str, timeframe: str, candle_ts: datetime, action: str
    ) -> str:
        ts = int(candle_ts.astimezone(UTC).timestamp())
        return f"{symbol}:{timeframe}:{ts}:{action}"

    def register_if_new(self, key: str) -> bool:
        if key in self.seen_keys:
            return False
        self.seen_keys.add(key)
        return True


@dataclass(slots=True)
class TradingSafetyController:
    """Centralized safety guard for kill-switch and idempotency."""

    safety: TradingSafetyState
    idempotency: IdempotencyGuard
    kill_switch: bool = False

    def make_key(
        self, symbol: str, timeframe: str, candle_ts: datetime, action: str
    ) -> str:
        return self.idempotency.make_key(symbol, timeframe, candle_ts, action)

    def should_force_exit(self) -> bool:
        return self.kill_switch

    def can_enter(
        self,
        portfolio_equity: float,
        current_exposure_value: float,
        action_key: str,
    ) -> tuple[bool, str]:
        if self.kill_switch:
            return False, "kill_switch_enabled"

        allowed, reason = self.safety.can_open(
            portfolio_equity, current_exposure_value
        )
        if not allowed:
            return False, reason

        if not self.idempotency.register_if_new(
            action_key
        ):
            return False, "duplicate_action"

        return True, "ok"

    def can_exit(self, action_key: str) -> bool:
        return self.idempotency.register_if_new(action_key)
