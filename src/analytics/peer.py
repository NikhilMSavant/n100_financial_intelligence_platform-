"""
peer.py
-------
Day 18 deliverable: computes PERCENT_RANK for 10 metrics within each of
the 11 peer groups, populating the peer_percentiles table.

Metrics ranked: ROE, ROCE, Net Profit Margin, D/E (inverted - lower is
better), FCF, PAT CAGR 5yr, Revenue CAGR 5yr, EPS CAGR 5yr, Interest
Coverage, Asset Turnover.
"""
import sqlite3

DB_PATH = "db/nifty100.db"

METRICS = {
    "roe": "return_on_equity_pct",
    "roce": "return_on_capital_employed_pct",
    "net_profit_margin": "net_profit_margin_pct",
    "debt_to_equity": "debt_to_equity",  # inverted below - lower D/E = higher percentile
    "fcf": "free_cash_flow_cr",
    "pat_cagr_5yr": "pat_cagr_5yr",
    "revenue_cagr_5yr": "revenue_cagr_5yr",
    "eps_cagr_5yr": "eps_cagr_5yr",
    "interest_coverage": "interest_coverage",
    "asset_turnover": "asset_turnover",
}

INVERTED_METRICS = {"debt_to_equity"}  # lower raw value = better = higher percentile


def percent_rank(values):
    """
    Given a list of (company_id, value) tuples (value may be None),
    returns {company_id: percentile_rank} using the standard PERCENT_RANK
    formula: rank / (n - 1), where rank is 0-indexed position after
    sorting ascending. Companies with a None value get None (can't be
    ranked without a real number). If there's only 1 company with a
    valid value, its percentile is defined as 1.0 (top of a group of one).
    """
    valid = [(cid, v) for cid, v in values if v is not None]
    result = {cid: None for cid, v in values if v is None}

    if not valid:
        return result

    if len(valid) == 1:
        result[valid[0][0]] = 1.0
        return result

    valid.sort(key=lambda x: x[1])
    n = len(valid)
    for idx, (cid, v) in enumerate(valid):
        result[cid] = idx / (n - 1)

    return result


def compute_peer_percentiles(db_path=DB_PATH):
    """
    Computes percentile ranks for all 10 metrics within each of the 11
    peer groups, using each company's latest fiscal year of financial_ratios
    data. Returns a list of dicts ready to insert into peer_percentiles:
    {company_id, peer_group_name, metric, value, percentile_rank, year}
    """
    conn = sqlite3.connect(db_path)

    peer_groups = conn.execute("SELECT DISTINCT peer_group_name FROM peer_groups").fetchall()
    peer_groups = [row[0] for row in peer_groups]

    output_rows = []

    for group_name in peer_groups:
        members = conn.execute(
            "SELECT company_id FROM peer_groups WHERE peer_group_name = ?", (group_name,)
        ).fetchall()
        member_ids = [row[0] for row in members]

        # latest fiscal year's financial_ratios row per member company
        placeholders = ",".join("?" * len(member_ids))
        rows = conn.execute(f"""
            SELECT fr.company_id, fr.year, {", ".join("fr." + col for col in set(METRICS.values()))}
            FROM financial_ratios fr
            WHERE fr.company_id IN ({placeholders})
            AND fr.year = (
                SELECT MAX(year) FROM financial_ratios fr2
                WHERE fr2.company_id = fr.company_id AND fr2.year != 'TTM'
            )
        """, member_ids).fetchall()

        col_names = ["company_id", "year"] + list(set(METRICS.values()))
        data_by_company = {r[0]: dict(zip(col_names, r)) for r in rows}

        for metric_key, column in METRICS.items():
            values = []
            for cid in member_ids:
                row = data_by_company.get(cid)
                raw_value = row[column] if row else None
                values.append((cid, raw_value))

            percentiles = percent_rank(values)

            if metric_key in INVERTED_METRICS:
                percentiles = {cid: (1 - p if p is not None else None) for cid, p in percentiles.items()}

            for cid, raw_value in values:
                row = data_by_company.get(cid)
                year = row["year"] if row else None
                output_rows.append({
                    "company_id": cid,
                    "peer_group_name": group_name,
                    "metric": metric_key,
                    "value": raw_value,
                    "percentile_rank": percentiles.get(cid),
                    "year": year,
                })

    conn.close()
    return output_rows


def populate_peer_percentiles_table(db_path=DB_PATH):
    """Writes compute_peer_percentiles() output into the peer_percentiles
    table, plus a 'No peer group assigned' row for every company not in
    any peer group - so a caller querying this table for ANY company
    always gets a result, never a silent absence."""
    rows = compute_peer_percentiles(db_path)

    conn = sqlite3.connect(db_path)

    all_companies = [r[0] for r in conn.execute("SELECT company_id FROM companies").fetchall()]
    companies_with_groups = {r["company_id"] for r in rows}
    companies_without_groups = [c for c in all_companies if c not in companies_with_groups]

    for cid in companies_without_groups:
        rows.append({
            "company_id": cid,
            "peer_group_name": None,
            "metric": "No peer group assigned",
            "value": None,
            "percentile_rank": None,
            "year": None,
        })

    conn.execute("DELETE FROM peer_percentiles")
    conn.executemany("""
        INSERT INTO peer_percentiles (company_id, peer_group_name, metric, value, percentile_rank, year)
        VALUES (:company_id, :peer_group_name, :metric, :value, :percentile_rank, :year)
    """, rows)
    conn.commit()

    count = conn.execute("SELECT COUNT(*) FROM peer_percentiles").fetchone()[0]
    conn.close()
    return count


if __name__ == "__main__":
    count = populate_peer_percentiles_table()
    print(f"Wrote {count} rows into peer_percentiles")