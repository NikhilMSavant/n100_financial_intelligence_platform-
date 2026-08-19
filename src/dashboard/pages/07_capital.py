import streamlit as st
import plotly.express as px
import pandas as pd
import pathlib

st.set_page_config(page_title="Capital Allocation Map", layout="wide")
st.title("Capital Allocation Map")

path = pathlib.Path(__file__).resolve().parent.parent.parent.parent / "output" / "capital_allocation.csv"
if not path.exists():
    st.warning("Run src/analytics/populate_ratios.py first to generate capital_allocation.csv")
else:
    df = pd.read_csv(path)
    # only rows with an actual pattern (excludes snapshots with no matching cash-flow data)
    df = df[df["pattern_label"].notna()]
    latest = df.sort_values("year").groupby("company_id").tail(1)

    fig = px.treemap(latest, path=["pattern_label", "company_id"], title="92 companies by capital allocation pattern")
    st.plotly_chart(fig, use_container_width=True)

    pattern = st.selectbox("Drill into a pattern", sorted(latest["pattern_label"].unique()))
    st.dataframe(latest[latest.pattern_label == pattern][["company_id", "year", "cfo_sign", "cfi_sign", "cff_sign"]])