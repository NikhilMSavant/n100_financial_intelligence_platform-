"""pages/02_profile.py — Sprint 4 / Day 23"""
import os
import sys
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "utils"))
from db import get_companies, get_ratios, get_pl, get_pros_cons

st.set_page_config(page_title="Company Profile | Nifty 100 Analytics", layout="wide")
st.title("🏢 Company Profile")

companies = get_companies()
options = (companies["company_id"] + " — " + companies["company_name"].fillna("")).tolist()
choice = st.selectbox("Search by company name or ticker", options=[""] + options)
ticker = choice.split(" — ")[0] if choice else None

if not ticker:
    st.info("Start typing a company name or ticker above to see its profile.")
    st.stop()

row = companies[companies.company_id == ticker]
if row.empty:
    st.error("Ticker not found — please try another")
    st.stop()
row = row.iloc[0]

st.header(f"{row.company_name} ({ticker})")
st.caption(f"{row.broad_sector or 'N/A'} · {row.sub_sector or 'N/A'} · NSE: {ticker}")
if row.about_company:
    st.write(row.about_company)

ratios = get_ratios(ticker=ticker).sort_values("year")
pl = get_pl(ticker)

if ratios.empty:
    st.warning("No ratio history available for this company.")
    st.stop()

latest = ratios.iloc[-1]
c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("ROE", f"{latest.return_on_equity_pct:.1f}%" if latest.return_on_equity_pct is not None else "N/A")
c2.metric("ROCE", f"{latest.return_on_capital_employed_pct:.1f}%" if latest.return_on_capital_employed_pct is not None else "N/A")
c3.metric("Net Profit Margin", f"{latest.net_profit_margin_pct:.1f}%" if latest.net_profit_margin_pct is not None else "N/A")
c4.metric("D/E", f"{latest.debt_to_equity:.2f}" if latest.debt_to_equity is not None else "N/A")
c5.metric("Revenue CAGR 5yr", f"{latest.revenue_cagr_5yr:.1f}%" if latest.revenue_cagr_5yr is not None else "N/A")
c6.metric("FCF (latest yr, Cr)", f"{latest.free_cash_flow_cr:,.0f}" if latest.free_cash_flow_cr is not None else "N/A")

st.divider()
col1, col2 = st.columns(2)
with col1:
    st.subheader("Revenue & Net Profit (10yr)")
    if not pl.empty:
        fig = go.Figure()
        fig.add_bar(x=pl.year, y=pl.sales, name="Revenue")
        fig.add_bar(x=pl.year, y=pl.net_profit, name="Net Profit")
        fig.update_layout(barmode="group", height=380)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No P&L data available.")

with col2:
    st.subheader("ROE vs ROCE (10yr)")
    fig2 = make_subplots(specs=[[{"secondary_y": True}]])
    fig2.add_trace(go.Scatter(x=ratios.year, y=ratios.return_on_equity_pct, name="ROE %"), secondary_y=False)
    fig2.add_trace(go.Scatter(x=ratios.year, y=ratios.return_on_capital_employed_pct, name="ROCE %"), secondary_y=True)
    fig2.update_layout(height=380)
    st.plotly_chart(fig2, use_container_width=True)

st.divider()
st.subheader("Pros & Cons")
pc = get_pros_cons(ticker=ticker)
pcol1, pcol2 = st.columns(2)
with pcol1:
    st.markdown("**Pros**")
    pros = pc[pc.type == "pro"] if not pc.empty else pc
    if len(pros):
        for _, p in pros.iterrows():
            st.success(f"✅ {p.text}")
    else:
        st.caption("No auto-generated pros above the confidence threshold.")
with pcol2:
    st.markdown("**Cons**")
    cons = pc[pc.type == "con"] if not pc.empty else pc
    if len(cons):
        for _, c in cons.iterrows():
            st.error(f"❌ {c.text}")
    else:
        st.caption("No auto-generated cons above the confidence threshold.")
