"""
populate_ratios.py — Sprint 2 / Day 12-13
Runs the ratio engine for all 92 companies across all available years and
writes financial_ratios (SQLite), output/capital_allocation.csv and
output/ratio_edge_cases.log.
"""
import os
import sys
import sqlite3
import logging
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from ratios import (net_profit_margin, operating_profit_margin, opm_cross_check,
                     return_on_equity, roe_reliable_flag, return_on_capital_employed, return_on_assets,
                     debt_to_equity, high_leverage_flag, interest_coverage_ratio,
                     icr_label, icr_warning_flag, net_debt, asset_turnover)
from cagr import cagr_from_series
from cashflow_kpis import (free_cash_flow, cfo_quality_score, capex_intensity,
                            fcf_conversion_rate, capital_allocation_pattern)

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DB_PATH = os.path.join(ROOT, "db", "nifty100.db")
OUT_DIR = os.path.join(ROOT, "output")


def load_frames(conn):
    companies = pd.read_sql("SELECT * FROM companies", conn)
    sectors = pd.read_sql("SELECT * FROM sectors", conn)
    pl = pd.read_sql("SELECT * FROM profitandloss", conn)
    bs = pd.read_sql("SELECT * FROM balancesheet", conn)
    cf = pd.read_sql("SELECT * FROM cashflow", conn)
    return companies, sectors, pl, bs, cf


def build_merged(pl, bs, cf, sectors):
    df = pl.merge(bs, on=["company_id", "year"], how="outer", suffixes=("_pl", "_bs"))
    df = df.merge(cf, on=["company_id", "year"], how="outer")
    df = df.merge(sectors[["company_id", "broad_sector"]], on="company_id", how="left")
    df["ebit"] = df["operating_profit"] + df["other_income"].fillna(0)
    return df.sort_values(["company_id", "year"])


def compute_row_ratios(row):
    npm = net_profit_margin(row.net_profit, row.sales)
    opm_computed = operating_profit_margin(row.operating_profit, row.sales)
    roe = return_on_equity(row.net_profit, row.equity_capital, row.reserves)
    roe_reliable = roe_reliable_flag(row.net_profit, row.equity_capital, row.reserves, row.total_assets)
    roce = return_on_capital_employed(row.ebit, row.equity_capital, row.reserves, row.borrowings)
    roa = return_on_assets(row.net_profit, row.total_assets)
    de = debt_to_equity(row.borrowings, row.equity_capital, row.reserves)
    hlf = high_leverage_flag(de, row.broad_sector)
    icr = interest_coverage_ratio(row.operating_profit, row.other_income, row.interest)
    icr_lbl = icr_label(icr)
    icr_warn = icr_warning_flag(icr)
    ndebt = net_debt(row.borrowings, row.investments)
    at = asset_turnover(row.sales, row.total_assets)
    fcf = free_cash_flow(row.operating_activity, row.investing_activity)
    capex_pct, capex_lbl = capex_intensity(row.investing_activity, row.sales)
    fcf_conv = fcf_conversion_rate(fcf, row.operating_profit)
    eps = row.eps
    bvps = None
    if row.equity_capital is not None and row.reserves is not None and row.face_value not in (None, 0):
        try:
            shares_cr = row.equity_capital / row.face_value  # equity_capital / face_value = shares (in crore units, matches book_value scale)
            bvps = (row.equity_capital + row.reserves) / shares_cr if shares_cr else None
        except (TypeError, ZeroDivisionError):
            bvps = None
    return dict(
        net_profit_margin_pct=npm, operating_profit_margin_pct=opm_computed,
        return_on_equity_pct=roe, roe_reliable_flag=(int(roe_reliable) if roe_reliable is not None else None),
        return_on_capital_employed_pct=roce, return_on_assets_pct=roa,
        debt_to_equity=de, high_leverage_flag=int(bool(hlf)),
        interest_coverage=icr, icr_label=icr_lbl, icr_warning_flag=int(bool(icr_warn)),
        net_debt_cr=ndebt, asset_turnover=at,
        free_cash_flow_cr=fcf, capex_cr=row.investing_activity,
        earnings_per_share=eps, book_value_per_share=bvps,
        dividend_payout_ratio_pct=row.dividend_payout, total_debt_cr=row.borrowings,
        cash_from_operations_cr=row.operating_activity,
        capex_intensity_pct=capex_pct, fcf_conversion_pct=fcf_conv,
        opm_cross_check_mismatch=(opm_cross_check(opm_computed, row.opm_percentage) is False),
    )


def run():
    os.makedirs(OUT_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    companies, sectors, pl, bs, cf = load_frames(conn)
    companies_fv = companies[["company_id", "face_value", "roce_percentage", "roe_percentage"]]

    merged = build_merged(pl, bs, cf, sectors)
    merged = merged.merge(companies_fv, on="company_id", how="left")

    logging.basicConfig(filename=os.path.join(OUT_DIR, "ratio_edge_cases.log"), level=logging.INFO,
                         format="%(message)s", filemode="w")
    log = logging.getLogger("ratio_edge_cases")

    rows_out = []
    capital_alloc_rows = []

    for cid, g in merged.groupby("company_id"):
        g = g.sort_values("year").reset_index(drop=True)
        years = g["year"].tolist()
        pat_series = list(zip(years, g["net_profit"]))
        rev_series = list(zip(years, g["sales"]))
        eps_series = list(zip(years, g["eps"]))
        cfo_pat_by_year = {}

        for i, row in g.iterrows():
            base = compute_row_ratios(row)

            for window in (3, 5, 10):
                rv, rf = cagr_from_series(rev_series, window)
                pv, pf = cagr_from_series(pat_series, window)
                ev, ef = cagr_from_series(eps_series, window)
                base[f"revenue_cagr_{window}yr"], base[f"revenue_cagr_{window}yr_flag"] = rv, rf
                base[f"pat_cagr_{window}yr"], base[f"pat_cagr_{window}yr_flag"] = pv, pf
                base[f"eps_cagr_{window}yr"], base[f"eps_cagr_{window}yr_flag"] = ev, ef

            # CFO Quality Score — trailing up to 5 years CFO/PAT
            cfo, pat = row.operating_activity, row.net_profit
            cfo_pat_ratio = (cfo / pat) if (cfo is not None and pat) else None
            cfo_pat_by_year[row.year] = cfo_pat_ratio
            trailing = [cfo_pat_by_year.get(y) for y in range(row.year - 4, row.year + 1)]
            cfo_q_score, cfo_q_label = cfo_quality_score(trailing)
            base["cfo_quality_score"] = cfo_q_score

            # Capital allocation pattern
            label, s_cfo, s_cfi, s_cff = capital_allocation_pattern(
                row.operating_activity, row.investing_activity, row.financing_activity, cfo_pat_ratio)
            if label is not None:
                capital_alloc_rows.append(dict(company_id=cid, year=row.year, cfo_sign=s_cfo,
                                                cfi_sign=s_cfi, cff_sign=s_cff, pattern_label=label))

            # Composite quality score placeholder (finalised with winsorisation in Sprint 3)
            base["composite_quality_score"] = None

            if base.pop("opm_cross_check_mismatch"):
                log.info(f"[OPM] {cid} {row.year}: computed={base['operating_profit_margin_pct']} "
                         f"stored={row.opm_percentage} diff>1pp")

            base["company_id"], base["year"] = cid, int(row.year)
            rows_out.append(base)

        # Bank ROCE / ROE carve-out cross-check (Day 13) vs companies.xlsx pre-computed values
        roce_src = g["roce_percentage"].iloc[-1] if len(g) else None
        roe_src = g["roe_percentage"].iloc[-1] if len(g) else None
        latest = [r for r in rows_out if r["company_id"] == cid][-1] if rows_out else None
        if latest and roce_src is not None and latest.get("return_on_capital_employed_pct") is not None:
            diff = abs(latest["return_on_capital_employed_pct"] - roce_src)
            if diff > 5:
                category = "version difference" if diff < 15 else "data source issue"
                log.info(f"[ROCE] {cid}: engine={latest['return_on_capital_employed_pct']:.1f}% "
                         f"source={roce_src:.1f}% diff={diff:.1f}pp category={category}")
        if latest and roe_src is not None and latest.get("return_on_equity_pct") is not None:
            diff = abs(latest["return_on_equity_pct"] - roe_src)
            if diff > 5:
                category = "formula discrepancy" if roe_src < 5 else "version difference"
                log.info(f"[ROE] {cid}: engine={latest['return_on_equity_pct']:.2f}% "
                         f"source={roe_src:.2f}% diff={diff:.1f}pp category={category} "
                         f"(engine value used for analytics, source value for display only)")

    ratios_df = pd.DataFrame(rows_out)

    # ---- composite_quality_score (first pass, absolute scale; refined with
    # winsorisation + sector-relative normalisation by screener/composite_score.py in Sprint 3) ----
    def minmax(s):
        s = s.astype(float)
        lo, hi = s.quantile(0.10), s.quantile(0.90)
        if hi == lo:
            return s * 0 + 50
        return ((s.clip(lo, hi) - lo) / (hi - lo) * 100)

    latest_year = ratios_df["year"].max()
    comp_cols = ["return_on_equity_pct", "return_on_capital_employed_pct", "net_profit_margin_pct",
                 "free_cash_flow_cr", "revenue_cagr_5yr", "pat_cagr_5yr"]
    scored = ratios_df.copy()
    for c in comp_cols:
        scored[c + "_n"] = minmax(scored[c].fillna(scored[c].median()))
    scored["composite_quality_score"] = (
        0.15 * scored["return_on_equity_pct_n"] + 0.10 * scored["return_on_capital_employed_pct_n"] +
        0.10 * scored["net_profit_margin_pct_n"] + 0.20 * scored["free_cash_flow_cr_n"] +
        0.10 * scored["revenue_cagr_5yr_n"] + 0.10 * scored["pat_cagr_5yr_n"] +
        # leverage component: reward low D/E, high ICR
        0.10 * (100 - minmax(scored["debt_to_equity"].fillna(scored["debt_to_equity"].median()))) +
        0.15 * minmax(scored["interest_coverage"].fillna(scored["interest_coverage"].median()))
    ).round(2)
    ratios_df["composite_quality_score"] = scored["composite_quality_score"]

    ratios_df = ratios_df[[
        "company_id", "year", "net_profit_margin_pct", "operating_profit_margin_pct",
        "return_on_equity_pct", "roe_reliable_flag", "return_on_capital_employed_pct", "return_on_assets_pct",
        "debt_to_equity", "high_leverage_flag", "interest_coverage", "icr_label", "icr_warning_flag",
        "net_debt_cr", "asset_turnover", "free_cash_flow_cr", "capex_cr", "earnings_per_share",
        "book_value_per_share", "dividend_payout_ratio_pct", "total_debt_cr", "cash_from_operations_cr",
        "revenue_cagr_3yr", "revenue_cagr_3yr_flag", "revenue_cagr_5yr", "revenue_cagr_5yr_flag",
        "revenue_cagr_10yr", "revenue_cagr_10yr_flag", "pat_cagr_3yr", "pat_cagr_3yr_flag",
        "pat_cagr_5yr", "pat_cagr_5yr_flag", "pat_cagr_10yr", "pat_cagr_10yr_flag",
        "eps_cagr_3yr", "eps_cagr_3yr_flag", "eps_cagr_5yr", "eps_cagr_5yr_flag",
        "eps_cagr_10yr", "eps_cagr_10yr_flag", "cfo_quality_score", "capex_intensity_pct",
        "fcf_conversion_pct", "composite_quality_score",
    ]]

    conn.execute("DELETE FROM financial_ratios")
    ratios_df.to_sql("financial_ratios", conn, if_exists="append", index=False)
    conn.commit()

    cap_df = pd.DataFrame(capital_alloc_rows)
    cap_df.to_csv(os.path.join(OUT_DIR, "capital_allocation.csv"), index=False)

    n_rows = conn.execute("SELECT COUNT(*) FROM financial_ratios").fetchone()[0]
    print(f"financial_ratios populated: {n_rows} rows")
    print(f"capital_allocation.csv: {len(cap_df)} rows")
    non_null_cols = [c for c in ratios_df.columns if ratios_df[c].notna().any()]
    print(f"Non-null KPI columns: {len(non_null_cols)}/{len(ratios_df.columns)}")
    conn.close()
    return ratios_df


if __name__ == "__main__":
    run()
