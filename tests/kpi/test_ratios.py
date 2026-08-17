import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent.parent / "src"))
from analytics import ratios as R
from analytics import cagr as C
from analytics import cashflow_kpis as CF


def test_npm_normal():
    assert R.net_profit_margin(100, 1000) == 10.0

def test_npm_zero_sales():
    assert R.net_profit_margin(100, 0) is None

def test_npm_negative_profit_allowed():
    assert R.net_profit_margin(-50, 1000) == -5.0

def test_opm_crosscheck_placeholder():
    # OPM computed directly; cross-check logic lives in populate_ratios batch driver
    assert R.operating_profit_margin(200, 1000) == 20.0

def test_roe_positive():
    assert R.return_on_equity(100, 400, 100) == 20.0

def test_roe_negative_equity_none():
    assert R.return_on_equity(100, -600, 100) is None

def test_roe_zero_equity_none():
    assert R.return_on_equity(100, 0, 0) is None

def test_roce_normal():
    val = R.return_on_capital_employed(300, 400, 100, 200)
    assert round(val, 2) == round(300 / 700 * 100, 2)

def test_roa_zero_assets_none():
    assert R.return_on_assets(100, 0) is None

def test_roa_normal():
    assert R.return_on_assets(100, 2000) == 5.0

def test_de_debtfree_returns_zero():
    assert R.debt_to_equity(0, 500, 100) == 0.0

def test_de_normal():
    assert R.debt_to_equity(300, 400, 100) == 0.6

def test_de_negative_equity_none():
    assert R.debt_to_equity(300, -600, 100) is None

def test_high_leverage_flag_nonfinancial():
    assert R.high_leverage_flag(6, is_financial_sector=False) is True

def test_high_leverage_flag_financial_suppressed():
    assert R.high_leverage_flag(6, is_financial_sector=True) is False

def test_icr_interest_zero_none():
    assert R.interest_coverage(500, 50, 0) is None

def test_icr_label_debt_free():
    icr = R.interest_coverage(500, 50, 0)
    assert R.icr_label(icr) == "Debt Free"

def test_icr_normal():
    assert R.interest_coverage(500, 50, 100) == 5.5

def test_icr_warning_flag_low():
    assert R.icr_warning_flag(1.2) is True

def test_icr_warning_flag_healthy():
    assert R.icr_warning_flag(5.0) is False

def test_asset_turnover_zero_assets_none():
    assert R.asset_turnover(1000, 0) is None
