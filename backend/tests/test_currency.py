"""Tests for the currency conversion engine."""

import pytest
from app.core.currency import (
    coins_to_cp,
    cp_to_breakdown,
    cp_to_single_currency,
    split_amount,
    CurrencyBreakdown,
)


class TestCoinsToCP:
    """Test converting coin denominations to copper."""

    def test_single_gold(self):
        assert coins_to_cp(gp=1) == 100

    def test_single_platinum(self):
        assert coins_to_cp(pp=1) == 1000

    def test_single_electrum(self):
        assert coins_to_cp(ep=1) == 50

    def test_single_silver(self):
        assert coins_to_cp(sp=1) == 10

    def test_single_copper(self):
        assert coins_to_cp(cp=1) == 1

    def test_mixed_coins(self):
        # 1 GP + 5 SP + 2 CP = 100 + 50 + 2 = 152 CP
        assert coins_to_cp(gp=1, sp=5, cp=2) == 152

    def test_all_denominations(self):
        # 1 PP + 2 GP + 1 EP + 3 SP + 7 CP = 1000 + 200 + 50 + 30 + 7 = 1287 CP
        assert coins_to_cp(pp=1, gp=2, ep=1, sp=3, cp=7) == 1287

    def test_zero_coins(self):
        assert coins_to_cp() == 0

    def test_large_amounts(self):
        assert coins_to_cp(pp=100) == 100000

    def test_negative_raises(self):
        with pytest.raises(ValueError, match="negative"):
            coins_to_cp(gp=-1)

    def test_unknown_coin_raises(self):
        with pytest.raises(ValueError, match="Unknown coin type"):
            coins_to_cp(xx=5)


class TestCPToBreakdown:
    """Test converting copper to coin breakdown."""

    def test_exact_gold(self):
        result = cp_to_breakdown(100, use_gold=True)
        assert result.gp == 1
        assert result.sp == 0
        assert result.cp == 0

    def test_gold_silver_copper(self):
        result = cp_to_breakdown(152, use_gold=True)
        assert result.gp == 1
        assert result.sp == 5
        assert result.cp == 2

    def test_without_gold(self):
        result = cp_to_breakdown(152, use_gold=False)
        assert result.gp == 0
        assert result.sp == 15
        assert result.cp == 2

    def test_with_platinum(self):
        result = cp_to_breakdown(1152, use_gold=True, use_platinum=True)
        assert result.pp == 1
        assert result.gp == 1
        assert result.sp == 5
        assert result.cp == 2

    def test_with_electrum(self):
        result = cp_to_breakdown(152, use_gold=True, use_electrum=True)
        assert result.gp == 1
        assert result.ep == 1
        assert result.sp == 0
        assert result.cp == 2

    def test_zero_cp(self):
        result = cp_to_breakdown(0)
        assert result.gp == 0
        assert result.sp == 0
        assert result.cp == 0

    def test_only_copper(self):
        result = cp_to_breakdown(7, use_gold=True)
        assert result.gp == 0
        assert result.sp == 0
        assert result.cp == 7

    def test_all_coins_enabled(self):
        result = cp_to_breakdown(1287, use_platinum=True, use_gold=True, use_electrum=True)
        # 1287 / 1000 = 1 PP remainder 287
        # 287 / 100 = 2 GP remainder 87
        # 87 / 50 = 1 EP remainder 37
        # 37 / 10 = 3 SP remainder 7
        # 7 CP
        assert result.pp == 1
        assert result.gp == 2
        assert result.ep == 1
        assert result.sp == 3
        assert result.cp == 7


class TestCPToSingleCurrency:
    """Test viewing total balance as a single currency."""

    def test_to_gold(self):
        assert cp_to_single_currency(152, "gp") == 1.52

    def test_to_copper(self):
        assert cp_to_single_currency(152, "cp") == 152.0

    def test_to_platinum(self):
        assert cp_to_single_currency(500, "pp") == 0.5

    def test_to_silver(self):
        assert cp_to_single_currency(35, "sp") == 3.5

    def test_to_electrum(self):
        assert cp_to_single_currency(100, "ep") == 2.0

    def test_unknown_raises(self):
        with pytest.raises(ValueError):
            cp_to_single_currency(100, "xx")


class TestSplitAmount:
    """Test splitting currency among participants."""

    def test_even_split(self):
        shares = split_amount(100, 2)
        assert sum(shares) == 100
        assert shares == [50, 50]

    def test_even_split_three(self):
        shares = split_amount(300, 3)
        assert sum(shares) == 300
        assert shares == [100, 100, 100]

    def test_uneven_split_remainder(self):
        shares = split_amount(100, 3)
        assert sum(shares) == 100
        assert len(shares) == 3
        # One person pays 34, two pay 33 (or any valid distribution)
        assert sorted(shares) == [33, 33, 34]

    def test_single_participant(self):
        shares = split_amount(100, 1)
        assert shares == [100]

    def test_single_copper_among_many(self):
        shares = split_amount(1, 5)
        assert sum(shares) == 1
        assert shares.count(1) == 1
        assert shares.count(0) == 4

    def test_zero_amount(self):
        shares = split_amount(0, 3)
        assert shares == [0, 0, 0]

    def test_negative_participants_raises(self):
        with pytest.raises(ValueError, match="positive"):
            split_amount(100, 0)

    def test_negative_amount_raises(self):
        with pytest.raises(ValueError, match="negative"):
            split_amount(-10, 2)

    def test_total_preserved_large_split(self):
        """Ensure total is always preserved even with large uneven splits."""
        for total in [1, 7, 13, 99, 1000, 9999]:
            for n in [2, 3, 5, 7, 11]:
                shares = split_amount(total, n)
                assert sum(shares) == total, f"Failed for {total}/{n}"
                assert len(shares) == n


class TestCurrencyBreakdown:
    """Test the CurrencyBreakdown dataclass methods."""

    def test_to_dict(self):
        b = CurrencyBreakdown(pp=1, gp=2, ep=0, sp=3, cp=7)
        assert b.to_dict() == {"pp": 1, "gp": 2, "ep": 0, "sp": 3, "cp": 7}

    def test_display_dict_filters_zeros(self):
        b = CurrencyBreakdown(pp=0, gp=1, ep=0, sp=5, cp=2)
        result = b.to_display_dict(use_gold=True)
        assert result == {"gp": 1, "sp": 5, "cp": 2}

    def test_display_dict_respects_enabled_coins(self):
        b = CurrencyBreakdown(pp=1, gp=2, ep=1, sp=3, cp=7)
        # Only gold enabled (not platinum or electrum)
        result = b.to_display_dict(use_platinum=False, use_gold=True, use_electrum=False)
        assert "pp" not in result
        assert "ep" not in result
        assert result["gp"] == 2

    def test_display_dict_empty_shows_copper(self):
        b = CurrencyBreakdown(pp=0, gp=0, ep=0, sp=0, cp=0)
        result = b.to_display_dict()
        assert result == {"cp": 0}
