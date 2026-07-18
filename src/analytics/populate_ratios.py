"""
populate_ratios.py
-------------------
Day 12 deliverable: runs the full ratio engine (ratios.py, cagr.py,
cashflow_kpis.py) against every company-year in the database and writes
the results into the financial_ratios table.

Run with: python src/analytics/populate_ratios.py
(Run AFTER loader.py, since it reads from and writes to db/nifty100.db.)
"""
import sqlite3
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from ratios import (
    net_profit_margin, operating_profit_margin, return_on_equity,
    return_on_capital_employed, return_on_assets, debt_to_equity,
    interest_coverage_ratio, net_debt, asset_turnover,
)
from cagr import compute_cagr_from_series
from cashflow_kpis import cfo_quality_score
from quality_score import composite_quality_score

DB_PATH = "db/nifty100.db"


def fetch_company_year_data(conn):
    """Joins profitandloss, balancesheet, cashflow, sectors into one
    per-(company_id, year) record so ratios can be computed row by row."""
    query = """
        SELECT
            pl.company_id, pl.year,
            pl.sales, pl.operating_profit, pl.opm_percentage, pl.other_income, pl.interest,
            pl.net_profit, pl.eps, pl.dividend_payout, pl.profit_before_tax,
            bs.equity_capital, bs.reserves, bs.borrowings, bs.investments, bs.total_assets,
            cf.operating_activity, cf.investing_activity, cf.financing_activity,
            s.broad_sector
        FROM profitandloss pl
        LEFT JOIN balancesheet bs ON bs.company_id = pl.company_id AND bs.year = pl.year
        LEFT JOIN cashflow cf ON cf.company_id = pl.company_id AND cf.year = pl.year
        LEFT JOIN sectors s ON s.company_id = pl.company_id
        ORDER BY pl.company_id, pl.year
    """
    cols = ["company_id", "year", "sales", "operating_profit", "opm_percentage", "other_income", "interest",
            "net_profit", "eps", "dividend_payout", "profit_before_tax",
            "equity_capital", "reserves", "borrowings", "investments", "total_assets",
            "operating_activity", "investing_activity", "financing_activity", "broad_sector"]
    rows = conn.execute(query).fetchall()
    return [dict(zip(cols, r)) for r in rows]


def build_year_series(all_rows, field):
    """Builds {company_id: {year: value}} for CAGR lookups.
    TTM is deliberately excluded here - it's a rolling current-period
    snapshot, not a fiscal year-end, so it must never be picked as a
    CAGR window endpoint (it would corrupt the 'n years apart' comparison)."""
    series = {}
    for r in all_rows:
        if r["year"] == "TTM":
            continue
        series.setdefault(r["company_id"], {})[r["year"]] = r[field]
    return series


def main():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")

    all_rows = fetch_company_year_data(conn)
    print(f"Fetched {len(all_rows)} company-year records to process")

    sales_series = build_year_series(all_rows, "sales")
    pat_series = build_year_series(all_rows, "net_profit")
    eps_series = build_year_series(all_rows, "eps")

    output_rows = []
    for r in all_rows:
        cid, year = r["company_id"], r["year"]

        npm = net_profit_margin(r["net_profit"], r["sales"])
        opm_result = operating_profit_margin(r["operating_profit"], r["sales"], r["opm_percentage"])
        roe = return_on_equity(r["net_profit"], r["equity_capital"], r["reserves"])
        roce_result = return_on_capital_employed(
            r["profit_before_tax"], r["equity_capital"], r["reserves"], r["borrowings"], r["broad_sector"]
        )
        de_result = debt_to_equity(r["borrowings"], r["equity_capital"], r["reserves"], r["broad_sector"])
        icr_result = interest_coverage_ratio(r["operating_profit"], r["other_income"], r["interest"])
        ndebt = net_debt(r["borrowings"], r["investments"])
        at = asset_turnover(r["sales"], r["total_assets"])
        fcf = (r["operating_activity"] or 0) + (r["investing_activity"] or 0)
        rev_cagr = compute_cagr_from_series(sales_series.get(cid, {}), 5)
        pat_cagr = compute_cagr_from_series(pat_series.get(cid, {}), 5)
        eps_cagr = compute_cagr_from_series(eps_series.get(cid, {}), 5)
        quality_score = composite_quality_score(
            roe, de_result["value"], icr_result["value"], icr_result["icr_label"],
            r["operating_activity"], r["net_profit"]
        )
        
        output_rows.append({
            "company_id": cid, "year": year,
            "net_profit_margin_pct": npm,
            "operating_profit_margin_pct": opm_result["value"],
            "return_on_equity_pct": roe,
            "debt_to_equity": de_result["value"],
            "interest_coverage": icr_result["value"],
            "asset_turnover": at,
            "free_cash_flow_cr": fcf,
            "capex_cr": r["investing_activity"],
            "earnings_per_share": r["eps"],
            "book_value_per_share": None,  # needs shares outstanding, not in current schema - left null, documented in Day 13 log
            "dividend_payout_ratio_pct": r["dividend_payout"],
            "total_debt_cr": r["borrowings"],
            "cash_from_operations_cr": r["operating_activity"],
            "revenue_cagr_5yr": rev_cagr["value"],
            "pat_cagr_5yr": pat_cagr["value"],
            "eps_cagr_5yr": eps_cagr["value"],
            "composite_quality_score": quality_score,
            "return_on_equity_pct": roe,
            "return_on_capital_employed_pct": roce_result["value"],
        })

    conn.execute("DELETE FROM financial_ratios")
    conn.executemany("""
        INSERT INTO financial_ratios (
            company_id, year, net_profit_margin_pct, operating_profit_margin_pct,
            return_on_equity_pct, return_on_capital_employed_pct, debt_to_equity, interest_coverage, asset_turnover,
            free_cash_flow_cr, capex_cr, earnings_per_share, book_value_per_share,
            dividend_payout_ratio_pct, total_debt_cr, cash_from_operations_cr,
            revenue_cagr_5yr, pat_cagr_5yr, eps_cagr_5yr, composite_quality_score
        ) VALUES (
            :company_id, :year, :net_profit_margin_pct, :operating_profit_margin_pct,
            :return_on_equity_pct, :return_on_capital_employed_pct, :debt_to_equity, :interest_coverage, :asset_turnover,
            :free_cash_flow_cr, :capex_cr, :earnings_per_share, :book_value_per_share,
            :dividend_payout_ratio_pct, :total_debt_cr, :cash_from_operations_cr,
            :revenue_cagr_5yr, :pat_cagr_5yr, :eps_cagr_5yr, :composite_quality_score
        )
    """, output_rows)
    conn.commit()

    count = conn.execute("SELECT COUNT(*) FROM financial_ratios").fetchone()[0]
    print(f"Wrote {count} rows into financial_ratios")

    conn.close()


if __name__ == "__main__":
    main()