"""
portfolio_summary.py — Sprint 5 / Day 35
One page per company (alphabetical by ticker): name, sector, top 6 KPIs,
trend arrows (up/down/flat within 2%) vs the prior fiscal year.
"""
import os
import sqlite3
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DB_PATH = os.path.join(ROOT, "db", "nifty100.db")
OUT_PATH = os.path.join(ROOT, "reports", "portfolio", "portfolio_summary.pdf")
NAVY = HexColor("#0B2545")

styles = getSampleStyleSheet()
CELL = ParagraphStyle("cell", parent=styles["Normal"], fontSize=10, leading=13)

TOP6 = ["return_on_equity_pct", "return_on_capital_employed_pct", "net_profit_margin_pct",
        "debt_to_equity", "revenue_cagr_5yr", "free_cash_flow_cr"]
LABELS = ["ROE %", "ROCE %", "NPM %", "D/E", "Revenue CAGR 5yr %", "FCF (Cr)"]


def trend_arrow(cur, prev):
    if pd.isna(cur) or pd.isna(prev) or prev == 0:
        return "→"
    pct_chg = (cur - prev) / abs(prev) * 100
    if pct_chg > 2:
        return "↑"
    if pct_chg < -2:
        return "↓"
    return "→"


def run():
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    fr = pd.read_sql("SELECT * FROM financial_ratios ORDER BY company_id, year", conn)
    companies = pd.read_sql("SELECT company_id, company_name FROM companies", conn)
    sectors = pd.read_sql("SELECT company_id, broad_sector FROM sectors", conn)

    doc = SimpleDocTemplate(OUT_PATH, pagesize=A4, topMargin=15 * mm, bottomMargin=15 * mm,
                             leftMargin=15 * mm, rightMargin=15 * mm)
    story = []

    for cid in sorted(companies.company_id):
        g = fr[fr.company_id == cid].sort_values("year")
        if g.empty:
            continue
        crow = companies[companies.company_id == cid].iloc[0]
        srow = sectors[sectors.company_id == cid]
        sector = srow.iloc[0]["broad_sector"] if len(srow) else "N/A"
        latest = g.iloc[-1]
        prior = g.iloc[-2] if len(g) >= 2 else None

        header_style = ParagraphStyle("h", parent=styles["Title"], textColor=colors.white, fontSize=16)
        header = Table([[Paragraph(f"{crow.company_name} ({cid})", header_style)]], colWidths=[180 * mm])
        header.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), NAVY),
                                     ("TOPPADDING", (0, 0), (-1, -1), 8), ("BOTTOMPADDING", (0, 0), (-1, -1), 8)]))
        story.append(header)
        story.append(Paragraph(f"{sector} · FY{int(latest.year)}", styles["Normal"]))
        story.append(Spacer(1, 10))

        rows = []
        for m, label in zip(TOP6, LABELS):
            cur_val = latest[m]
            prev_val = prior[m] if prior is not None else None
            arrow = trend_arrow(cur_val, prev_val)
            val_str = f"{cur_val:,.1f}" if pd.notna(cur_val) else "N/A"
            rows.append([label, val_str, arrow])

        tbl = Table([["Metric", "Value", "Trend"]] + rows, colWidths=[70 * mm, 50 * mm, 30 * mm])
        tbl.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ("BACKGROUND", (0, 0), (-1, 0), colors.whitesmoke),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        story.append(tbl)
        story.append(PageBreak())

    if story:
        story.pop()  # drop trailing page break
    doc.build(story)
    print(f"portfolio_summary.pdf written -> {OUT_PATH} ({companies.company_id.nunique()} companies)")
    conn.close()


if __name__ == "__main__":
    run()
