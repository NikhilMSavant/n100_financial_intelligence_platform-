"""pages/03_screener.py — Sprint 4 / Day 24"""
import os
import sys
import sqlite3
import streamlit as st

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "src", "screener"))
from engine import load_config, build_universe, apply_filters

st.set_page_config(page_title="Screener | Nifty 100 Analytics", layout="wide")
st.title("🔎 Screener")

config = load_config()
conn = sqlite3.connect(os.path.join(ROOT, "db", "nifty100.db"))
universe = build_universe(conn)

PRESET_DEFAULTS = {
    "Quality": dict(roe_min=15, de_max=1.0, fcf_min=0, revenue_cagr_5yr_min=10, pat_cagr_5yr_min=0,
                    opm_min=0, pe_max=1000, pb_max=1000, dividend_yield_min=0, icr_min=0),
    "Value": dict(roe_min=0, de_max=2.0, fcf_min=-1e9, revenue_cagr_5yr_min=-100, pat_cagr_5yr_min=-100,
                  opm_min=0, pe_max=35, pb_max=6.0, dividend_yield_min=1, icr_min=0),
    "Growth": dict(roe_min=0, de_max=2.0, fcf_min=-1e9, revenue_cagr_5yr_min=15, pat_cagr_5yr_min=20,
                   opm_min=0, pe_max=1000, pb_max=1000, dividend_yield_min=0, icr_min=0),
    "Dividend": dict(roe_min=0, de_max=1000, fcf_min=0, revenue_cagr_5yr_min=-100, pat_cagr_5yr_min=-100,
                      opm_min=0, pe_max=1000, pb_max=1000, dividend_yield_min=2, icr_min=0),
    "Debt-Free": dict(roe_min=12, de_max=0, fcf_min=-1e9, revenue_cagr_5yr_min=-100, pat_cagr_5yr_min=-100,
                       opm_min=0, pe_max=1000, pb_max=1000, dividend_yield_min=0, icr_min=0),
    "Turnaround": dict(roe_min=-100, de_max=1000, fcf_min=0, revenue_cagr_5yr_min=-100, pat_cagr_5yr_min=-100,
                        opm_min=0, pe_max=1000, pb_max=1000, dividend_yield_min=0, icr_min=0),
}

if "slider_vals" not in st.session_state:
    st.session_state.slider_vals = PRESET_DEFAULTS["Quality"].copy()

st.sidebar.subheader("Presets")
preset_cols = st.sidebar.columns(3)
preset_names = list(PRESET_DEFAULTS.keys())
for i, name in enumerate(preset_names):
    if preset_cols[i % 3].button(name):
        st.session_state.slider_vals = PRESET_DEFAULTS[name].copy()

st.sidebar.subheader("Filters")
sv = st.session_state.slider_vals
roe_min = st.sidebar.slider("ROE min (%)", -50, 100, int(sv["roe_min"]))
de_max = st.sidebar.slider("D/E max", 0.0, 10.0, float(sv["de_max"]))
fcf_min = st.sidebar.slider("FCF min (Cr)", -5000, 5000, int(min(max(sv["fcf_min"], -5000), 5000)))
rev_cagr_min = st.sidebar.slider("Revenue CAGR 5yr min (%)", -50, 100, int(sv["revenue_cagr_5yr_min"]))
pat_cagr_min = st.sidebar.slider("PAT CAGR 5yr min (%)", -50, 100, int(sv["pat_cagr_5yr_min"]))
opm_min = st.sidebar.slider("OPM min (%)", -50, 100, int(sv["opm_min"]))
pe_max = st.sidebar.slider("P/E max", 0, 200, int(min(sv["pe_max"], 200)))
pb_max = st.sidebar.slider("P/B max", 0.0, 50.0, float(min(sv["pb_max"], 50.0)))
div_yield_min = st.sidebar.slider("Dividend Yield min (%)", 0.0, 10.0, float(sv["dividend_yield_min"]))
icr_min = st.sidebar.slider("ICR min", 0, 50, int(min(sv["icr_min"], 50)))

filters = dict(roe_min=roe_min, de_max=de_max, fcf_min=fcf_min, revenue_cagr_5yr_min=rev_cagr_min,
                pat_cagr_5yr_min=pat_cagr_min, opm_min=opm_min, pe_max=pe_max, pb_max=pb_max,
                dividend_yield_min=div_yield_min, icr_min=icr_min)

result = apply_filters(universe, filters, config).sort_values("composite_quality_score", ascending=False)

st.markdown(f"### {len(result)} companies match your filters")

show_cols = ["company_id", "company_name", "broad_sector", "composite_quality_score",
             "return_on_equity_pct", "debt_to_equity", "free_cash_flow_cr",
             "revenue_cagr_5yr", "pat_cagr_5yr", "operating_profit_margin_pct",
             "pe_ratio", "pb_ratio", "dividend_yield_pct", "interest_coverage"]
show_cols = [c for c in show_cols if c in result.columns]
st.dataframe(result[show_cols], use_container_width=True, hide_index=True)

csv = result[show_cols].to_csv(index=False).encode("utf-8")
st.download_button("⬇️ Download CSV", data=csv, file_name="screener_results.csv", mime="text/csv")
