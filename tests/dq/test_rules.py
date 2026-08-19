import sys, pathlib
import pandas as pd
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent.parent / "src"))
from etl import validator as V


def test_dq01_duplicate_pk():
    df = pd.DataFrame({"id": ["TCS", "TCS", "INFY"]})
    v = V.dq01_company_pk_uniqueness(df)
    assert len(v) == 1 and v[0]["rule_id"] == "DQ-01"

def test_dq02_duplicate_annual_pk():
    df = pd.DataFrame({"company_id": ["TCS", "TCS"], "year": ["2023-03", "2023-03"]})
    v = V.dq02_annual_pk_uniqueness(df, "profitandloss")
    assert len(v) == 2 and v[0]["severity"] == "CRITICAL"

def test_dq03_fk_orphan():
    df = pd.DataFrame({"company_id": ["XXXX"], "year": ["2023-03"]})
    v = V.dq03_fk_integrity(df, {"TCS", "INFY"}, "profitandloss")
    assert len(v) == 1 and v[0]["rule_id"] == "DQ-03"

def test_dq04_bs_balance_violation():
    bs = pd.DataFrame({"company_id": ["TCS"], "year": ["2023-03"],
                        "total_assets": [1000.0], "total_liabilities": [1020.0]})
    v = V.dq04_bs_balance(bs)
    assert len(v) == 1 and v[0]["severity"] == "WARNING"

def test_dq05_opm_crosscheck_mismatch():
    pl = pd.DataFrame({"company_id": ["TCS"], "year": ["2023-03"], "sales": [1000.0],
                        "operating_profit": [200.0], "opm_percentage": [30.0]})
    v = V.dq05_opm_crosscheck(pl)
    assert len(v) == 1

def test_dq06_zero_sales():
    pl = pd.DataFrame({"company_id": ["TCS"], "year": ["2023-03"], "sales": [0]})
    v = V.dq06_positive_sales(pl)
    assert len(v) == 1

def test_dq07_unparseable_year():
    v = V.dq07_year_format(pd.Series(["garbage"]), "profitandloss")
    assert len(v) == 1 and v[0]["severity"] == "CRITICAL"

def test_dq08_ticker_length():
    v = V.dq08_ticker_format(pd.Series(["A"]), "profitandloss")
    assert len(v) == 1

def test_dq09_net_cash_mismatch():
    cf = pd.DataFrame({"company_id": ["TCS"], "year": ["2023-03"], "operating_activity": [100.0],
                        "investing_activity": [-50.0], "financing_activity": [-20.0], "net_cash_flow": [100.0]})
    v = V.dq09_net_cash_check(cf)
    assert len(v) == 1  # |100 - 30| = 70 > 10 tolerance

def test_dq10_negative_fixed_assets():
    bs = pd.DataFrame({"company_id": ["TCS"], "year": ["2023-03"], "fixed_assets": [-5.0]})
    v = V.dq10_nonneg_fixed_assets(bs)
    assert len(v) == 1

def test_dq11_tax_rate_out_of_range():
    pl = pd.DataFrame({"company_id": ["TCS"], "year": ["2023-03"], "tax_percentage": [75.0]})
    v = V.dq11_tax_rate_range(pl)
    assert len(v) == 1

def test_dq12_dividend_payout_cap():
    pl = pd.DataFrame({"company_id": ["TCS"], "year": ["2023-03"], "dividend_payout": [250.0]})
    v = V.dq12_dividend_payout_cap(pl)
    assert len(v) == 1

def test_dq14_eps_sign_mismatch():
    pl = pd.DataFrame({"company_id": ["TCS"], "year": ["2023-03"], "net_profit": [100.0], "eps": [-1.0]})
    v = V.dq14_eps_sign_consistency(pl)
    assert len(v) == 1

def test_dq16_coverage_short_history():
    pl = pd.DataFrame({"company_id": ["TCS"] * 3, "year": ["2021-03", "2022-03", "2023-03"]})
    bs = pd.DataFrame({"company_id": [], "year": []})
    cf = pd.DataFrame({"company_id": [], "year": []})
    v = V.dq16_coverage_check(pl, bs, cf)
    assert any(x["rule_id"] == "DQ-16" and x["company_id"] == "TCS" for x in v)
