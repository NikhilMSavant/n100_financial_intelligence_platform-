"""
export_peer_comparison.py
--------------------------
Day 20 deliverable: generates output/peer_comparison.xlsx - 11 sheets,
one per peer group, with percentile-colored cells, benchmark row
highlighting, and a median summary row.
"""
import sqlite3
import os

from openpyxl import Workbook
from openpyxl.styles import PatternFill, Font

DB_PATH = "db/nifty100.db"
OUT_PATH = "output/peer_comparison.xlsx"

GREEN_FILL = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
YELLOW_FILL = PatternFill(start_color="FFEB9C", end_color="FFEB9C", fill_type="solid")
RED_FILL = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
BENCHMARK_FILL = PatternFill(start_color="FFD966", end_color="FFD966", fill_type="solid")  # gold/amber
HEADER_FONT = Font(bold=True)
SUMMARY_FONT = Font(bold=True, italic=True)

METRIC_ORDER = ["roe", "roce", "net_profit_margin", "debt_to_equity", "fcf",
                "pat_cagr_5yr", "revenue_cagr_5yr", "eps_cagr_5yr",
                "interest_coverage", "asset_turnover"]

METRIC_LABELS = {
    "roe": "ROE %", "roce": "ROCE %", "net_profit_margin": "NPM %",
    "debt_to_equity": "D/E", "fcf": "FCF (Cr)", "pat_cagr_5yr": "PAT CAGR 5yr %",
    "revenue_cagr_5yr": "Revenue CAGR 5yr %", "eps_cagr_5yr": "EPS CAGR 5yr %",
    "interest_coverage": "Interest Coverage", "asset_turnover": "Asset Turnover",
}


def percentile_fill(percentile):
    if percentile is None:
        return None
    if percentile >= 0.75:
        return GREEN_FILL
    if percentile >= 0.25:
        return YELLOW_FILL
    return RED_FILL


def build_group_sheet(wb, group_name, conn):
    ws = wb.create_sheet(title=group_name[:31])

    members = conn.execute(
        "SELECT company_id, is_benchmark FROM peer_groups WHERE peer_group_name = ?", (group_name,)
    ).fetchall()
    member_ids = [m[0] for m in members]
    benchmark_ids = {m[0] for m in members if m[1] == 1}

    names = dict(conn.execute(
        f"SELECT company_id, company_name FROM companies WHERE company_id IN ({','.join('?' * len(member_ids))})",
        member_ids,
    ).fetchall())

    percentile_rows = conn.execute(f"""
        SELECT company_id, metric, value, percentile_rank
        FROM peer_percentiles
        WHERE peer_group_name = ?
    """, (group_name,)).fetchall()

    data = {}
    for cid, metric, value, pct in percentile_rows:
        data.setdefault(cid, {})[metric] = (value, pct)

    # Header row
    headers = ["company_id", "company_name"]
    for m in METRIC_ORDER:
        headers.append(METRIC_LABELS[m])
        headers.append(f"{METRIC_LABELS[m]} %ile")

    for col_idx, h in enumerate(headers, start=1):
        cell = ws.cell(row=1, column=col_idx, value=h)
        cell.font = HEADER_FONT
        ws.column_dimensions[cell.column_letter].width = max(len(h) + 2, 12)

    # Data rows
    for row_idx, cid in enumerate(member_ids, start=2):
        ws.cell(row=row_idx, column=1, value=cid)
        ws.cell(row=row_idx, column=2, value=names.get(cid))

        col_idx = 3
        for m in METRIC_ORDER:
            value, pct = data.get(cid, {}).get(m, (None, None))
            value_cell = ws.cell(row=row_idx, column=col_idx, value=value)
            pct_cell = ws.cell(row=row_idx, column=col_idx + 1, value=pct)
            fill = percentile_fill(pct)
            if fill:
                pct_cell.fill = fill
            col_idx += 2

        if cid in benchmark_ids:
            for c in range(1, len(headers) + 1):
                ws.cell(row=row_idx, column=c).fill = BENCHMARK_FILL

    # Median summary row
    summary_row = len(member_ids) + 2
    ws.cell(row=summary_row, column=1, value="MEDIAN").font = SUMMARY_FONT
    col_idx = 3
    for m in METRIC_ORDER:
        values = [data.get(cid, {}).get(m, (None, None))[0] for cid in member_ids]
        values = [v for v in values if v is not None]
        median = sorted(values)[len(values) // 2] if values else None
        if values and len(values) % 2 == 0:
            median = (sorted(values)[len(values) // 2 - 1] + sorted(values)[len(values) // 2]) / 2
        cell = ws.cell(row=summary_row, column=col_idx, value=median)
        cell.font = SUMMARY_FONT
        col_idx += 2

    return len(member_ids)


def main():
    conn = sqlite3.connect(DB_PATH)
    groups = [r[0] for r in conn.execute("SELECT DISTINCT peer_group_name FROM peer_groups ORDER BY peer_group_name").fetchall()]

    wb = Workbook()
    wb.remove(wb.active)

    for group_name in groups:
        n = build_group_sheet(wb, group_name, conn)
        print(f"{group_name}: {n} companies")

    conn.close()

    os.makedirs("output", exist_ok=True)
    wb.save(OUT_PATH)
    print(f"\nWrote {OUT_PATH} with {len(groups)} sheets")


if __name__ == "__main__":
    main()