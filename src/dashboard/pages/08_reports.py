import streamlit as st
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from utils.db import get_companies
import sqlite3
import pandas as pd

st.set_page_config(page_title="Annual Reports", layout="wide")
st.title("Annual Reports")

companies = get_companies()
ticker = st.selectbox("Company", companies["id"].tolist())

DB = str(pathlib.Path(__file__).resolve().parent.parent.parent.parent / "data" / "nifty100.db")
conn = sqlite3.connect(DB)
docs = pd.read_sql("SELECT year, annual_report FROM documents WHERE company_id=? ORDER BY year DESC", conn, params=(ticker,))

if docs.empty:
    st.warning("No annual reports on file for this company.")
else:
    for _, r in docs.iterrows():
        col1, col2 = st.columns([1, 4])
        col1.write(f"**{r['year']}**")
        url = r["annual_report"]
        if isinstance(url, str) and url.startswith("http"):
            col2.markdown(f"[Open report]({url})")
        else:
            col2.markdown(":red[Report unavailable]")
