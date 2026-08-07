"""pages/04_peers.py — Sprint 4 / Day 24"""
import os
import sys
import numpy as np
import streamlit as st
import plotly.graph_objects as go

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "utils"))
from db import get_companies, get_ratios, get_peers, get_peer_percentiles

st.set_page_config(page_title="Peer Comparison | Nifty 100 Analytics", layout="wide")
st.title("👥 Peer Comparison")

companies = get_companies()
ratios = get_ratios()
idx = ratios.groupby("company_id")["year"].idxmax()
latest = ratios.loc[idx]

groups = sorted(get_peer_percentiles()["peer_group_name"].dropna().unique().tolist())
group = st.selectbox("Peer group", options=groups)

members = get_peers(group)
member_ids = members["company_id"].tolist()
group_latest = latest[latest.company_id.isin(member_ids)].merge(
    companies[["company_id", "company_name"]], on="company_id", how="left")

axes = ["return_on_equity_pct", "return_on_capital_employed_pct", "net_profit_margin_pct",
        "debt_to_equity", "free_cash_flow_cr", "pat_cagr_5yr", "revenue_cagr_5yr",
        "composite_quality_score"]
axes_labels = ["ROE", "ROCE", "NPM", "D/E", "FCF", "PAT CAGR 5yr", "Rev CAGR 5yr", "Composite"]

sel_ticker = st.selectbox("Company", options=member_ids)

norm = group_latest.copy()
for c in axes:
    lo, hi = norm[c].min(), norm[c].max()
    if hi == lo:
        norm[c + "_n"] = 50.0
    else:
        scaled = (norm[c] - lo) / (hi - lo) * 100
        if c == "debt_to_equity":
            scaled = 100 - scaled
        norm[c + "_n"] = scaled.fillna(scaled.median())

company_row = norm[norm.company_id == sel_ticker].iloc[0]
avg_vals = [norm[c + "_n"].mean() for c in axes]
company_vals = [company_row[c + "_n"] for c in axes]

fig = go.Figure()
fig.add_trace(go.Scatterpolar(r=company_vals + [company_vals[0]], theta=axes_labels + [axes_labels[0]],
                               fill="toself", name=sel_ticker))
fig.add_trace(go.Scatterpolar(r=avg_vals + [avg_vals[0]], theta=axes_labels + [axes_labels[0]],
                               name=f"{group} avg", line=dict(dash="dash")))
fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), height=500)
st.plotly_chart(fig, use_container_width=True)

st.subheader(f"{group} — side-by-side KPIs")
bench_ids = set(members[members.is_benchmark == 1]["company_id"])
display_cols = ["company_id", "company_name"] + axes
table = group_latest[display_cols].copy()
table.insert(0, "Benchmark", table.company_id.apply(lambda c: "⭐" if c in bench_ids else ""))
st.dataframe(table, use_container_width=True, hide_index=True)
