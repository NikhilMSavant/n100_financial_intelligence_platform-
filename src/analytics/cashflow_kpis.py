"""
cashflow_kpis.py — Sprint 2 / Day 11 (+ Sprint 5 / Day 31 distress/deleveraging flags)
"""


def free_cash_flow(operating_activity, investing_activity):
    if operating_activity is None or investing_activity is None:
        return None
    return operating_activity + investing_activity  # negative allowed


def cfo_quality_score(cfo_pat_ratios):
    """cfo_pat_ratios: list of CFO/PAT values (up to 5 years), pre-computed by caller."""
    vals = [v for v in cfo_pat_ratios if v is not None]
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


def capex_intensity(investing_activity, sales):
    if investing_activity is None or not sales:
        return None, None
    pct = abs(investing_activity) / sales * 100
    if pct < 3:
        label = "Asset Light"
    elif pct <= 8:
        label = "Moderate"
    else:
        label = "Capital Intensive"
    return pct, label


def fcf_conversion_rate(fcf, operating_profit):
    if fcf is None or not operating_profit:
        return None
    return fcf / operating_profit * 100


def capital_allocation_pattern(cfo, cfi, cff, cfo_pat_ratio=None):
    """
    Classifies a company-year into one of 8 capital-allocation patterns based
    on the sign of (CFO, CFI, CFF). Returns (pattern_label, cfo_sign, cfi_sign, cff_sign).
    """
    if cfo is None or cfi is None or cff is None:
        return None, None, None, None

    def sign(x):
        return "+" if x >= 0 else "-"

    s_cfo, s_cfi, s_cff = sign(cfo), sign(cfi), sign(cff)

    if s_cfo == "+" and s_cfi == "-" and s_cff == "-":
        label = "Shareholder Returns" if (cfo_pat_ratio is not None and cfo_pat_ratio > 1.0) else "Reinvestor"
    elif s_cfo == "+" and s_cfi == "+" and s_cff == "-":
        label = "Liquidating Assets"
    elif s_cfo == "-" and s_cfi == "+" and s_cff == "+":
        label = "Distress Signal"
    elif s_cfo == "-" and s_cfi == "-" and s_cff == "+":
        label = "Growth Funded by Debt"
    elif s_cfo == "+" and s_cfi == "+" and s_cff == "+":
        label = "Cash Accumulator"
    elif s_cfo == "-" and s_cfi == "-" and s_cff == "-":
        label = "Pre-Revenue"
    elif s_cfo == "+" and s_cfi == "-" and s_cff == "+":
        label = "Mixed"
    else:
        label = "Mixed"
    return label, s_cfo, s_cfi, s_cff


def distress_signal(cfo, cff):
    if cfo is None or cff is None:
        return False
    return cfo < 0 and cff > 0


def deleveraging_flag(cff, borrowings_this_year, borrowings_prior_year):
    if cff is None or borrowings_this_year is None or borrowings_prior_year is None:
        return False
    return cff < 0 and borrowings_this_year < borrowings_prior_year


if __name__ == "__main__":
    print(capital_allocation_pattern(100, -40, -30, cfo_pat_ratio=1.2))
    print(capital_allocation_pattern(-50, 20, 40))
