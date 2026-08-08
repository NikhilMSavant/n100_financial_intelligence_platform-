import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src", "analytics"))
from ratios import (net_profit_margin, operating_profit_margin, opm_cross_check,
                     return_on_equity, roe_reliable_flag,
                     return_on_capital_employed, return_on_assets,
                     debt_to_equity, high_leverage_flag, interest_coverage_ratio,
                     icr_label, icr_warning_flag, net_debt, asset_turnover)


def test_npm_normal():
    assert net_profit_margin(100, 1000) == 10.0


def test_npm_zero_sales_is_none():
    assert net_profit_margin(100, 0) is None


def test_roe_normal():
    assert round(return_on_equity(100, 10, 90), 2) == 100.0


def test_roe_negative_equity_is_none():
    assert return_on_equity(100, -50, -60) is None


def test_roe_zero_denom_is_none():
    assert return_on_equity(100, 0, 0) is None


def test_opm_cross_check_within_tolerance():
    assert opm_cross_check(12.3, 12.9) is True


def test_opm_cross_check_mismatch():
    assert opm_cross_check(10.0, 15.0) is False


def test_roce_normal():
    assert round(return_on_capital_employed(200, 10, 90, 100), 2) == 100.0


def test_roa_zero_assets_is_none():
    assert return_on_assets(100, 0) is None


def test_de_debtfree_returns_zero_not_none():
    assert debt_to_equity(0, 10, 90) == 0.0


def test_de_normal():
    assert debt_to_equity(200, 10, 90) == 2.0


def test_de_negative_networth_is_none():
    assert debt_to_equity(100, -10, -20) is None


def test_high_leverage_flag_true_nonfinancial():
    assert high_leverage_flag(6.0, "Industrials") is True


def test_high_leverage_flag_suppressed_for_financials():
    assert high_leverage_flag(10.0, "Financials") is False


def test_icr_interest_zero_returns_none():
    assert interest_coverage_ratio(100, 10, 0) is None


def test_icr_label_debt_free():
    assert icr_label(None) == "Debt Free"


def test_icr_label_normal_is_none():
    assert icr_label(5.0) is None


def test_icr_warning_flag_low():
    assert icr_warning_flag(1.2) is True


def test_icr_warning_flag_ok():
    assert icr_warning_flag(3.0) is False


def test_net_debt():
    assert net_debt(500, 120) == 380


def test_asset_turnover_zero_assets_is_none():
    assert asset_turnover(1000, 0) is None


def test_roe_reliable_normal_case():
    # net_profit well within total_assets, healthy equity base -> reliable
    assert roe_reliable_flag(100, 300, 700, 5000) is True


def test_roe_reliable_flags_thin_equity_base():
    # net worth is 2% of total assets -> flagged unreliable even with sane profit
    assert roe_reliable_flag(10, 5, 15, 1000) is False


def test_roe_reliable_flags_implausible_profit_scale():
    # net_profit (7595) exceeds total_assets (476) -- economically impossible
    # in a single year, points to a units/scale mismatch in source data
    assert roe_reliable_flag(7595, 5, 202, 476) is False


def test_roe_reliable_none_when_total_assets_missing():
    assert roe_reliable_flag(100, 10, 90, None) is None


def test_roe_reliable_false_for_negative_net_worth():
    assert roe_reliable_flag(100, -50, -60, 1000) is False
