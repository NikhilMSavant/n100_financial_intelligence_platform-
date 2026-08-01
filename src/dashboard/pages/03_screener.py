"""
03_screener.py
--------------
Day 24 deliverable: Screener screen. 10 metric sliders, 6 preset buttons,
live-updating results table, CSV download, result count label.
"""
import streamlit as st
import sys
import os
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "screener"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "utils"))
from engine import (
    load_screener_universe, apply_filters, run_preset, PRESETS,
    FILTER_COLUMN_MAP, PRESET_EXTRA_COLUMNS,
)
from composite_score import compute_scores_for_universe

st.set_page_config(page_title="Screener", layout="wide")
st.title("Screener")

# Slider ranges capped at sensible bounds - the raw data has extreme
# outliers (e.g. BEL's 4744% ROE, a known DATA_SOURCE_ISSUE from Sprint 2
# Day 13) that would make a literal min-max slider unusable for finding
# realistic thresholds like 15-30% ROE.
SLIDER_CONFIG = {
    "roe_min": ("ROE min (%)", -10, 60, 0),
    "de_max": ("D/E max", 0.0, 5.0, 5.0),
    "fcf_min": ("FCF min (Cr)", -5000, 20000, -5000),
    "revenue_cagr_5yr_min": ("Revenue CAGR 5yr min (%)", -10, 40, -10),
    "pat_cagr_5yr_min": ("PAT CAGR 5yr min (%)", -30, 120, -30),
    "opm_min": ("OPM min (%)", -20, 100, -20),
    "pe_max": ("P/E max", 5, 80, 80),
    "pb_max": ("P/B max", 0.5, 15.0, 15.0),
    "dividend_yield_min": ("Dividend Yield min (%)", 0.0, 5.0, 0.0),
    "icr_min": ("ICR min", 0.0, 20.0, 0.0),
}

# Seed initial widget state once, before first render (subsequent reruns
# skip this since the keys will already exist in session_state)
for key, (label, lo, hi, default) in SLIDER_CONFIG.items():
    if f"enable_{key}" not in st.session_state:
        st.session_state[f"enable_{key}"] = False
    if f"slider_{key}" not in st.session_state:
        st.session_state[f"slider_{key}"] = default
# --- Preset buttons ---
st.sidebar.subheader("Presets")
preset_clicked = None
for preset_name in PRESETS:
    if st.sidebar.button(preset_name, use_container_width=True):
        preset_clicked = preset_name

if "active_preset_name" not in st.session_state:
    st.session_state["active_preset_name"] = None


def _clear_active_preset():
    """
    Fires on any manual slider/checkbox edit. A preset's correct result
    can depend on logic beyond what sliders can represent (e.g. Debt-Free
    Blue Chip's D/E<0.05 + Financials exclusion, Dividend Champion's
    payout-ratio<80%, Turnaround Watch's 3-part check) - see run_preset().
    Once the user starts hand-editing filters, keep them in full control
    of plain apply_filters() rather than silently mixing the two.
    """
    st.session_state["active_preset_name"] = None


if preset_clicked:
    # Write directly into the widget state keys BEFORE the widgets are
    # created below - once a widget has a `key`, only session_state
    # writes (not the `value=` parameter) can change it on a rerun.
    # These slider positions are shown for reference only once a preset
    # is active - the actual filtering below uses run_preset(), which
    # also applies each preset's special-case logic that a slider alone
    # can't represent.
    preset_filters = PRESETS[preset_clicked]
    for key, (label, lo, hi, default) in SLIDER_CONFIG.items():
        is_active = key in preset_filters
        st.session_state[f"enable_{key}"] = is_active
        st.session_state[f"slider_{key}"] = preset_filters.get(key, default)
    st.session_state["active_preset_name"] = preset_clicked

st.sidebar.divider()
st.sidebar.subheader("Custom Filters")

# --- 10 sliders, each with an explicit "enable this filter" checkbox ---
# A slider alone can't represent "no filter" - it always has SOME value.
# Using a checkbox alongside each slider makes "not filtering on this
# metric" an explicit, correct state, rather than silently applying
# whatever number the slider happens to show.
filters = {}

for key, (label, lo, hi, default) in SLIDER_CONFIG.items():
    enabled = st.sidebar.checkbox(f"Filter: {label}", key=f"enable_{key}", on_change=_clear_active_preset)
    value = st.sidebar.slider(
        label, lo, hi,
        disabled=not enabled,
        key=f"slider_{key}",
        on_change=_clear_active_preset,
    )
    if enabled:
        filters[key] = value

st.divider()

active_preset = st.session_state["active_preset_name"]

# --- Apply filters and compute scores ---
universe = load_screener_universe()
universe = compute_scores_for_universe(universe)

if active_preset:
    # Full preset logic, including the special-case rules sliders can't
    # represent - not just the subset of the preset that happens to map
    # onto a slider (see known_exceptions_sprint4.md for the bug this fixes).
    result = run_preset(universe, active_preset)
    st.caption(
        f"Showing results for preset: **{active_preset}** "
        "(sliders reflect its slider-representable thresholds; edit any "
        "slider to switch to custom filtering)"
    )
else:
    result = apply_filters(universe, filters)

result = result.sort_values("final_composite_score", ascending=False)

st.subheader(f"{len(result)} companies match your filters")

# Spec requires company_id, name, sector, composite score, and filtered
# metrics - merge in name/sector, which weren't part of the screener
# universe join used for filtering.
from db import get_companies, get_sectors  # reuse the already-cleaned company_name (Day 23 fix)

companies_clean = get_companies()[["company_id", "company_name"]]
sectors_lookup = get_sectors()[["company_id", "broad_sector"]].rename(columns={"broad_sector": "sector"})
name_sector = companies_clean.merge(sectors_lookup, on="company_id", how="left")
result_display = result.merge(name_sector, on="company_id", how="left")

# Show whichever metric columns are actually driving the current result -
# the filters dict when custom filtering, or the preset's own filter keys
# (plus any hardcoded extra columns from run_preset()) when a preset is
# active - rather than always showing the same fixed 4 metrics regardless
# of what's actually being filtered on.
base_cols = ["company_id", "company_name", "sector"]
if active_preset:
    active_keys = list(PRESETS[active_preset].keys())
    metric_cols = [FILTER_COLUMN_MAP[k] for k in active_keys if k in FILTER_COLUMN_MAP]
    metric_cols += PRESET_EXTRA_COLUMNS.get(active_preset, [])
else:
    metric_cols = [FILTER_COLUMN_MAP[k] for k in filters if k in FILTER_COLUMN_MAP]

# De-duplicate while preserving order, then drop anything already in base_cols
seen = set()
metric_cols = [c for c in metric_cols if c not in base_cols and not (c in seen or seen.add(c))]

display_cols = base_cols + metric_cols + ["final_composite_score"]
st.dataframe(result_display[display_cols], use_container_width=True, hide_index=True)

# --- CSV download ---
# Spec: "generates well-formed CSV with all visible columns" - exports
# exactly the (now dynamic) display_cols shown in the on-screen table,
# not every raw internal column, so the download matches what the user
# actually sees.
csv_data = result_display[display_cols].to_csv(index=False)
st.download_button("Download results as CSV", csv_data, file_name="screener_results.csv", mime="text/csv")