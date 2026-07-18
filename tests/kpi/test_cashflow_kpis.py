"""
Day 11 deliverable: unit tests for cash flow KPIs and capital allocation.
Run with: python -m pytest tests/kpi/test_cashflow_kpis.py -v
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src", "analytics"))

from cashflow_kpis import (
    free_cash_flow,
    cfo_quality_score,
    capex_intensity,
    fcf_conversion_rate,
    classify_capital_allocation,
)


def test_01_fcf_normal_positive():
    assert free_cash_flow(500, -200) == 300


def test_02_fcf_negative_allowed():
    assert free_cash_flow(500, -800) == -300


def test_03_cfo_quality_high():
    result = cfo_quality_score([120, 130, 110, 140, 125], [100, 100, 100, 100, 100])
    assert result["label"] == "High Quality"


def test_04_cfo_quality_skips_zero_pat_year():
    result = cfo_quality_score([100, 100], [0, 100])
    assert result["value"] == 1.0


def test_05_capex_asset_light():
    result = capex_intensity(-20, 1000)
    assert result["label"] == "Asset Light"


def test_06_capex_capital_intensive():
    result = capex_intensity(-150, 1000)
    assert result["label"] == "Capital Intensive"


def test_07_capex_zero_sales_returns_none():
    result = capex_intensity(-50, 0)
    assert result["value"] is None


def test_08_fcf_conversion_zero_operating_profit_returns_none():
    assert fcf_conversion_rate(80, 0) is None


def test_09_capital_allocation_reinvestor():
    result = classify_capital_allocation(100, -50, -30)
    assert result["pattern_label"] == "Reinvestor"


def test_10_capital_allocation_shareholder_returns_needs_high_quality():
    result = classify_capital_allocation(100, -50, -30, cfo_quality_value=1.5)
    assert result["pattern_label"] == "Shareholder Returns"


def test_11_capital_allocation_distress_signal():
    result = classify_capital_allocation(-100, 50, 30)
    assert result["pattern_label"] == "Distress Signal"


def test_12_capital_allocation_mixed():
    result = classify_capital_allocation(100, -50, 30)
    assert result["pattern_label"] == "Mixed"
    