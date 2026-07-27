"""
05_trends.py
------------
Day 25 deliverable: Trend Analysis screen. Company search, multi-metric
selector (overlay up to 3 metrics), 10-year line chart with YoY % change
annotations.
"""
import streamlit as st
import plotly.graph_objects as go
import sys
import os
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "utils"))
from db import get_companies, get_ratios, get_pl, search_companies

st.set_page_config(page_title="Trend Analysis", layout="wide")
st.title("Trend Analysis")

search_text = st.text_input("Search by company name or ticker", "")
matches = search_companies(search_text) if search_text else get_companies()[["company_id", "company_name"]]

if matches.empty:
    st.warning("Ticker not found - please try another")
    st.stop()

options = [f"{row['company_id']} - {row['company_name']}" for _, row in matches.iterrows()]
selected = st.selectbox("Select a company", options)
selected_ticker = selected.split(" - ")[0]

METRIC_OPTIONS = {
    "Sales (Cr)": ("pl", "sales"),
    "Net Profit (Cr)": ("pl", "net_profit"),
    "ROE (%)": ("ratios", "return_on_equity_pct"),
    "ROCE (%)": ("ratios", "return_on_capital_employed_pct"),
    "Net Profit Margin (%)": ("ratios", "net_profit_margin_pct"),
    "D/E": ("ratios", "debt_to_equity"),
    "Free Cash Flow (Cr)": ("ratios", "free_cash_flow_cr"),
}

selected_metrics = st.multiselect(
    "Select up to 3 metrics to overlay", list(METRIC_OPTIONS.keys()),
    default=["Sales (Cr)"], max_selections=3,
)

if not selected_metrics:
    st.info("Select at least one metric to see the trend chart")
    st.stop()

pl = get_pl(selected_ticker)
pl = pl[pl["year"] != "TTM"].tail(10)
ratios = get_ratios(selected_ticker)
ratios = ratios[ratios["year"] != "TTM"].tail(10)

# Each metric gets its own y-axis (yaxis, yaxis2, yaxis3) since metrics
# like Sales (Cr, ~200,000) and ROE (%, ~50) are on wildly different
# scales - plotting them on one shared axis squashes the smaller-scale
# metric flat and makes its annotations unreadable.
fig = go.Figure()
axis_colors = ["#2563eb", "#dc2626", "#16a34a"]
layout_updates = {}

for i, metric_label in enumerate(selected_metrics):
    source, col = METRIC_OPTIONS[metric_label]
    df = pl if source == "pl" else ratios

    if df.empty or col not in df.columns:
        continue

    values = df[col]
    years = df["year"]

    yoy_pct = values.pct_change() * 100
    text_labels = [f"{v:,.1f}" + (f" ({yoy:+.1f}%)" if pd.notna(yoy) else "") for v, yoy in zip(values, yoy_pct)]

    axis_name = "y" if i == 0 else f"y{i + 1}"
    fig.add_trace(go.Scatter(
        x=years, y=values, name=metric_label, mode="lines+markers+text",
        text=text_labels, textposition="top center",
        yaxis=axis_name, line=dict(color=axis_colors[i % 3]),
    ))

    axis_key = "yaxis" if i == 0 else f"yaxis{i + 1}"
    layout_updates[axis_key] = dict(
        title=dict(text=metric_label, font=dict(color=axis_colors[i % 3])),
        tickfont=dict(color=axis_colors[i % 3]),
        overlaying="y" if i > 0 else None,
        side="right" if i == 1 else ("left" if i == 0 else "right"),
        anchor="free" if i == 2 else "x",
        position=0.95 if i == 2 else None,
    )

fig.update_layout(height=550, xaxis_title="Fiscal Year", xaxis_type="category", **layout_updates)
st.plotly_chart(fig, use_container_width=True)