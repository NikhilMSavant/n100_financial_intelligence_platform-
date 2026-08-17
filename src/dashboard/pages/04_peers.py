import streamlit as st
import plotly.graph_objects as go
import sys, pathlib, sqlite3
import pandas as pd
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from utils.db import get_screener_universe

st.set_page_config(page_title="Peer Comparison", layout="wide")
st.title("Peer Comparison")

DB = str(pathlib.Path(__file__).resolve().parent.parent.parent.parent / "data" / "nifty100.db")
conn = sqlite3.connect(DB)
groups = pd.read_sql("SELECT DISTINCT peer_group_name FROM peer_groups", conn)["peer_group_name"].tolist()
group = st.selectbox("Peer group", groups)

members = pd.read_sql("SELECT * FROM peer_groups WHERE peer_group_name=?", conn, params=(group,))
universe = get_screener_universe()
grp = universe[universe.company_id.isin(members.company_id)]

RADAR_AXES = ["return_on_equity_pct", "return_on_capital_employed_pct", "net_profit_margin_pct",
              "debt_to_equity", "free_cash_flow_cr", "pat_cagr_5yr", "revenue_cagr_5yr", "composite_quality_score"]

if not grp.empty:
    ticker = st.selectbox("Company", grp.company_id.tolist())
    row = grp[grp.company_id == ticker].iloc[0]
    avg = grp[RADAR_AXES].mean()

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=[row[a] or 0 for a in RADAR_AXES], theta=RADAR_AXES, fill="toself", name=ticker))
    fig.add_trace(go.Scatterpolar(r=[avg[a] or 0 for a in RADAR_AXES], theta=RADAR_AXES, fill="toself", name="Peer avg"))
    st.plotly_chart(fig, use_container_width=True)

    benchmark = members[members.is_benchmark == 1]["company_id"].tolist()
    def highlight(r):
        return ["background-color: gold" if r["company_id"] in benchmark else "" for _ in r]
    st.dataframe(grp[["company_id", "company_name"] + RADAR_AXES].style.apply(highlight, axis=1))
