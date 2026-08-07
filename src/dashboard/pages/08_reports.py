"""pages/08_reports.py — Sprint 4 / Day 25"""
import os
import sys
import requests
import streamlit as st

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "utils"))
from db import get_companies, get_documents

st.set_page_config(page_title="Annual Reports | Nifty 100 Analytics", layout="wide")
st.title("📄 Annual Reports")

companies = get_companies()
options = (companies["company_id"] + " — " + companies["company_name"].fillna("")).tolist()
choice = st.selectbox("Company", options=options)
ticker = choice.split(" — ")[0]

docs = get_documents(ticker)
if docs.empty:
    st.info("No annual report links on file for this company.")
    st.stop()

st.write(f"**{len(docs)} report years available**")


def check_url(url, timeout=4):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    try:
        r = requests.head(url, timeout=timeout, allow_redirects=True, headers=headers)
        if r.status_code in (403, 405):
            # server blocks HEAD or bots -- try a lightweight GET instead
            r = requests.get(url, timeout=timeout, allow_redirects=True, headers=headers, stream=True)
        return r.status_code < 400
    except Exception:
        return None  # unknown -- shown as unverified, not failed


for _, row in docs.iterrows():
    c1, c2, c3 = st.columns([1, 4, 2])
    c1.write(f"**{row.year}**")
    c2.write(row.annual_report or "—")
    if row.annual_report:
        ok = check_url(row.annual_report)
        if ok is False:
            c3.markdown(":red[Report unavailable]")
        elif ok is True:
            c3.markdown(f"[Open report]({row.annual_report})")
        else:
            c3.markdown(f"[Open report (unverified)]({row.annual_report})")
    else:
        c3.markdown(":red[Report unavailable]")
