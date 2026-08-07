import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src", "analytics"))
from cashflow_kpis import (free_cash_flow, cfo_quality_score, capex_intensity,
                            fcf_conversion_rate, capital_allocation_pattern,
                            distress_signal, deleveraging_flag)


def test_fcf_negative_allowed():
    assert free_cash_flow(100, -150) == -50


def test_cfo_quality_high():
    avg, label = cfo_quality_score([1.2, 1.1, 1.3])
    assert label == "High Quality"


def test_cfo_quality_moderate():
    avg, label = cfo_quality_score([0.6, 0.7])
    assert label == "Moderate"


def test_cfo_quality_accrual_risk():
    avg, label = cfo_quality_score([0.2, 0.3])
    assert label == "Accrual Risk"


def test_capex_intensity_asset_light():
    pct, label = capex_intensity(-20, 1000)
    assert label == "Asset Light"


def test_capex_intensity_capital_intensive():
    pct, label = capex_intensity(-150, 1000)
    assert label == "Capital Intensive"


def test_fcf_conversion_zero_opm_is_none():
    assert fcf_conversion_rate(100, 0) is None


def test_pattern_reinvestor():
    label, *_ = capital_allocation_pattern(100, -40, -30, cfo_pat_ratio=0.6)
    assert label == "Reinvestor"


def test_pattern_shareholder_returns():
    label, *_ = capital_allocation_pattern(100, -40, -30, cfo_pat_ratio=1.5)
    assert label == "Shareholder Returns"


def test_pattern_distress_signal():
    label, *_ = capital_allocation_pattern(-50, 20, 40)
    assert label == "Distress Signal"


def test_pattern_growth_funded_by_debt():
    label, *_ = capital_allocation_pattern(-10, -20, 50)
    assert label == "Growth Funded by Debt"


def test_pattern_cash_accumulator():
    label, *_ = capital_allocation_pattern(50, 10, 5)
    assert label == "Cash Accumulator"


def test_distress_signal_true():
    assert distress_signal(-10, 20) is True


def test_distress_signal_false():
    assert distress_signal(10, 20) is False


def test_deleveraging_true():
    assert deleveraging_flag(-10, 400, 500) is True
