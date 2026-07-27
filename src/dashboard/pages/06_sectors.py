"""
06_sectors.py
-------------
Day 25 deliverable: Sector Analysis screen. Sector dropdown, bubble chart
(X=Revenue, Y=ROE, size=Market Cap, color=sub_sector), sector median KPI
bar chart.
"""
import streamlit as st
import plotly.express as px
import sqlite3
import sys
import os
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "utils"))
from db import get_sectors

st.set_page_config(page_title="Sector Analysis", layout="wide")
st.title("Sector Analysis")

sectors_df = get_sectors()
broad_sectors = sorted(sectors_df["broad_sector"].dropna().unique())
selected_sector = st.selectbox("Select sector", broad_sectors)

conn = sqlite3.connect("db/nifty100.db")
data = pd.read_sql("""
    SELECT s.company_id, s.sub_sector, pl.sales, fr.return_on_equity_pct, mc.market_cap_crore
    FROM sectors s
    JOIN profitandloss pl ON pl.company_id = s.company_id
    JOIN financial_ratios fr ON fr.company_id = s.company_id AND fr.year = pl.year
    JOIN market_cap mc ON mc.company_id = s.company_id AND mc.year = pl.year
    WHERE s.broad_sector = ? AND pl.year = (
        SELECT MAX(year) FROM profitandloss pl2
        WHERE pl2.company_id = pl.company_id AND pl2.year != 'TTM'
    )
""", conn, params=(selected_sector,))
conn.close()

st.divider()
st.subheader(f"{selected_sector} — Revenue vs ROE (bubble size = Market Cap)")

if data.empty:
    st.info("No data available for this sector")
else:
    # Known DATA_SOURCE_ISSUE companies (Sprint 2 Day 13) excluded from
    # ROE axis distortion - same reasoning applied throughout the project
    KNOWN_BAD_ROE_COMPANIES = {"BEL", "HAL", "INDIGO", "LT", "PNB"}
    data_clean = data[~data["company_id"].isin(KNOWN_BAD_ROE_COMPANIES)]

    if data_clean.empty:
        st.info("All companies in this sector are excluded due to known data issues")
    else:
        fig = px.scatter(
            data_clean, x="sales", y="return_on_equity_pct", size="market_cap_crore",
            color="sub_sector", hover_name="company_id",
            labels={"sales": "Revenue (Cr)", "return_on_equity_pct": "ROE (%)", "market_cap_crore": "Market Cap (Cr)"},
        )
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)

        if len(data) != len(data_clean):
            excluded = set(data["company_id"]) - set(data_clean["company_id"])
            st.caption(f"Note: {', '.join(excluded)} excluded from this chart due to known ROE data issues (see Sprint 2 Day 13 findings)")

st.divider()

# --- Sector median KPI bar chart ---
st.subheader(f"{selected_sector} — Median KPIs")
conn = sqlite3.connect("db/nifty100.db")
median_data = pd.read_sql("""
    SELECT fr.return_on_equity_pct, fr.debt_to_equity, fr.net_profit_margin_pct, fr.revenue_cagr_5yr
    FROM sectors s
    JOIN financial_ratios fr ON fr.company_id = s.company_id
    WHERE s.broad_sector = ? AND fr.year = (
        SELECT MAX(year) FROM financial_ratios fr2
        WHERE fr2.company_id = fr.company_id AND fr2.year != 'TTM'
    )
""", conn, params=(selected_sector,))
conn.close()

if median_data.empty:
    st.info("No data available for this sector")
else:
    medians = {
        "ROE (%)": median_data["return_on_equity_pct"].median(),
        "D/E": median_data["debt_to_equity"].median(),
        "Net Profit Margin (%)": median_data["net_profit_margin_pct"].median(),
        "Revenue CAGR 5yr (%)": median_data["revenue_cagr_5yr"].median(),
    }
    bar_fig = px.bar(x=list(medians.keys()), y=list(medians.values()), labels={"x": "Metric", "y": "Median Value"})
    bar_fig.update_layout(height=400)
    st.plotly_chart(bar_fig, use_container_width=True)