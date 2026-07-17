"""
Day 10 deliverable: 10 unit tests for the CAGR engine.
Run with: python -m pytest tests/kpi/test_cagr.py -v
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src", "analytics"))

from cagr import compute_cagr, compute_cagr_from_series


def test_01_normal_case_positive_to_positive():
    result = compute_cagr(100, 200, 5)
    assert result["flag"] is None
    assert round(result["value"], 2) == 14.87


def test_02_zero_base_returns_none_with_flag():
    result = compute_cagr(0, 200, 5)
    assert result["value"] is None
    assert result["flag"] == "ZERO_BASE"


def test_03_both_negative_returns_none_with_flag():
    result = compute_cagr(-200, -50, 5)
    assert result["value"] is None
    assert result["flag"] == "BOTH_NEGATIVE"


def test_04_decline_to_loss_returns_none_with_flag():
    result = compute_cagr(100, -50, 5)
    assert result["value"] is None
    assert result["flag"] == "DECLINE_TO_LOSS"


def test_05_turnaround_returns_none_with_flag():
    result = compute_cagr(-50, 100, 5)
    assert result["value"] is None
    assert result["flag"] == "TURNAROUND"


def test_06_zero_n_years_returns_insufficient():
    result = compute_cagr(100, 200, 0)
    assert result["flag"] == "INSUFFICIENT"


def test_07_negative_n_years_returns_insufficient():
    result = compute_cagr(100, 200, -1)
    assert result["flag"] == "INSUFFICIENT"


def test_08_series_insufficient_history():
    series = {"2020-03": 100, "2021-03": 110, "2022-03": 120}
    result = compute_cagr_from_series(series, 5)
    assert result["flag"] == "INSUFFICIENT"


def test_09_series_sufficient_history_computes_normally():
    series = {"2018-03": 100, "2019-03": 105, "2020-03": 110,
              "2021-03": 115, "2022-03": 120, "2023-03": 200}
    result = compute_cagr_from_series(series, 5)
    assert result["flag"] is None
    assert round(result["value"], 2) == 14.87


def test_10_series_exact_boundary_n_plus_1_years():
    # exactly n+1 = 6 years should be enough, not flagged INSUFFICIENT
    series = {"2018-03": 50, "2019-03": 55, "2020-03": 60,
              "2021-03": 65, "2022-03": 70, "2023-03": 100}
    result = compute_cagr_from_series(series, 5)
    assert result["flag"] is None