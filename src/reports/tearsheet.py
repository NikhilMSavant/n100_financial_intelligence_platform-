"""Sprint 5 Day 33-34 — 2-page company tearsheet via ReportLab."""
import sys
import pathlib
import sqlite3
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

PAGE_W, PAGE_H = A4
MARGIN = 1.5 * cm
UW = PAGE_W - 2 * MARGIN  # usable width

styles = getSampleStyleSheet()
navy = colors.HexColor("#1F4E78")
green = colors.HexColor("#2E7D32")
red = colors.HexColor("#C62828")

header_style = ParagraphStyle("hdr", parent=styles["Title"], textColor=colors.white, fontSize=18)
section_style = ParagraphStyle("sec", parent=styles["Heading2"], textColor=navy)
body_style = ParagraphStyle("body", parent=styles["Normal"], fontSize=8, wordWrap="CJK")
pro_style = ParagraphStyle("pro", parent=body_style, textColor=green)
con_style = ParagraphStyle("con", parent=body_style, textColor=red)


def _kpi_table(kpis: dict):
    items = list(kpis.items())
    rows = [items[i:i + 3] for i in range(0, len(items), 3)]
    data = []
    for row in rows:
        label_row = [Paragraph(f"<b>{k}</b>", body_style) for k, v in row]
        val_row = [Paragraph(str(v), body_style) for k, v in row]
        data.append(label_row)
        data.append(val_row)
    t = Table(data, colWidths=[UW / 3] * 3)
    t.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E8EEF4")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return t


def _bar_chart_png(pl: pd.DataFrame, path):
    fig, ax = plt.subplots(figsize=(6.3, 2.6))
    ax.bar(pl["year"], pl["sales"], label="Revenue", color="#1F4E78", width=0.4, align="edge")
    ax.bar(pl["year"], pl["net_profit"], label="Net Profit", color="#7FA8C9", width=-0.4, align="edge")
    ax.set_title("Revenue & Net Profit (₹ Cr)", fontsize=9)
    ax.tick_params(axis="x", rotation=90, labelsize=6)
    ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)


def _line_chart_png(ratios: pd.DataFrame, path):
    fig, ax = plt.subplots(figsize=(6.3, 2.6))
    ax.plot(ratios["year"], ratios["return_on_equity_pct"], marker="o", label="ROE %", color="#1F4E78")
    ax.plot(ratios["year"], ratios["return_on_capital_employed_pct"], marker="s", label="ROCE %", color="#C62828")
    ax.set_title("ROE vs ROCE", fontsize=9)
    ax.tick_params(axis="x", rotation=90, labelsize=6)
    ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)


def _bs_composition_png(bs: pd.DataFrame, path):
    fig, ax = plt.subplots(figsize=(6.3, 2.6))
    equity = bs["equity_capital"].fillna(0) + bs["reserves"].fillna(0)
    ax.bar(bs["year"], equity, label="Equity", color="#1F4E78")
    ax.bar(bs["year"], bs["borrowings"].fillna(0), bottom=equity, label="Borrowings", color="#C62828")
    ax.bar(bs["year"], bs["other_liabilities"].fillna(0), bottom=equity + bs["borrowings"].fillna(0),
           label="Other Liab.", color="#B0B0B0")
    ax.set_title("Balance Sheet Composition (₹ Cr)", fontsize=9)
    ax.tick_params(axis="x", rotation=90, labelsize=6)
    ax.legend(fontsize=6)
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)


def _cf_waterfall_png(cf_latest, path):
    labels = ["CFO", "CFI", "CFF", "Net"]
    vals = [cf_latest.get("operating_activity", 0) or 0, cf_latest.get("investing_activity", 0) or 0,
            cf_latest.get("financing_activity", 0) or 0, cf_latest.get("net_cash_flow", 0) or 0]
    colors_list = ["#2E7D32" if v >= 0 else "#C62828" for v in vals]
    fig, ax = plt.subplots(figsize=(6.3, 2.6))
    ax.bar(labels, vals, color=colors_list)
    ax.axhline(0, color="black", linewidth=0.5)
    ax.set_title(f"Cash Flow Waterfall — {cf_latest.get('year', '')} (₹ Cr)", fontsize=9)
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)


def generate_tearsheet(cid, company_row, ratios, pl, bs, cf, pros, cons, out_path, tmp_dir):
    doc = SimpleDocTemplate(out_path, pagesize=A4, leftMargin=MARGIN, rightMargin=MARGIN,
                             topMargin=MARGIN, bottomMargin=MARGIN)
    story = []

    header_tbl = Table([[Paragraph(f"{company_row['company_name']} ({cid})", header_style)]], colWidths=[UW])
    header_tbl.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), navy), ("TOPPADDING", (0, 0), (-1, -1), 10),
                                     ("BOTTOMPADDING", (0, 0), (-1, -1), 10), ("LEFTPADDING", (0, 0), (-1, -1), 10)]))
    story.append(header_tbl)
    story.append(Spacer(1, 10))

    latest = ratios.iloc[-1] if not ratios.empty else {}
    def fmt(v, suffix=""):
        return f"{v:.1f}{suffix}" if isinstance(v, (int, float)) and v == v else "N/A"

    kpis = {
        "ROE": fmt(latest.get("return_on_equity_pct"), "%"),
        "ROCE": fmt(latest.get("return_on_capital_employed_pct"), "%"),
        "Net Profit Margin": fmt(latest.get("net_profit_margin_pct"), "%"),
        "D/E": fmt(latest.get("debt_to_equity")),
        "Revenue CAGR 5yr": fmt(latest.get("revenue_cagr_5yr"), "%"),
        "Free Cash Flow (Cr)": fmt(latest.get("free_cash_flow_cr")),
    }
    story.append(_kpi_table(kpis))
    story.append(Spacer(1, 8))

    if not pl.empty:
        p1 = f"{tmp_dir}/{cid}_bar.png"
        _bar_chart_png(pl.tail(10), p1)
        story.append(Image(p1, width=UW, height=UW * 2.6 / 6.3))
    if not ratios.empty:
        p2 = f"{tmp_dir}/{cid}_line.png"
        _line_chart_png(ratios.tail(10), p2)
        story.append(Image(p2, width=UW, height=UW * 2.6 / 6.3))

    story.append(__import__("reportlab.platypus", fromlist=["PageBreak"]).PageBreak())

    if not bs.empty:
        p3 = f"{tmp_dir}/{cid}_bs.png"
        _bs_composition_png(bs.tail(10), p3)
        story.append(Image(p3, width=UW, height=UW * 2.6 / 6.3))
    if not cf.empty:
        p4 = f"{tmp_dir}/{cid}_cf.png"
        _cf_waterfall_png(cf.iloc[-1], p4)
        story.append(Image(p4, width=UW, height=UW * 2.6 / 6.3))

    story.append(Spacer(1, 8))
    story.append(Paragraph("Pros", section_style))
    for p in pros[:5]:
        story.append(Paragraph(f"✓ {p}", pro_style))
    story.append(Spacer(1, 6))
    story.append(Paragraph("Cons", section_style))
    for c in cons[:5]:
        story.append(Paragraph(f"✗ {c}", con_style))

    label = latest.get("icr_label") if hasattr(latest, "get") else None
    story.append(Spacer(1, 8))
    story.append(Paragraph(f"<b>Capital Allocation:</b> see cashflow_intelligence.xlsx for this company's pattern", body_style))

    doc.build(story)


def batch_generate():
    conn = sqlite3.connect("data/nifty100.db")
    companies = pd.read_sql("SELECT * FROM companies", conn)
    ratios_all = pd.read_sql("SELECT * FROM financial_ratios WHERE net_profit_margin_pct IS NOT NULL", conn)
    pl_all = pd.read_sql("SELECT * FROM profitandloss", conn)
    bs_all = pd.read_sql("SELECT * FROM balancesheet", conn)
    cf_all = pd.read_sql("SELECT * FROM cashflow", conn)
    conn.close()
    pros_cons = pd.read_csv("output/pros_cons_generated.csv")

    tmp_dir = "output/_tearsheet_tmp"
    pathlib.Path(tmp_dir).mkdir(parents=True, exist_ok=True)
    pathlib.Path("reports/tearsheets").mkdir(parents=True, exist_ok=True)

    skipped = []
    generated = 0
    for _, row in companies.iterrows():
        cid = row["id"]
        pl = pl_all[pl_all.company_id == cid].sort_values("year")
        if len(pl) < 3:
            skipped.append(dict(company_id=cid, reason="fewer than 3 years of P&L data"))
            continue
        ratios = ratios_all[ratios_all.company_id == cid].sort_values("year")
        bs = bs_all[bs_all.company_id == cid].sort_values("year")
        cf = cf_all[cf_all.company_id == cid].sort_values("year")
        pc = pros_cons[pros_cons.company_id == cid]
        pros = pc[pc.type == "pro"]["text"].tolist()
        cons = pc[pc.type == "con"]["text"].tolist()

        out_path = f"reports/tearsheets/{cid}_tearsheet.pdf"
        try:
            generate_tearsheet(cid, row, ratios, pl, bs, cf, pros, cons, out_path, tmp_dir)
            generated += 1
        except Exception as e:
            skipped.append(dict(company_id=cid, reason=f"generation error: {e}"))

    pd.DataFrame(skipped).to_csv("output/skipped_tearsheets.csv", index=False)
    print(f"Tearsheets generated: {generated}")
    print(f"Skipped: {len(skipped)}")
    return generated, skipped


if __name__ == "__main__":
    batch_generate()
