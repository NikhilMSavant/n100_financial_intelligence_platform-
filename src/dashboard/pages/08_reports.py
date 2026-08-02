"""
08_reports.py
-------------
Day 25 deliverable: Annual Reports screen. Company search, list of
available annual report years with clickable BSE PDF links, badge if a
URL doesn't resolve.

Fixed after live testing showed nearly every year except the most recent
flagged as "Report unavailable": 894 of 1,457 stored URLs (61%) point to
bseindia.com/bseplus/AnnualReport/... - BSE's own login-gated premium
archive (confirmed via bseplus.bseindia.com/login.aspx), not a broken
link. A plain anonymous request to that path predictably gets blocked or
redirected to a login page regardless of headers/method, so the original
single "Report unavailable" badge was misleading - it looked identical
for "this link is dead" and "this link requires a BSE Plus subscription
we don't have," when only the first is actually a problem with the app.
Now shown as two distinct badges; also added a GET-with-Range fallback
for the small number of non-bseplus links that reject HEAD outright
(some static file servers do, independent of the bseplus issue).
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

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}


def is_bseplus_login_gated(url):
    """BSE's premium archive tier - see module docstring. Structural
    check on the URL path, not a network call, so it's always accurate
    regardless of what an anonymous request to it happens to return."""
    return "bseplus.bseindia.com" in url or "/bseplus/" in url


def is_url_reachable(url):
    """
    Tries HEAD first (cheap), falls back to a 1-byte ranged GET for
    servers that reject HEAD outright (some static file hosts do this
    independent of any login-wall issue). Browser User-Agent is required
    - BSE returns 403 to requests without one even for genuinely public
    files (confirmed by direct testing).
    """
    try:
        resp = requests.head(url, timeout=5, allow_redirects=True, headers=HEADERS)
        if resp.status_code < 400:
            return True
    except requests.RequestException:
        pass

    try:
        range_headers = {**HEADERS, "Range": "bytes=0-0"}
        resp = requests.get(url, timeout=5, allow_redirects=True, headers=range_headers, stream=True)
        return resp.status_code < 400
    except requests.RequestException:
        return False


for year, url in reports:
    col1, col2 = st.columns([3, 1])
    with col1:
        has_url = url and url.lower() != "null" and url.startswith("http")

        if not has_url:
            st.markdown(f"**{year}** — :red-badge[Report unavailable]")
        elif is_bseplus_login_gated(url):
            # Never runs a network check for these - the URL structure
            # alone tells us it's gated, and an anonymous check result
            # (blocked/redirected either way) wouldn't add information.
            st.markdown(f"**{year}** — [View Report]({url}) :orange-badge[Requires BSE Plus login]")
        elif check_live:
            if is_url_reachable(url):
                st.markdown(f"**{year}** — [View Report]({url})")
            else:
                st.markdown(f"**{year}** — :red-badge[Report unavailable]")
        else:
            st.markdown(f"**{year}** — [View Report]({url})")