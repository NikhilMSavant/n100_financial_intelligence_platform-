"""
cagr.py — Sprint 2 / Day 10
CAGR engine. Every call returns (value_or_None, flag_or_None).

Flags:
  DECLINE_TO_LOSS  start > 0, end < 0
  TURNAROUND       start < 0, end > 0
  BOTH_NEGATIVE    start < 0, end < 0
  ZERO_BASE        start == 0
  INSUFFICIENT     fewer than n years of data supplied
"""
import math


def cagr(start, end, n_years):
    """
    start/end: the metric value at the beginning / end of the window.
    n_years: length of the window in years (denominator of the CAGR exponent).
    Returns (value, flag).
    """
    if start is None or end is None or n_years is None:
        return None, "INSUFFICIENT"
    if n_years <= 0:
        return None, "INSUFFICIENT"

    if start == 0:
        return None, "ZERO_BASE"
    if start > 0 and end < 0:
        return None, "DECLINE_TO_LOSS"
    if start < 0 and end > 0:
        return None, "TURNAROUND"
    if start < 0 and end < 0:
        return None, "BOTH_NEGATIVE"

    # start > 0, end >= 0 (normal case, incl. end == 0 -> -100% CAGR, allowed)
    try:
        value = ((end / start) ** (1.0 / n_years) - 1) * 100
    except (ValueError, ZeroDivisionError):
        return None, "INSUFFICIENT"
    if isinstance(value, complex) or math.isnan(value):
        return None, "INSUFFICIENT"
    return value, None


def cagr_from_series(year_value_pairs, window_years):
    """
    year_value_pairs: list of (year:int, value:float) sorted or unsorted.
    window_years: 3, 5, or 10.
    Picks the latest year as `end` and (latest - window_years) as `start`,
    requiring an exact match on both endpoints; else INSUFFICIENT.
    """
    if not year_value_pairs:
        return None, "INSUFFICIENT"
    by_year = {y: v for y, v in year_value_pairs if v is not None}
    if not by_year:
        return None, "INSUFFICIENT"
    end_year = max(by_year)
    start_year = end_year - window_years
    if start_year not in by_year or end_year not in by_year:
        return None, "INSUFFICIENT"
    return cagr(by_year[start_year], by_year[end_year], window_years)


if __name__ == "__main__":
    print(cagr(100, 200, 5))          # normal
    print(cagr(100, -50, 5))          # DECLINE_TO_LOSS
    print(cagr(-100, 50, 5))          # TURNAROUND
    print(cagr(-100, -50, 5))         # BOTH_NEGATIVE
    print(cagr(0, 100, 5))            # ZERO_BASE
    print(cagr(100, 200, None))       # INSUFFICIENT
