from __future__ import annotations

from datetime import UTC, datetime

import pytest

from trading_bot.application.trading_safety import (
    IdempotencyGuard,
    RiskPolicy,
    TradingSafetyController,
    TradingSafetyState,
)


def test_risk_policy_validation_rejects_invalid_bounds() -> None:
    with pytest.raises(ValueError):
        RiskPolicy(
            max_position_pct=0.0,
            max_total_exposure_pct=0.02,
            max_daily_loss_pct=0.03,
            max_open_positions=1,
        )


def test_risk_policy_validation_rejects_position_above_total_exposure() -> None:
    with pytest.raises(ValueError):
        RiskPolicy(
            max_position_pct=0.03,
            max_total_exposure_pct=0.02,
            max_daily_loss_pct=0.03,
            max_open_positions=1,
        )


def test_can_open_blocks_when_limits_hit() -> None:
    policy = RiskPolicy(
        max_position_pct=0.02,
        max_total_exposure_pct=0.03,
        max_daily_loss_pct=0.03,
        max_open_positions=1,
    )
    state = TradingSafetyState(policy=policy)
    state.sync_day(
        datetime(2026, 2, 8, 9, 0, tzinfo=UTC),
        current_equity=1000.0,
    )

    state.open_positions = 1
    allowed, reason = state.can_open(1000.0, current_exposure_value=0.0)
    assert not allowed
    assert reason == "max_open_positions_reached"

    state.open_positions = 0
    allowed, reason = state.can_open(1000.0, current_exposure_value=50.0)
    assert not allowed
    assert reason == "max_total_exposure_reached"

    state.daily_realized_pnl = -40.0  # below -3% of 1000
    allowed, reason = state.can_open(1000.0, current_exposure_value=0.0)
    assert not allowed
    assert reason == "max_daily_loss_breached"


def test_max_entry_notional_respects_position_and_exposure_caps() -> None:
    policy = RiskPolicy(
        max_position_pct=0.02,
        max_total_exposure_pct=0.03,
        max_daily_loss_pct=0.03,
        max_open_positions=1,
    )
    state = TradingSafetyState(policy=policy)

    # by_position=20, by_exposure=30-15=15 => min=15
    assert state.max_entry_notional(1000.0, current_exposure_value=15.0) == 15.0


def test_sync_day_resets_daily_pnl_on_new_day() -> None:
    policy = RiskPolicy(
        max_position_pct=0.02,
        max_total_exposure_pct=0.03,
        max_daily_loss_pct=0.03,
        max_open_positions=1,
    )
    state = TradingSafetyState(policy=policy)

    state.sync_day(
        datetime(2026, 2, 8, 23, 0, tzinfo=UTC),
        current_equity=1000.0,
    )
    state.daily_realized_pnl = -10.0

    state.sync_day(
        datetime(2026, 2, 9, 0, 5, tzinfo=UTC),
        current_equity=900.0,
    )
    assert state.day_start_equity == 900.0
    assert state.daily_realized_pnl == 0.0


def test_idempotency_guard_registers_only_once() -> None:
    guard = IdempotencyGuard()
    key = guard.make_key(
        "BTC-USDT",
        "1h",
        datetime(2026, 2, 8, 12, 0, tzinfo=UTC),
        "buy_entry",
    )
    assert guard.register_if_new(key)
    assert not guard.register_if_new(key)


def test_controller_blocks_entry_when_kill_switch_enabled() -> None:
    policy = RiskPolicy(
        max_position_pct=0.02,
        max_total_exposure_pct=0.03,
        max_daily_loss_pct=0.03,
        max_open_positions=1,
    )
    safety = TradingSafetyState(policy=policy)
    controller = TradingSafetyController(
        safety=safety,
        idempotency=IdempotencyGuard(),
        kill_switch=True,
    )
    key = controller.make_key(
        "BTC-USDT",
        "1h",
        datetime(2026, 2, 8, 12, 0, tzinfo=UTC),
        "buy_entry",
    )
    allowed, reason = controller.can_enter(
        1000.0,
        0.0,
        key,
    )
    assert not allowed
    assert reason == "kill_switch_enabled"


def test_controller_rejects_duplicate_entries() -> None:
    policy = RiskPolicy(
        max_position_pct=0.02,
        max_total_exposure_pct=0.03,
        max_daily_loss_pct=0.03,
        max_open_positions=1,
    )
    safety = TradingSafetyState(policy=policy)
    controller = TradingSafetyController(
        safety=safety,
        idempotency=IdempotencyGuard(),
        kill_switch=False,
    )
    key = controller.make_key(
        "BTC-USDT",
        "1h",
        datetime(2026, 2, 8, 12, 0, tzinfo=UTC),
        "buy_entry",
    )
    allowed, reason = controller.can_enter(
        1000.0,
        0.0,
        key,
    )
    assert allowed
    assert reason == "ok"

    allowed, reason = controller.can_enter(
        1000.0,
        0.0,
        key,
    )
    assert not allowed
    assert reason == "duplicate_action"
