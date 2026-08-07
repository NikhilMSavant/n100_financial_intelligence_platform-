"""
sector_report.py — Sprint 5 / Day 34
Generates one PDF per broad_sector: a summary page with median KPIs plus a
list of all companies in that sector with 8 metrics each.
"""
import os
import sqlite3
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DB_PATH = os.path.join(ROOT, "db", "nifty100.db")
OUT_DIR = os.path.join(ROOT, "reports", "sector")
NAVY = HexColor("#0B2545")

styles = getSampleStyleSheet()
CELL = ParagraphStyle("cell", parent=styles["Normal"], fontSize=7.5, leading=9, wordWrap="CJK")

METRICS = ["return_on_equity_pct", "return_on_capital_employed_pct", "net_profit_margin_pct",
           "debt_to_equity", "interest_coverage", "free_cash_flow_cr", "revenue_cagr_5yr",
           "composite_quality_score"]
METRIC_LABELS = ["ROE %", "ROCE %", "NPM %", "D/E", "ICR", "FCF Cr", "Rev CAGR5", "Score"]


def build_sector_pdf(sector, companies_df, out_path):
    doc = SimpleDocTemplate(out_path, pagesize=A4, topMargin=10 * mm, bottomMargin=10 * mm,
                             leftMargin=10 * mm, rightMargin=10 * mm)
    story = []
    header_style = ParagraphStyle("h", parent=styles["Title"], textColor=colors.white, fontSize=16)
    header = Table([[Paragraph(f"{sector} — Sector Report", header_style)]], colWidths=[190 * mm])
    header.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), NAVY),
                                 ("TOPPADDING", (0, 0), (-1, -1), 8), ("BOTTOMPADDING", (0, 0), (-1, -1), 8)]))
    story.append(header)
    story.append(Spacer(1, 8))

    story.append(Paragraph(f"<b>{len(companies_df)} companies</b> — median KPIs", styles["Heading3"]))
    med_row = ["Median"] + [f"{companies_df[m].median():.1f}" if pd.notna(companies_df[m].median()) else "N/A"
                             for m in METRICS]
    med_tbl = Table([["Metric"] + METRIC_LABELS, med_row], colWidths=[25 * mm] + [21 * mm] * 8)
    med_tbl.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                                  ("BACKGROUND", (0, 0), (-1, 0), colors.whitesmoke),
                                  ("FONTSIZE", (0, 0), (-1, -1), 8)]))
    story.append(med_tbl)
    story.append(Spacer(1, 10))

    story.append(Paragraph("All companies", styles["Heading3"]))
    header_cells = [Paragraph("<b>Company</b>", CELL)] + [Paragraph(f"<b>{l}</b>", CELL) for l in METRIC_LABELS]
    data = [header_cells]
    for _, r in companies_df.sort_values("composite_quality_score", ascending=False).iterrows():
        row = [Paragraph(f"{r.company_id}", CELL)]
        for m in METRICS:
            v = r[m]
            row.append(Paragraph(f"{v:.1f}" if pd.notna(v) else "N/A", CELL))
        data.append(row)
    tbl = Table(data, colWidths=[25 * mm] + [20.6 * mm] * 8, repeatRows=1)
    tbl.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.4, colors.lightgrey),
                              ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                              ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                              ("VALIGN", (0, 0), (-1, -1), "TOP")]))
    story.append(tbl)
    doc.build(story)


def run():
    os.makedirs(OUT_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    fr = pd.read_sql("SELECT * FROM financial_ratios", conn)
    idx = fr.groupby("company_id")["year"].idxmax()
    latest = fr.loc[idx]
    sectors = pd.read_sql("SELECT company_id, broad_sector FROM sectors", conn)
    df = latest.merge(sectors, on="company_id", how="left")

    n = 0
    for sector, g in df.groupby("broad_sector"):
        safe_name = sector.replace("/", "-").replace(" ", "_")
        out_path = os.path.join(OUT_DIR, f"{safe_name}_report.pdf")
        build_sector_pdf(sector, g, out_path)
        n += 1
    print(f"Sector PDFs written: {n} -> {OUT_DIR}")
    conn.close()
    return n


if __name__ == "__main__":
    run()
