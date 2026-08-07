"""
db.py — Sprint 4 / Day 22
Shared, cached data-access layer for the Streamlit dashboard. Every query
function is wrapped with @st.cache_data(ttl=600).
"""
import os
import sqlite3
import pandas as pd
import streamlit as st

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
DB_PATH = os.path.join(ROOT, "db", "nifty100.db")


def _conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)


@st.cache_data(ttl=600)
def get_companies():
    conn = _conn()
    df = pd.read_sql("""
        SELECT c.company_id, c.company_name, c.about_company, c.website,
               c.face_value, c.book_value, s.broad_sector, s.sub_sector,
               s.market_cap_category
        FROM companies c LEFT JOIN sectors s ON c.company_id = s.company_id
    """, conn)
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_ratios(ticker=None, year=None):
    conn = _conn()
    q = "SELECT * FROM financial_ratios WHERE 1=1"
    params = []
    if ticker:
        q += " AND company_id = ?"
        params.append(ticker)
    if year:
        q += " AND year = ?"
        params.append(year)
    df = pd.read_sql(q, conn, params=params)
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_pl(ticker):
    conn = _conn()
    df = pd.read_sql("SELECT * FROM profitandloss WHERE company_id = ? ORDER BY year", conn, params=[ticker])
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_bs(ticker):
    conn = _conn()
    df = pd.read_sql("SELECT * FROM balancesheet WHERE company_id = ? ORDER BY year", conn, params=[ticker])
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_cf(ticker):
    conn = _conn()
    df = pd.read_sql("SELECT * FROM cashflow WHERE company_id = ? ORDER BY year", conn, params=[ticker])
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_sectors():
    conn = _conn()
    df = pd.read_sql("SELECT * FROM sectors", conn)
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_peers(group_name):
    conn = _conn()
    df = pd.read_sql("SELECT * FROM peer_groups WHERE peer_group_name = ?", conn, params=[group_name])
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_peer_percentiles(group_name=None):
    conn = _conn()
    if group_name:
        df = pd.read_sql("SELECT * FROM peer_percentiles WHERE peer_group_name = ?", conn, params=[group_name])
    else:
        df = pd.read_sql("SELECT * FROM peer_percentiles", conn)
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_valuation(ticker=None):
    conn = _conn()
    q = "SELECT * FROM market_cap"
    params = []
    if ticker:
        q += " WHERE company_id = ?"
        params.append(ticker)
    df = pd.read_sql(q, conn, params=params)
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_capital_allocation():
    path = os.path.join(ROOT, "output", "capital_allocation.csv")
    if os.path.exists(path):
        return pd.read_csv(path)
    return pd.DataFrame()


@st.cache_data(ttl=600)
def get_pros_cons(ticker=None):
    path = os.path.join(ROOT, "output", "pros_cons_generated.csv")
    if not os.path.exists(path):
        return pd.DataFrame()
    df = pd.read_csv(path)
    if ticker:
        df = df[df.company_id == ticker]
    return df


@st.cache_data(ttl=600)
def get_documents(ticker):
    conn = _conn()
    df = pd.read_sql("SELECT * FROM documents WHERE company_id = ? ORDER BY year DESC", conn, params=[ticker])
    conn.close()
    return df
