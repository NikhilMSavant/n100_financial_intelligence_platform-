"""Shared, cached data-loader functions for the Streamlit dashboard.
Every query function is wrapped with @st.cache_data(ttl=600) per spec."""
import sqlite3
import pathlib
import pandas as pd
import streamlit as st

DB_PATH = str(pathlib.Path(__file__).resolve().parent.parent.parent.parent / "data" / "nifty100.db")


def _conn():
    return sqlite3.connect(DB_PATH)


@st.cache_data(ttl=600)
def get_companies():
    with _conn() as c:
        return pd.read_sql("""
            SELECT co.id, co.company_name, co.about_company, co.roe_percentage, co.roce_percentage,
                   s.broad_sector, s.sub_sector, s.market_cap_category
            FROM companies co LEFT JOIN sectors s ON co.id = s.company_id
        """, c)


@st.cache_data(ttl=600)
def get_ratios(ticker: str, year: str = None):
    with _conn() as c:
        if year:
            return pd.read_sql("SELECT * FROM financial_ratios WHERE company_id=? AND year=?", c, params=(ticker, year))
        return pd.read_sql("SELECT * FROM financial_ratios WHERE company_id=? ORDER BY year", c, params=(ticker,))


@st.cache_data(ttl=600)
def get_pl(ticker: str):
    with _conn() as c:
        return pd.read_sql("SELECT * FROM profitandloss WHERE company_id=? ORDER BY year", c, params=(ticker,))


@st.cache_data(ttl=600)
def get_bs(ticker: str):
    with _conn() as c:
        return pd.read_sql("SELECT * FROM balancesheet WHERE company_id=? ORDER BY year", c, params=(ticker,))


@st.cache_data(ttl=600)
def get_cf(ticker: str):
    with _conn() as c:
        return pd.read_sql("SELECT * FROM cashflow WHERE company_id=? ORDER BY year", c, params=(ticker,))


@st.cache_data(ttl=600)
def get_sectors():
    with _conn() as c:
        return pd.read_sql("SELECT * FROM sectors", c)


@st.cache_data(ttl=600)
def get_peers(group_name: str):
    with _conn() as c:
        return pd.read_sql("SELECT * FROM peer_groups WHERE peer_group_name=?", c, params=(group_name,))


@st.cache_data(ttl=600)
def get_valuation(ticker: str):
    import pathlib as _p
    path = _p.Path(__file__).resolve().parent.parent.parent.parent / "output" / "valuation_summary.xlsx"
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_excel(path)
    return df[df.company_id == ticker]


@st.cache_data(ttl=600)
def get_screener_universe():
    """Latest-year financial_ratios + market_cap + sector, one row per company (for the screener screen)."""
    import sys
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent.parent))
    from screener.engine import load_latest_universe
    with _conn() as c:
        return load_latest_universe(c)
