"""Behaviour tests for sats conversion, fee schedule and hard limits."""

from decimal import Decimal

import pytest

from trading_bot.domain.fees import FEE_CAP, FeeCapExceededError, FeeSchedule
from trading_bot.domain.limits import HardLimits
from trading_bot.domain.sats import btc_to_sats, sats_to_btc

D = Decimal


class TestSats:
    """BTC and sats conversions are exact and refuse float and non-finite values."""

    @pytest.mark.parametrize("sats", [0, 1, 123_456, 2_100_000_000_000_000])
    def test_round_trip(self, sats):
        assert btc_to_sats(sats_to_btc(sats)) == sats

    def test_smallest_unit_and_exponent_notation(self):
        assert btc_to_sats(D("0.00000001")) == 1
        assert btc_to_sats(D("1E-8")) == 1
        assert sats_to_btc(123_456) == D("0.00123456")

    def test_refuses_float(self):
        with pytest.raises(TypeError, match="Decimal"):
            btc_to_sats(0.1)

    def test_refuses_fraction_of_a_sat(self):
        arg = D("0.000000001")
        with pytest.raises(ValueError, match="whole number"):
            btc_to_sats(arg)

    @pytest.mark.parametrize("bad", ["NaN", "sNaN", "Infinity", "-Infinity"])
    def test_refuses_non_finite(self, bad):
        value = D(bad)
        with pytest.raises(ValueError, match="finite"):
            btc_to_sats(value)

    def test_refuses_absurd_exponent(self):
        value = D("1E+999999")
        with pytest.raises(ValueError, match="range"):
            btc_to_sats(value)

    @pytest.mark.parametrize("bad", [1.5, True, "3"])
    def test_sats_must_be_int(self, bad):
        with pytest.raises(TypeError, match="int"):
            sats_to_btc(bad)


class TestFeeSchedule:
    """The fee cap of R17 is enforced at start-up."""

    def test_owner_tier_is_accepted(self):
        FeeSchedule(D("0.0008"), D("0.0010")).assert_below_cap()

    def test_rates_exactly_at_the_cap_are_accepted(self):
        FeeSchedule(FEE_CAP, FEE_CAP).assert_below_cap()

    def test_taker_above_cap_is_refused(self):
        schedule = FeeSchedule(D("0.0008"), D("0.0011"))
        with pytest.raises(FeeCapExceededError):
            schedule.assert_below_cap()

    def test_maker_above_cap_is_refused(self):
        schedule = FeeSchedule(D("0.0011"), D("0.0008"))
        with pytest.raises(FeeCapExceededError):
            schedule.assert_below_cap()

    def test_spot_only_tier_is_refused(self):
        schedule = FeeSchedule(D("0.0010"), D("0.0020"))
        with pytest.raises(FeeCapExceededError, match="0.0020"):
            schedule.assert_below_cap()

    def test_custom_cap(self):
        schedule = FeeSchedule(D("0.0005"), D("0.0005"))
        arg = D("0.0004")
        with pytest.raises(FeeCapExceededError):
            schedule.assert_below_cap(arg)

    def test_nan_cap_fails_closed_with_value_error(self):
        schedule = FeeSchedule(D("0.0005"), D("0.0005"))
        cap = D("NaN")
        with pytest.raises(ValueError, match="finite"):
            schedule.assert_below_cap(cap)

    def test_rate_for(self):
        schedule = FeeSchedule(D("0.0008"), D("0.0010"))
        assert schedule.rate_for(maker=True) == D("0.0008")
        assert schedule.rate_for(maker=False) == D("0.0010")

    def test_zero_rate_is_valid(self):
        assert FeeSchedule(D("0"), D("0")).rate_for(maker=True) == 0

    def test_float_rate_is_refused(self):
        arg = D("0.001")
        with pytest.raises(TypeError, match="Decimal"):
            FeeSchedule(0.0008, arg)

    @pytest.mark.parametrize("bad", ["-0.1", "1", "NaN", "Infinity"])
    def test_out_of_range_rate_is_refused(self, bad):
        rate = D(bad)
        arg = D("0.001")
        with pytest.raises(ValueError):
            FeeSchedule(rate, arg)


class TestHardLimits:
    """R06: orders per day and order size are bounded."""

    limits = HardLimits(max_orders_per_day=3, max_order_sats=1_000_000)

    def test_allows_within_limits_at_the_boundary(self):
        assert self.limits.check(order_count=2, sats=1_000_000)

    def test_refuses_too_many_orders(self):
        assert not self.limits.check(order_count=3, sats=1)

    def test_refuses_too_large_order(self):
        assert not self.limits.check(order_count=0, sats=1_000_001)

    def test_refuses_when_both_limits_are_breached(self):
        assert not self.limits.check(order_count=9, sats=9_000_000)

    @pytest.mark.parametrize(("count", "sats"), [(-1, 10), (0, 0), (0, -5)])
    def test_invalid_arguments_are_a_caller_bug(self, count, sats):
        with pytest.raises(ValueError, match="order_count"):
            self.limits.check(order_count=count, sats=sats)

    def test_bool_argument_is_refused(self):
        with pytest.raises(TypeError):
            self.limits.check(order_count=0, sats=True)

    @pytest.mark.parametrize("bad", [0, -1])
    def test_limits_must_be_positive(self, bad):
        with pytest.raises(ValueError, match="positive"):
            HardLimits(max_orders_per_day=bad, max_order_sats=1)
        with pytest.raises(ValueError, match="positive"):
            HardLimits(max_orders_per_day=1, max_order_sats=bad)

    @pytest.mark.parametrize("bad", [True, 1.5])
    def test_limits_must_be_ints(self, bad):
        with pytest.raises(TypeError):
            HardLimits(max_orders_per_day=bad, max_order_sats=1)
