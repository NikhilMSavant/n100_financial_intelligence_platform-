import streamlit as st
import plotly.express as px
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from utils.db import get_companies, get_screener_universe

st.set_page_config(page_title="Home", layout="wide")
st.title("Nifty 100 — Overview")

year = st.sidebar.select_slider("Year", options=list(range(2019, 2025)), value=2024)

universe = get_screener_universe()
companies = get_companies()

c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("Average ROE", f"{universe['return_on_equity_pct'].mean():.1f}%")
c2.metric("Median P/E", f"{universe['pe_ratio'].median():.1f}x")
c3.metric("Median D/E", f"{universe['debt_to_equity'].median():.2f}")
c4.metric("Total Companies", f"{len(companies)}")
c5.metric("Median Revenue CAGR 5yr", f"{universe['revenue_cagr_5yr'].median():.1f}%")
c6.metric("Debt-Free Companies", f"{(universe['debt_to_equity'] == 0).sum()}")

st.subheader("Sector breakdown")
sector_counts = companies["broad_sector"].value_counts().reset_index()
sector_counts.columns = ["broad_sector", "count"]
fig = px.pie(sector_counts, names="broad_sector", values="count", hole=0.5)
st.plotly_chart(fig, use_container_width=True)

st.subheader("Top 5 by composite quality score")
top5 = universe.sort_values("composite_quality_score", ascending=False).head(5)
st.dataframe(top5[["company_id", "company_name", "broad_sector", "composite_quality_score"]])
