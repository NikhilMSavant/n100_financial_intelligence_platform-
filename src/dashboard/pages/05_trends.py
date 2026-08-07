"""pages/05_trends.py — Sprint 4 / Day 25"""
import os
import sys
import pandas as pd
import streamlit as st
import plotly.graph_objects as go

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "utils"))
from db import get_companies, get_ratios

st.set_page_config(page_title="Trend Analysis | Nifty 100 Analytics", layout="wide")
st.title("📈 Trend Analysis")

companies = get_companies()
options = (companies["company_id"] + " — " + companies["company_name"].fillna("")).tolist()
choice = st.selectbox("Company", options=options)
ticker = choice.split(" — ")[0]

METRIC_CHOICES = {
    "ROE %": "return_on_equity_pct", "ROCE %": "return_on_capital_employed_pct",
    "Net Profit Margin %": "net_profit_margin_pct", "D/E": "debt_to_equity",
    "Revenue CAGR 5yr %": "revenue_cagr_5yr", "PAT CAGR 5yr %": "pat_cagr_5yr",
    "FCF (Cr)": "free_cash_flow_cr", "Composite Score": "composite_quality_score",
}
selected = st.multiselect("Metrics to overlay (up to 3)", options=list(METRIC_CHOICES.keys()),
                           default=["ROE %"], max_selections=3)

ratios = get_ratios(ticker=ticker).sort_values("year")
if ratios.empty:
    st.warning("No data available for this company.")
    st.stop()

fig = go.Figure()
for label in selected:
    col = METRIC_CHOICES[label]
    y = ratios[col]
    fig.add_trace(go.Scatter(x=ratios.year, y=y, mode="lines+markers", name=label))
    yoy = y.pct_change() * 100
    for xi, yi, chg in zip(ratios.year, y, yoy):
        if pd.notna(chg) and pd.notna(yi):
            fig.add_annotation(x=xi, y=yi, text=f"{chg:+.0f}%", showarrow=False, yshift=12, font=dict(size=9))

fig.update_layout(height=500, xaxis_title="Fiscal Year")
st.plotly_chart(fig, use_container_width=True)
