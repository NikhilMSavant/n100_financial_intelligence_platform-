"""
export_screener.py
-------------------
Day 17 deliverable: generates output/screener_output.xlsx - one sheet per
preset, sorted by composite score descending, with green/red fill on
cells that meet/fail that preset's own threshold criteria.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from engine import load_screener_universe, run_preset, PRESETS
from composite_score import compute_scores_for_universe

from openpyxl import Workbook
from openpyxl.styles import PatternFill, Font

OUT_PATH = "output/screener_output.xlsx"

GREEN_FILL = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
RED_FILL = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
HEADER_FONT = Font(bold=True)

# Maps each preset's filter keys to the DataFrame column + comparison type,
# so we know which cells to color and how to judge pass/fail.
# NOTE: only filters expressible as a simple column/threshold comparison
# are colorable this way; presets with custom logic (Dividend Champion's
# payout<80%, Debt-Free Blue Chip's D/E<0.05 & non-Financials, Turnaround
# Watch's D/E trend) are colored based on the equivalent condition,
# documented per-preset below.
PRESET_THRESHOLD_COLUMNS = {
    "Quality Compounder": [
        ("return_on_equity_pct", ">=", 15), ("debt_to_equity", "<=", 1.0),
        ("free_cash_flow_cr", ">=", 0), ("revenue_cagr_5yr", ">=", 10),
    ],
    "Value Pick": [
        ("pe_ratio", "<=", 30), ("pb_ratio", "<=", 5.0),
        ("debt_to_equity", "<=", 2.5), ("dividend_yield_pct", ">=", 0.5),
    ],
    "Growth Accelerator": [
        ("pat_cagr_5yr", ">=", 20), ("revenue_cagr_5yr", ">=", 15), ("debt_to_equity", "<=", 2.0),
    ],
    "Dividend Champion": [
        ("dividend_yield_pct", ">=", 2), ("dividend_payout_ratio_pct", "<", 80), ("free_cash_flow_cr", ">=", 0),
    ],
    "Debt-Free Blue Chip": [
        ("debt_to_equity", "<", 0.05), ("return_on_equity_pct", ">=", 12), ("sales", ">=", 5000),
    ],
    "Turnaround Watch": [
        ("revenue_cagr_3yr", ">=", 10), ("free_cash_flow_cr", ">=", 0),
    ],
}

DISPLAY_COLUMNS = [
    "company_id", "return_on_equity_pct", "return_on_capital_employed_pct",
    "net_profit_margin_pct", "operating_profit_margin_pct", "debt_to_equity",
    "interest_coverage", "asset_turnover", "free_cash_flow_cr", "revenue_cagr_3yr",
    "revenue_cagr_5yr", "pat_cagr_5yr", "eps_cagr_5yr", "pe_ratio", "pb_ratio",
    "dividend_yield_pct", "dividend_payout_ratio_pct", "market_cap_crore",
    "sales", "final_composite_score",
]


def passes_threshold(value, op, threshold, column=None, broad_sector=None):
    """
    column/broad_sector let this mirror apply_filters' special cases so
    the displayed color never contradicts why a row is actually in the
    sheet:
      - debt_to_equity: Financials-sector companies are exempt from any
        D/E threshold (same reasoning as apply_filters' de_max exemption)
        - shown green regardless of the raw value, not red.
      - interest_coverage: a None value (Debt Free) always counts as
        passing any minimum threshold, same as apply_filters' icr_min.
    """
    if column == "debt_to_equity" and broad_sector == "Financials":
        return True

    if column == "interest_coverage" and value is None:
        return True

    if value is None:
        return None  # can't judge a missing value - leave uncolored
    if op == ">=":
        return value >= threshold
    if op == "<=":
        return value <= threshold
    if op == "<":
        return value < threshold
    if op == ">":
        return value > threshold
    raise ValueError(f"Unknown operator: {op}")


def write_preset_sheet(wb, preset_name, universe_df):
    result = run_preset(universe_df, preset_name)
    result = result.sort_values("final_composite_score", ascending=False)

    ws = wb.create_sheet(title=preset_name[:31])  # Excel sheet name limit is 31 chars

    for col_idx, col_name in enumerate(DISPLAY_COLUMNS, start=1):
        cell = ws.cell(row=1, column=col_idx, value=col_name)
        cell.font = HEADER_FONT
        ws.column_dimensions[cell.column_letter].width = max(len(col_name) + 2, 12)

    threshold_rules = PRESET_THRESHOLD_COLUMNS.get(preset_name, [])
    threshold_cols = {col for col, _, _ in threshold_rules}

    for row_idx, (_, row) in enumerate(result.iterrows(), start=2):
        for col_idx, col_name in enumerate(DISPLAY_COLUMNS, start=1):
            value = row.get(col_name)
            if value is not None and isinstance(value, float) and value != value:  # NaN check
                value = None
            cell = ws.cell(row=row_idx, column=col_idx, value=value)

            if col_name in threshold_cols:
                op, threshold = next((op, t) for c, op, t in threshold_rules if c == col_name)
                passed = passes_threshold(value, op, threshold, column=col_name, broad_sector=row.get("broad_sector"))
                if passed is True:
                    cell.fill = GREEN_FILL
                elif passed is False:
                    cell.fill = RED_FILL

    return len(result)


def main():
    universe = load_screener_universe()
    universe = compute_scores_for_universe(universe)

    wb = Workbook()
    wb.remove(wb.active)  # remove default blank sheet

    for preset_name in PRESETS:
        count = write_preset_sheet(wb, preset_name, universe)
        print(f"{preset_name}: {count} companies written")

    os.makedirs("output", exist_ok=True)
    wb.save(OUT_PATH)
    print(f"\nWrote {OUT_PATH}")


if __name__ == "__main__":
    main()