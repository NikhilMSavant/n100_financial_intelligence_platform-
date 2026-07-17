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
    