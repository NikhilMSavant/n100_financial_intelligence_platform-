"""Sprint 5 Day 34-35 — 11 sector PDFs + 1 portfolio summary PDF."""
import sys
import pathlib
import sqlite3
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from screener.engine import load_latest_universe

MARGIN = 1.5 * cm
PAGE_W, _ = A4
UW = PAGE_W - 2 * MARGIN
styles = getSampleStyleSheet()
navy = colors.HexColor("#1F4E78")
header_style = ParagraphStyle("hdr", parent=styles["Title"], textColor=colors.white, fontSize=16)
body_style = ParagraphStyle("body", parent=styles["Normal"], fontSize=7, wordWrap="CJK")


def _header(text):
    t = Table([[Paragraph(text, header_style)]], colWidths=[UW])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), navy), ("TOPPADDING", (0, 0), (-1, -1), 8),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 8), ("LEFTPADDING", (0, 0), (-1, -1), 8)]))
    return t


def generate_sector_reports(universe):
    pathlib.Path("reports/sector").mkdir(parents=True, exist_ok=True)
    n = 0
    for sector, grp in universe.groupby("broad_sector"):
        if pd.isna(sector):
            continue
        safe_name = str(sector).replace("/", "-").replace(" ", "_")
        path = f"reports/sector/{safe_name}_report.pdf"
        doc = SimpleDocTemplate(path, pagesize=A4, leftMargin=MARGIN, rightMargin=MARGIN, topMargin=MARGIN, bottomMargin=MARGIN)
        story = [_header(f"{sector} — Sector Report"), Spacer(1, 10)]

        med = grp[["return_on_equity_pct", "debt_to_equity", "operating_profit_margin_pct", "pe_ratio"]].median()
        summary_data = [["Metric", "Sector Median"]] + [[k, f"{v:.2f}" if v == v else "N/A"] for k, v in med.items()]
        st_tbl = Table(summary_data, colWidths=[UW * 0.6, UW * 0.4])
        st_tbl.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
                                     ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E8EEF4"))]))
        story.append(st_tbl)
        story.append(Spacer(1, 10))

        cols = ["company_id", "company_name", "return_on_equity_pct", "debt_to_equity",
                "operating_profit_margin_pct", "pe_ratio", "revenue_cagr_5yr", "composite_quality_score"]
        header_row = [Paragraph(f"<b>{c}</b>", body_style) for c in cols]
        rows = [header_row]
        for _, r in grp.sort_values("composite_quality_score", ascending=False).iterrows():
            rows.append([Paragraph(str(r[c])[:20] if pd.notna(r[c]) else "N/A", body_style) for c in cols])
        comp_tbl = Table(rows, colWidths=[UW / len(cols)] * len(cols), repeatRows=1)
        comp_tbl.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.3, colors.lightgrey),
                                       ("BACKGROUND", (0, 0), (-1, 0), navy)]))
        story.append(comp_tbl)
        doc.build(story)
        n += 1
    print(f"Sector reports generated: {n}")
    return n


def generate_portfolio_summary(universe):
    pathlib.Path("reports/portfolio").mkdir(parents=True, exist_ok=True)
    path = "reports/portfolio/portfolio_summary.pdf"
    doc = SimpleDocTemplate(path, pagesize=A4, leftMargin=MARGIN, rightMargin=MARGIN, topMargin=MARGIN, bottomMargin=MARGIN)
    story = [_header("Nifty 100 — Portfolio Summary"), Spacer(1, 10)]

    for _, row in universe.sort_values("company_id").iterrows():
        story.append(Paragraph(f"<b>{row['company_name']} ({row['company_id']})</b> — {row.get('broad_sector')}",
                                ParagraphStyle("co", parent=styles["Heading3"], textColor=navy, fontSize=10)))
        kpis = {
            "ROE": row.get("return_on_equity_pct"), "ROCE": row.get("return_on_capital_employed_pct"),
            "NPM": row.get("net_profit_margin_pct"), "D/E": row.get("debt_to_equity"),
            "Rev CAGR 5yr": row.get("revenue_cagr_5yr"), "Composite Score": row.get("composite_quality_score"),
        }
        line = "  |  ".join(f"{k}: {v:.1f}" if isinstance(v, (int, float)) and v == v else f"{k}: N/A" for k, v in kpis.items())
        story.append(Paragraph(line, body_style))
        story.append(Spacer(1, 6))
    doc.build(story)
    print("Portfolio summary generated:", path)


if __name__ == "__main__":
    conn = sqlite3.connect("data/nifty100.db")
    universe = load_latest_universe(conn)
    conn.close()
    generate_sector_reports(universe)
    generate_portfolio_summary(universe)
