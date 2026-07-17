"""
cashflow_kpis.py
----------------
Day 11 deliverable: Free Cash Flow, CFO Quality Score, CapEx Intensity,
FCF Conversion Rate, and the 8-pattern capital allocation classifier.
"""


def free_cash_flow(operating_activity, investing_activity):
    """
    FCF = operating_activity + investing_activity.
    A negative result is allowed and meaningful (heavy investment phase,
    e.g. building a new plant) - it is NOT an error case to guard against.
    """
    return (operating_activity or 0) + (investing_activity or 0)


def cfo_quality_score(cfo_values, pat_values):
    """
    CFO Quality Score = average(CFO / PAT) over the years provided.
    cfo_values and pat_values must be same-length, same-order lists
    (typically the trailing 5 years, per spec - but this function just
    averages whatever it's given, so the caller controls the window).

    Quality label:
      > 1.0        -> "High Quality"   (cash earnings exceed paper profit)
      0.5 to 1.0    -> "Moderate"
      < 0.5         -> "Accrual Risk"   (profit not backed by real cash)

    A year is skipped (not averaged in) if that year's PAT == 0, since
    CFO/PAT is undefined there - not silently treated as a 0 ratio.
    Returns {"value": None, "label": None} if there's no usable year at all.
    """
    ratios = []
    for cfo, pat in zip(cfo_values, pat_values):
        if pat == 0 or pat is None:
            continue
        ratios.append(cfo / pat)

    if not ratios:
        return {"value": None, "label": None}

    avg_ratio = sum(ratios) / len(ratios)

    if avg_ratio > 1.0:
        label = "High Quality"
    elif avg_ratio >= 0.5:
        label = "Moderate"
    else:
        label = "Accrual Risk"

    return {"value": avg_ratio, "label": label}


def capex_intensity(investing_activity, sales):
    """
    CapEx Intensity % = abs(investing_activity) / sales * 100.
    Label: <3% = Asset Light, 3-8% = Moderate, >8% = Capital Intensive.
    Returns {"value": None, "label": None} if sales == 0.
    """
    if sales is None or sales == 0:
        return {"value": None, "label": None}

    value = abs(investing_activity or 0) / sales * 100

    if value < 3:
        label = "Asset Light"
    elif value <= 8:
        label = "Moderate"
    else:
        label = "Capital Intensive"

    return {"value": value, "label": label}


def fcf_conversion_rate(fcf, operating_profit):
    """FCF Conversion % = FCF / operating_profit * 100. None if operating_profit == 0."""
    if operating_profit is None or operating_profit == 0:
        return None
    return (fcf / operating_profit) * 100

def _sign(value):
    """Returns '+', '-', or '0' for a cash flow value."""
    if value > 0:
        return "+"
    if value < 0:
        return "-"
    return "0"


def classify_capital_allocation(cfo, cfi, cff, cfo_quality_value=None):
    """
    Classifies a company-year into one of 8 capital allocation patterns
    based on the signs of (CFO, CFI, CFF).

    Returns {"cfo_sign": str, "cfi_sign": str, "cff_sign": str, "pattern_label": str}

    Pattern table (spec):
      (+,-,-)                     -> Reinvestor
      (+,-,-) AND cfo_quality>1.0 -> Shareholder Returns  (more specific case
                                      of the same signs, checked first)
      (+,+,-)                     -> Liquidating Assets
      (-,+,+)                     -> Distress Signal
      (-,-,+)                     -> Growth Funded by Debt
      (+,+,+)                     -> Cash Accumulator
      (-,-,-)                     -> Pre-Revenue
      (+,-,+)                     -> Mixed
    """
    cfo_sign = _sign(cfo)
    cfi_sign = _sign(cfi)
    cff_sign = _sign(cff)
    signs = (cfo_sign, cfi_sign, cff_sign)

    if signs == ("+", "-", "-") and cfo_quality_value is not None and cfo_quality_value > 1.0:
        label = "Shareholder Returns"
    elif signs == ("+", "-", "-"):
        label = "Reinvestor"
    elif signs == ("+", "+", "-"):
        label = "Liquidating Assets"
    elif signs == ("-", "+", "+"):
        label = "Distress Signal"
    elif signs == ("-", "-", "+"):
        label = "Growth Funded by Debt"
    elif signs == ("+", "+", "+"):
        label = "Cash Accumulator"
    elif signs == ("-", "-", "-"):
        label = "Pre-Revenue"
    elif signs == ("+", "-", "+"):
        label = "Mixed"
    else:
        label = "Unclassified"

    return {"cfo_sign": cfo_sign, "cfi_sign": cfi_sign, "cff_sign": cff_sign, "pattern_label": label}