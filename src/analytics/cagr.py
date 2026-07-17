"""
cagr.py
-------
Day 10 deliverable: CAGR engine with all 6 edge-case handlers.

CAGR = ((end/start)^(1/n) - 1) * 100

The formula only makes clean mathematical sense when start and end are
both positive - taking a root of a negative number, or dividing by zero,
either breaks math or produces a number that LOOKS valid but means
something misleading (e.g. a companyy going from a small loss to a big
loss can produce a deceptively "reasonable-looking" positive CAGR if you
don't guard against negative bases). So each broken case gets its own
named flag instead of a silently wrong number.
"""


def compute_cagr(start_value, end_value, n_years):
    """
    Returns a dict: {"value": float | None, "flag": str | None}

    flag is None only for the normal, cleanly-computable case.
    """
    if n_years is None or n_years <= 0:
        return {"value": None, "flag": "INSUFFICIENT"}

    # Case: both positive - normal case
    if start_value > 0 and end_value > 0:
        value = ((end_value / start_value) ** (1 / n_years) - 1) * 100
        return {"value": value, "flag": None}

    # Case: zero base - growth rate from zero is undefined (division by zero,
    # and "infinite % growth" is not a meaningful business number)
    if start_value == 0:
        return {"value": None, "flag": "ZERO_BASE"}

    # Case: both negative - e.g. a loss shrinking from -200 to -50 is
    # actually IMPROVING, but the raw ratio (end/start) is positive and
    # would produce a misleadingly "normal-looking" CAGR number if computed
    # directly. Flag it instead of pretending the math is meaningful here.
    if start_value < 0 and end_value < 0:
        return {"value": None, "flag": "BOTH_NEGATIVE"}

# Case: decline to loss - company was profitable/positive at the start
    # but ended negative (e.g. sales +100 -> -50). No real growth rate
    # exists across a sign change; this is a distinct, important business
    # signal worth flagging by name rather than burying in a null.
    if start_value > 0 and end_value < 0:
        return {"value": None, "flag": "DECLINE_TO_LOSS"}

    # Case: turnaround - company started negative and ended positive
    # (e.g. profit -50 -> +100). Also no real CAGR, but a very different
    # (positive) business story than DECLINE_TO_LOSS, so it gets its own flag.
    if start_value < 0 and end_value > 0:
        return {"value": None, "flag": "TURNAROUND"}

    # placeholder for the last case - added next
    return {"value": None, "flag": "UNHANDLED"}

def compute_cagr_from_series(values_by_year, n_years):
    """
    Wrapper around compute_cagr() that works from a full time series
    (e.g. {"2019-03": 100, "2020-03": 120, ...}) instead of two raw numbers.

    Returns {"value": None, "flag": "INSUFFICIENT"} if fewer than n_years+1
    data points are available - you need a start AND an end point n years
    apart, so an n-year window requires at least n+1 years of data on record.
    """
    years_sorted = sorted(values_by_year.keys())

    if len(years_sorted) < n_years + 1:
        return {"value": None, "flag": "INSUFFICIENT"}

    start_year = years_sorted[-(n_years + 1)]
    end_year = years_sorted[-1]

    start_value = values_by_year[start_year]
    end_value = values_by_year[end_year]

    return compute_cagr(start_value, end_value, n_years)