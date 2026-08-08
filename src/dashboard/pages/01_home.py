"""pages/01_home.py — Sprint 4 / Day 23"""
import os
import sys
import pandas as pd
import streamlit as st
import plotly.express as px

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "utils"))
from db import get_companies, get_ratios

st.set_page_config(page_title="Home | Nifty 100 Analytics", layout="wide")
st.title("🏠 Home")

companies = get_companies()
ratios = get_ratios()

years = sorted(ratios["year"].dropna().unique().astype(int).tolist())
default_year = years[-1] if years else 2024
year = st.sidebar.selectbox("Year", options=years, index=len(years) - 1 if years else 0)

latest = ratios[ratios["year"] == year]

col1, col2, col3, col4, col5, col6 = st.columns(6)
col1.metric("Median ROE", f"{latest['return_on_equity_pct'].median():.1f}%")
col2.metric("Median D/E", f"{latest['debt_to_equity'].median():.2f}")
col3.metric("Total Companies", f"{companies['company_id'].nunique()}")
col4.metric("Median Revenue CAGR 5yr", f"{latest['revenue_cagr_5yr'].median():.1f}%")
col5.metric("Debt-Free Companies", f"{(latest['icr_label'] == 'Debt Free').sum()}")
col6.metric("Median Net Profit Margin", f"{latest['net_profit_margin_pct'].median():.1f}%")

st.divider()

c1, c2 = st.columns([1, 1])
with c1:
    st.subheader("Sector breakdown")
    sector_counts = companies["broad_sector"].value_counts().reset_index()
    sector_counts.columns = ["broad_sector", "count"]
    fig = px.pie(sector_counts, names="broad_sector", values="count", hole=0.5)
    st.plotly_chart(fig, use_container_width=True)

with c2:
    st.subheader("Top 5 by composite quality score")
    merged = latest.merge(companies[["company_id", "company_name"]], on="company_id", how="left")
    top5 = merged.sort_values("composite_quality_score", ascending=False).head(5).copy()
    # ROE can be mathematically enormous (100s of %) for companies with a very
    # thin equity base relative to total assets -- the ratio is still correct,
    # but not a meaningful headline number. Show "N/M" for those rather than
    # a distorted figure; roe_reliable_flag is computed once in populate_ratios.py.
    top5["ROE %"] = top5.apply(
        lambda r: "N/M*" if r.get("roe_reliable_flag") == 0
        else (f"{r['return_on_equity_pct']:.1f}%" if pd.notna(r["return_on_equity_pct"]) else "N/A"),
        axis=1)
    st.dataframe(
        top5[["company_id", "company_name", "composite_quality_score", "ROE %", "debt_to_equity"]]
        .rename(columns={"composite_quality_score": "Composite Score", "debt_to_equity": "D/E"}),
        use_container_width=True, hide_index=True,
    )
    if (top5["ROE %"] == "N/M*").any():
        st.caption("*N/M = ROE not meaningful (equity base is a thin sliver of total assets)")
