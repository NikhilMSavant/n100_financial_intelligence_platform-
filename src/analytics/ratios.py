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


def debt_to_equity(borrowings, equity_capital, reserves, broad_sector=None, threshold=5.0):
    """
    D/E = borrowings / (equity_capital + reserves).
    Returns 0 (not None) if borrowings == 0 - a debt-free company has a
    genuinely zero ratio, not an undefined one.

    high_leverage_flag is True if D/E > threshold AND the company is NOT
    in the Financials sector (banks/NBFCs are structurally high-leverage
    by business model, so the flag is suppressed for them - see Day 13).
    """
    borrowings = borrowings or 0
    net_worth = (equity_capital or 0) + (reserves or 0)

    if borrowings == 0:
        return {"value": 0, "high_leverage_flag": False}

    if net_worth <= 0:
        return {"value": None, "high_leverage_flag": False}

    value = borrowings / net_worth
    is_financials = broad_sector == "Financials"
    high_leverage_flag = (value > threshold) and not is_financials

    return {"value": value, "high_leverage_flag": high_leverage_flag}


def interest_coverage_ratio(operating_profit, other_income, interest, risk_threshold=1.5):
    """
    ICR = (operating_profit + other_income) / interest.
    Returns None with icr_label='Debt Free' if interest == 0 - a company
    with no interest expense isn't "infinitely good", it's just not
    carrying debt, so the numeric ratio is meaningless here.

    icr_warning is True if ICR < risk_threshold (at risk of not covering
    interest payments).
    """
    if interest is None or interest == 0:
        return {"value": None, "icr_label": "Debt Free", "icr_warning": False}

    value = ((operating_profit or 0) + (other_income or 0)) / interest
    icr_warning = value < risk_threshold

    return {"value": value, "icr_label": None, "icr_warning": icr_warning}


def net_debt(borrowings, investments):
    """
    Net Debt = borrowings - investments (investments used as a liquid-asset
    proxy, per spec). Can be negative - that just means liquid investments
    exceed borrowings, i.e. the company is net cash-rich, not "an error".
    """
    return (borrowings or 0) - (investments or 0)


def asset_turnover(sales, total_assets):
    """Asset Turnover = sales / total_assets. Returns None if total_assets == 0."""
    if total_assets is None or total_assets == 0:
        return None
    return sales / total_assets