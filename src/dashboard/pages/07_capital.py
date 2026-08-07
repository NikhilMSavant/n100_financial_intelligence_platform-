"""pages/07_capital.py — Sprint 4 / Day 25"""
import os
import sys
import streamlit as st
import plotly.express as px

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "utils"))
from db import get_companies, get_capital_allocation

st.set_page_config(page_title="Capital Allocation Map | Nifty 100 Analytics", layout="wide")
st.title("🗺️ Capital Allocation Map")

cap = get_capital_allocation()
companies = get_companies()

if cap.empty:
    st.warning("capital_allocation.csv not found — run src/analytics/populate_ratios.py first.")
    st.stop()

idx = cap.groupby("company_id")["year"].idxmax()
latest_cap = cap.loc[idx].merge(companies[["company_id", "company_name", "broad_sector"]],
                                 on="company_id", how="left")

fig = px.treemap(
    latest_cap, path=["pattern_label", "company_name"], color="pattern_label",
    hover_data=["company_id", "broad_sector"],
)
fig.update_layout(height=600)
st.plotly_chart(fig, use_container_width=True)

st.subheader("Companies by pattern")
pattern = st.selectbox("Pattern", options=sorted(latest_cap["pattern_label"].dropna().unique().tolist()))
st.dataframe(
    latest_cap[latest_cap.pattern_label == pattern][["company_id", "company_name", "broad_sector", "year"]],
    use_container_width=True, hide_index=True,
)
