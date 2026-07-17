"""
Day 8 deliverable: 8 unit tests for profitability ratios.
Run with: python -m pytest tests/kpi/test_ratios.py -v
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src", "analytics"))

from ratios import (
    net_profit_margin,
    operating_profit_margin,
    return_on_equity,
    return_on_capital_employed,
    return_on_assets,
    debt_to_equity,
    interest_coverage_ratio,
    net_debt,
    asset_turnover,
)

def test_01_net_profit_margin_normal_case():
    assert net_profit_margin(100, 1000) == 10.0


def test_02_net_profit_margin_zero_sales_returns_none():
    assert net_profit_margin(100, 0) is None


def test_03_opm_normal_case_no_mismatch():
    result = operating_profit_margin(200, 1000, stated_opm_percentage=20.0)
    assert result["value"] == 20.0
    assert result["mismatch"] is False


def test_04_opm_cross_check_mismatch_flagged():
    result = operating_profit_margin(200, 1000, stated_opm_percentage=15.0)
    assert result["mismatch"] is True


def test_05_roe_normal_case():
    assert return_on_equity(100, 10, 90) == 100.0


def test_06_roe_negative_equity_returns_none():
    assert return_on_equity(100, 10, -50) is None


def test_07_roce_financials_sector_flag():
    result = return_on_capital_employed(150, 10, 90, 50, broad_sector="Financials")
    assert result["is_financials_sector"] is True


def test_08_roa_zero_total_assets_returns_none():
    assert return_on_assets(100, 0) is None
    

def test_09_de_debt_free_returns_zero_not_none():
    result = debt_to_equity(0, 10, 90)
    assert result["value"] == 0
    assert result["high_leverage_flag"] is False


def test_10_de_high_leverage_flag_triggers():
    result = debt_to_equity(600, 10, 90)
    assert result["value"] == 6.0
    assert result["high_leverage_flag"] is True


def test_11_de_high_leverage_flag_suppressed_for_financials():
    result = debt_to_equity(600, 10, 90, broad_sector="Financials")
    assert result["high_leverage_flag"] is False


def test_12_icr_interest_zero_returns_none_with_debt_free_label():
    result = interest_coverage_ratio(100, 20, 0)
    assert result["value"] is None
    assert result["icr_label"] == "Debt Free"


def test_13_icr_normal_case_no_warning():
    result = interest_coverage_ratio(100, 20, 40)
    assert result["value"] == 3.0
    assert result["icr_warning"] is False


def test_14_icr_low_coverage_triggers_warning():
    result = interest_coverage_ratio(10, 5, 40)
    assert result["icr_warning"] is True


def test_15_net_debt_can_be_negative_when_cash_rich():
    assert net_debt(200, 500) == -300


def test_16_asset_turnover_zero_assets_returns_none():
    assert asset_turnover(1000, 0) is None