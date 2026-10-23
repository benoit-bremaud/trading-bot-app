"""Behaviour tests for the pocket lifecycle (diagram 05a) and tranche stops (R16)."""

from decimal import Decimal
from uuid import UUID, uuid4

import pytest

from trading_bot.domain.orders import Fill
from trading_bot.domain.pocket import Pocket, PocketError, PocketState, Tranche

ONE_BTC = 100_000_000
T1 = UUID(int=1)
T2 = UUID(int=2)


def fill(sats: int, price: str, fee: str = "0") -> Fill:
    """Build a fill with a given price and fee rate."""
    return Fill(sats, Decimal(price), Decimal(fee), maker=True)


def pocket(btc: int = ONE_BTC, usdc: str = "0") -> Pocket:
    """A 10 % pocket holding ``btc`` sats and ``usdc``."""
    return Pocket(btc_sats=btc, usdc=Decimal(usdc), pocket_target_bps=1000)


class TestTranche:
    """The stop sits 5 % above the exit VWAP."""

    def test_stop_price(self):
        assert Tranche(T1, 1, Decimal("60000")).stop_price == Decimal("63000.00")

    def test_stop_reached_at_and_above_but_not_below(self):
        tranche = Tranche(T1, 1, Decimal("100"))
        assert tranche.is_stop_reached(Decimal("105"))
        assert tranche.is_stop_reached(Decimal("110"))
        assert not tranche.is_stop_reached(Decimal("104.99"))


class TestExitAndBuyback:
    """Partial and full exits, then buy-backs, move sats and USDC exactly."""

    def test_partial_exit(self):
        out = pocket().record_exit(T1, fill(ONE_BTC // 2, "60000", "0.0008"))
        assert out.state is PocketState.PARTIALLY_OUT
        assert out.btc_sats == ONE_BTC // 2
        assert out.usdc == Decimal("30000") - Decimal("24")
        assert out.open_tranches() == (Tranche(T1, ONE_BTC // 2, Decimal("60000")),)

    def test_full_exit(self):
        assert pocket().record_exit(T1, fill(ONE_BTC, "60000")).state is PocketState.FULLY_OUT

    def test_cannot_sell_more_than_held(self):
        with pytest.raises(PocketError):
            pocket(btc=10).record_exit(T1, fill(11, "60000"))

    def test_full_buyback_returns_to_btc(self):
        out = pocket().record_exit(T1, fill(ONE_BTC, "60000"))
        back = out.record_buyback(T1, fill(ONE_BTC, "60000"))
        assert back.state is PocketState.IN_BTC
        assert back.btc_sats == ONE_BTC
        assert back.usdc == Decimal(0)
        assert back.open_tranches() == ()

    def test_sats_gain_when_buying_back_cheaper(self):
        out = pocket().record_exit(T1, fill(ONE_BTC, "60000"))
        back = out.record_buyback(T1, fill(120_000_000, "50000"))
        assert back.btc_sats == 120_000_000  # more sats than before the exit
        assert back.state is PocketState.IN_BTC
        assert back.open_tranches() == ()

    def test_partial_buyback_keeps_remaining_tranche(self):
        out = pocket().record_exit(T1, fill(ONE_BTC, "60000"))
        back = out.record_buyback(T1, fill(ONE_BTC // 4, "60000"))
        assert back.state is PocketState.PARTIALLY_OUT
        assert back.open_tranches() == (Tranche(T1, 3 * ONE_BTC // 4, Decimal("60000")),)

    def test_two_tranches_tracked_independently(self):
        out = pocket().record_exit(T1, fill(ONE_BTC // 2, "60000"))
        out = out.record_exit(T2, fill(ONE_BTC // 2, "70000"))
        assert out.state is PocketState.FULLY_OUT
        back = out.record_buyback(T1, fill(ONE_BTC // 2, "60000"))
        assert back.state is PocketState.PARTIALLY_OUT
        assert [t.id for t in back.open_tranches()] == [T2]

    def test_buyback_errors(self):
        out = pocket().record_exit(T1, fill(ONE_BTC // 2, "60000"))
        with pytest.raises(PocketError):
            out.record_buyback(uuid4(), fill(1, "60000"))
        with pytest.raises(PocketError):
            pocket(usdc="0").record_exit(T1, fill(1, "1")).record_buyback(T1, fill(1, "99999999"))


class TestPauseAndHalt:
    """Pause blocks exits only; halt is operator-only (diagram 05a)."""

    def test_pause_blocks_exit(self):
        with pytest.raises(PocketError):
            pocket().pause().record_exit(T1, fill(1, "60000"))

    def test_pause_allows_buyback_and_stays_paused(self):
        out = pocket().record_exit(T1, fill(ONE_BTC, "60000")).pause()
        back = out.record_buyback(T1, fill(ONE_BTC, "60000"))
        assert back.state is PocketState.PAUSED
        assert back.resume().state is PocketState.IN_BTC

    def test_resume_with_open_tranche_follows_holdings(self):
        out = pocket().record_exit(T1, fill(ONE_BTC // 2, "60000")).pause().resume()
        assert out.state is PocketState.PARTIALLY_OUT

    def test_only_paused_can_resume(self):
        with pytest.raises(PocketError):
            pocket().resume()

    def test_halt_from_btc_and_from_pause(self):
        assert pocket().halt().state is PocketState.HALTED
        assert pocket().pause().halt().state is PocketState.HALTED

    def test_halt_refused_while_out_of_btc(self):
        out = pocket().record_exit(T1, fill(ONE_BTC, "60000"))
        with pytest.raises(PocketError):
            out.halt()

    def test_halted_is_terminal(self):
        halted = pocket().halt()
        for action in (halted.pause, lambda: halted.record_exit(T1, fill(1, "1"))):
            with pytest.raises(PocketError):
                action()
        with pytest.raises(PocketError):
            halted.record_buyback(T1, fill(1, "1"))

    def test_pocket_validation(self):
        with pytest.raises(ValueError):
            Pocket(btc_sats=-1, usdc=Decimal(0), pocket_target_bps=1000)
        with pytest.raises(ValueError):
            Pocket(btc_sats=0, usdc=Decimal(0), pocket_target_bps=0)
