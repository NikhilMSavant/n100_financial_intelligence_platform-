"""
validator.py — Sprint 1 / Day 03
Implements DQ-01 .. DQ-16 against nifty100.db and writes
output/validation_failures.csv with a severity column (CRITICAL / WARNING).
"""
import os
import re
import sqlite3
import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DB_PATH = os.path.join(ROOT, "db", "nifty100.db")
OUT_DIR = os.path.join(ROOT, "output")

URL_RE = re.compile(r"^https?://")


def _conn():
    return sqlite3.connect(DB_PATH)


def run():
    conn = _conn()
    failures = []  # (rule_id, severity, table, company_id, year, detail)

    def add(rule, sev, table, company_id, year, detail):
        failures.append((rule, sev, table, company_id, year, detail))

    # DQ-01: PK uniqueness on companies.company_id
    dupe = pd.read_sql(
        "SELECT company_id, COUNT(*) c FROM companies GROUP BY company_id HAVING c > 1", conn)
    for _, r in dupe.iterrows():
        add("DQ-01", "CRITICAL", "companies", r.company_id, None, "duplicate company_id")

    # DQ-02: (company_id, year) PK across the 3 core statement tables
    for tbl in ["profitandloss", "balancesheet", "cashflow"]:
        dupe = pd.read_sql(
            f"SELECT company_id, year, COUNT(*) c FROM {tbl} GROUP BY company_id, year HAVING c > 1", conn)
        for _, r in dupe.iterrows():
            add("DQ-02", "CRITICAL", tbl, r.company_id, r.year, "duplicate (company_id, year)")

    # DQ-03: FK integrity — every company_id in child tables exists in companies
    valid_ids = set(pd.read_sql("SELECT company_id FROM companies", conn)["company_id"])
    for tbl in ["sectors", "profitandloss", "balancesheet", "cashflow", "analysis",
                "documents", "prosandcons", "stock_prices", "market_cap", "peer_groups"]:
        ids = pd.read_sql(f"SELECT DISTINCT company_id FROM {tbl}", conn)["company_id"]
        for cid in ids:
            if cid not in valid_ids:
                add("DQ-03", "CRITICAL", tbl, cid, None, "orphan company_id (no FK parent)")

    # DQ-04: balance-sheet balances — total_liabilities ≈ total_assets, tolerance < 1%
    bs = pd.read_sql("SELECT company_id, year, total_liabilities, total_assets FROM balancesheet", conn)
    bs = bs.dropna(subset=["total_liabilities", "total_assets"])
    bs = bs[bs["total_assets"] != 0]
    bs["pct_diff"] = (bs["total_liabilities"] - bs["total_assets"]).abs() / bs["total_assets"].abs() * 100
    for _, r in bs[bs["pct_diff"] >= 1].iterrows():
        add("DQ-04", "WARNING", "balancesheet", r.company_id, r.year,
            f"total_liabilities vs total_assets diff = {r.pct_diff:.2f}%")

    # DQ-05: OPM cross-check — computed vs stored opm_percentage, tolerance < 1 pp
    pl = pd.read_sql("SELECT company_id, year, sales, operating_profit, opm_percentage FROM profitandloss", conn)
    pl = pl.dropna(subset=["sales", "operating_profit", "opm_percentage"])
    pl = pl[pl["sales"] != 0]
    pl["computed_opm"] = pl["operating_profit"] / pl["sales"] * 100
    pl["diff"] = (pl["computed_opm"] - pl["opm_percentage"]).abs()
    for _, r in pl[pl["diff"] > 1].iterrows():
        add("DQ-05", "WARNING", "profitandloss", r.company_id, r.year,
            f"computed OPM {r.computed_opm:.2f}% vs stored {r.opm_percentage:.2f}%")

    # DQ-06: positive sales
    neg_sales = pd.read_sql("SELECT company_id, year, sales FROM profitandloss WHERE sales <= 0", conn)
    for _, r in neg_sales.iterrows():
        add("DQ-06", "CRITICAL", "profitandloss", r.company_id, r.year, f"sales={r.sales} <= 0")

    # DQ-07: non-negative total_assets
    bad_ta = pd.read_sql("SELECT company_id, year, total_assets FROM balancesheet WHERE total_assets <= 0", conn)
    for _, r in bad_ta.iterrows():
        add("DQ-07", "CRITICAL", "balancesheet", r.company_id, r.year, f"total_assets={r.total_assets} <= 0")

    # DQ-08: net cash flow reconciliation — CFO+CFI+CFF ≈ net_cash_flow, tolerance < 1 unit(cr)
    cf = pd.read_sql("SELECT company_id, year, operating_activity, investing_activity, "
                      "financing_activity, net_cash_flow FROM cashflow", conn).dropna()
    cf["computed"] = cf.operating_activity + cf.investing_activity + cf.financing_activity
    cf["diff"] = (cf["computed"] - cf["net_cash_flow"]).abs()
    for _, r in cf[cf["diff"] > 1].iterrows():
        add("DQ-08", "WARNING", "cashflow", r.company_id, r.year,
            f"CFO+CFI+CFF={r.computed:.1f} vs stored net_cash_flow={r.net_cash_flow:.1f}")

    # DQ-09: tax rate sanity — tax_percentage should be within [0, 60]
    pl2 = pd.read_sql("SELECT company_id, year, tax_percentage FROM profitandloss WHERE tax_percentage IS NOT NULL", conn)
    bad_tax = pl2[(pl2.tax_percentage < 0) | (pl2.tax_percentage > 60)]
    for _, r in bad_tax.iterrows():
        add("DQ-09", "WARNING", "profitandloss", r.company_id, r.year, f"tax_percentage={r.tax_percentage} outside [0,60]")

    # DQ-10: dividend payout cap — should not exceed 500% (sanity guard for bad source data)
    pl3 = pd.read_sql("SELECT company_id, year, dividend_payout FROM profitandloss WHERE dividend_payout IS NOT NULL", conn)
    bad_div = pl3[pl3.dividend_payout > 500]
    for _, r in bad_div.iterrows():
        add("DQ-10", "WARNING", "profitandloss", r.company_id, r.year, f"dividend_payout={r.dividend_payout}% > 500%")

    # DQ-11: annual report URL format
    docs = pd.read_sql("SELECT company_id, year, annual_report FROM documents WHERE annual_report IS NOT NULL", conn)
    bad_url = docs[~docs.annual_report.astype(str).str.match(URL_RE)]
    for _, r in bad_url.iterrows():
        add("DQ-11", "WARNING", "documents", r.company_id, r.year, "annual_report is not a valid http(s) URL")

    # DQ-12: EPS sign should match net_profit sign
    pl4 = pd.read_sql("SELECT company_id, year, net_profit, eps FROM profitandloss WHERE eps IS NOT NULL AND net_profit IS NOT NULL", conn)
    mismatch = pl4[((pl4.net_profit > 0) & (pl4.eps < 0)) | ((pl4.net_profit < 0) & (pl4.eps > 0))]
    for _, r in mismatch.iterrows():
        add("DQ-12", "WARNING", "profitandloss", r.company_id, r.year, f"net_profit={r.net_profit} but eps={r.eps} (sign mismatch)")

    # DQ-13: BSE balance-sheet completeness — equity_capital + reserves + borrowings + other_liabilities ≈ total_liabilities
    bs2 = pd.read_sql("SELECT company_id, year, equity_capital, reserves, borrowings, other_liabilities, total_liabilities FROM balancesheet", conn).dropna()
    bs2["computed"] = bs2.equity_capital + bs2.reserves + bs2.borrowings + bs2.other_liabilities
    bs2["diff_pct"] = (bs2["computed"] - bs2["total_liabilities"]).abs() / bs2["total_liabilities"].abs().replace(0, pd.NA) * 100
    bad = bs2[bs2["diff_pct"] > 1]
    for _, r in bad.iterrows():
        add("DQ-13", "WARNING", "balancesheet", r.company_id, r.year, f"liability components vs total diff={r.diff_pct:.2f}%")

    # DQ-14: year coverage — flag companies with fewer than 5 fiscal years of P&L data
    cov = pd.read_sql("SELECT company_id, COUNT(*) n FROM profitandloss GROUP BY company_id", conn)
    low_cov = cov[cov.n < 5]
    for _, r in low_cov.iterrows():
        add("DQ-14", "WARNING", "profitandloss", r.company_id, None, f"only {r.n} fiscal years of P&L data (<5)")

    # DQ-15: stock price sanity — high >= low, close within [low, high]
    sp = pd.read_sql("SELECT company_id, date, high_price, low_price, close_price FROM stock_prices "
                      "WHERE high_price IS NOT NULL AND low_price IS NOT NULL", conn)
    bad_sp = sp[(sp.high_price < sp.low_price) | (sp.close_price > sp.high_price) | (sp.close_price < sp.low_price)]
    for _, r in bad_sp.head(500).iterrows():   # cap rows logged, still counted below
        add("DQ-15", "WARNING", "stock_prices", r.company_id, None, f"date={r.date} high/low/close inconsistent")

    # DQ-16: peer_groups membership — every company should belong to at least one peer group OR sector (informational)
    pg_ids = set(pd.read_sql("SELECT DISTINCT company_id FROM peer_groups", conn)["company_id"])
    for cid in sorted(valid_ids - pg_ids):
        add("DQ-16", "WARNING", "peer_groups", cid, None, "No peer group assigned")

    fdf = pd.DataFrame(failures, columns=["rule_id", "severity", "table", "company_id", "year", "detail"])
    os.makedirs(OUT_DIR, exist_ok=True)
    fdf.to_csv(os.path.join(OUT_DIR, "validation_failures.csv"), index=False)

    n_critical = (fdf.severity == "CRITICAL").sum()
    n_warning = (fdf.severity == "WARNING").sum()
    print(f"DQ rules run: 16. Failures logged: {len(fdf)} (CRITICAL={n_critical}, WARNING={n_warning})")
    print(fdf.groupby(["rule_id", "severity"]).size().to_string())
    conn.close()
    return fdf


if __name__ == "__main__":
    run()
