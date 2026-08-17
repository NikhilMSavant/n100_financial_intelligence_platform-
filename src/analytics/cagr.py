"""Sprint 2 — CAGR engine. Implements ((end/start)^(1/n) - 1) x 100 with all
6 edge-case flags from the project spec's decision table."""


def cagr(start, end, n_years, n_available_years=None):
    """Return (cagr_pct_or_None, flag_or_None).

    flag in {None, 'DECLINE_TO_LOSS', 'TURNAROUND', 'BOTH_NEGATIVE', 'ZERO_BASE', 'INSUFFICIENT'}
    """
    if n_available_years is not None and n_available_years < n_years:
        return None, "INSUFFICIENT"
    if start is None or end is None:
        return None, "INSUFFICIENT"
    if start == 0:
        return None, "ZERO_BASE"
    if start > 0 and end > 0:
        value = ((end / start) ** (1 / n_years) - 1) * 100
        return value, None
    if start > 0 and end < 0:
        return None, "DECLINE_TO_LOSS"
    if start < 0 and end > 0:
        return None, "TURNAROUND"
    if start < 0 and end < 0:
        return None, "BOTH_NEGATIVE"
    # start > 0 and end == 0, or other residual cases
    return None, "ZERO_BASE"
