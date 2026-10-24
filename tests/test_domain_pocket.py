"""Behaviour tests for the pocket lifecycle (diagram 05a) and tranche stops (R16)."""

from decimal import Decimal
from uuid import UUID

import pytest

from trading_bot.domain.orders import Fill
from trading_bot.domain.pocket import Pocket, PocketError, PocketState, Tranche

D = Decimal
ONE_BTC = 100_000_000
T1 = UUID(int=1)
T2 = UUID(int=2)


def fill(sats: int, price: str, fee: str = "0") -> Fill:
    """Build a maker fill at ``price`` with fee rate ``fee``."""
    return Fill(sats, D(price), D(fee), maker=True)


def pocket(btc: int = ONE_BTC, usdc: str = "0") -> Pocket:
    """A 10 % pocket holding ``btc`` sats and ``usdc``."""
    return Pocket(btc_sats=btc, usdc=D(usdc), pocket_target_bps=1000)


def sold(btc_part: int = ONE_BTC, price: str = "60000", fee: str = "0") -> Pocket:
    """A pocket that sold ``btc_part`` sats in tranche T1."""
    return pocket().record_exit(T1, [fill(btc_part, price, fee)])


class TestTranche:
    """The stop sits 5 % above the exit VWAP."""

    def test_stop_price(self):
        assert Tranche(T1, 1, D("60000")).stop_price == D("63000")

    def test_stop_reached_at_and_above_but_not_below(self):
        tranche = Tranche(T1, 1, D("100"))
        assert tranche.is_stop_reached(D("105"))
        assert tranche.is_stop_reached(D("110"))
        assert not tranche.is_stop_reached(D("104.99"))

    @pytest.mark.parametrize(("sats", "vwap"), [(0, "1"), (-1, "1"), (1, "0"), (1, "NaN")])
    def test_invalid_tranche_is_refused(self, sats, vwap):
        price = D(vwap)
        with pytest.raises(ValueError):
            Tranche(T1, sats, price)


class TestExit:
    """Exits move BTC to USDC net of fees and open one tranche per order."""

    def test_partial_exit_with_fee(self):
        out = sold(ONE_BTC // 2, fee="0.0008")
        assert out.state is PocketState.PARTIALLY_OUT
        assert out.btc_sats == ONE_BTC // 2
        assert out.usdc == D("30000") - D("24")
        assert out.open_tranches() == (Tranche(T1, ONE_BTC // 2, D("60000")),)

    def test_full_exit(self):
        assert sold().state is PocketState.FULLY_OUT

    def test_several_fills_of_one_order_make_one_tranche_at_their_vwap(self):
        out = pocket().record_exit(T1, [fill(ONE_BTC // 2, "60000"), fill(ONE_BTC // 2, "62000")])
        assert out.open_tranches() == (Tranche(T1, ONE_BTC, D("61000")),)
        assert out.usdc == D("61000")

    def test_vwap_is_weighted_by_size(self):
        out = pocket().record_exit(
            T1, [fill(ONE_BTC // 4, "60000"), fill(3 * ONE_BTC // 4, "80000")]
        )
        assert out.open_tranches()[0].exit_vwap == D("75000")

    def test_cannot_sell_more_than_held(self):
        arg1 = [fill(11, "60000")]
        target2 = pocket(btc=10)
        with pytest.raises(PocketError, match="more sats"):
            target2.record_exit(T1, arg1)

    def test_exit_needs_a_fill(self):
        target = pocket()
        with pytest.raises(PocketError, match="at least one"):
            target.record_exit(T1, [])

    def test_tranche_id_cannot_be_reused(self):
        out = sold(ONE_BTC // 2)
        arg = [fill(1, "60000")]
        with pytest.raises(PocketError, match="already exists"):
            out.record_exit(T1, arg)


class TestBuyback:
    """Buy-backs close tranches; buying more sats than sold is the gain."""

    def test_full_buyback_at_same_price_returns_to_btc(self):
        back = sold().record_buyback(T1, fill(ONE_BTC, "60000"))
        assert back.state is PocketState.IN_BTC
        assert (back.btc_sats, back.usdc, back.open_tranches()) == (ONE_BTC, 0, ())

    def test_cheaper_buyback_gains_sats(self):
        back = sold().record_buyback(T1, fill(120_000_000, "50000"))
        assert back.btc_sats == 120_000_000
        assert back.usdc == 0
        assert back.state is PocketState.IN_BTC

    def test_fees_on_both_legs_are_charged_exactly(self):
        out = sold(fee="0.0008")  # +60000 - 48
        back = out.record_buyback(T1, fill(ONE_BTC, "59000", "0.001"))
        # buy costs 59000 + 59 = 59059
        assert back.usdc == D("60000") - D("48") - D("59059")

    def test_partial_buyback_keeps_remaining_tranche(self):
        back = sold().record_buyback(T1, fill(ONE_BTC // 4, "60000"))
        assert back.state is PocketState.PARTIALLY_OUT
        assert back.open_tranches() == (Tranche(T1, 3 * ONE_BTC // 4, D("60000")),)

    def test_two_tranches_tracked_independently(self):
        out = pocket().record_exit(T1, [fill(ONE_BTC // 2, "60000")])
        out = out.record_exit(T2, [fill(ONE_BTC // 2, "70000")])
        assert out.state is PocketState.FULLY_OUT
        back = out.record_buyback(T1, fill(ONE_BTC // 2, "60000"))
        assert back.state is PocketState.PARTIALLY_OUT
        assert [t.id for t in back.open_tranches()] == [T2]

    def test_overshooting_one_tranche_leaves_the_other_untouched(self):
        out = pocket().record_exit(T1, [fill(ONE_BTC // 2, "60000")])
        out = out.record_exit(T2, [fill(ONE_BTC // 2, "60000")])
        back = out.record_buyback(T1, fill(ONE_BTC // 2 + 10, "60000"))
        assert back.open_tranches() == (Tranche(T2, ONE_BTC // 2, D("60000")),)

    def test_unknown_tranche_is_refused(self):
        arg1 = fill(1, "60000")
        target2 = sold(ONE_BTC // 2)
        with pytest.raises(PocketError, match="unknown tranche"):
            target2.record_buyback(T2, arg1)

    def test_funds_boundary(self):
        out = sold(ONE_BTC // 2, price="60000")  # holds 30000 USDC
        exact = out.record_buyback(T1, fill(ONE_BTC // 2, "60000"))
        assert exact.usdc == 0
        arg = fill(ONE_BTC // 2 + 1, "60000")
        with pytest.raises(PocketError, match="USDC"):
            out.record_buyback(T1, arg)


class TestPauseAndHalt:
    """Pause blocks exits only; halt is operator-only (diagram 05a)."""

    def test_pause_blocks_exit(self):
        arg1 = [fill(1, "60000")]
        target2 = pocket().pause()
        with pytest.raises(PocketError, match="blocked"):
            target2.record_exit(T1, arg1)

    def test_pause_allows_buyback_and_stays_paused(self):
        back = sold().pause().record_buyback(T1, fill(ONE_BTC, "60000"))
        assert back.state is PocketState.PAUSED
        assert back.resume().state is PocketState.IN_BTC

    def test_paused_buyback_with_open_tranche_keeps_the_stop_armed(self):
        back = sold().pause().record_buyback(T1, fill(ONE_BTC // 2, "60000"))
        assert back.state is PocketState.PAUSED
        assert back.open_tranches() == (Tranche(T1, ONE_BTC // 2, D("60000")),)
        assert back.resume().state is PocketState.PARTIALLY_OUT

    @pytest.mark.parametrize(
        ("part", "expected"),
        [(ONE_BTC // 2, PocketState.PARTIALLY_OUT), (ONE_BTC, PocketState.FULLY_OUT)],
    )
    def test_resume_follows_the_holdings(self, part, expected):
        assert sold(part).pause().resume().state is expected

    def test_only_paused_can_resume(self):
        target = pocket()
        with pytest.raises(PocketError, match="only a paused"):
            target.resume()

    def test_halt_from_btc_and_from_pause(self):
        assert pocket().halt().state is PocketState.HALTED
        assert pocket().pause().halt().state is PocketState.HALTED

    @pytest.mark.parametrize("pause_first", [False, True])
    def test_halt_refused_while_a_tranche_is_open(self, pause_first):
        out = sold(ONE_BTC // 2)
        if pause_first:
            out = out.pause()
        with pytest.raises(PocketError, match="back in BTC"):
            out.halt()

    @pytest.mark.parametrize("action", ["pause", "resume", "halt", "exit", "buyback"])
    def test_halted_is_terminal(self, action):
        halted = pocket().halt()
        actions = {
            "pause": halted.pause,
            "resume": halted.resume,
            "halt": halted.halt,
            "exit": lambda: halted.record_exit(T1, [fill(1, "1")]),
            "buyback": lambda: halted.record_buyback(T1, fill(1, "1")),
        }
        with pytest.raises(PocketError):
            actions[action]()
        assert halted.state is PocketState.HALTED


class TestConstruction:
    """Invalid pockets cannot be built."""

    @pytest.mark.parametrize(
        ("btc", "usdc", "bps"),
        [(-1, "0", 1000), (0, "-1", 1000), (0, "0", 0), (0, "0", 10_001)],
    )
    def test_out_of_range_values_are_refused(self, btc, usdc, bps):
        arg = D(usdc)
        with pytest.raises(ValueError):
            Pocket(btc_sats=btc, usdc=arg, pocket_target_bps=bps)

    def test_full_target_is_allowed(self):
        assert Pocket(0, D(0), 10_000).pocket_target_bps == 10_000

    def test_float_usdc_is_refused(self):
        with pytest.raises(TypeError, match="Decimal"):
            Pocket(btc_sats=1, usdc=5.0, pocket_target_bps=1000)

    @pytest.mark.parametrize("bad", [True, 1.5])
    def test_btc_must_be_int(self, bad):
        arg = D(0)
        with pytest.raises(TypeError, match="int"):
            Pocket(btc_sats=bad, usdc=arg, pocket_target_bps=1000)

    def test_infinite_usdc_is_refused(self):
        arg = D("Infinity")
        with pytest.raises(ValueError, match="finite"):
            Pocket(btc_sats=1, usdc=arg, pocket_target_bps=1000)

    def test_state_must_match_the_holdings(self):
        arg = D(0)
        with pytest.raises(ValueError, match="contradicts"):
            Pocket(btc_sats=1, usdc=arg, pocket_target_bps=1000, state=PocketState.FULLY_OUT)
