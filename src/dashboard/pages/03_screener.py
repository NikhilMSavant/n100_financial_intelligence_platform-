import streamlit as st
import sys, pathlib
import yaml
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent.parent))
from utils.db import get_screener_universe
from screener.engine import apply_filters

st.set_page_config(page_title="Screener", layout="wide")
st.title("Financial Screener")

with open(str(pathlib.Path(__file__).resolve().parent.parent.parent.parent / "config" / "screener_config.yaml")) as f:
    config = yaml.safe_load(f)

st.sidebar.header("Preset")
preset_key = st.sidebar.selectbox("Choose a preset (auto-fills sliders)",
                                   ["Custom"] + list(config["presets"].keys()))

st.sidebar.header("Filters")
roe_min = st.sidebar.slider("ROE min %", -20, 60, 15)
de_max = st.sidebar.slider("D/E max", 0.0, 10.0, 5.0)
fcf_min = st.sidebar.number_input("FCF min (Cr)", value=0)
rev_cagr_min = st.sidebar.slider("Revenue CAGR 5yr min %", -20, 40, 0)
pat_cagr_min = st.sidebar.slider("PAT CAGR 5yr min %", -20, 60, 0)
opm_min = st.sidebar.slider("OPM min %", -20, 60, 0)
pe_max = st.sidebar.slider("P/E max", 0, 100, 100)
pb_max = st.sidebar.slider("P/B max", 0.0, 20.0, 20.0)
div_yield_min = st.sidebar.slider("Dividend Yield min %", 0.0, 6.0, 0.0)
icr_min = st.sidebar.number_input("ICR min", value=0.0)

universe = get_screener_universe()

if preset_key != "Custom":
    filters = config["presets"][preset_key]["filters"]
    result = apply_filters(universe, filters, config)
else:
    filters = {
        "return_on_equity_pct": {"min": roe_min}, "debt_to_equity": {"max": de_max},
        "free_cash_flow_cr": {"min": fcf_min}, "revenue_cagr_5yr": {"min": rev_cagr_min},
        "pat_cagr_5yr": {"min": pat_cagr_min}, "operating_profit_margin_pct": {"min": opm_min},
        "pe_ratio": {"max": pe_max}, "pb_ratio": {"max": pb_max},
        "dividend_yield_pct": {"min": div_yield_min}, "interest_coverage": {"min": icr_min},
    }
    result = apply_filters(universe, filters, config)

st.write(f"**{len(result)} companies match your filters**")
display_cols = ["company_id", "company_name", "broad_sector", "composite_quality_score",
                 "return_on_equity_pct", "debt_to_equity", "free_cash_flow_cr",
                 "revenue_cagr_5yr", "pat_cagr_5yr", "pe_ratio", "pb_ratio", "dividend_yield_pct"]
result_display = result[display_cols].sort_values("composite_quality_score", ascending=False)
st.dataframe(result_display, use_container_width=True)

csv = result_display.to_csv(index=False).encode("utf-8")
st.download_button("Download CSV", csv, "screener_results.csv", "text/csv")
