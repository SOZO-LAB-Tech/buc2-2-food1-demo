"""Build the sample data behind the "Nescafé complaints in 2025" chat demo.

Writes two files that always agree, because both come from this script:
  assets/demo/nescafe-2025.json            read by assets/demo/demo-chat.js
  assets/demo/nescafe-complaints-2025.xlsx offered as the download in the chat

All figures are made-up sample data for the demo. To change the story, edit the
numbers below and run (from the demo-site folder):
  python3 tools/build_demo_data.py
Needs openpyxl.
"""
import datetime as dt
import json
import os
import random

from openpyxl import Workbook
from openpyxl.chart import BarChart, PieChart, Reference
from openpyxl.chart.label import DataLabelList
from openpyxl.chart.series import DataPoint
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets", "demo")
XLSX = "nescafe-complaints-2025.xlsx"

BRAND, YEAR = "Nescafé", 2025
SURVEY = {"name": "Nescafé consumer survey 2025", "respondents": 1240, "complained": 223}
FEEDBACK_TOTAL = 8412

# Complaint reports by source (sums to the complaint total).
SOURCES = [("Shopee reviews", 412), ("Careline", 231), ("Lazada reviews", 188),
           ("Complaints system", 162), ("Facebook Page", 153)]

THEMES = ["Too sweet (3-in-1)", "Promotion price changes at checkout",
          "Strength and caffeine labels unclear", "Sachets tear or powder clumps",
          "Out of stock online"]

# Breakdowns: (group, all feedback items from the group, complaints).
# Age groups also carry how their complaints split across THEMES (in order).
DIMS = {
    "age": ("Age group", True, [
        ("18–24", 1310, 214, [.22, .20, .12, .12, .34]),
        ("25–34", 2950, 452, [.42, .20, .16, .12, .10]),
        ("35–44", 2240, 279, [.25, .34, .17, .14, .10]),
        ("45–54", 1180, 129, [.22, .18, .34, .18, .08]),
        ("55+",    732,  72, [.20, .12, .24, .38, .06]),
    ]),
    "region": ("Region", False, [
        ("Hồ Chí Minh City", 3620, 528), ("Hà Nội", 2510, 331), ("Mekong Delta", 820, 118),
        ("Đà Nẵng", 640, 79), ("Other provinces", 822, 90),
    ]),
    "gender": ("Gender", False, [
        ("Female", 4630, 668), ("Male", 3410, 431), ("Not stated", 372, 47),
    ]),
}

# Chart colours: same as the chat (validated palettes).
AGE_RAMP = ["6DA7EC", "3987E5", "256ABF", "184F95", "0D366B"]
CATEGORICAL = ["2A78D6", "EB6834", "1BAF7A", "EDA100", "E87BA4"]
BAR = "2A78D6"

QUOTES = {
    THEMES[0]: ["Nescafé 3in1 is far too sweet now. I want the same coffee with less sugar.",
                "Two sachets a day and it's like drinking syrup. Please make a less-sweet version.",
                "Too much sugar for an afternoon coffee at the office.",
                "My doctor told me to cut sugar, but there's no less-sweet 3in1.",
                "Tastes more like candy than coffee lately."],
    THEMES[1]: ["The promo price on Shopee was different from what I was charged at checkout.",
                "Flash sale showed 89k, but the cart charged 112k.",
                "The voucher disappeared at payment for the Nescafé Gold jar.",
                "The bundle discount didn't apply on Lazada, and the price jumped at checkout.",
                "The price in the livestream didn't match my order."],
    THEMES[2]: ["I can't tell which pack is stronger. The strength labels mean nothing to me.",
                "I work night shifts and need to know the caffeine per sachet. It's not on the pack.",
                "Café Việt or Original: which one has more caffeine?",
                "The intensity numbers on the jar are confusing.",
                "I bought the 'strong' one and it tasted weaker than the regular."],
    THEMES[3]: ["Sachets tear in the wrong place and powder spills everywhere.",
                "The powder was clumped into a hard block when I opened the box.",
                "Half the sachets in the bag were stuck together.",
                "Hard to tear the sachet open with wet hands at my market stall.",
                "The powder clumps in humid weather, well before the expiry date."],
    THEMES[4]: ["Nescafé Café Việt has been out of stock on Shopee for two weeks.",
                "Lazada keeps cancelling my order because the 3in1 bag is out of stock.",
                "The 50-sachet bag is always sold out online.",
                "I ordered on 11.11 and it was cancelled for no stock.",
                "I can't find Black Ice anywhere online."],
}
PRODUCTS = {
    THEMES[0]: ["Nescafé 3in1 Original", "Nescafé 3in1 Original", "Nescafé Latte"],
    THEMES[1]: ["Nescafé Gold", "Nescafé 3in1 Original", "Nescafé Café Việt"],
    THEMES[2]: ["Nescafé Café Việt", "Nescafé 3in1 Original", "Nescafé Gold"],
    THEMES[3]: ["Nescafé 3in1 Original", "Nescafé Café Việt", "Nescafé Latte"],
    THEMES[4]: ["Nescafé Café Việt", "Nescafé Black Ice", "Nescafé 3in1 Original"],
}
# Busier months: Tết (Jan–Feb) and the 9.9 / 11.11 / 12.12 sales.
MONTH_WEIGHT = [11, 10, 7, 7, 7, 7, 7, 8, 10, 8, 11, 10]


def split(n, weights):
    """Whole numbers that follow `weights` and add up to exactly n."""
    raw = [n * w / sum(weights) for w in weights]
    out = [int(x) for x in raw]
    for i in sorted(range(len(raw)), key=lambda i: raw[i] - out[i], reverse=True)[: n - sum(out)]:
        out[i] += 1
    return out


def build_rows(rng):
    complaints = sum(n for _, n in SOURCES)
    for key, (_, _, groups) in DIMS.items():
        assert sum(g[2] for g in groups) == complaints, key
        assert sum(g[1] for g in groups) == FEEDBACK_TOTAL, key

    rows = []
    for name, _, n, mix in DIMS["age"][2]:  # themes follow each age group's mix
        for theme, k in zip(THEMES, split(n, mix)):
            rows += [{"age": name, "theme": theme} for _ in range(k)]
    rng.shuffle(rows)
    for key in ("region", "gender"):
        vals = [g[0] for g in DIMS[key][2] for _ in range(g[2])]
        rng.shuffle(vals)
        for r, v in zip(rows, vals):
            r[key] = v
    srcs = [s for s, k in SOURCES for _ in range(k)]
    rng.shuffle(srcs)
    months = [m for m, k in enumerate(split(complaints, MONTH_WEIGHT), 1) for _ in range(k)]
    rng.shuffle(months)
    for i, r in enumerate(rows):
        m = months[i]
        last = (dt.date(YEAR + (m == 12), m % 12 + 1, 1) - dt.timedelta(days=1)).day
        r["date"] = dt.date(YEAR, m, rng.randint(1, last))
        r["source"] = srcs[i]
        r["product"] = rng.choice(PRODUCTS[r["theme"]])
        r["comment"] = rng.choice(QUOTES[r["theme"]])
        r["rating"] = rng.choice([1, 1, 2, 2, 3]) if "reviews" in r["source"] else None
    rows.sort(key=lambda r: r["date"])
    for i, r in enumerate(rows, 1):
        r["id"] = f"NC25-{i:05d}"
    return rows


def summarise(rows):
    complaints = len(rows)
    theme_n = {t: sum(r["theme"] == t for r in rows) for t in THEMES}
    themes = sorted(THEMES, key=lambda t: -theme_n[t])
    dims = {}
    for key, (label, ordinal, groups) in DIMS.items():
        out = []
        for g in groups:
            name, total, n = g[0], g[1], g[2]
            mine = [r["theme"] for r in rows if r[key] == name]
            top = max(THEMES, key=lambda t: (mine.count(t), -THEMES.index(t)))
            out.append({"name": name, "total": total, "n": n, "top": top,
                        "top_n": mine.count(top)})
        dims[key] = {"label": label, "ordinal": ordinal, "groups": out}
    return {
        "brand": BRAND, "year": YEAR, "survey": SURVEY,
        "feedback": {"total": FEEDBACK_TOTAL, "complaints": complaints},
        "sources": [{"name": s, "n": n} for s, n in SOURCES],
        "themes": [{"name": t, "n": theme_n[t], "quote": QUOTES[t][0]} for t in themes],
        "dims": dims,
    }


# ---------- Excel ----------
INK, MUTED, HEAD = "1F2125", "6E7482", "30271D"
THIN = Side(style="thin", color="E2DFDB")
HFONT = Font(name="Arial", bold=True, color="FFFFFF", size=10)
HFILL = PatternFill("solid", fgColor=HEAD)
BODY = Font(name="Arial", size=10, color=INK)
BOLD = Font(name="Arial", size=10, color=INK, bold=True)
PCT, INT = "0.0%", "#,##0"


def header(ws, row, cols):
    for c, v in enumerate(cols, 1):
        cell = ws.cell(row, c, v)
        cell.font, cell.fill = HFONT, HFILL
        cell.alignment = Alignment(vertical="center", wrap_text=True)
    ws.row_dimensions[row].height = 30


def body(cell, fmt=None, bold=False):
    cell.font = BOLD if bold else BODY
    cell.border = Border(bottom=THIN)
    if fmt:
        cell.number_format = fmt
    return cell


def title(ws, text, sub):
    ws["A1"] = text
    ws["A1"].font = Font(name="Arial", size=16, bold=True, color=INK)
    ws["A2"] = sub
    ws["A2"].font = Font(name="Arial", size=10, color=MUTED, italic=True)


def widths(ws, w):
    for i, x in enumerate(w, 1):
        ws.column_dimensions[get_column_letter(i)].width = x


def breakdown_sheet(wb, key, S):
    d = S["dims"][key]
    ws = wb.create_sheet(f"By {d['label'].lower()}")
    title(ws, f"Complaints by {d['label'].lower()}, {YEAR}",
          "Complaint rate = complaints ÷ all feedback items from that group. Sample data for demonstration.")
    header(ws, 4, [d["label"], "Feedback items", "Complaints", "Complaint rate", "Share of complaints", "Top complaint theme"])
    # Plain values, not formulas: previews that don't recalculate (Quick Look,
    # chat-app file previews) still show every number and chart.
    first, G = 5, d["groups"]
    tot_all, tot_n = sum(g["total"] for g in G), sum(g["n"] for g in G)
    for i, g in enumerate(G):
        r = first + i
        body(ws.cell(r, 1, g["name"]), bold=True)
        body(ws.cell(r, 2, g["total"]), INT)
        body(ws.cell(r, 3, g["n"]), INT)
        body(ws.cell(r, 4, g["n"] / g["total"]), PCT)
        body(ws.cell(r, 5, g["n"] / tot_n), PCT)
        body(ws.cell(r, 6, g["top"]))
    last = first + len(G) - 1
    t = last + 1
    body(ws.cell(t, 1, "Total"), bold=True)
    body(ws.cell(t, 2, tot_all), INT, True)
    body(ws.cell(t, 3, tot_n), INT, True)
    body(ws.cell(t, 4, tot_n / tot_all), PCT, True)
    body(ws.cell(t, 5, 1), PCT, True)
    widths(ws, [22, 15, 13, 15, 19, 38])
    ws.freeze_panes = "A5"

    colors = AGE_RAMP if d["ordinal"] else CATEGORICAL
    pie = PieChart()
    pie.title = "Share of complaints"
    pie.add_data(Reference(ws, min_col=3, min_row=4, max_row=last), titles_from_data=True)
    pie.set_categories(Reference(ws, min_col=1, min_row=first, max_row=last))
    for i in range(len(d["groups"])):
        pt = DataPoint(idx=i)
        pt.graphicalProperties.solidFill = colors[i]
        pt.graphicalProperties.line.solidFill = "FFFFFF"
        pie.series[0].dPt.append(pt)
    pie.dataLabels = DataLabelList()
    pie.dataLabels.showPercent = True
    pie.height, pie.width = 8, 12
    ws.add_chart(pie, f"A{t + 3}")

    bar = BarChart()
    bar.type, bar.style = "bar", 10
    bar.title = "Complaint rate"
    bar.add_data(Reference(ws, min_col=4, min_row=4, max_row=last), titles_from_data=True)
    bar.set_categories(Reference(ws, min_col=1, min_row=first, max_row=last))
    bar.series[0].graphicalProperties.solidFill = BAR
    bar.series[0].graphicalProperties.line.solidFill = BAR
    bar.y_axis.numFmt = "0%"
    bar.y_axis.majorGridlines = None
    bar.x_axis.scaling.orientation = "maxMin"  # keep the table's order top to bottom
    bar.legend = None
    bar.dataLabels = DataLabelList()
    bar.dataLabels.showVal = True
    bar.height, bar.width = 8, 14
    ws.add_chart(bar, f"D{t + 3}")


def build_xlsx(rows, S, path):
    wb = Workbook()
    ws = wb.active
    ws.title = "Summary"
    title(ws, f"{BRAND} consumer complaints, {YEAR}",
          "Exported from Consumer Truth Hub · Nestlé Vietnam · 1 Jan – 31 Dec 2025")
    ws["A3"] = "Demo file: all figures, names and comments are illustrative sample data, not real consumer feedback."
    ws["A3"].font = Font(name="Arial", size=10, bold=True, color="B4532A")

    header(ws, 5, ["Measure", "Value"])
    sv, fb = S["survey"], S["feedback"]
    kpis = [("Feedback items", fb["total"], INT), ("Complaints", fb["complaints"], INT),
            ("Complaints as a share of feedback", fb["complaints"] / fb["total"], PCT),
            ("Survey respondents", sv["respondents"], INT),
            ("Survey respondents with a complaint", sv["complained"], INT),
            ("Share of survey respondents with a complaint", sv["complained"] / sv["respondents"], PCT)]
    for i, (k, v, f) in enumerate(kpis, 6):
        body(ws.cell(i, 1, k), bold=True)
        body(ws.cell(i, 2, v), f)

    header(ws, 13, ["Source", "Complaints", "Share"])
    for i, s in enumerate(S["sources"], 14):
        body(ws.cell(i, 1, s["name"]), bold=True)
        body(ws.cell(i, 2, s["n"]), INT)
        body(ws.cell(i, 3, s["n"] / fb["complaints"]), PCT)

    r0 = 14 + len(S["sources"]) + 1
    header(ws, r0, ["Complaint theme", "Complaints", "Share", "Example comment"])
    for i, t in enumerate(S["themes"], r0 + 1):
        body(ws.cell(i, 1, t["name"]), bold=True)
        body(ws.cell(i, 2, t["n"]), INT)
        body(ws.cell(i, 3, t["n"] / fb["complaints"]), PCT)
        body(ws.cell(i, 4, f"“{t['quote']}”")).alignment = Alignment(wrap_text=True, vertical="top")
    widths(ws, [44, 14, 10, 70])

    for key in ("age", "region", "gender"):
        breakdown_sheet(wb, key, S)

    ws = wb.create_sheet("Complaints")
    cols = ["ID", "Date", "Source", "Product", "Complaint theme", "Age group", "Gender", "Region", "Rating (1–5)", "Comment"]
    header(ws, 1, cols)
    for i, r in enumerate(rows, 2):
        vals = [r["id"], r["date"], r["source"], r["product"], r["theme"], r["age"], r["gender"], r["region"], r["rating"], r["comment"]]
        for c, v in enumerate(vals, 1):
            cell = ws.cell(i, c, v)
            cell.font = BODY
        ws.cell(i, 2).number_format = "dd mmm yyyy"
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = f"A1:{get_column_letter(len(cols))}{len(rows) + 1}"
    widths(ws, [12, 13, 18, 22, 34, 10, 11, 18, 12, 80])

    wb.save(path)


def main():
    os.makedirs(OUT, exist_ok=True)
    rows = build_rows(random.Random(2025))
    S = summarise(rows)
    xlsx = os.path.join(OUT, XLSX)
    build_xlsx(rows, S, xlsx)
    S["file"] = {"name": XLSX, "url": f"/assets/demo/{XLSX}", "bytes": os.path.getsize(xlsx),
                 "sheets": ["Summary", "By age group", "By region", "By gender", "Complaints"]}
    with open(os.path.join(OUT, "nescafe-2025.json"), "w", encoding="utf-8") as f:
        json.dump(S, f, ensure_ascii=False, indent=1)
    print(f"wrote {XLSX} ({S['file']['bytes']:,} bytes, {len(rows):,} complaint rows) and nescafe-2025.json")
    for t in S["themes"]:
        print(f"  {t['n']:4d}  {t['name']}")
    for g in S["dims"]["age"]["groups"]:
        print(f"  {g['name']:6s} n={g['n']:3d} rate={g['n'] / g['total']:.1%} top={g['top']}")


if __name__ == "__main__":
    main()
