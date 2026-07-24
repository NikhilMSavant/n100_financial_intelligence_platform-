"""
tests/etl/test_dq_rules.py
---------------------------
Sprint 3 Day 21 gap fix: unit tests for all 16 DQ rules from validator.py,
using synthetic data crafted to trigger/not trigger each rule - closing
the "14 DQ rule unit tests" exit criteria gap (spec says 14, we have 16
rules; none were previously pytest-ized).

Run with: python -m pytest tests/etl/test_dq_rules.py -v
"""
import sys
import os
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src", "etl"))

from validator import (
    check_dq01_pk_uniqueness, check_dq02_composite_key_uniqueness,
    check_dq03_fk_integrity, check_dq04_balance_sheet_tolerance,
    check_dq05_opm_cross_check, check_dq06_positive_sales,
    check_dq07_net_profit_vs_pbt, check_dq08_eps_sign_match,
    check_dq09_net_cash_flow_reconciliation, check_dq10_positive_balance_sheet_totals,
    check_dq11_tax_rate_range, check_dq12_dividend_payout_cap,
    check_dq13_url_wellformed, check_dq14_ohlc_sanity,
    check_dq15_market_cap_pe_sanity, check_dq16_year_coverage,
)


def test_dq01_flags_duplicate_pk():
    df = pd.DataFrame({"id": [1, 2, 2, 3]})
    findings = check_dq01_pk_uniqueness(df, "id", "profitandloss")
    assert len(findings) == 1
    assert findings[0]["rule"] == "DQ-01"
    assert findings[0]["severity"] == "CRITICAL"


def test_dq01_no_duplicates_no_findings():
    df = pd.DataFrame({"id": [1, 2, 3]})
    assert check_dq01_pk_uniqueness(df, "id", "profitandloss") == []


def test_dq02_flags_duplicate_company_year():
    df = pd.DataFrame({"company_id": ["A", "A", "B"], "year": ["2020-03", "2020-03", "2021-03"]})
    findings = check_dq02_composite_key_uniqueness(df, "profitandloss")
    assert len(findings) == 1
    assert findings[0]["severity"] == "CRITICAL"


def test_dq03_flags_orphan_company_id():
    df = pd.DataFrame({"company_id": ["A", "B", "ORPHAN"]})
    findings = check_dq03_fk_integrity(df, known_company_ids=["A", "B"], table_name="profitandloss")
    assert len(findings) == 1
    assert findings[0]["company_id"] == "ORPHAN"


def test_dq04_flags_balance_sheet_mismatch_over_tolerance():
    df = pd.DataFrame({
        "company_id": ["A", "B"], "year": ["2020-03", "2020-03"],
        "total_assets": [100, 100], "total_liabilities": [100, 80],  # A matches, B is 25% off
    })
    findings = check_dq04_balance_sheet_tolerance(df, tolerance_pct=1.0)
    assert len(findings) == 1
    assert findings[0]["company_id"] == "B"


def test_dq05_flags_opm_mismatch_over_tolerance():
    df = pd.DataFrame({
        "company_id": ["A"], "year": ["2020-03"], "sales": [1000],
        "operating_profit": [200], "opm_percentage": [10.0],  # computed=20%, stated=10% -> 10pt gap
    })
    findings = check_dq05_opm_cross_check(df, tolerance_pct=1.0)
    assert len(findings) == 1


def test_dq06_flags_non_positive_sales():
    df = pd.DataFrame({"company_id": ["A", "B"], "year": ["2020-03", "2020-03"], "sales": [0, 100]})
    findings = check_dq06_positive_sales(df)
    assert len(findings) == 1
    assert findings[0]["company_id"] == "A"


def test_dq07_flags_net_profit_exceeding_pbt():
    df = pd.DataFrame({
        "company_id": ["A"], "year": ["2020-03"],
        "net_profit": [150], "profit_before_tax": [100],
    })
    findings = check_dq07_net_profit_vs_pbt(df)
    assert len(findings) == 1


def test_dq08_flags_opposite_sign_eps_and_profit():
    df = pd.DataFrame({
        "company_id": ["A"], "year": ["2020-03"],
        "eps": [-5.0], "net_profit": [100],  # negative eps, positive profit -> flagged
    })
    findings = check_dq08_eps_sign_match(df)
    assert len(findings) == 1


def test_dq09_flags_cash_flow_reconciliation_mismatch():
    df = pd.DataFrame({
        "company_id": ["A"], "year": ["2020-03"],
        "operating_activity": [100], "investing_activity": [-50], "financing_activity": [-20],
        "net_cash_flow": [100],  # computed=30, stated=100, diff=70 > 10 tolerance
    })
    findings = check_dq09_net_cash_flow_reconciliation(df, tolerance_cr=10)
    assert len(findings) == 1


def test_dq10_flags_non_positive_balance_sheet_totals():
    df = pd.DataFrame({
        "company_id": ["A", "B"], "year": ["2020-03", "2020-03"],
        "total_assets": [0, 100], "total_liabilities": [100, 100],
    })
    findings = check_dq10_positive_balance_sheet_totals(df)
    assert len(findings) == 1
    assert findings[0]["company_id"] == "A"


def test_dq11_flags_tax_rate_outside_range():
    df = pd.DataFrame({"company_id": ["A", "B"], "year": ["2020-03", "2020-03"], "tax_percentage": [75, 25]})
    findings = check_dq11_tax_rate_range(df, min_rate=0, max_rate=60)
    assert len(findings) == 1
    assert findings[0]["company_id"] == "A"


def test_dq12_flags_dividend_payout_over_cap():
    df = pd.DataFrame({"company_id": ["A", "B"], "year": ["2020-03", "2020-03"], "dividend_payout": [250, 50]})
    findings = check_dq12_dividend_payout_cap(df, cap_pct=200)
    assert len(findings) == 1
    assert findings[0]["company_id"] == "A"


def test_dq13_flags_malformed_url():
    df = pd.DataFrame({
        "company_id": ["A", "B"], "year": ["2020-03", "2020-03"],
        "annual_report": ["not-a-url", "https://example.com/report.pdf"],
    })
    findings = check_dq13_url_wellformed(df)
    assert len(findings) == 1
    assert findings[0]["company_id"] == "A"


def test_dq14_flags_ohlc_out_of_order():
    df = pd.DataFrame({
        "company_id": ["A"], "date": ["2020-01-01"],
        "open_price": [100], "high_price": [90], "low_price": [80], "close_price": [95],  # high < open, invalid
    })
    findings = check_dq14_ohlc_sanity(df)
    assert len(findings) == 1


def test_dq15_flags_absurd_pe_ratio():
    df = pd.DataFrame({
        "company_id": ["A", "B"], "year": ["2020-03", "2020-03"],
        "market_cap_crore": [1000, 1000], "pe_ratio": [600, 25],  # A's PE > 500 cap
    })
    findings = check_dq15_market_cap_pe_sanity(df)
    assert len(findings) == 1
    assert findings[0]["company_id"] == "A"


def test_dq16_flags_low_year_coverage_as_warning():
    df = pd.DataFrame({
        "company_id": ["A"] * 4,  # 4 years - below target(5), above critical(3) -> WARNING
        "year": ["2020-03", "2021-03", "2022-03", "2023-03"],
    })
    findings = check_dq16_year_coverage(df, target_years=5, critical_years=3)
    assert len(findings) == 1
    assert findings[0]["severity"] == "WARNING"


def test_dq16_flags_very_low_year_coverage_as_critical():
    df = pd.DataFrame({
        "company_id": ["A", "A"],  # only 2 years - below critical(3) -> CRITICAL
        "year": ["2022-03", "2023-03"],
    })
    findings = check_dq16_year_coverage(df, target_years=5, critical_years=3)
    assert len(findings) == 1
    assert findings[0]["severity"] == "CRITICAL"