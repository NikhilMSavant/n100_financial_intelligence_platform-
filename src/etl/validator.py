"""16 data-quality rules (DQ-01 .. DQ-16). Each rule function returns a list
of violation dicts: {company_id, year, field, issue, severity, rule_id}.
"""
import pandas as pd

CRITICAL, WARNING, INFO = "CRITICAL", "WARNING", "INFO"


def dq01_company_pk_uniqueness(companies: pd.DataFrame):
    v = []
    if companies["id"].nunique() != len(companies):
        dupes = companies[companies["id"].duplicated(keep=False)]["id"].unique()
        for d in dupes:
            v.append(dict(company_id=d, year=None, field="id", issue="Duplicate ticker PK",
                           severity=CRITICAL, rule_id="DQ-01"))
    return v


def dq02_annual_pk_uniqueness(df: pd.DataFrame, table: str):
    v = []
    dupes = df[df.duplicated(subset=["company_id", "year"], keep=False)]
    for _, r in dupes.iterrows():
        v.append(dict(company_id=r["company_id"], year=r["year"], field=f"{table}.pk",
                       issue="Duplicate (company_id, year)", severity=CRITICAL, rule_id="DQ-02"))
    return v


def dq03_fk_integrity(df: pd.DataFrame, valid_ids: set, table: str):
    v = []
    orphans = df[~df["company_id"].isin(valid_ids)]
    for _, r in orphans.iterrows():
        v.append(dict(company_id=r["company_id"], year=r.get("year"), field=f"{table}.company_id",
                       issue="Orphan row - company_id not in companies table", severity=CRITICAL, rule_id="DQ-03"))
    return v


def dq04_bs_balance(bs: pd.DataFrame):
    v = []
    d = bs.copy()
    d["diff"] = (d["total_assets"] - d["total_liabilities"]).abs() / d["total_assets"].replace(0, pd.NA)
    bad = d[d["diff"] > 0.01]
    for _, r in bad.iterrows():
        v.append(dict(company_id=r["company_id"], year=r["year"], field="total_assets/total_liabilities",
                       issue=f"Balance sheet mismatch {r['diff']:.2%}", severity=WARNING, rule_id="DQ-04"))
    return v


def dq05_opm_crosscheck(pl: pd.DataFrame):
    v = []
    d = pl.copy()
    computed = (d["operating_profit"] / d["sales"].replace(0, pd.NA)) * 100
    diff = (d["opm_percentage"] - computed).abs()
    bad = d[diff > 1.0]
    for _, r in bad.iterrows():
        v.append(dict(company_id=r["company_id"], year=r["year"], field="opm_percentage",
                       issue="OPM cross-check diff > 1%", severity=WARNING, rule_id="DQ-05"))
    return v


def dq06_positive_sales(pl: pd.DataFrame):
    v = []
    bad = pl[pl["sales"] <= 0]
    for _, r in bad.iterrows():
        v.append(dict(company_id=r["company_id"], year=r["year"], field="sales",
                       issue="Sales <= 0", severity=WARNING, rule_id="DQ-06"))
    return v


def dq07_year_format(raw_series: pd.Series, table: str):
    from .normaliser import normalize_year
    v = []
    for raw in raw_series:
        if normalize_year(raw) == "PARSE_ERROR":
            v.append(dict(company_id=None, year=raw, field=f"{table}.year",
                           issue=f"Unparseable year value: {raw!r}", severity=CRITICAL, rule_id="DQ-07"))
    return v


def dq08_ticker_format(raw_series: pd.Series, table: str):
    v = []
    for raw in raw_series:
        t = str(raw).strip().upper()
        if not (2 <= len(t) <= 12):
            v.append(dict(company_id=raw, year=None, field=f"{table}.company_id",
                           issue="Ticker length out of range", severity=CRITICAL, rule_id="DQ-08"))
    return v


def dq09_net_cash_check(cf: pd.DataFrame):
    v = []
    d = cf.copy()
    computed = d["operating_activity"] + d["investing_activity"] + d["financing_activity"]
    diff = (d["net_cash_flow"] - computed).abs()
    bad = d[diff > 10]
    for _, r in bad.iterrows():
        v.append(dict(company_id=r["company_id"], year=r["year"], field="net_cash_flow",
                       issue="net_cash_flow != CFO+CFI+CFF (>10cr tolerance)", severity=WARNING, rule_id="DQ-09"))
    return v


def dq10_nonneg_fixed_assets(bs: pd.DataFrame):
    v = []
    bad = bs[bs["fixed_assets"] < 0]
    for _, r in bad.iterrows():
        v.append(dict(company_id=r["company_id"], year=r["year"], field="fixed_assets",
                       issue="Negative fixed_assets", severity=WARNING, rule_id="DQ-10"))
    return v


def dq11_tax_rate_range(pl: pd.DataFrame):
    v = []
    bad = pl[(pl["tax_percentage"] < 0) | (pl["tax_percentage"] > 60)]
    for _, r in bad.iterrows():
        v.append(dict(company_id=r["company_id"], year=r["year"], field="tax_percentage",
                       issue="Tax rate outside 0-60% range", severity=WARNING, rule_id="DQ-11"))
    return v


def dq12_dividend_payout_cap(pl: pd.DataFrame):
    v = []
    bad = pl[pl["dividend_payout"] > 200]
    for _, r in bad.iterrows():
        v.append(dict(company_id=r["company_id"], year=r["year"], field="dividend_payout",
                       issue="Dividend payout > 200%", severity=WARNING, rule_id="DQ-12"))
    return v


def dq13_url_validity_placeholder(documents: pd.DataFrame):
    # Network access disabled in this environment - URLs logged as UNVERIFIED rather than checked live.
    v = []
    for _, r in documents.iterrows():
        if not str(r.get("annual_report", "")).startswith("http"):
            v.append(dict(company_id=r["company_id"], year=r.get("year"), field="Annual_Report",
                           issue="Missing or malformed URL", severity=WARNING, rule_id="DQ-13"))
    return v


def dq14_eps_sign_consistency(pl: pd.DataFrame):
    v = []
    bad = pl[(pl["net_profit"] > 0) & (pl["eps"] <= 0)]
    for _, r in bad.iterrows():
        v.append(dict(company_id=r["company_id"], year=r["year"], field="eps",
                       issue="eps <= 0 while net_profit > 0", severity=WARNING, rule_id="DQ-14"))
    return v


def dq15_bse_asset_balance_strict(bs: pd.DataFrame):
    v = []
    bad = bs[bs["total_assets"] != bs["total_liabilities"]]
    for _, r in bad.iterrows():
        v.append(dict(company_id=r["company_id"], year=r["year"], field="total_assets",
                       issue="Strict assets != liabilities (informational)", severity=INFO, rule_id="DQ-15"))
    return v


def dq16_coverage_check(pl: pd.DataFrame, bs: pd.DataFrame, cf: pd.DataFrame):
    v = []
    for table, name in [(pl, "profitandloss"), (bs, "balancesheet"), (cf, "cashflow")]:
        counts = table.groupby("company_id").size()
        short = counts[counts < 5]
        for cid, n in short.items():
            v.append(dict(company_id=cid, year=None, field=f"{name}.coverage",
                           issue=f"Only {n} years of history (<5)", severity=WARNING, rule_id="DQ-16"))
    return v
