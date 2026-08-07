"""pages/06_sectors.py — Sprint 4 / Day 25"""
import os
import sys
import streamlit as st
import plotly.express as px

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "utils"))
from db import get_companies, get_ratios, get_valuation

st.set_page_config(page_title="Sector Analysis | Nifty 100 Analytics", layout="wide")
st.title("🏭 Sector Analysis")

import sqlite3
import pandas as pd
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))

companies = get_companies()
ratios = get_ratios()
idx = ratios.groupby("company_id")["year"].idxmax()
latest = ratios.loc[idx]
mc = get_valuation()
mc_idx = mc.groupby("company_id")["year"].idxmax()
mc_latest = mc.loc[mc_idx]

_conn = sqlite3.connect(os.path.join(ROOT, "db", "nifty100.db"))
pl_latest = pd.read_sql("SELECT company_id, year, sales FROM profitandloss", _conn)
pl_idx = pl_latest.groupby("company_id")["year"].idxmax()
pl_latest = pl_latest.loc[pl_idx][["company_id", "sales"]]
_conn.close()

df = latest.merge(companies, on="company_id", how="left").merge(
    mc_latest[["company_id", "market_cap_crore"]], on="company_id", how="left").merge(
    pl_latest, on="company_id", how="left")

sectors = sorted(df["broad_sector"].dropna().unique().tolist())
sector = st.selectbox("Sector", options=["All"] + sectors)
plot_df = df if sector == "All" else df[df.broad_sector == sector]

st.subheader("Revenue vs ROE (bubble = Market Cap)")
fig = px.scatter(
    plot_df, x="sales", y="return_on_equity_pct", size="market_cap_crore",
    color="sub_sector", hover_name="company_name",
    labels={"sales": "Revenue (Cr)", "return_on_equity_pct": "ROE (%)"},
    size_max=45,
)
fig.update_layout(height=500)
st.plotly_chart(fig, use_container_width=True)

st.subheader("Sector median KPIs")
medians = df.groupby("broad_sector")[
    ["return_on_equity_pct", "debt_to_equity", "net_profit_margin_pct", "revenue_cagr_5yr"]
].median().reset_index()
fig2 = px.bar(medians, x="broad_sector", y="return_on_equity_pct", title="Median ROE by sector")
fig2.update_layout(height=400, xaxis_tickangle=-40)
st.plotly_chart(fig2, use_container_width=True)
