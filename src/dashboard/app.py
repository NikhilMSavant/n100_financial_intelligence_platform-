"""
app.py — Sprint 4 / Day 22
Main Streamlit entry point for the Nifty 100 Analytics dashboard.
Run with: streamlit run src/dashboard/app.py
"""
import streamlit as st

st.set_page_config(
    page_title="Nifty 100 Analytics",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("📊 Nifty 100 Financial Intelligence Platform")
st.markdown(
    """
Use the sidebar to navigate between screens:

1. **Home** — market-wide summary tiles and sector breakdown
2. **Company Profile** — deep-dive on a single company
3. **Screener** — filter the universe with sliders or presets
4. **Peer Comparison** — radar chart + KPI table vs peer group
5. **Trend Analysis** — multi-metric 10-year trend lines
6. **Sector Analysis** — bubble chart + sector medians
7. **Capital Allocation Map** — treemap of the 8 capital-allocation patterns
8. **Annual Reports** — company report archive links

Data source: `db/nifty100.db` (92 Nifty 100 companies, built end-to-end by the
Sprint 1-5 ETL/analytics/NLP pipeline in this repo).
"""
)
