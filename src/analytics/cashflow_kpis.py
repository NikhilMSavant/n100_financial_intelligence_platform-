"""Sprint 2/5 — Cash flow KPI formulas: FCF, CFO quality, CapEx intensity,
FCF conversion, and the 8-pattern capital allocation classifier."""


def free_cash_flow(operating_activity, investing_activity):
    return (operating_activity or 0) + (investing_activity or 0)


def cfo_quality_score(cfo_pat_ratios_5yr: list):
    """cfo_pat_ratios_5yr: list of CFO/PAT values (already computed) over up to 5 years."""
    vals = [v for v in cfo_pat_ratios_5yr if v is not None]
    if not vals:
        return None, None
    avg = sum(vals) / len(vals)
    if avg > 1.0:
        label = "High Quality"
    elif avg >= 0.5:
        label = "Moderate"
    else:
        label = "Accrual Risk"
    return avg, label


def cfo_pat_ratio(cfo, pat):
    if not pat:
        return None
    return cfo / pat


def capex_intensity(investing_activity, sales):
    if not sales:
        return None, None
    pct = abs(investing_activity or 0) / sales * 100
    if pct < 3:
        label = "Asset Light"
    elif pct <= 8:
        label = "Moderate"
    else:
        label = "Capital Intensive"
    return pct, label


def fcf_conversion_rate(fcf, operating_profit):
    if not operating_profit:
        return None
    return fcf / operating_profit * 100


def capital_allocation_pattern(cfo, cfi, cff, cfo_pat_ratio_val=None):
    """Classify by sign of (CFO, CFI, CFF) into one of 8 patterns."""
    s = lambda x: "+" if (x or 0) >= 0 else "-"
    cfo_s, cfi_s, cff_s = s(cfo), s(cfi), s(cff)
    pattern = (cfo_s, cfi_s, cff_s)

    if pattern == ("+", "-", "-"):
        if cfo_pat_ratio_val is not None and cfo_pat_ratio_val > 1.2:
            return cfo_s, cfi_s, cff_s, "Shareholder Returns"
        return cfo_s, cfi_s, cff_s, "Reinvestor"
    if pattern == ("+", "+", "-"):
        return cfo_s, cfi_s, cff_s, "Liquidating Assets"
    if pattern == ("-", "+", "+"):
        return cfo_s, cfi_s, cff_s, "Distress Signal"
    if pattern == ("-", "-", "+"):
        return cfo_s, cfi_s, cff_s, "Growth Funded by Debt"
    if pattern == ("+", "+", "+"):
        return cfo_s, cfi_s, cff_s, "Cash Accumulator"
    if pattern == ("-", "-", "-"):
        return cfo_s, cfi_s, cff_s, "Pre-Revenue"
    if pattern == ("+", "-", "+"):
        return cfo_s, cfi_s, cff_s, "Mixed"
    # (-, +, -) not in the 8-pattern spec table; label generically
    return cfo_s, cfi_s, cff_s, "Mixed"


def distress_signal(cfo, cff):
    return (cfo or 0) < 0 and (cff or 0) > 0


def deleveraging_flag(cff, borrowings_this_year, borrowings_last_year):
    if borrowings_last_year is None:
        return False
    return (cff or 0) < 0 and borrowings_this_year < borrowings_last_year
