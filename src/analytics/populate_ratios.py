"""Sprint 2 — Day 12/13: run the full ratio engine for all 92 companies across
all available years and populate the financial_ratios table in SQLite."""
import sqlite3
import sys
import pathlib
import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from analytics import ratios as R
from analytics import cagr as C
from analytics import cashflow_kpis as CF

DB_PATH = "data/nifty100.db"


def load_tables(conn):
    pl = pd.read_sql("SELECT * FROM profitandloss", conn)
    bs = pd.read_sql("SELECT * FROM balancesheet", conn)
    cf = pd.read_sql("SELECT * FROM cashflow", conn)
    sectors = pd.read_sql("SELECT * FROM sectors", conn)
    return pl, bs, cf, sectors


def build_merged(pl, bs, cf, sectors):
    df = pl.merge(bs, on=["company_id", "year"], how="outer", suffixes=("", "_bs"))
    df = df.merge(cf, on=["company_id", "year"], how="outer", suffixes=("", "_cf"))
    df = df.merge(sectors[["company_id", "broad_sector"]], on="company_id", how="left")
    df = df.sort_values(["company_id", "year"]).reset_index(drop=True)
    df["ebit"] = df["operating_profit"] - df["depreciation"].fillna(0)
    return df


def run(log_edge_cases=True):
    conn = sqlite3.connect(DB_PATH)
    pl, bs, cf, sectors = load_tables(conn)
    companies = pd.read_sql("SELECT id AS company_id, face_value FROM companies", conn)
    df = build_merged(pl, bs, cf, sectors)
    df = df.merge(companies, on="company_id", how="left")

    edge_log_lines = []
    out_rows = []
    capital_alloc_rows = []

    for cid, g in df.groupby("company_id"):
        g = g.sort_values("year").reset_index(drop=True)
        is_financial = (g["broad_sector"].iloc[0] == "Financials") if pd.notna(g["broad_sector"].iloc[0]) else False
        n = len(g)

        # pre-compute CFO/PAT ratio series for 5yr rolling quality score
        g["cfo_pat"] = g.apply(lambda r: CF.cfo_pat_ratio(r.get("operating_activity"), r.get("net_profit")), axis=1)
        has_cf_data = g["operating_activity"].notna() & g["investing_activity"].notna() & g["financing_activity"].notna()

        for i in range(n):
            row = g.iloc[i]
            year = row["year"]
            sales, net_profit = row.get("sales"), row.get("net_profit")
            eq_cap, reserves, borrowings = row.get("equity_capital"), row.get("reserves"), row.get("borrowings")
            total_assets = row.get("total_assets")
            op_profit, other_income, interest = row.get("operating_profit"), row.get("other_income"), row.get("interest")
            ebit = row.get("ebit")
            cfo, cfi, cff = row.get("operating_activity"), row.get("investing_activity"), row.get("financing_activity")
            investments = row.get("investments")

            npm = R.net_profit_margin(net_profit, sales)
            opm = R.operating_profit_margin(op_profit, sales)
            if pd.notna(row.get("opm_percentage")) and opm is not None and abs(row["opm_percentage"] - opm) > 1:
                edge_log_lines.append(f"{cid},{year},OPM_CROSSCHECK_MISMATCH,source={row['opm_percentage']},computed={opm:.2f}")

            roe = R.return_on_equity(net_profit, eq_cap, reserves)
            if roe is None and (eq_cap is not None or reserves is not None):
                edge_log_lines.append(f"{cid},{year},ROE_NEGATIVE_EQUITY,equity_plus_reserves={(eq_cap or 0)+(reserves or 0):.1f}")

            roce = R.return_on_capital_employed(ebit, eq_cap, reserves, borrowings)
            roa = R.return_on_assets(net_profit, total_assets)

            de = R.debt_to_equity(borrowings, eq_cap, reserves)
            hlf = R.high_leverage_flag(de, is_financial)

            icr = R.interest_coverage(op_profit, other_income, interest)
            icr_lbl = R.icr_label(icr)
            if icr is None:
                edge_log_lines.append(f"{cid},{year},ICR_DEBT_FREE,interest={interest}")
            icr_warn = R.icr_warning_flag(icr)

            ndebt = R.net_debt(borrowings, investments)
            atr = R.asset_turnover(sales, total_assets)

            fcf = CF.free_cash_flow(cfo, cfi)
            capex_pct, capex_lbl = CF.capex_intensity(cfi, sales)
            fcf_conv = CF.fcf_conversion_rate(fcf, op_profit)

            # 5yr trailing CFO/PAT quality score
            window = g["cfo_pat"].iloc[max(0, i - 4): i + 1].tolist()
            cfo_pat_avg, cfo_quality_lbl = CF.cfo_quality_score(window)

            cfo_s, cfi_s, cff_s, pattern_label = CF.capital_allocation_pattern(cfo, cfi, cff, cfo_pat_avg)
            if not has_cf_data.iloc[i]:
                cfo_s = cfi_s = cff_s = pattern_label = None  # no CF statement for this snapshot - don't classify
            capital_alloc_rows.append(dict(company_id=cid, year=year, cfo_sign=cfo_s, cfi_sign=cfi_s,
                                            cff_sign=cff_s, pattern_label=pattern_label))

            def get_n_back(field, n_back):
                j = i - n_back
                return g[field].iloc[j] if j >= 0 else None

            def cagr_for(field, n_years):
                start = get_n_back(field, n_years)
                end = row.get(field)
                avail = i + 1
                val, flag = C.cagr(start, end, n_years, n_available_years=avail if avail < n_years else None)
                if flag == "TURNAROUND":
                    edge_log_lines.append(f"{cid},{year},CAGR_TURNAROUND,field={field},window={n_years}yr")
                elif flag == "DECLINE_TO_LOSS":
                    edge_log_lines.append(f"{cid},{year},CAGR_DECLINE_TO_LOSS,field={field},window={n_years}yr")
                return val, flag

            rev3, rev3f = cagr_for("sales", 3)
            rev5, rev5f = cagr_for("sales", 5)
            rev10, rev10f = cagr_for("sales", 10)
            pat3, pat3f = cagr_for("net_profit", 3)
            pat5, pat5f = cagr_for("net_profit", 5)
            pat10, pat10f = cagr_for("net_profit", 10)
            eps3, eps3f = cagr_for("eps", 3)
            eps5, eps5f = cagr_for("eps", 5)
            eps10, eps10f = cagr_for("eps", 10)

            eps = row.get("eps")
            face_value = row.get("face_value")
            bvps = None
            if eq_cap and face_value:
                num_shares = eq_cap / face_value  # equity_capital / face_value = shares outstanding (crore units cancel)
                if num_shares:
                    bvps = ((eq_cap or 0) + (reserves or 0)) / num_shares

            out_rows.append(dict(
                company_id=cid, year=year,
                net_profit_margin_pct=npm, operating_profit_margin_pct=opm,
                return_on_equity_pct=roe, return_on_capital_employed_pct=roce, return_on_assets_pct=roa,
                debt_to_equity=de, high_leverage_flag=int(hlf),
                interest_coverage=icr, icr_label=icr_lbl, icr_warning_flag=int(icr_warn),
                net_debt_cr=ndebt, asset_turnover=atr,
                revenue_cagr_3yr=rev3, revenue_cagr_3yr_flag=rev3f,
                revenue_cagr_5yr=rev5, revenue_cagr_5yr_flag=rev5f,
                revenue_cagr_10yr=rev10, revenue_cagr_10yr_flag=rev10f,
                pat_cagr_3yr=pat3, pat_cagr_3yr_flag=pat3f,
                pat_cagr_5yr=pat5, pat_cagr_5yr_flag=pat5f,
                pat_cagr_10yr=pat10, pat_cagr_10yr_flag=pat10f,
                eps_cagr_3yr=eps3, eps_cagr_3yr_flag=eps3f,
                eps_cagr_5yr=eps5, eps_cagr_5yr_flag=eps5f,
                eps_cagr_10yr=eps10, eps_cagr_10yr_flag=eps10f,
                free_cash_flow_cr=fcf, capex_cr=abs(cfi) if cfi is not None else None,
                capex_intensity_pct=capex_pct, capex_label=capex_lbl,
                cfo_pat_ratio=cfo_pat_avg, cfo_quality_label=cfo_quality_lbl,
                fcf_conversion_pct=fcf_conv,
                earnings_per_share=eps, book_value_per_share=bvps,
                dividend_payout_ratio_pct=row.get("dividend_payout"),
                total_debt_cr=borrowings, cash_from_operations_cr=cfo,
                composite_quality_score=None,  # computed in Sprint 3 (screener module)
            ))

    ratios_df = pd.DataFrame(out_rows)
    capital_df = pd.DataFrame(capital_alloc_rows)

    # write to SQLite
    conn.execute("DELETE FROM financial_ratios")
    ratios_df.to_sql("financial_ratios", conn, if_exists="append", index=False)
    conn.commit()

    row_count = conn.execute("SELECT COUNT(*) FROM financial_ratios").fetchone()[0]
    conn.close()

    capital_df.to_csv("output/capital_allocation.csv", index=False)
    with open("output/ratio_edge_cases.log", "w") as f:
        f.write("company_id,year,category,detail\n")
        for line in edge_log_lines:
            f.write(line + "\n")

    print(f"financial_ratios rows: {row_count}")
    print(f"capital_allocation.csv rows: {len(capital_df)}")
    print(f"edge cases logged: {len(edge_log_lines)}")
    return row_count


if __name__ == "__main__":
    run()
