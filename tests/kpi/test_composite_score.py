"""
Day 17 deliverable: unit tests for the composite score engine.
Run with: python -m pytest tests/kpi/test_composite_score.py -v
"""
import sys
import os
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src", "screener"))

from composite_score import (
    compute_weighted_score, winsorize_scale, sanitize_known_bad_values,
    KNOWN_BAD_ROE_ROCE_COMPANIES, _weighted_average, winsorize_scale_by_sector,
)


def test_01_weighted_score_all_present():
    result = compute_weighted_score(90, 85, 80, 70, 75, 100, 60, 65, 90, 85)
    assert round(result, 2) == 78.75


def test_02_weighted_score_missing_signal_reweights():
    result = compute_weighted_score(90, 85, 80, None, 75, 100, 60, 65, 90, 85)
    assert round(result, 2) == 80.75


def test_03_weighted_score_all_missing_returns_none():
    result = compute_weighted_score(*([None] * 10))
    assert result is None


def test_04_nan_treated_same_as_none():
    # regression test for the None-vs-NaN bug found while building this:
    # NaN must be skipped exactly like None, not silently poison the sum
    result_with_none = _weighted_average([(90, 15), (None, 10), (80, 10)])
    result_with_nan = _weighted_average([(90, 15), (float("nan"), 10), (80, 10)])
    assert result_with_none == result_with_nan


def test_05_winsorize_clamps_extremes():
    s = pd.Series(range(1, 101))  # 1..100
    scaled = winsorize_scale(s)
    assert scaled.iloc[0] == 0.0     # value=1, below P10
    assert scaled.iloc[-1] == 100.0  # value=100, above P90


def test_06_winsorize_exclude_from_boundaries():
    s = pd.Series([1, 2, 3, 4, 5, 6, 7, 8, 9, 10000])
    exclude = pd.Series([False] * 9 + [True])
    scaled = winsorize_scale(s, exclude_from_boundaries=exclude)
    # the excluded extreme value should still get scored (clamped to 100)
    assert scaled.iloc[-1] == 100.0
    # but normal values should spread out sensibly, not compress near 0
    assert scaled.iloc[4] > 10  # value=5 shouldn't be squashed near the bottom


def test_07_sanitize_known_bad_nulls_roe_roce():
    df = pd.DataFrame([
        {"company_id": "BEL", "return_on_equity_pct": 4744.0, "return_on_capital_employed_pct": 4146.0},
        {"company_id": "TCS", "return_on_equity_pct": 50.9, "return_on_capital_employed_pct": 62.9},
    ])
    result = sanitize_known_bad_values(df)
    bel_row = result[result["company_id"] == "BEL"].iloc[0]
    tcs_row = result[result["company_id"] == "TCS"].iloc[0]
    assert pd.isna(bel_row["return_on_equity_pct"])
    assert pd.isna(bel_row["return_on_capital_employed_pct"])
    assert tcs_row["return_on_equity_pct"] == 50.9


def test_08_known_bad_company_list_matches_sprint2_findings():
    assert KNOWN_BAD_ROE_ROCE_COMPANIES == {"BEL", "HAL", "INDIGO", "LT", "PNB"}


def test_09_sector_relative_scoring_differs_by_sector():
    series = pd.Series([10, 20, 30, 40, 50, 60, 70, 80, 90, 100])
    sectors = pd.Series(["A"] * 6 + ["B"] * 2 + ["C"] * 2)
    result = winsorize_scale_by_sector(series, sectors)
    # sector A (6 companies, big enough) should show real within-sector spread
    assert result.iloc[0] == 0.0
    assert result.iloc[5] == 100.0


def test_10_small_sector_falls_back_to_universe_wide():
    series = pd.Series([10, 20, 30, 40, 50, 60, 70, 80, 90, 100])
    sectors = pd.Series(["A"] * 6 + ["B"] * 2 + ["C"] * 2)
    result = winsorize_scale_by_sector(series, sectors)
    universe_wide = winsorize_scale(series)
    # sector B and C (2 companies each, below MIN_SECTOR_SIZE) should match
    # the universe-wide scaling exactly, not a degenerate 2-point scale
    assert result.iloc[6] == universe_wide.iloc[6]
    assert result.iloc[7] == universe_wide.iloc[7]
    assert result.iloc[8] == universe_wide.iloc[8]
    assert result.iloc[9] == universe_wide.iloc[9]