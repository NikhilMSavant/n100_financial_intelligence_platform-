"""
07_capital.py
-------------
Day 25 deliverable: Capital Allocation Map screen. Treemap of all 92
companies grouped by their latest capital allocation pattern, with
click-to-filter behavior showing the company list for a selected pattern.
"""
import streamlit as st
import plotly.express as px
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "utils"))
from db import get_companies

st.set_page_config(page_title="Capital Allocation Map", layout="wide")
st.title("Capital Allocation Map")

capital_df = pd.read_csv("output/capital_allocation.csv")

# Take each company's LATEST year only - the source CSV has one row per
# company-year, but this screen maps all 92 companies once each.
capital_df = capital_df[capital_df["year"] != "TTM"]
latest = capital_df.sort_values("year").groupby("company_id").tail(1)

companies = get_companies()
latest = latest.merge(companies[["company_id", "company_name"]], on="company_id", how="left")

total_companies_expected = get_companies()["company_id"].nunique()
n_in_treemap = latest["company_id"].nunique()
st.subheader(f"Latest Capital Allocation Pattern — {n_in_treemap} Companies")

if n_in_treemap < total_companies_expected:
    missing_companies = set(get_companies()["company_id"]) - set(latest["company_id"])
    st.caption(
        f"Note: {n_in_treemap} of {total_companies_expected} companies shown. "
        f"{', '.join(sorted(missing_companies))} excluded due to no cash flow data available in the source data."
    )

fig = px.treemap(
    latest, path=[px.Constant("All Companies"), "pattern_label", "company_id"],
    values=[1] * len(latest),
)
fig.update_layout(height=600)
st.plotly_chart(fig, use_container_width=True)

st.divider()

# --- Click-to-filter: dropdown as a reliable alternative to treemap click events ---
st.subheader("View Companies by Pattern")
selected_pattern = st.selectbox("Select a pattern", sorted(latest["pattern_label"].unique()))
pattern_companies = latest[latest["pattern_label"] == selected_pattern][["company_id", "company_name", "year", "cfo_sign", "cfi_sign", "cff_sign"]]
st.dataframe(pattern_companies, use_container_width=True, hide_index=True)