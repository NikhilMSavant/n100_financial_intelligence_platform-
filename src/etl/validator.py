"""
validator.py
------------
Day 3 deliverable: runs all 16 data-quality rules (DQ-01 .. DQ-16) against
nifty100.db and writes output/validation_failures.csv with a severity per row.

Run with: python src/etl/validator.py
(Run AFTER loader.py, since it reads from db/nifty100.db.)
"""
import os
import sqlite3
import pandas as pd

DB_PATH = "db/nifty100.db"
OUT_PATH = "output/validation_failures.csv"

failures = []


def flag(rule, severity, table, company_id, detail):
    failures.append({
        "rule": rule,
        "severity": severity,
        "table": table,
        "company_id": company_id,
        "detail": detail,
    })


def run(conn):
    # ---- DQ-01: PK uniqueness on every table's own `id` column ----
    tables = ["companies", "profitandloss", "balancesheet", "cashflow", "analysis",
              "documents", "prosandcons", "sectors", "stock_prices", "market_cap",
              "financial_ratios", "peer_groups"]
    for t in tables:
        pk_col = "company_id" if t == "companies" else "id"
        df = pd.read_sql(f"SELECT {pk_col} FROM {t}", conn)
        dupes = df[df.duplicated()]
        if len(dupes) > 0:
            flag("DQ-01", "CRITICAL", t, None, f"{len(dupes)} duplicate {pk_col} values found")

    # ---- DQ-02: (company_id, year) composite key uniqueness ----
    for t in ["profitandloss", "balancesheet", "cashflow", "market_cap", "financial_ratios"]:
        df = pd.read_sql(f"SELECT company_id, year FROM {t}", conn)
        dupes = df[df.duplicated(subset=["company_id", "year"])]
        if len(dupes) > 0:
            flag("DQ-02", "CRITICAL", t, None,
                 f"{len(dupes)} duplicate (company_id, year) pairs (should have been caught by loader dedup)")

    # ---- DQ-03: FK integrity - every company_id must exist in companies ----
    known = set(pd.read_sql("SELECT company_id FROM companies", conn)["company_id"])
    for t in [x for x in tables if x != "companies"]:
        df = pd.read_sql(f"SELECT DISTINCT company_id FROM {t}", conn)
        orphans = set(df["company_id"]) - known
        for cid in orphans:
            flag("DQ-03", "CRITICAL", t, cid, "company_id not present in companies table")

    # ---- DQ-04: Balance sheet must balance (total_assets == total_liabilities, <1%) ----
    df = pd.read_sql("SELECT company_id, year, total_assets, total_liabilities FROM balancesheet", conn)
    df["diff_pct"] = ((df["total_assets"] - df["total_liabilities"]).abs()
                       / df["total_liabilities"].replace(0, pd.NA)) * 100
    bad = df[df["diff_pct"] > 1.0]
    for _, r in bad.iterrows():
        flag("DQ-04", "WARNING", "balancesheet", r["company_id"],
             f"year={r['year']}: assets/liabilities differ by {r['diff_pct']:.2f}% (>1%)")

    # ---- DQ-05: OPM cross-check (opm_percentage ~= operating_profit/sales*100) ----
    df = pd.read_sql("SELECT company_id, year, sales, operating_profit, opm_percentage FROM profitandloss", conn)
    df = df[df["sales"] > 0]
    df["computed_opm"] = df["operating_profit"] / df["sales"] * 100
    df["diff"] = (df["computed_opm"] - df["opm_percentage"]).abs()
    bad = df[df["diff"] > 1.0]
    for _, r in bad.iterrows():
        flag("DQ-05", "WARNING", "profitandloss", r["company_id"],
             f"year={r['year']}: stated OPM {r['opm_percentage']}% vs computed {r['computed_opm']:.2f}%")

    # ---- DQ-06: Positive sales ----
    df = pd.read_sql("SELECT company_id, year, sales FROM profitandloss", conn)
    bad = df[df["sales"] <= 0]
    for _, r in bad.iterrows():
        flag("DQ-06", "CRITICAL", "profitandloss", r["company_id"], f"year={r['year']}: sales={r['sales']} <= 0")

    # ---- DQ-07: net_profit should not exceed profit_before_tax ----
    df = pd.read_sql("SELECT company_id, year, net_profit, profit_before_tax FROM profitandloss", conn)
    bad = df[df["net_profit"] > df["profit_before_tax"]]
    for _, r in bad.iterrows():
        flag("DQ-07", "WARNING", "profitandloss", r["company_id"],
             f"year={r['year']}: net_profit ({r['net_profit']}) > profit_before_tax ({r['profit_before_tax']})")

    # ---- DQ-08: EPS sign should match net_profit sign ----
    df = pd.read_sql("SELECT company_id, year, eps, net_profit FROM profitandloss", conn)
    df = df.dropna(subset=["eps", "net_profit"])
    bad = df[(df["eps"] * df["net_profit"]) < 0]
    for _, r in bad.iterrows():
        flag("DQ-08", "WARNING", "profitandloss", r["company_id"],
             f"year={r['year']}: eps={r['eps']} and net_profit={r['net_profit']} have opposite signs")

    # ---- DQ-09: net cash flow = operating + investing + financing (Cr tolerance) ----
    df = pd.read_sql("SELECT company_id, year, operating_activity, investing_activity, "
                      "financing_activity, net_cash_flow FROM cashflow", conn)
    df["computed"] = df["operating_activity"] + df["investing_activity"] + df["financing_activity"]
    df["diff"] = (df["computed"] - df["net_cash_flow"]).abs()
    bad = df[df["diff"] > 10]  # DQ_NET_CASH_TOLERANCE_CR
    for _, r in bad.iterrows():
        flag("DQ-09", "WARNING", "cashflow", r["company_id"],
             f"year={r['year']}: stated net_cash_flow {r['net_cash_flow']} vs computed {r['computed']:.1f} "
             f"(diff {r['diff']:.1f} Cr)")

    # ---- DQ-10: total_assets and total_liabilities must be positive ----
    df = pd.read_sql("SELECT company_id, year, total_assets, total_liabilities FROM balancesheet", conn)
    bad = df[(df["total_assets"] <= 0) | (df["total_liabilities"] <= 0)]
    for _, r in bad.iterrows():
        flag("DQ-10", "CRITICAL", "balancesheet", r["company_id"],
             f"year={r['year']}: total_assets={r['total_assets']}, total_liabilities={r['total_liabilities']}")

    # ---- DQ-11: tax_percentage should be within [0, 60] ----
    df = pd.read_sql("SELECT company_id, year, tax_percentage FROM profitandloss", conn)
    bad = df[(df["tax_percentage"] < 0) | (df["tax_percentage"] > 60)]
    for _, r in bad.iterrows():
        flag("DQ-11", "WARNING", "profitandloss", r["company_id"],
             f"year={r['year']}: tax_percentage={r['tax_percentage']}% outside [0,60]")

    # ---- DQ-12: dividend_payout should not exceed 200% cap ----
    df = pd.read_sql("SELECT company_id, year, dividend_payout FROM profitandloss", conn)
    bad = df[df["dividend_payout"] > 200]
    for _, r in bad.iterrows():
        flag("DQ-12", "WARNING", "profitandloss", r["company_id"],
             f"year={r['year']}: dividend_payout={r['dividend_payout']}% exceeds 200% cap")

    # ---- DQ-13: annual_report URL well-formed ----
    df = pd.read_sql("SELECT company_id, year, annual_report FROM documents", conn)
    bad = df[~df["annual_report"].fillna("").str.startswith("http")]
    for _, r in bad.iterrows():
        flag("DQ-13", "WARNING", "documents", r["company_id"], f"year={r['year']}: malformed URL '{r['annual_report']}'")

    # ---- DQ-14: stock price OHLC sanity (low <= open/close <= high) ----
    df = pd.read_sql("SELECT company_id, date, open_price, high_price, low_price, close_price FROM stock_prices", conn)
    bad = df[(df["low_price"] > df["open_price"]) | (df["open_price"] > df["high_price"]) |
             (df["low_price"] > df["close_price"]) | (df["close_price"] > df["high_price"])]
    for _, r in bad.iterrows():
        flag("DQ-14", "WARNING", "stock_prices", r["company_id"],
             f"date={r['date']}: OHLC out of order (low={r['low_price']}, open={r['open_price']}, "
             f"close={r['close_price']}, high={r['high_price']})")

    # ---- DQ-15: market_cap and PE ratio sanity (positive, PE not absurd) ----
    df = pd.read_sql("SELECT company_id, year, market_cap_crore, pe_ratio FROM market_cap", conn)
    bad = df[(df["market_cap_crore"] <= 0) | (df["pe_ratio"] < 0) | (df["pe_ratio"] > 500)]
    for _, r in bad.iterrows():
        flag("DQ-15", "WARNING", "market_cap", r["company_id"],
             f"year={r['year']}: market_cap={r['market_cap_crore']}, pe_ratio={r['pe_ratio']}")

    # ---- DQ-16: year coverage - each company should have >=5 years of P&L (>=3 minimum for CAGR) ----
    df = pd.read_sql("SELECT company_id, year FROM profitandloss WHERE year != 'TTM'", conn)
    counts = df.groupby("company_id")["year"].nunique()
    low_coverage = counts[counts < 5]
    for cid, n in low_coverage.items():
        sev = "CRITICAL" if n < 3 else "WARNING"
        flag("DQ-16", sev, "profitandloss", cid, f"only {n} distinct fiscal years of P&L data (<5 target, <3 is critical)")


def main():
    if not os.path.exists(DB_PATH):
        raise SystemExit(f"{DB_PATH} not found - run loader.py first")

    os.makedirs("output", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    run(conn)
    conn.close()

    df = pd.DataFrame(failures)
    df.to_csv(OUT_PATH, index=False)

    n_critical = (df["severity"] == "CRITICAL").sum() if len(df) else 0
    n_warning = (df["severity"] == "WARNING").sum() if len(df) else 0
    print(f"Wrote {OUT_PATH}: {len(df)} total findings ({n_critical} CRITICAL, {n_warning} WARNING)")
    if len(df):
        print("\nFindings by rule:")
        print(df.groupby(["rule", "severity"]).size().to_string())


if __name__ == "__main__":
    main()
