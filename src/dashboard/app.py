"""
app.py
------
Day 22 deliverable: main Streamlit entry point.
Run with: streamlit run src/dashboard/app.py
"""
import streamlit as st

st.set_page_config(
    page_title="Nifty 100 Analytics",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("Nifty 100 Financial Intelligence Platform")
st.markdown(
    "Use the sidebar to navigate between screens: Home, Company Profile, "
    "Screener, Peer Comparison, Trend Analysis, Sector Analysis, "
    "Capital Allocation Map, and Annual Reports."
)

st.info("Select a screen from the sidebar on the left to get started.")