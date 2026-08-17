import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent.parent / "src"))
from analytics import cagr as C
from analytics import cashflow_kpis as CF


def test_cagr_normal():
    val, flag = C.cagr(100, 161.05, 5)
    assert flag is None and round(val, 1) == 10.0

def test_cagr_turnaround():
    val, flag = C.cagr(-100, 200, 3)
    assert val is None and flag == "TURNAROUND"

def test_cagr_decline_to_loss():
    val, flag = C.cagr(100, -50, 3)
    assert val is None and flag == "DECLINE_TO_LOSS"

def test_cagr_both_negative():
    val, flag = C.cagr(-100, -50, 3)
    assert val is None and flag == "BOTH_NEGATIVE"

def test_cagr_zero_base():
    val, flag = C.cagr(0, 100, 3)
    assert val is None and flag == "ZERO_BASE"

def test_cagr_insufficient_data():
    val, flag = C.cagr(100, 150, 5, n_available_years=3)
    assert val is None and flag == "INSUFFICIENT"

def test_cagr_ten_year_window():
    val, flag = C.cagr(100, 259.4, 10)
    assert flag is None and round(val, 1) == 10.0

def test_cfo_quality_high():
    avg, label = CF.cfo_quality_score([1.2, 1.1, 1.3])
    assert label == "High Quality"

def test_cfo_quality_moderate():
    avg, label = CF.cfo_quality_score([0.6, 0.7])
    assert label == "Moderate"

def test_cfo_quality_accrual_risk():
    avg, label = CF.cfo_quality_score([0.2, 0.3])
    assert label == "Accrual Risk"

def test_capex_intensity_asset_light():
    pct, label = CF.capex_intensity(-20, 1000)
    assert label == "Asset Light"

def test_capex_intensity_capital_intensive():
    pct, label = CF.capex_intensity(-150, 1000)
    assert label == "Capital Intensive"

def test_capital_allocation_reinvestor():
    _, _, _, label = CF.capital_allocation_pattern(100, -50, -30, cfo_pat_ratio_val=0.9)
    assert label == "Reinvestor"

def test_capital_allocation_shareholder_returns():
    _, _, _, label = CF.capital_allocation_pattern(100, -50, -30, cfo_pat_ratio_val=1.5)
    assert label == "Shareholder Returns"

def test_capital_allocation_distress():
    _, _, _, label = CF.capital_allocation_pattern(-100, 20, 60)
    assert label == "Distress Signal"

def test_distress_signal_flag():
    assert CF.distress_signal(-50, 30) is True

def test_deleveraging_flag_true():
    assert CF.deleveraging_flag(-40, 100, 150) is True

def test_deleveraging_flag_false_rising_debt():
    assert CF.deleveraging_flag(-40, 200, 150) is False

def test_free_cash_flow_negative_allowed():
    assert CF.free_cash_flow(50, -80) == -30

def test_fcf_conversion_zero_opprofit_none():
    assert CF.fcf_conversion_rate(50, 0) is None
