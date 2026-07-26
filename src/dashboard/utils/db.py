"""
db.py
-----
Day 22 deliverable: shared, cached database access layer for the
Streamlit dashboard. Every function is decorated with
@st.cache_data(ttl=600) per spec, so repeated calls within a 10-minute
window hit an in-memory cache instead of re-querying SQLite - important
since Streamlit re-runs the entire script on every user interaction
(slider move, button click, etc).
"""
import sqlite3
import streamlit as st
import pandas as pd

DB_PATH = "db/nifty100.db"


def _connect():
    return sqlite3.connect(DB_PATH)


@st.cache_data(ttl=600)
def get_companies():
    """Returns all 92 companies with basic profile info."""
    conn = _connect()
    df = pd.read_sql("SELECT * FROM companies", conn)
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_ratios(ticker, year=None):
    """
    Returns financial_ratios rows for a ticker. If year is None, returns
    all years (sorted ascending) - useful for trend charts. If year is
    given, returns just that year's row (or empty if not found).
    """
    conn = _connect()
    if year is None:
        df = pd.read_sql(
            "SELECT * FROM financial_ratios WHERE company_id = ? AND year != 'TTM' ORDER BY year",
            conn, params=(ticker,),
        )
    else:
        df = pd.read_sql(
            "SELECT * FROM financial_ratios WHERE company_id = ? AND year = ?",
            conn, params=(ticker, year),
        )
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_pl(ticker):
    """Returns all profitandloss rows for a ticker, sorted by year."""
    conn = _connect()
    df = pd.read_sql(
        "SELECT * FROM profitandloss WHERE company_id = ? ORDER BY year",
        conn, params=(ticker,),
    )
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_bs(ticker):
    """Returns all balancesheet rows for a ticker, sorted by year."""
    conn = _connect()
    df = pd.read_sql(
        "SELECT * FROM balancesheet WHERE company_id = ? ORDER BY year",
        conn, params=(ticker,),
    )
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_cf(ticker):
    """Returns all cashflow rows for a ticker, sorted by year."""
    conn = _connect()
    df = pd.read_sql(
        "SELECT * FROM cashflow WHERE company_id = ? ORDER BY year",
        conn, params=(ticker,),
    )
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_sectors():
    """Returns the sectors table (company_id, broad_sector, sub_sector, etc)."""
    conn = _connect()
    df = pd.read_sql("SELECT * FROM sectors", conn)
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_peers(group_name):
    """Returns peer_groups membership rows for a given peer group name."""
    conn = _connect()
    df = pd.read_sql(
        "SELECT * FROM peer_groups WHERE peer_group_name = ?",
        conn, params=(group_name,),
    )
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_valuation(ticker):
    """
    Returns the valuation_summary row for a ticker.
    NOTE: the 'valuation' table is a Day 26 deliverable (src/analytics/valuation.py)
    and does not exist yet as of Day 22 - this function will raise a
    clear, informative error until Day 26 populates it, rather than
    silently returning something misleading.
    """
    conn = _connect()
    try:
        df = pd.read_sql(
            "SELECT * FROM valuation WHERE company_id = ?",
            conn, params=(ticker,),
        )
    except pd.errors.DatabaseError as e:
        conn.close()
        raise RuntimeError(
            "valuation table does not exist yet - it is populated by src/analytics/valuation.py (Day 26)"
        ) from e
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_home_summary(year=None):
    """
    Day 23: aggregates the 6 Home screen KPI tiles.
    If year is given, filters to that specific fiscal year; otherwise
    uses each company's latest available year (consistent with how we've
    handled 'latest year' throughout Sprints 2-3).
    """
    conn = _connect()

    if year is not None:
        year_filter = f"= '{year}-03'"  # dashboard year selector uses plain years (2019-2024); data uses fiscal-year-end format
    else:
        year_filter = None

    if year_filter:
        query = f"""
            SELECT fr.company_id, fr.return_on_equity_pct, fr.debt_to_equity,
                   fr.revenue_cagr_5yr, mc.pe_ratio
            FROM financial_ratios fr
            LEFT JOIN market_cap mc ON mc.company_id = fr.company_id AND mc.year = fr.year
            WHERE fr.year {year_filter}
        """
    else:
        query = """
            SELECT fr.company_id, fr.return_on_equity_pct, fr.debt_to_equity,
                   fr.revenue_cagr_5yr, mc.pe_ratio
            FROM financial_ratios fr
            LEFT JOIN market_cap mc ON mc.company_id = fr.company_id AND mc.year = fr.year
            WHERE fr.year = (
                SELECT MAX(year) FROM financial_ratios fr2
                WHERE fr2.company_id = fr.company_id AND fr2.year != 'TTM'
            )
        """

    df = pd.read_sql(query, conn)
    conn.close()

    # Exclude known DATA_SOURCE_ISSUE companies (understated equity/reserves,
    # see Sprint 2 Day 13 / Sprint 3 known_exceptions) from the average ROE -
    # a mean (unlike median) is highly sensitive to their extreme values
    # (BEL 4744%, HAL 3816%, INDIGO 892%), which would badly mislead a
    # dashboard summary tile.
    KNOWN_BAD_ROE_COMPANIES = {"BEL", "HAL", "INDIGO", "LT", "PNB"}
    clean_roe = df[~df["company_id"].isin(KNOWN_BAD_ROE_COMPANIES)]["return_on_equity_pct"]

    return {
        "avg_roe": clean_roe.mean(),
        "median_pe": df["pe_ratio"].median(),
        "median_de": df["debt_to_equity"].median(),
        "total_companies": df["company_id"].nunique(),
        "median_revenue_cagr_5yr": df["revenue_cagr_5yr"].median(),
        "debt_free_count": (df["debt_to_equity"] == 0).sum(),
    }


@st.cache_data(ttl=600)
def get_top5_by_composite_score():
    """
    Day 23: top 5 companies by the Sprint 3 sector-relative composite
    score (final_composite_score), NOT the simpler Sprint 2
    composite_quality_score column - the latter lacks the known-bad-data
    sanitization (BEL/HAL/INDIGO/LT/PNB), so using it directly would
    surface companies with broken ROE data as false "top performers"
    on the dashboard. Reuses the same scoring pipeline as the screener.
    """
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "screener"))
    from engine import load_screener_universe
    from composite_score import compute_scores_for_universe

    df = load_screener_universe()
    df = compute_scores_for_universe(df)
    df = df.sort_values("final_composite_score", ascending=False)
    return df[["company_id", "final_composite_score"]].head(5).reset_index(drop=True)