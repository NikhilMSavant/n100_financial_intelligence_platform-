"""
01_home.py
----------
Day 23 deliverable: Home screen - 6 KPI tiles, sector breakdown donut
chart, top-5 companies by composite score, year selector.
"""
import streamlit as st
import plotly.express as px
import sys
import os
import sqlite3
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "utils"))
from db import get_home_summary, get_sectors, get_top5_by_composite_score

st.set_page_config(page_title="Home", layout="wide")
st.title("Home")

# --- Year selector (sidebar) ---
year_options = ["Latest"] + [str(y) for y in range(2024, 2018, -1)]
selected_year = st.sidebar.selectbox("Select year", year_options, index=0)
year_param = None if selected_year == "Latest" else int(selected_year)

# --- 6 KPI tiles ---
summary = get_home_summary(year=year_param)

col1, col2, col3, col4, col5, col6 = st.columns(6)
col1.metric("Average ROE", f"{summary['avg_roe']:.1f}%" if pd.notna(summary['avg_roe']) else "N/A")
col2.metric("Median P/E", f"{summary['median_pe']:.1f}" if pd.notna(summary['median_pe']) else "N/A")
col3.metric("Median D/E", f"{summary['median_de']:.2f}" if pd.notna(summary['median_de']) else "N/A")
col4.metric("Total Companies", summary["total_companies"])
col5.metric("Median Rev CAGR 5yr", f"{summary['median_revenue_cagr_5yr']:.1f}%" if pd.notna(summary['median_revenue_cagr_5yr']) else "N/A")
col6.metric("Debt-Free Companies", summary["debt_free_count"])

st.divider()

# --- Sector breakdown donut chart ---
st.subheader("Sector Breakdown")
sectors_df = get_sectors()
sector_counts = sectors_df["broad_sector"].value_counts().reset_index()
sector_counts.columns = ["sector", "count"]

fig = px.pie(sector_counts, names="sector", values="count", hole=0.5)
fig.update_layout(height=450)
st.plotly_chart(fig, use_container_width=True)

st.divider()

# --- Top 5 companies by composite quality score ---
st.subheader("Top 5 Companies by Composite Quality Score")
top5 = get_top5_by_composite_score()

KNOWN_DATA_ISSUE_COMPANIES = {"BEL", "HAL", "INDIGO", "LT", "PNB"}
top5_display = top5.copy()
top5_display["company_id"] = top5_display["company_id"].apply(
    lambda cid: f"{cid} *" if cid in KNOWN_DATA_ISSUE_COMPANIES else cid
)
st.dataframe(top5_display, use_container_width=True, hide_index=True)

if top5["company_id"].isin(KNOWN_DATA_ISSUE_COMPANIES).any():
    st.caption(
        "* This company's ROE/ROCE data has a known source-data issue "
        "(understated equity/reserves) and is excluded from those two "
        "sub-scores; its other metrics (margins, growth, leverage, cash "
        "quality) are unaffected and contribute normally."
    )