import streamlit as st
import plotly.graph_objects as go
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from utils.db import get_companies, get_ratios

st.set_page_config(page_title="Trend Analysis", layout="wide")
st.title("Trend Analysis")

companies = get_companies()
ticker = st.selectbox("Company", companies["id"].tolist())
metrics = st.multiselect("Metrics (up to 3)", [
    "return_on_equity_pct", "return_on_capital_employed_pct", "net_profit_margin_pct",
    "debt_to_equity", "revenue_cagr_5yr", "pat_cagr_5yr", "free_cash_flow_cr",
], default=["return_on_equity_pct"], max_selections=3)

ratios = get_ratios(ticker)
if not ratios.empty and metrics:
    fig = go.Figure()
    for m in metrics:
        series = ratios[m]
        yoy = series.pct_change() * 100
        fig.add_trace(go.Scatter(x=ratios["year"], y=series, mode="lines+markers+text", name=m,
                                  text=[f"{v:+.1f}%" if v == v else "" for v in yoy],
                                  textposition="top center"))
    fig.update_layout(title=f"{ticker} — 10 year trend with YoY % change annotations")
    st.plotly_chart(fig, use_container_width=True)
    st.download_button("Download CSV", ratios.to_csv(index=False).encode(), f"{ticker}_trends.csv", "text/csv")
