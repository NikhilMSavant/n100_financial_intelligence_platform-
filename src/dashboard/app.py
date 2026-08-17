"""Nifty 100 Financial Intelligence Platform — Streamlit dashboard entry point.
Run with: streamlit run src/dashboard/app.py
"""
import streamlit as st

st.set_page_config(page_title="Nifty 100 Analytics", layout="wide", initial_sidebar_state="expanded")

st.sidebar.title("Nifty 100 Financial Intelligence")
st.sidebar.caption("Navigate using the pages listed above (Streamlit auto-discovers pages/ directory).")

st.title("Nifty 100 Financial Intelligence Platform")
st.markdown("""
Use the sidebar to navigate between the 8 screens:

1. **Home** — universe overview, sector breakdown, top companies
2. **Company Profile** — search any of 92 companies, KPI tiles, 10-year charts
3. **Screener** — 10 sliders + 6 presets, live results, CSV export
4. **Peer Comparison** — radar chart + side-by-side table for 11 peer groups
5. **Trend Analysis** — multi-metric overlay with YoY annotations
6. **Sector Analysis** — bubble chart + sector median KPIs
7. **Capital Allocation Map** — treemap of the 8 capital allocation patterns
8. **Annual Reports** — BSE annual report links per company/year

All data is served from the local `nifty100.db` SQLite database built by the Sprint 1 ETL pipeline.
""")
