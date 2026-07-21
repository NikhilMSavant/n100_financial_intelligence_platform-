"""
engine.py
---------
Day 15 deliverable: Filter Engine Core.
Loads and joins financial_ratios, market_cap, and profitandloss (latest
fiscal year per company) into one DataFrame with all 15 filterable metrics
as columns, then applies threshold filters from screener_config.yaml.
"""
import sqlite3
import pandas as pd

DB_PATH = "db/nifty100.db"


def load_screener_universe(db_path=DB_PATH):
    """
    Returns one row per company (latest non-TTM fiscal year), with columns
    from financial_ratios, market_cap, and profitandloss joined together,
    plus broad_sector from sectors (needed for the Financials D/E carve-out).
    """
    conn = sqlite3.connect(db_path)

    query = """
        SELECT
            fr.company_id,
            fr.return_on_equity_pct, fr.return_on_capital_employed_pct,
            fr.debt_to_equity, fr.free_cash_flow_cr, fr.revenue_cagr_5yr,
            fr.pat_cagr_5yr, fr.operating_profit_margin_pct, fr.interest_coverage,
            fr.eps_cagr_5yr, fr.asset_turnover, fr.dividend_payout_ratio_pct,
            fr.composite_quality_score,
            mc.pe_ratio, mc.pb_ratio, mc.dividend_yield_pct, mc.market_cap_crore,
            pl.net_profit, pl.sales,
            s.broad_sector
        FROM financial_ratios fr
        LEFT JOIN market_cap mc ON mc.company_id = fr.company_id AND mc.year = fr.year
        LEFT JOIN profitandloss pl ON pl.company_id = fr.company_id AND pl.year = fr.year
        LEFT JOIN sectors s ON s.company_id = fr.company_id
        WHERE fr.year = (
            SELECT MAX(year) FROM financial_ratios fr2
            WHERE fr2.company_id = fr.company_id AND fr2.year != 'TTM'
        )
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df


def apply_filters(df, filters):
    """
    Applies threshold filters to the screener universe DataFrame.

    filters: dict like {"roe_min": 15, "de_max": 1.0, "icr_min": 1.5, ...}

    Supported keys:
      roe_min, roce_min, fcf_min, revenue_cagr_5yr_min, pat_cagr_5yr_min,
      opm_min, eps_cagr_5yr_min, asset_turnover_min, sales_min,
      net_profit_min, market_cap_min, dividend_yield_min  -> simple >= filters
      de_max, pe_max, pb_max                                -> simple <= filters
      icr_min                                                -> special (Debt Free = infinity)

    Special cases:
      - de_max: companies in the 'Financials' broad_sector are exempt from
        this filter entirely (skipped, not failed).
      - icr_min: interest_coverage is None for debt-free companies. Since a
        debt-free company can never fail an interest coverage MINIMUM,
        these rows pass automatically rather than being dropped for a null.

    Any filter key referencing a column with a null value in a given row
    (other than the icr_min/de_free special cases) causes that row to be
    excluded for that filter, since a missing value can't be confirmed to
    pass a threshold.
    """
    result = df.copy()

    # --- special cases first ---
    if "de_max" in filters:
        de_max = filters["de_max"]
        exempt = result["broad_sector"] == "Financials"
        passes_de = result["debt_to_equity"] <= de_max
        result = result[exempt | passes_de]

    if "icr_min" in filters:
        icr_min = filters["icr_min"]
        is_debt_free = result["interest_coverage"].isna()
        passes_icr = result["interest_coverage"] >= icr_min
        result = result[is_debt_free | passes_icr]

    # --- simple min filters (column >= threshold) ---
    min_filter_columns = {
        "roe_min": "return_on_equity_pct",
        "roce_min": "return_on_capital_employed_pct",
        "fcf_min": "free_cash_flow_cr",
        "revenue_cagr_5yr_min": "revenue_cagr_5yr",
        "pat_cagr_5yr_min": "pat_cagr_5yr",
        "opm_min": "operating_profit_margin_pct",
        "eps_cagr_5yr_min": "eps_cagr_5yr",
        "asset_turnover_min": "asset_turnover",
        "sales_min": "sales",
        "net_profit_min": "net_profit",
        "market_cap_min": "market_cap_crore",
        "dividend_yield_min": "dividend_yield_pct",
    }
    for filter_key, column in min_filter_columns.items():
        if filter_key in filters:
            threshold = filters[filter_key]
            result = result[result[column] >= threshold]

    # --- simple max filters (column <= threshold) ---
    max_filter_columns = {
        "pe_max": "pe_ratio",
        "pb_max": "pb_ratio",
    }
    for filter_key, column in max_filter_columns.items():
        if filter_key in filters:
            threshold = filters[filter_key]
            result = result[result[column] <= threshold]

    return result


if __name__ == "__main__":
    df = load_screener_universe()
    print(f"Loaded {len(df)} companies (expected: 92)")

    test1 = apply_filters(df, {"de_max": 1.0, "icr_min": 1.5})
    print(f"After de_max=1.0, icr_min=1.5: {len(test1)} companies")

    test2 = apply_filters(df, {"roe_min": 15, "de_max": 1.0})
    print(f"After roe_min=15, de_max=1.0: {len(test2)} companies")

    test3 = apply_filters(df, {"pe_max": 20, "pb_max": 3.0, "dividend_yield_min": 1})
    print(f"After pe_max=20, pb_max=3.0, dividend_yield_min=1: {len(test3)} companies")