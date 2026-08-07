import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src", "analytics"))
from cagr import cagr, cagr_from_series


def test_normal_growth():
    v, f = cagr(100, 200, 5)
    assert f is None and round(v, 2) == 14.87


def test_decline_to_loss():
    v, f = cagr(100, -50, 5)
    assert v is None and f == "DECLINE_TO_LOSS"


def test_turnaround():
    v, f = cagr(-100, 50, 5)
    assert v is None and f == "TURNAROUND"


def test_both_negative():
    v, f = cagr(-100, -50, 5)
    assert v is None and f == "BOTH_NEGATIVE"


def test_zero_base():
    v, f = cagr(0, 100, 5)
    assert v is None and f == "ZERO_BASE"


def test_insufficient_missing_years():
    v, f = cagr(100, 200, None)
    assert v is None and f == "INSUFFICIENT"


def test_insufficient_missing_start():
    v, f = cagr(None, 200, 5)
    assert v is None and f == "INSUFFICIENT"


def test_flat_growth_is_zero():
    v, f = cagr(100, 100, 5)
    assert f is None and round(v, 4) == 0.0


def test_end_zero_is_minus_100():
    v, f = cagr(100, 0, 5)
    assert f is None and round(v, 2) == -100.0


def test_from_series_normal():
    pairs = [(2019, 100), (2020, 110), (2021, 121), (2022, 133), (2023, 146), (2024, 161)]
    v, f = cagr_from_series(pairs, 5)
    assert f is None and round(v, 1) == 10.0


def test_from_series_insufficient_years():
    pairs = [(2022, 100), (2023, 110), (2024, 121)]
    v, f = cagr_from_series(pairs, 5)
    assert v is None and f == "INSUFFICIENT"
