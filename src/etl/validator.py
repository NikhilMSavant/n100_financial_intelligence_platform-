"""
validator.py
------------
Day 3 deliverable: runs all 16 data-quality rules (DQ-01 .. DQ-16) against
nifty100.db and writes output/validation_failures.csv with a severity per row.

Refactored (Sprint 3 Day 21 gap fix): each rule is now an independently
callable, independently testable function that takes a DataFrame and
returns a list of finding dicts - rather than being inline logic appending
to a module-level global list. This lets each rule be unit-tested with
synthetic data (see tests/etl/test_dq_rules.py), addressing the spec's
"14 DQ rule unit tests" requirement (Sprint 1 built 16 rules; they were
never previously structured as pytest tests).

Run with: python src/etl/validator.py
(Run AFTER loader.py, since it reads from db/nifty100.db.)
"""
import os
import sqlite3
import pandas as pd

DB_PATH = "db/nifty100.db"
OUT_PATH = "output/validation_failures.csv"


def _finding(rule, severity, table, company_id, detail):
    return {"rule": rule, "severity": severity, "table": table, "company_id": company_id, "detail": detail}


def check_dq01_pk_uniqueness(df, pk_col, table_name):
    """DQ-01: no duplicate values in a table's own primary key column."""
    dupes = df[df.duplicated()]
    if len(dupes) > 0:
        return [_finding("DQ-01", "CRITICAL", table_name, None, f"{len(dupes)} duplicate {pk_col} values found")]
    return []


def check_dq02_composite_key_uniqueness(df, table_name):
    """DQ-02: no duplicate (company_id, year) pairs."""
    dupes = df[df.duplicated(subset=["company_id", "year"])]
    if len(dupes) > 0:
        return [_finding("DQ-02", "CRITICAL", table_name, None,
                          f"{len(dupes)} duplicate (company_id, year) pairs (should have been caught by loader dedup)")]
    return []


def check_dq03_fk_integrity(df, known_company_ids, table_name):
    """DQ-03: every company_id must exist in the companies table."""
    orphans = set(df["company_id"]) - set(known_company_ids)
    return [_finding("DQ-03", "CRITICAL", table_name, cid, "company_id not present in companies table")
            for cid in orphans]


def check_dq04_balance_sheet_tolerance(df, tolerance_pct=1.0):
    """DQ-04: total_assets and total_liabilities must match within tolerance_pct%."""
    df = df.copy()
    df["diff_pct"] = ((df["total_assets"] - df["total_liabilities"]).abs()
                       / df["total_liabilities"].replace(0, pd.NA)) * 100
    bad = df[df["diff_pct"] > tolerance_pct]
    return [_finding("DQ-04", "WARNING", "balancesheet", r["company_id"],
                      f"year={r['year']}: assets/liabilities differ by {r['diff_pct']:.2f}% (>{tolerance_pct}%)")
            for _, r in bad.iterrows()]


def check_dq05_opm_cross_check(df, tolerance_pct=1.0):
    """DQ-05: opm_percentage should match operating_profit/sales*100 within tolerance_pct."""
    df = df[df["sales"] > 0].copy()
    df["computed_opm"] = df["operating_profit"] / df["sales"] * 100
    df["diff"] = (df["computed_opm"] - df["opm_percentage"]).abs()
    bad = df[df["diff"] > tolerance_pct]
    return [_finding("DQ-05", "WARNING", "profitandloss", r["company_id"],
                      f"year={r['year']}: stated OPM {r['opm_percentage']}% vs computed {r['computed_opm']:.2f}%")
            for _, r in bad.iterrows()]


def check_dq06_positive_sales(df):
    """DQ-06: sales must be > 0."""
    bad = df[df["sales"] <= 0]
    return [_finding("DQ-06", "CRITICAL", "profitandloss", r["company_id"], f"year={r['year']}: sales={r['sales']} <= 0")
            for _, r in bad.iterrows()]


def check_dq07_net_profit_vs_pbt(df):
    """DQ-07: net_profit should not exceed profit_before_tax."""
    bad = df[df["net_profit"] > df["profit_before_tax"]]
    return [_finding("DQ-07", "WARNING", "profitandloss", r["company_id"],
                      f"year={r['year']}: net_profit ({r['net_profit']}) > profit_before_tax ({r['profit_before_tax']})")
            for _, r in bad.iterrows()]


def check_dq08_eps_sign_match(df):
    """DQ-08: EPS sign should match net_profit sign."""
    df = df.dropna(subset=["eps", "net_profit"])
    bad = df[(df["eps"] * df["net_profit"]) < 0]
    return [_finding("DQ-08", "WARNING", "profitandloss", r["company_id"],
                      f"year={r['year']}: eps={r['eps']} and net_profit={r['net_profit']} have opposite signs")
            for _, r in bad.iterrows()]


def check_dq09_net_cash_flow_reconciliation(df, tolerance_cr=10):
    """DQ-09: net_cash_flow should equal operating+investing+financing within tolerance_cr."""
    df = df.copy()
    df["computed"] = df["operating_activity"] + df["investing_activity"] + df["financing_activity"]
    df["diff"] = (df["computed"] - df["net_cash_flow"]).abs()
    bad = df[df["diff"] > tolerance_cr]
    return [_finding("DQ-09", "WARNING", "cashflow", r["company_id"],
                      f"year={r['year']}: stated net_cash_flow {r['net_cash_flow']} vs computed {r['computed']:.1f} "
                      f"(diff {r['diff']:.1f} Cr)")
            for _, r in bad.iterrows()]


def check_dq10_positive_balance_sheet_totals(df):
    """DQ-10: total_assets and total_liabilities must both be positive."""
    bad = df[(df["total_assets"] <= 0) | (df["total_liabilities"] <= 0)]
    return [_finding("DQ-10", "CRITICAL", "balancesheet", r["company_id"],
                      f"year={r['year']}: total_assets={r['total_assets']}, total_liabilities={r['total_liabilities']}")
            for _, r in bad.iterrows()]


def check_dq11_tax_rate_range(df, min_rate=0, max_rate=60):
    """DQ-11: tax_percentage should be within [min_rate, max_rate]."""
    bad = df[(df["tax_percentage"] < min_rate) | (df["tax_percentage"] > max_rate)]
    return [_finding("DQ-11", "WARNING", "profitandloss", r["company_id"],
                      f"year={r['year']}: tax_percentage={r['tax_percentage']}% outside [{min_rate},{max_rate}]")
            for _, r in bad.iterrows()]


def check_dq12_dividend_payout_cap(df, cap_pct=200):
    """DQ-12: dividend_payout should not exceed cap_pct%."""
    bad = df[df["dividend_payout"] > cap_pct]
    return [_finding("DQ-12", "WARNING", "profitandloss", r["company_id"],
                      f"year={r['year']}: dividend_payout={r['dividend_payout']}% exceeds {cap_pct}% cap")
            for _, r in bad.iterrows()]


def check_dq13_url_wellformed(df):
    """DQ-13: annual_report should be a well-formed URL (starts with http)."""
    bad = df[~df["annual_report"].fillna("").str.startswith("http")]
    return [_finding("DQ-13", "WARNING", "documents", r["company_id"],
                      f"year={r['year']}: malformed URL '{r['annual_report']}'")
            for _, r in bad.iterrows()]


def check_dq14_ohlc_sanity(df):
    """DQ-14: low <= open/close <= high for every stock price row."""
    bad = df[(df["low_price"] > df["open_price"]) | (df["open_price"] > df["high_price"]) |
              (df["low_price"] > df["close_price"]) | (df["close_price"] > df["high_price"])]
    return [_finding("DQ-14", "WARNING", "stock_prices", r["company_id"],
                      f"date={r['date']}: OHLC out of order (low={r['low_price']}, open={r['open_price']}, "
                      f"close={r['close_price']}, high={r['high_price']})")
            for _, r in bad.iterrows()]


def check_dq15_market_cap_pe_sanity(df):
    """DQ-15: market_cap must be positive, pe_ratio within [0, 500]."""
    bad = df[(df["market_cap_crore"] <= 0) | (df["pe_ratio"] < 0) | (df["pe_ratio"] > 500)]
    return [_finding("DQ-15", "WARNING", "market_cap", r["company_id"],
                      f"year={r['year']}: market_cap={r['market_cap_crore']}, pe_ratio={r['pe_ratio']}")
            for _, r in bad.iterrows()]


def check_dq16_year_coverage(df, target_years=5, critical_years=3):
    """DQ-16: each company should have >= target_years of P&L history (< critical_years is CRITICAL)."""
    counts = df.groupby("company_id")["year"].nunique()
    low_coverage = counts[counts < target_years]
    findings = []
    for cid, n in low_coverage.items():
        sev = "CRITICAL" if n < critical_years else "WARNING"
        findings.append(_finding("DQ-16", sev, "profitandloss", cid,
                                  f"only {n} distinct fiscal years of P&L data (<{target_years} target, <{critical_years} is critical)"))
    return findings


def run(conn):
    """Runs all 16 rules against a live database connection, fetching the
    data each rule needs, then delegating to the pure check_* functions."""
    findings = []

    tables = ["companies", "profitandloss", "balancesheet", "cashflow", "analysis",
              "documents", "prosandcons", "sectors", "stock_prices", "market_cap",
              "financial_ratios", "peer_groups"]

    for t in tables:
        pk_col = "company_id" if t == "companies" else "id"
        df = pd.read_sql(f"SELECT {pk_col} FROM {t}", conn)
        findings += check_dq01_pk_uniqueness(df, pk_col, t)

    for t in ["profitandloss", "balancesheet", "cashflow", "market_cap", "financial_ratios"]:
        df = pd.read_sql(f"SELECT company_id, year FROM {t}", conn)
        findings += check_dq02_composite_key_uniqueness(df, t)

    known = pd.read_sql("SELECT company_id FROM companies", conn)["company_id"].tolist()
    for t in [x for x in tables if x != "companies"]:
        df = pd.read_sql(f"SELECT DISTINCT company_id FROM {t}", conn)
        findings += check_dq03_fk_integrity(df, known, t)

    df = pd.read_sql("SELECT company_id, year, total_assets, total_liabilities FROM balancesheet", conn)
    findings += check_dq04_balance_sheet_tolerance(df)

    df = pd.read_sql("SELECT company_id, year, sales, operating_profit, opm_percentage FROM profitandloss", conn)
    findings += check_dq05_opm_cross_check(df)

    df = pd.read_sql("SELECT company_id, year, sales FROM profitandloss", conn)
    findings += check_dq06_positive_sales(df)

    df = pd.read_sql("SELECT company_id, year, net_profit, profit_before_tax FROM profitandloss", conn)
    findings += check_dq07_net_profit_vs_pbt(df)

    df = pd.read_sql("SELECT company_id, year, eps, net_profit FROM profitandloss", conn)
    findings += check_dq08_eps_sign_match(df)

    df = pd.read_sql("SELECT company_id, year, operating_activity, investing_activity, "
                      "financing_activity, net_cash_flow FROM cashflow", conn)
    findings += check_dq09_net_cash_flow_reconciliation(df)

    df = pd.read_sql("SELECT company_id, year, total_assets, total_liabilities FROM balancesheet", conn)
    findings += check_dq10_positive_balance_sheet_totals(df)

    df = pd.read_sql("SELECT company_id, year, tax_percentage FROM profitandloss", conn)
    findings += check_dq11_tax_rate_range(df)

    df = pd.read_sql("SELECT company_id, year, dividend_payout FROM profitandloss", conn)
    findings += check_dq12_dividend_payout_cap(df)

    df = pd.read_sql("SELECT company_id, year, annual_report FROM documents", conn)
    findings += check_dq13_url_wellformed(df)

    df = pd.read_sql("SELECT company_id, date, open_price, high_price, low_price, close_price FROM stock_prices", conn)
    findings += check_dq14_ohlc_sanity(df)

    df = pd.read_sql("SELECT company_id, year, market_cap_crore, pe_ratio FROM market_cap", conn)
    findings += check_dq15_market_cap_pe_sanity(df)

    df = pd.read_sql("SELECT company_id, year FROM profitandloss WHERE year != 'TTM'", conn)
    findings += check_dq16_year_coverage(df)

    return findings


def main():
    if not os.path.exists(DB_PATH):
        raise SystemExit(f"{DB_PATH} not found - run loader.py first")

    os.makedirs("output", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    findings = run(conn)
    conn.close()

    df = pd.DataFrame(findings)
    df.to_csv(OUT_PATH, index=False)

    n_critical = (df["severity"] == "CRITICAL").sum() if len(df) else 0
    n_warning = (df["severity"] == "WARNING").sum() if len(df) else 0
    print(f"Wrote {OUT_PATH}: {len(df)} total findings ({n_critical} CRITICAL, {n_warning} WARNING)")
    if len(df):
        print("\nFindings by rule:")
        print(df.groupby(["rule", "severity"]).size().to_string())


if __name__ == "__main__":
    main()