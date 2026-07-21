"""
Day 15 deliverable: unit tests for the screener filter engine.
Uses a small synthetic DataFrame rather than the real database, so tests
run fast and don't depend on data that might change.
Run with: python -m pytest tests/kpi/test_screener_engine.py -v
"""
import sys
import os
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src", "screener"))

from engine import apply_filters, load_screener_universe, run_preset, PRESETS


def make_sample_df():
    return pd.DataFrame([
        {"company_id": "A", "return_on_equity_pct": 20, "debt_to_equity": 0.5,
         "interest_coverage": 3.0, "broad_sector": "Industrials"},
        {"company_id": "B", "return_on_equity_pct": 10, "debt_to_equity": 6.0,
         "interest_coverage": 1.0, "broad_sector": "Financials"},
        {"company_id": "C", "return_on_equity_pct": 25, "debt_to_equity": None,
         "interest_coverage": None, "broad_sector": "Industrials"},
    ])


def test_01_roe_min_filter():
    df = make_sample_df()
    result = apply_filters(df, {"roe_min": 15})
    assert set(result["company_id"]) == {"A", "C"}


def test_02_de_max_exempts_financials_sector():
    df = make_sample_df()
    # company B has D/E=6.0 (would fail de_max=1.0) but is Financials -> exempt
    result = apply_filters(df, {"de_max": 1.0})
    assert "B" in set(result["company_id"])


def test_03_de_max_still_applies_to_non_financials():
    df = make_sample_df()
    # company A has D/E=0.5, passes; a high-D/E non-Financials company should fail
    df.loc[df["company_id"] == "A", "debt_to_equity"] = 5.0
    result = apply_filters(df, {"de_max": 1.0})
    assert "A" not in set(result["company_id"])


def test_04_icr_min_debt_free_always_passes():
    df = make_sample_df()
    # company C has interest_coverage=None (debt-free) -> should always pass icr_min
    result = apply_filters(df, {"icr_min": 5.0})
    assert "C" in set(result["company_id"])


def test_05_icr_min_normal_company_must_meet_threshold():
    df = make_sample_df()
    # company B has interest_coverage=1.0, fails icr_min=1.5
    result = apply_filters(df, {"icr_min": 1.5})
    assert "B" not in set(result["company_id"])


def test_06_combined_filters():
    df = make_sample_df()
    result = apply_filters(df, {"roe_min": 15, "de_max": 1.0})
    # A passes both; C has None D/E so fails de_max (not Financials-exempt, not
    # a special-cased column); B fails ROE
    assert set(result["company_id"]) == {"A"}

def test_07_all_presets_exist():
    expected = {"Quality Compounder", "Value Pick", "Growth Accelerator",
                "Dividend Champion", "Debt-Free Blue Chip", "Turnaround Watch"}
    assert expected == set(PRESETS.keys())


def test_08_unknown_preset_raises():
    df = load_screener_universe()
    try:
        run_preset(df, "Not A Real Preset")
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_09_all_presets_return_between_5_and_50():
    df = load_screener_universe()
    for preset_name in PRESETS:
        result = run_preset(df, preset_name)
        assert 5 <= len(result) <= 50, f"{preset_name} returned {len(result)} companies, expected 5-50"