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