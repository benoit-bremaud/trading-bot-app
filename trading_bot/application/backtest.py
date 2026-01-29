from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime

from trading_bot.application.ports import BacktestEngine, CandleRepository
from trading_bot.domain.entities import BacktestResult, Candle


class BuyAndHoldBacktestEngine(BacktestEngine):
    def __init__(self, repository: CandleRepository, initial_cash: float = 1000.0) -> None:
        self._repository = repository
        self._initial_cash = initial_cash

    def run(
        self,
        symbol: str,
        timeframe: str,
        start: datetime,
        end: datetime,
    ) -> BacktestResult:
        candles = self._load_candles(symbol, timeframe, start, end)
        if not candles:
            raise ValueError("No candles available for backtest window.")

        entry_price = candles[0].open
        exit_price = candles[-1].close
        units = self._initial_cash / entry_price
        final_cash = units * exit_price
        pnl = final_cash - self._initial_cash
        return_pct = pnl / self._initial_cash if self._initial_cash else 0.0

        return BacktestResult(
            symbol=symbol,
            timeframe=timeframe,
            start=start,
            end=end,
            initial_cash=self._initial_cash,
            final_cash=final_cash,
            pnl=pnl,
            return_pct=return_pct,
            trades=1,
        )

    def _load_candles(
        self, symbol: str, timeframe: str, start: datetime, end: datetime
    ) -> Sequence[Candle]:
        return self._repository.load(symbol, timeframe, start=start, end=end)
