import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from utils.db import get_companies, get_ratios, get_pl

st.set_page_config(page_title="Company Profile", layout="wide")
st.title("Company Profile")

companies = get_companies()
query = st.text_input("Search company name or ticker").strip().upper()
matches = companies[companies["id"].str.contains(query) | companies["company_name"].str.upper().str.contains(query)] if query else companies
ticker = st.selectbox("Select company", matches["id"].tolist()) if not matches.empty else None

if ticker is None:
    st.warning("Ticker not found — please try another")
else:
    row = companies[companies["id"] == ticker].iloc[0]
    st.header(f"{row['company_name']} ({ticker})")
    st.caption(f"{row['broad_sector']} · {row['sub_sector']}")
    st.write(row.get("about_company") or "")

    ratios = get_ratios(ticker)
    if ratios.empty:
        st.info("No ratio history available for this ticker.")
    else:
        latest = ratios.dropna(subset=["net_profit_margin_pct"]).iloc[-1] if ratios["net_profit_margin_pct"].notna().any() else ratios.iloc[-1]
        c1, c2, c3, c4, c5, c6 = st.columns(6)
        c1.metric("ROE", f"{latest['return_on_equity_pct']:.1f}%" if latest['return_on_equity_pct'] == latest['return_on_equity_pct'] else "N/A")
        c2.metric("ROCE", f"{latest['return_on_capital_employed_pct']:.1f}%" if latest['return_on_capital_employed_pct'] == latest['return_on_capital_employed_pct'] else "N/A")
        c3.metric("Net Profit Margin", f"{latest['net_profit_margin_pct']:.1f}%" if latest['net_profit_margin_pct'] == latest['net_profit_margin_pct'] else "N/A")
        c4.metric("D/E", f"{latest['debt_to_equity']:.2f}" if latest['debt_to_equity'] == latest['debt_to_equity'] else "N/A")
        c5.metric("Revenue CAGR 5yr", f"{latest['revenue_cagr_5yr']:.1f}%" if latest['revenue_cagr_5yr'] == latest['revenue_cagr_5yr'] else "N/A")
        c6.metric("FCF (Cr)", f"₹{latest['free_cash_flow_cr']:.0f}" if latest['free_cash_flow_cr'] == latest['free_cash_flow_cr'] else "N/A")

        pl = get_pl(ticker)
        if not pl.empty:
            fig1 = go.Figure()
            fig1.add_bar(x=pl["year"], y=pl["sales"], name="Revenue")
            fig1.add_bar(x=pl["year"], y=pl["net_profit"], name="Net Profit")
            fig1.update_layout(barmode="group", title="10-Year Revenue & Net Profit (₹ Cr)")
            st.plotly_chart(fig1, use_container_width=True)

        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(x=ratios["year"], y=ratios["return_on_equity_pct"], name="ROE %", yaxis="y1"))
        fig2.add_trace(go.Scatter(x=ratios["year"], y=ratios["return_on_capital_employed_pct"], name="ROCE %", yaxis="y1"))
        fig2.update_layout(title="ROE vs ROCE trend")
        st.plotly_chart(fig2, use_container_width=True)

    st.subheader("Pros & Cons")
    import sqlite3
    conn = sqlite3.connect(str(pathlib.Path(__file__).resolve().parent.parent.parent.parent / "data" / "nifty100.db"))
    pc = conn.execute("SELECT pros, cons FROM prosandcons WHERE company_id=?", (ticker,)).fetchall()
    # Auto-generated pros/cons (Sprint 5) supplement sparse source data:
    import pandas as pd
    gen_path = pathlib.Path(__file__).resolve().parent.parent.parent.parent / "output" / "pros_cons_generated.csv"
    if gen_path.exists():
        gen = pd.read_csv(gen_path)
        gen = gen[gen.company_id == ticker]
        colp, colc = st.columns(2)
        with colp:
            for _, r in gen[gen.type == "pro"].iterrows():
                st.success(f"✅ {r['text']}")
        with colc:
            for _, r in gen[gen.type == "con"].iterrows():
                st.error(f"❌ {r['text']}")
