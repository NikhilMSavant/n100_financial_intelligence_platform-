"""
ratios.py — Sprint 2 / Day 08-09
Profitability, leverage & efficiency ratio functions. Every function is pure
(takes plain numbers, returns a value or None) so it's trivially unit-testable.
"""
import math


def _safe(v):
    if v is None:
        return None
    try:
        if isinstance(v, float) and math.isnan(v):
            return None
    except TypeError:
        return v
    return v


# ---------- Day 08: Profitability ----------

def net_profit_margin(net_profit, sales):
    net_profit, sales = _safe(net_profit), _safe(sales)
    if not sales or net_profit is None:
        return None
    return net_profit / sales * 100


def operating_profit_margin(operating_profit, sales):
    operating_profit, sales = _safe(operating_profit), _safe(sales)
    if not sales or operating_profit is None:
        return None
    return operating_profit / sales * 100


def opm_cross_check(computed_opm, stored_opm_pct, tolerance=1.0):
    """Returns True if computed and stored OPM agree within `tolerance` pp."""
    if computed_opm is None or stored_opm_pct is None:
        return None
    return abs(computed_opm - stored_opm_pct) <= tolerance


def return_on_equity(net_profit, equity_capital, reserves):
    net_profit, equity_capital, reserves = _safe(net_profit), _safe(equity_capital), _safe(reserves)
    if equity_capital is None or reserves is None or net_profit is None:
        return None
    denom = equity_capital + reserves
    if denom <= 0:
        return None
    return net_profit / denom * 100


def roe_reliable_flag(net_profit, equity_capital, reserves, total_assets, equity_threshold_pct=5.0):
    """
    ROE = net_profit / net_worth is mathematically well-defined even when the
    inputs are economically implausible, so this flags two distinct failure
    modes rather than just one:
      1. Thin equity base: net worth is a tiny sliver of total assets (e.g.
         after large buybacks), so ROE can look enormous even with a normal
         profit -- ROE is "real" but not a meaningful efficiency signal.
      2. Implausible profit scale: net_profit exceeds total_assets outright
         (ROA > 100%), which isn't achievable by a real business in a single
         year -- this points to a units/scale mismatch in the source data
         between the P&L and balance-sheet figures, not a thin-equity effect.
    Returns False if either condition holds, True if neither does, None if
    required inputs are missing.
    """
    net_profit = _safe(net_profit)
    equity_capital, reserves, total_assets = _safe(equity_capital), _safe(reserves), _safe(total_assets)
    if equity_capital is None or reserves is None or not total_assets:
        return None
    net_worth = equity_capital + reserves
    thin_equity = net_worth <= 0 or (net_worth / total_assets * 100) < equity_threshold_pct
    implausible_profit_scale = net_profit is not None and abs(net_profit) > total_assets
    return not (thin_equity or implausible_profit_scale)


def return_on_capital_employed(ebit, equity_capital, reserves, borrowings):
    ebit, equity_capital, reserves, borrowings = (_safe(x) for x in (ebit, equity_capital, reserves, borrowings))
    if None in (ebit, equity_capital, reserves, borrowings):
        return None
    denom = equity_capital + reserves + borrowings
    if denom <= 0:
        return None
    return ebit / denom * 100


def return_on_assets(net_profit, total_assets):
    net_profit, total_assets = _safe(net_profit), _safe(total_assets)
    if not total_assets or net_profit is None:
        return None
    return net_profit / total_assets * 100


# ---------- Day 09: Leverage & Efficiency ----------

def debt_to_equity(borrowings, equity_capital, reserves):
    borrowings, equity_capital, reserves = _safe(borrowings), _safe(equity_capital), _safe(reserves)
    if not borrowings:
        return 0.0
    denom = (equity_capital or 0) + (reserves or 0)
    if denom <= 0:
        return None
    return borrowings / denom


def high_leverage_flag(de_ratio, broad_sector, threshold=5.0):
    if de_ratio is None:
        return False
    if broad_sector == "Financials":
        return False
    return de_ratio > threshold


def interest_coverage_ratio(operating_profit, other_income, interest):
    operating_profit, other_income, interest = _safe(operating_profit), _safe(other_income), _safe(interest)
    if not interest:
        return None
    return ((operating_profit or 0) + (other_income or 0)) / interest


def icr_label(icr):
    return "Debt Free" if icr is None else None


def icr_warning_flag(icr, threshold=1.5):
    if icr is None:
        return False
    return icr < threshold


def net_debt(borrowings, investments):
    borrowings, investments = _safe(borrowings), _safe(investments)
    if borrowings is None:
        return None
    return borrowings - (investments or 0)


def asset_turnover(sales, total_assets):
    sales, total_assets = _safe(sales), _safe(total_assets)
    if not total_assets or sales is None:
        return None
    return sales / total_assets


if __name__ == "__main__":
    print("net_profit_margin(100,1000) =", net_profit_margin(100, 1000))
    print("debt_to_equity(0, 10, 90) =", debt_to_equity(0, 10, 90))
    print("interest_coverage_ratio(100,10,0) =", interest_coverage_ratio(100, 10, 0), icr_label(None))
