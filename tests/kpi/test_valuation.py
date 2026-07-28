"""
Day 26 deliverable: unit tests for the valuation module.
Run with: python -m pytest tests/kpi/test_valuation.py -v
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src", "analytics"))

from valuation import compute_fcf_yield, classify_valuation_flag


def test_01_fcf_yield_normal_case():
    assert compute_fcf_yield(500, 10000) == 5.0


def test_02_fcf_yield_zero_market_cap_returns_none():
    assert compute_fcf_yield(500, 0) is None


def test_03_fcf_yield_none_market_cap_returns_none():
    assert compute_fcf_yield(500, None) is None


def test_04_fcf_yield_negative_fcf_allowed():
    assert compute_fcf_yield(-500, 10000) == -5.0


def test_05_flag_caution_when_pe_exceeds_threshold():
    # sector median 20, threshold = 30 (20*1.5), pe=35 > 30 -> Caution
    assert classify_valuation_flag(35, 20) == "Caution"


def test_06_flag_discount_when_pe_below_threshold():
    # sector median 20, threshold = 14 (20*0.7), pe=10 < 14 -> Discount
    assert classify_valuation_flag(10, 20) == "Discount"


def test_07_flag_fair_in_between():
    assert classify_valuation_flag(20, 20) == "Fair"


def test_08_flag_none_when_pe_missing():
    assert classify_valuation_flag(None, 20) is None


def test_09_flag_none_when_sector_median_missing():
    assert classify_valuation_flag(20, None) is None


def test_10_flag_boundary_exactly_at_caution_threshold_is_fair():
    # exactly 1.5x is NOT > threshold, so should be Fair, not Caution
    assert classify_valuation_flag(30, 20) == "Fair"


def test_11_flag_boundary_exactly_at_discount_threshold_is_fair():
    # exactly 0.7x is NOT < threshold, so should be Fair, not Discount
    assert classify_valuation_flag(14, 20) == "Fair"