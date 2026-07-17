"""
ratios.py
---------
Day 8-9 deliverable: profitability, leverage, and efficiency ratios.
Every function returns None where the spec calls for it (rather than
raising or returning 0/inf), so downstream code can distinguish
"not computable" from "computed to zero".
"""


def net_profit_margin(net_profit, sales):
    """Net Profit Margin % = net_profit / sales * 100. None if sales == 0."""
    if sales is None or sales == 0:
        return None
    return (net_profit / sales) * 100


def operating_profit_margin(operating_profit, sales, stated_opm_percentage=None, tolerance_pct=1.0):
    """
    Operating Profit Margin % = operating_profit / sales * 100.
    If stated_opm_percentage is provided (from the profitandloss table),
    cross-check against it and return a warning flag if they differ by
    more than tolerance_pct.

    Returns a dict: {"value": float | None, "mismatch": bool, "stated": float | None}
    """
    if sales is None or sales == 0:
        return {"value": None, "mismatch": False, "stated": stated_opm_percentage}

    computed = (operating_profit / sales) * 100
    mismatch = False
    if stated_opm_percentage is not None:
        mismatch = abs(computed - stated_opm_percentage) > tolerance_pct

    return {"value": computed, "mismatch": mismatch, "stated": stated_opm_percentage}


def return_on_equity(net_profit, equity_capital, reserves):
    """
    ROE % = net_profit / (equity_capital + reserves) * 100.
    Returns None if equity + reserves <= 0 (negative or zero net worth
    makes the ratio meaningless/misleading, not just undefined).
    """
    net_worth = (equity_capital or 0) + (reserves or 0)
    if net_worth <= 0:
        return None
    return (net_profit / net_worth) * 100


def return_on_capital_employed(ebit, equity_capital, reserves, borrowings, broad_sector=None):
    """
    ROCE % = EBIT / (equity_capital + reserves + borrowings) * 100.
    Returns None if capital employed <= 0.

    For companies in the 'Financials' broad_sector (banks, NBFCs, insurance),
    absolute ROCE thresholds are misleading because leverage is structurally
    part of their business model. This function still computes the raw
    number either way, but flags `is_financials_sector=True` so the caller
    (Day 12/13 logic) knows to apply a sector-relative benchmark instead of
    an absolute cutoff, rather than skipping the calculation entirely.
    """
    capital_employed = (equity_capital or 0) + (reserves or 0) + (borrowings or 0)
    if capital_employed <= 0:
        return {"value": None, "is_financials_sector": broad_sector == "Financials"}

    value = (ebit / capital_employed) * 100
    return {"value": value, "is_financials_sector": broad_sector == "Financials"}


def return_on_assets(net_profit, total_assets):
    """ROA % = net_profit / total_assets * 100. Returns None if total_assets == 0."""
    if total_assets is None or total_assets == 0:
        return None
    return (net_profit / total_assets) * 100