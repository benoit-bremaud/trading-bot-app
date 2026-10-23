"""Behaviour tests for sats conversion, fee schedule and hard limits."""

from decimal import Decimal

import pytest

from trading_bot.domain.fees import FEE_CAP, FeeCapExceededError, FeeSchedule
from trading_bot.domain.limits import HardLimits
from trading_bot.domain.sats import btc_to_sats, sats_to_btc


class TestSats:
    """BTC and sats conversions are exact and refuse float."""

    def test_round_trip(self):
        assert btc_to_sats(Decimal("0.00123456")) == 123_456
        assert sats_to_btc(123_456) == Decimal("0.00123456")

    def test_refuses_float(self):
        with pytest.raises(TypeError):
            btc_to_sats(0.1)

    def test_refuses_fraction_of_a_sat(self):
        with pytest.raises(ValueError):
            btc_to_sats(Decimal("0.000000001"))

    def test_sats_must_be_int(self):
        with pytest.raises(TypeError):
            sats_to_btc(1.5)
        with pytest.raises(TypeError):
            sats_to_btc(True)


class TestFeeSchedule:
    """The fee cap of R17 is enforced at start-up."""

    def test_owner_tier_is_accepted(self):
        FeeSchedule(Decimal("0.0008"), Decimal("0.0010")).assert_below_cap()

    def test_spot_only_tier_is_refused(self):
        with pytest.raises(FeeCapExceededError):
            FeeSchedule(Decimal("0.0010"), Decimal("0.0020")).assert_below_cap()

    def test_custom_cap(self):
        schedule = FeeSchedule(Decimal("0.0005"), Decimal("0.0005"))
        with pytest.raises(FeeCapExceededError):
            schedule.assert_below_cap(Decimal("0.0004"))

    def test_cap_is_ten_basis_points(self):
        assert FEE_CAP == Decimal("0.001")

    def test_rate_for(self):
        schedule = FeeSchedule(Decimal("0.0008"), Decimal("0.0010"))
        assert schedule.rate_for(maker=True) == Decimal("0.0008")
        assert schedule.rate_for(maker=False) == Decimal("0.0010")

    def test_rejects_float_and_out_of_range(self):
        with pytest.raises(TypeError):
            FeeSchedule(0.0008, Decimal("0.001"))
        with pytest.raises(ValueError):
            FeeSchedule(Decimal("-0.1"), Decimal("0.001"))


class TestHardLimits:
    """R06: orders per day and order size are bounded."""

    limits = HardLimits(max_orders_per_day=3, max_order_sats=1_000_000)

    def test_allows_within_limits(self):
        assert self.limits.check(order_count=2, sats=1_000_000)

    def test_refuses_too_many_orders(self):
        assert not self.limits.check(order_count=3, sats=1)

    def test_refuses_too_large_order(self):
        assert not self.limits.check(order_count=0, sats=1_000_001)

    @pytest.mark.parametrize("bad", [0, -1, True, 1.5])
    def test_limits_must_be_positive_ints(self, bad):
        with pytest.raises(ValueError):
            HardLimits(max_orders_per_day=bad, max_order_sats=1)
        with pytest.raises(ValueError):
            HardLimits(max_orders_per_day=1, max_order_sats=bad)
