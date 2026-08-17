"""Sprint 2 — Profitability, leverage & efficiency ratio formulas.
All functions are pure and operate on plain numbers so they are trivially
unit-testable; batch application to DataFrames happens in populate_ratios.py.
"""
import math


def net_profit_margin(net_profit, sales):
    if sales in (0, None) or (isinstance(sales, float) and math.isnan(sales)):
        return None
    return net_profit / sales * 100


def operating_profit_margin(operating_profit, sales):
    if not sales:
        return None
    return operating_profit / sales * 100


def return_on_equity(net_profit, equity_capital, reserves):
    equity = (equity_capital or 0) + (reserves or 0)
    if equity <= 0:
        return None
    return net_profit / equity * 100


def return_on_capital_employed(ebit, equity_capital, reserves, borrowings):
    capital_employed = (equity_capital or 0) + (reserves or 0) + (borrowings or 0)
    if capital_employed <= 0:
        return None
    return ebit / capital_employed * 100


def return_on_assets(net_profit, total_assets):
    if not total_assets:
        return None
    return net_profit / total_assets * 100


def debt_to_equity(borrowings, equity_capital, reserves):
    equity = (equity_capital or 0) + (reserves or 0)
    if not borrowings:
        return 0.0
    if equity <= 0:
        return None
    return borrowings / equity


def high_leverage_flag(de, is_financial_sector):
    if de is None or is_financial_sector:
        return False
    return de > 5


def interest_coverage(operating_profit, other_income, interest):
    if not interest:
        return None  # debt-free -> caller sets icr_label='Debt Free'
    return ((operating_profit or 0) + (other_income or 0)) / interest


def icr_label(icr):
    return "Debt Free" if icr is None else None


def icr_warning_flag(icr):
    return icr is not None and icr < 1.5


def net_debt(borrowings, investments):
    return (borrowings or 0) - (investments or 0)


def asset_turnover(sales, total_assets):
    if not total_assets:
        return None
    return sales / total_assets
