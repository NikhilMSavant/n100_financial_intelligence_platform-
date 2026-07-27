"""
04_peers.py
-----------
Day 24 deliverable: Peer Comparison screen. Peer group dropdown, radar
chart (company vs peer average), side-by-side KPI table with benchmark
highlighting.
"""
import streamlit as st
import plotly.graph_objects as go
import sqlite3
import sys
import os
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "utils"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "analytics"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "screener"))

from db import get_peers, get_companies
from radar import build_radar_dataframe, RADAR_AXES

st.set_page_config(page_title="Peer Comparison", layout="wide")
st.title("Peer Comparison")

# --- Peer group dropdown ---
conn = sqlite3.connect("db/nifty100.db")
peer_groups = pd.read_sql("SELECT DISTINCT peer_group_name FROM peer_groups ORDER BY peer_group_name", conn)["peer_group_name"].tolist()
conn.close()

selected_group = st.selectbox("Select peer group", peer_groups)

members = get_peers(selected_group)
companies = get_companies()
members = members.merge(companies[["company_id", "company_name"]], on="company_id", how="left")

selected_company = st.selectbox("Select company for radar comparison", members["company_id"].tolist())

st.divider()

# --- Radar chart: selected company vs peer group average ---
st.subheader(f"{selected_company} vs {selected_group} Average")

radar_df = build_radar_dataframe()
axis_cols = [f"axis_{a}" for a in RADAR_AXES]

company_row = radar_df[radar_df["company_id"] == selected_company]
if company_row.empty:
    st.warning("No radar data available for this company")
else:
    company_values = [company_row.iloc[0][c] for c in axis_cols]
    peer_df = radar_df[radar_df["company_id"].isin(members["company_id"])]
    peer_avg_values = [peer_df[c].mean() for c in axis_cols]

    company_values_clean = [0 if pd.isna(v) else v for v in company_values]
    peer_avg_clean = [0 if pd.isna(v) else v for v in peer_avg_values]

    angles = list(range(len(RADAR_AXES)))
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=company_values_clean + [company_values_clean[0]],
                                    theta=RADAR_AXES + [RADAR_AXES[0]],
                                    fill="toself", name=selected_company))
    fig.add_trace(go.Scatterpolar(r=peer_avg_clean + [peer_avg_clean[0]],
                                    theta=RADAR_AXES + [RADAR_AXES[0]],
                                    name=f"{selected_group} avg", line=dict(dash="dash")))
    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), height=500)
    st.plotly_chart(fig, use_container_width=True)


st.divider()

# --- Side-by-side KPI table with benchmark highlighting ---
st.subheader(f"{selected_group} — All Members")

conn = sqlite3.connect("db/nifty100.db")
percentile_rows = pd.read_sql("""
    SELECT company_id, metric, value
    FROM peer_percentiles
    WHERE peer_group_name = ?
""", conn, params=(selected_group,))
conn.close()

pivot = percentile_rows.pivot(index="company_id", columns="metric", values="value").reset_index()
pivot = pivot.merge(members[["company_id", "company_name", "is_benchmark"]], on="company_id", how="left")

# Reorder so name/benchmark come first
cols = ["company_id", "company_name"] + [c for c in pivot.columns if c not in ("company_id", "company_name", "is_benchmark")]
display_table = pivot[cols].copy()

def highlight_benchmark(row):
    is_bench = pivot.loc[pivot["company_id"] == row["company_id"], "is_benchmark"].iloc[0]
    return ["background-color: #FFD966" if is_bench == 1 else "" for _ in row]

st.dataframe(display_table.style.apply(highlight_benchmark, axis=1), use_container_width=True, hide_index=True)