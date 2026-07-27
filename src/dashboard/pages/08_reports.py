"""
08_reports.py
-------------
Day 25 deliverable: Annual Reports screen. Company search, list of
available annual report years with clickable BSE PDF links, red
"Report unavailable" badge if a URL returns 404 or doesn't resolve.
"""
import streamlit as st
import sqlite3
import requests
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "utils"))
from db import get_companies, search_companies

st.set_page_config(page_title="Annual Reports", layout="wide")
st.title("Annual Reports")

search_text = st.text_input("Search by company name or ticker", "")
matches = search_companies(search_text) if search_text else get_companies()[["company_id", "company_name"]]

if matches.empty:
    st.warning("Ticker not found - please try another")
    st.stop()

options = [f"{row['company_id']} - {row['company_name']}" for _, row in matches.iterrows()]
selected = st.selectbox("Select a company", options)
selected_ticker = selected.split(" - ")[0]

st.divider()

conn = sqlite3.connect("db/nifty100.db")
reports = conn.execute(
    "SELECT year, annual_report FROM documents WHERE company_id = ? ORDER BY year DESC",
    (selected_ticker,),
).fetchall()
conn.close()

if not reports:
    st.info("No annual report records available for this company")
    st.stop()

check_live = st.checkbox("Check links for availability (may take a moment)", value=False)


def is_url_reachable(url):
    """
    Uses a browser-like User-Agent since BSE's servers return 403
    Forbidden to requests without one, which would otherwise cause every
    genuinely working report link to be incorrectly flagged as
    unavailable (confirmed by direct testing - same URL returns 403
    with no User-Agent, 200 with one).
    """
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        resp = requests.head(url, timeout=5, allow_redirects=True, headers=headers)
        return resp.status_code < 400
    except requests.RequestException:
        return False

for year, url in reports:
    col1, col2 = st.columns([3, 1])
    with col1:
        if url and url.lower() != "null" and url.startswith("http"):
            if check_live:
                if is_url_reachable(url):
                    st.markdown(f"**{year}** — [View Report]({url})")
                else:
                    st.markdown(f"**{year}** — :red-badge[Report unavailable]")
            else:
                st.markdown(f"**{year}** — [View Report]({url})")
        else:
            st.markdown(f"**{year}** — :red-badge[Report unavailable]")