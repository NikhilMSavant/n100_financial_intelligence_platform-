"""
tearsheet.py — Sprint 5 / Day 33-34
2-page company tearsheet PDF using ReportLab, with matplotlib-rendered charts.
"""
import os
import io
import sqlite3
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (SimpleDocTemplate, Table, TableStyle, Paragraph,
                                 Spacer, Image, PageBreak)
from reportlab.lib import colors

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DB_PATH = os.path.join(ROOT, "db", "nifty100.db")
OUT_DIR = os.path.join(ROOT, "reports", "tearsheets")
NAVY = HexColor("#0B2545")
GREEN = HexColor("#1B7F3A")
RED = HexColor("#B3261E")

styles = getSampleStyleSheet()
STYLE_PRO = ParagraphStyle("pro", parent=styles["Normal"], textColor=GREEN, fontSize=9, leading=12, wordWrap="CJK")
STYLE_CON = ParagraphStyle("con", parent=styles["Normal"], textColor=RED, fontSize=9, leading=12, wordWrap="CJK")
STYLE_CELL = ParagraphStyle("cell", parent=styles["Normal"], fontSize=8, leading=10, wordWrap="CJK")


def _fig_to_image(fig, width=248):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=130, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    img = Image(buf, width=width, height=width * 0.62)
    return img


def _revenue_np_chart(pl):
    fig, ax = plt.subplots(figsize=(4.2, 2.6))
    ax.bar(pl.year - 0.15, pl.sales, width=0.3, label="Revenue", color="#1f77b4")
    ax.bar(pl.year + 0.15, pl.net_profit, width=0.3, label="Net Profit", color="#ff7f0e")
    ax.set_title("Revenue & Net Profit (Cr)", fontsize=9)
    ax.tick_params(labelsize=7)
    ax.legend(fontsize=6)
    fig.tight_layout()
    return fig


def _roe_roce_chart(fr):
    fig, ax1 = plt.subplots(figsize=(4.2, 2.6))
    ax1.plot(fr.year, fr.return_on_equity_pct, color="#1f77b4", marker="o", ms=3, label="ROE %")
    ax2 = ax1.twinx()
    ax2.plot(fr.year, fr.return_on_capital_employed_pct, color="#d62728", marker="s", ms=3, label="ROCE %")
    ax1.set_title("ROE vs ROCE", fontsize=9)
    ax1.tick_params(labelsize=7)
    ax2.tick_params(labelsize=7)
    fig.tight_layout()
    return fig


def _bs_composition_chart(bs):
    fig, ax = plt.subplots(figsize=(4.2, 2.6))
    ax.bar(bs.year, bs.equity_capital.fillna(0) + bs.reserves.fillna(0), label="Equity", color="#2ca02c")
    bottom = bs.equity_capital.fillna(0) + bs.reserves.fillna(0)
    ax.bar(bs.year, bs.borrowings.fillna(0), bottom=bottom, label="Borrowings", color="#d62728")
    bottom2 = bottom + bs.borrowings.fillna(0)
    ax.bar(bs.year, bs.other_liabilities.fillna(0), bottom=bottom2, label="Other Liab.", color="#7f7f7f")
    ax.set_title("Balance Sheet Composition (Cr)", fontsize=9)
    ax.tick_params(labelsize=7)
    ax.legend(fontsize=6)
    fig.tight_layout()
    return fig


def _cashflow_waterfall(cf_latest_row):
    labels = ["CFO", "CFI", "CFF", "Net"]
    vals = [cf_latest_row.operating_activity or 0, cf_latest_row.investing_activity or 0,
            cf_latest_row.financing_activity or 0, cf_latest_row.net_cash_flow or 0]
    colors_ = ["#2ca02c" if v >= 0 else "#d62728" for v in vals]
    fig, ax = plt.subplots(figsize=(4.2, 2.6))
    ax.bar(labels, vals, color=colors_)
    ax.axhline(0, color="black", linewidth=0.6)
    ax.set_title(f"Cash Flow — FY{int(cf_latest_row.year)} (Cr)", fontsize=9)
    ax.tick_params(labelsize=7)
    fig.tight_layout()
    return fig


def build_tearsheet(cid, conn, companies, sectors, pros_cons_df, cap_df, out_path):
    fr = pd.read_sql("SELECT * FROM financial_ratios WHERE company_id=? ORDER BY year", conn, params=[cid])
    pl = pd.read_sql("SELECT * FROM profitandloss WHERE company_id=? ORDER BY year", conn, params=[cid])
    bs = pd.read_sql("SELECT * FROM balancesheet WHERE company_id=? ORDER BY year", conn, params=[cid])
    cf = pd.read_sql("SELECT * FROM cashflow WHERE company_id=? ORDER BY year", conn, params=[cid])

    if len(fr) < 3:
        return False, "insufficient_years"

    crow = companies[companies.company_id == cid].iloc[0]
    srow = sectors[sectors.company_id == cid]
    sector = srow.iloc[0]["broad_sector"] if len(srow) else "N/A"
    latest = fr.iloc[-1]

    doc = SimpleDocTemplate(out_path, pagesize=A4, topMargin=10 * mm, bottomMargin=10 * mm,
                             leftMargin=12 * mm, rightMargin=12 * mm)
    story = []

    # ---- Page 1 header ----
    header_style = ParagraphStyle("header", parent=styles["Title"], textColor=colors.white, fontSize=18)
    header_tbl = Table([[Paragraph(f"{crow.company_name}  ({cid})", header_style)]], colWidths=[186 * mm])
    header_tbl.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), NAVY),
                                     ("TOPPADDING", (0, 0), (-1, -1), 10),
                                     ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
                                     ("LEFTPADDING", (0, 0), (-1, -1), 10)]))
    story.append(header_tbl)
    story.append(Paragraph(f"{sector}  ·  Fiscal Year {int(latest.year)}", styles["Normal"]))
    story.append(Spacer(1, 6))

    def fmt(v, suffix="%"):
        return f"{v:.1f}{suffix}" if pd.notna(v) else "N/A"

    kpi_vals = [
        ("ROE", fmt(latest.return_on_equity_pct)), ("ROCE", fmt(latest.return_on_capital_employed_pct)),
        ("Net Profit Margin", fmt(latest.net_profit_margin_pct)),
        ("D/E", fmt(latest.debt_to_equity, "")), ("Revenue CAGR 5yr", fmt(latest.revenue_cagr_5yr)),
        ("FCF (Cr)", f"{latest.free_cash_flow_cr:,.0f}" if pd.notna(latest.free_cash_flow_cr) else "N/A"),
    ]
    kpi_rows = [[Paragraph(f"<b>{k}</b><br/>{v}", STYLE_CELL) for k, v in kpi_vals[i:i + 3]]
                for i in range(0, 6, 3)]
    kpi_tbl = Table(kpi_rows, colWidths=[62 * mm] * 3)
    kpi_tbl.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
                                  ("BACKGROUND", (0, 0), (-1, -1), colors.whitesmoke),
                                  ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
    story.append(kpi_tbl)
    story.append(Spacer(1, 8))

    charts_row = []
    if len(pl) >= 2:
        charts_row.append(_fig_to_image(_revenue_np_chart(pl)))
    if len(fr) >= 2:
        charts_row.append(_fig_to_image(_roe_roce_chart(fr)))
    if charts_row:
        story.append(Table([charts_row], colWidths=[93 * mm] * len(charts_row)))

    story.append(PageBreak())

    # ---- Page 2 ----
    charts_row2 = []
    if len(bs) >= 2:
        charts_row2.append(_fig_to_image(_bs_composition_chart(bs)))
    if len(cf) >= 1:
        charts_row2.append(_fig_to_image(_cashflow_waterfall(cf.iloc[-1])))
    if charts_row2:
        story.append(Table([charts_row2], colWidths=[93 * mm] * len(charts_row2)))
    story.append(Spacer(1, 8))

    pc = pros_cons_df[pros_cons_df.company_id == cid] if len(pros_cons_df) else pd.DataFrame()
    pros = pc[pc.type == "pro"]["text"].tolist() if len(pc) else []
    cons = pc[pc.type == "con"]["text"].tolist() if len(pc) else []
    story.append(Paragraph("<b>Pros</b>", styles["Heading3"]))
    for p in pros:
        story.append(Paragraph(f"&#8226; {p}", STYLE_PRO))
    story.append(Spacer(1, 4))
    story.append(Paragraph("<b>Cons</b>", styles["Heading3"]))
    for c in cons:
        story.append(Paragraph(f"&#8226; {c}", STYLE_CON))

    cap_row = cap_df[(cap_df.company_id == cid)].sort_values("year").tail(1) if len(cap_df) else pd.DataFrame()
    if len(cap_row):
        badge_text = f"Capital Allocation: {cap_row.iloc[0]['pattern_label']}"
        story.append(Spacer(1, 6))
        badge = Table([[badge_text]], colWidths=[100 * mm])
        badge.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), HexColor("#FFE699")),
                                    ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                                    ("LEFTPADDING", (0, 0), (-1, -1), 8)]))
        story.append(badge)

    doc.build(story)
    return True, "ok"


def run():
    os.makedirs(OUT_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    companies = pd.read_sql("SELECT company_id, company_name FROM companies", conn)
    sectors = pd.read_sql("SELECT company_id, broad_sector FROM sectors", conn)
    pc_path = os.path.join(ROOT, "output", "pros_cons_generated.csv")
    pros_cons_df = pd.read_csv(pc_path) if os.path.exists(pc_path) else pd.DataFrame()
    cap_path = os.path.join(ROOT, "output", "capital_allocation.csv")
    cap_df = pd.read_csv(cap_path) if os.path.exists(cap_path) else pd.DataFrame()

    skipped = []
    written = 0
    for cid in companies.company_id:
        out_path = os.path.join(OUT_DIR, f"{cid}_tearsheet.pdf")
        try:
            ok, reason = build_tearsheet(cid, conn, companies, sectors, pros_cons_df, cap_df, out_path)
        except Exception as e:
            ok, reason = False, f"error: {e}"
        if ok:
            written += 1
        else:
            skipped.append(dict(company_id=cid, reason=reason))

    pd.DataFrame(skipped).to_csv(os.path.join(ROOT, "output", "skipped_tearsheets.csv"), index=False)
    print(f"Tearsheets written: {written}, skipped: {len(skipped)}")
    conn.close()
    return written, skipped


if __name__ == "__main__":
    run()
