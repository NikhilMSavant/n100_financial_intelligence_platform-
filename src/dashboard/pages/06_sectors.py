import streamlit as st
import plotly.express as px
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from utils.db import get_screener_universe

st.set_page_config(page_title="Sector Analysis", layout="wide")
st.title("Sector Analysis")

universe = get_screener_universe()
sector = st.selectbox("Sector", ["All"] + sorted(universe["broad_sector"].dropna().unique().tolist()))
df = universe if sector == "All" else universe[universe.broad_sector == sector]

fig = px.scatter(df, x="sales", y="return_on_equity_pct", size="market_cap_crore",
                  color="sub_sector", hover_name="company_name",
                  labels={"sales": "Revenue (₹ Cr)", "return_on_equity_pct": "ROE %"})
st.plotly_chart(fig, use_container_width=True)

st.subheader("Sector median KPIs")
med = universe.groupby("broad_sector")[["return_on_equity_pct", "pe_ratio", "debt_to_equity"]].median().reset_index()
fig2 = px.bar(med, x="broad_sector", y="return_on_equity_pct", title="Median ROE by sector")
st.plotly_chart(fig2, use_container_width=True)
