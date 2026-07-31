"""
02_profile.py
-------------
Day 23 deliverable: Company Profile screen.
Search box, company card, 6 KPI tiles, 10-year Revenue/Profit bar chart,
ROE/ROCE dual-axis line chart, pros/cons badges.
"""
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "utils"))
from db import get_companies, get_ratios, get_pl, search_companies, get_pros_cons, get_sectors
st.set_page_config(page_title="Company Profile", layout="wide")
st.title("Company Profile")

search_text = st.text_input("Search by company name or ticker", "")

if search_text:
    matches = search_companies(search_text)
else:
    matches = get_companies()[["company_id", "company_name"]]

if matches.empty:
    st.warning("Ticker not found - please try another")
    st.stop()

options = [f"{row['company_id']} - {row['company_name']}" for _, row in matches.iterrows()]
selected = st.selectbox("Select a company", options)
selected_ticker = selected.split(" - ")[0]

st.divider()

companies = get_companies()
company_row = companies[companies["company_id"] == selected_ticker]

if company_row.empty:
    st.warning("Ticker not found - please try another")
    st.stop()

company = company_row.iloc[0]

# --- Company card ---
sectors_df = get_sectors()
sector_row = sectors_df[sectors_df["company_id"] == selected_ticker]
broad_sector = sector_row.iloc[0]["broad_sector"] if not sector_row.empty else "N/A"
sub_sector = sector_row.iloc[0]["sub_sector"] if not sector_row.empty else "N/A"
nse_ticker = company.get("nse_profile", "N/A")

st.subheader(f"{company['company_name']} ({selected_ticker})")
info_col1, info_col2, info_col3 = st.columns(3)
info_col1.markdown(f"**Sector:** {broad_sector}")
info_col2.markdown(f"**Sub-sector:** {sub_sector}")
info_col3.markdown(f"**NSE Ticker:** {nse_ticker}")
st.write(company.get("about_company", "No description available"))

st.divider()

ratios = get_ratios(selected_ticker)  # all years, for the charts later
latest_ratios = ratios.iloc[-1] if not ratios.empty else None

if latest_ratios is None:
    st.warning("No financial ratio data available for this company")
else:
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("ROE", f"{latest_ratios['return_on_equity_pct']:.1f}%" if pd.notna(latest_ratios['return_on_equity_pct']) else "N/A")
    c2.metric("ROCE", f"{latest_ratios['return_on_capital_employed_pct']:.1f}%" if pd.notna(latest_ratios['return_on_capital_employed_pct']) else "N/A")
    c3.metric("Net Profit Margin", f"{latest_ratios['net_profit_margin_pct']:.1f}%" if pd.notna(latest_ratios['net_profit_margin_pct']) else "N/A")
    c4.metric("D/E", f"{latest_ratios['debt_to_equity']:.2f}" if pd.notna(latest_ratios['debt_to_equity']) else "N/A")
    c5.metric("Revenue CAGR 5yr", f"{latest_ratios['revenue_cagr_5yr']:.1f}%" if pd.notna(latest_ratios['revenue_cagr_5yr']) else "N/A")
    c6.metric("FCF (Cr)", f"{latest_ratios['free_cash_flow_cr']:,.0f}" if pd.notna(latest_ratios['free_cash_flow_cr']) else "N/A")
    st.divider()

# --- 10-year Revenue and Net Profit bar chart ---
st.subheader("Revenue & Net Profit (10-Year)")
pl = get_pl(selected_ticker)
pl = pl[pl["year"] != "TTM"].tail(10)

if pl.empty:
    st.info("No profit & loss data available for this company")
else:
    fig_bar = go.Figure()
    fig_bar.add_trace(go.Bar(x=pl["year"], y=pl["sales"], name="Revenue"))
    fig_bar.add_trace(go.Bar(x=pl["year"], y=pl["net_profit"], name="Net Profit"))
    fig_bar.update_layout(barmode="group", height=400, xaxis_title="Fiscal Year", yaxis_title="₹ Crore", xaxis_type="category")
    st.plotly_chart(fig_bar, use_container_width=True)

st.divider()
st.divider()

# --- ROE / ROCE dual-axis line chart ---
st.subheader("ROE vs ROCE (10-Year)")
ratios_chart = ratios[ratios["year"] != "TTM"].tail(10)

if ratios_chart.empty:
    st.info("No ratio history available for this company")
else:
    fig_line = go.Figure()
    fig_line.add_trace(go.Scatter(
        x=ratios_chart["year"], y=ratios_chart["return_on_equity_pct"],
        name="ROE %", mode="lines+markers", yaxis="y", line=dict(color="#2563eb"),
    ))
    fig_line.add_trace(go.Scatter(
        x=ratios_chart["year"], y=ratios_chart["return_on_capital_employed_pct"],
        name="ROCE %", mode="lines+markers", yaxis="y2", line=dict(color="#dc2626"),
    ))
    fig_line.update_layout(
        height=400, xaxis_title="Fiscal Year", xaxis_type="category",
        yaxis=dict(title=dict(text="ROE %", font=dict(color="#2563eb")), tickfont=dict(color="#2563eb")),
        yaxis2=dict(title=dict(text="ROCE %", font=dict(color="#dc2626")), tickfont=dict(color="#dc2626"),
                    overlaying="y", side="right"),
    )
    st.plotly_chart(fig_line, use_container_width=True)

st.divider()

# --- Pros and Cons badges ---
st.subheader("Pros & Cons")
pros_cons = get_pros_cons(selected_ticker)

if pros_cons.empty:
    st.info("No pros/cons data available for this company")
else:
    # Some companies (e.g. INFY) have multiple pros/cons rows, not just
    # one - combine all rows' text rather than silently showing only
    # the first (found during Day 27 QA testing).
    all_pros = "\n".join(str(v) for v in pros_cons["pros"].dropna())
    all_cons = "\n".join(str(v) for v in pros_cons["cons"].dropna())

    col_pros, col_cons = st.columns(2)
    with col_pros:
        st.markdown("**Pros**")
        for line in all_pros.split("\n"):
            if line.strip():
                st.success(f"✅ {line.strip()}")
    with col_cons:
        st.markdown("**Cons**")
        for line in all_cons.split("\n"):
            if line.strip():
                st.error(f"❌ {line.strip()}")
