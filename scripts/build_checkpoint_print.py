#!/usr/bin/env python3
"""
DSC106 Project 2 — checkpoint deliverable as *print-ready HTML* (exactly 3 pages when printed).

Checkpoint requirements covered:
  • Page 1: two persuasive visualizations arguing the proposition is TRUE (here: world GHG has *not* stabilized).
  • Page 2: two persuasive visualizations arguing the proposition is NOT TRUE (same charts swapped: plateau + intensity).
  • Page 3: proposition stated; same claim on both sides; dataset + WLD identified; which visuals
    you lean toward for the final; deceptive / earnest techniques per chart; limitations; group roster placeholders.

Gradescope: open the HTML → Print → Save as PDF → enable “Background graphics” → confirm 3 pages → upload.

No third-party deps (stdlib csv + pathlib only).
"""

from __future__ import annotations

import csv
import html
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
AGG = REPO / "World-Bank-Data-by-Indicators" / "climate-change" / "cleaned" / "climate_aggregates_wide.csv"
OUT_HTML = REPO / "checkpoint" / "DSC106_Project2_Checkpoint.html"

GHG_COL = "Total greenhouse gas emissions (kt of CO2 equivalent)"
CO2_INT_COL = "CO2 emissions (kg per 2010 US$ of GDP)"


def _f(row: dict[str, str], key: str) -> float | None:
    v = (row.get(key) or "").strip()
    if not v:
        return None
    return float(v)


def load_wld() -> list[dict]:
    with AGG.open(newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        rows = [row for row in r if (row.get("Country Code") or "").strip() == "WLD"]
    out = []
    for row in rows:
        y = int((row.get("Year") or "0").strip())
        ghg = _f(row, GHG_COL)
        co2i = _f(row, CO2_INT_COL)
        out.append({"Year": y, GHG_COL: ghg, CO2_INT_COL: co2i})
    out.sort(key=lambda z: z["Year"])
    return out


def kt_to_gt(kt: float | None) -> float | None:
    if kt is None:
        return None
    return kt / 1e6


def svg_line_chart(
    title: str,
    xs: list[float],
    ys: list[float],
    xlabel: str,
    ylabel: str,
    ylim: tuple[float, float],
    *,
    color: str = "#1565c0",
    fill_under: bool = False,
    fill_color: str = "#ffcdd2",
    width: int = 720,
    height: int = 300,
    pad_l: int = 72,
    pad_r: int = 28,
    pad_t: int = 56,
    pad_b: int = 46,
) -> str:
    esc = html.escape
    pw = width - pad_l - pad_r
    ph = height - pad_t - pad_b
    x0, x1 = min(xs), max(xs)
    y0, y1 = ylim

    def sx(x: float) -> float:
        return pad_l + (x - x0) / (x1 - x0 + 1e-9) * pw

    def sy(y: float) -> float:
        return pad_t + ph - (y - y0) / (y1 - y0 + 1e-9) * ph

    pts = " ".join(f"{sx(x):.2f},{sy(y):.2f}" for x, y in zip(xs, ys))
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#fafafa"/>',
        f'<text x="{width/2}" y="30" text-anchor="middle" font-size="14" font-weight="700" fill="#111">{esc(title)}</text>',
    ]
    # grid
    for i in range(5):
        gy = pad_t + (ph * i / 4)
        parts.append(f'<line x1="{pad_l}" y1="{gy:.1f}" x2="{width-pad_r}" y2="{gy:.1f}" stroke="#e0e0e0" stroke-width="1"/>')
    if fill_under:
        base_y = sy(y0)
        poly = f"{sx(xs[0]):.2f},{base_y:.2f} " + " ".join(f"{sx(x):.2f},{sy(y):.2f}" for x, y in zip(xs, ys))
        poly += f" {sx(xs[-1]):.2f},{base_y:.2f}"
        parts.append(f'<polygon points="{poly}" fill="{fill_color}" opacity="0.45"/>')
    parts.append(f'<polyline fill="none" stroke="{color}" stroke-width="2.5" points="{pts}"/>')
    for x, y in zip(xs, ys):
        parts.append(
            f'<circle cx="{sx(x):.2f}" cy="{sy(y):.2f}" r="3.5" fill="{color}" stroke="#fff" stroke-width="1"/>'
        )
    parts.append(
        f'<text x="{width/2}" y="{height - 10}" text-anchor="middle" font-size="11" fill="#333">{esc(xlabel)}</text>'
    )
    parts.append(
        f'<text x="22" y="{pad_t + ph/2}" text-anchor="middle" font-size="11" fill="#333" transform="rotate(-90 22 {pad_t + ph/2})">{esc(ylabel)}</text>'
    )
    # Y tick labels (aligned with grid: top = y1, bottom = y0)
    for i in range(5):
        gv = y1 - (y1 - y0) * (i / 4)
        gy = sy(gv)
        parts.append(
            f'<text x="{pad_l - 6}" y="{gy + 4:.1f}" text-anchor="end" font-size="9" fill="#555">{gv:.1f}</text>'
        )
    # X tick labels (sparse, unique indices)
    nx = min(6, len(xs))
    if nx >= 2 and len(xs) >= 1:
        raw = [min(len(xs) - 1, round(j * (len(xs) - 1) / (nx - 1))) for j in range(nx)]
        idxs = list(dict.fromkeys(raw))
        for j in idxs:
            x = xs[j]
            parts.append(
                f'<text x="{sx(x):.1f}" y="{height - 24:.0f}" text-anchor="middle" font-size="9" fill="#555">{x:.0f}</text>'
            )
    parts.append("</svg>")
    return "\n".join(parts)


def svg_bar_chart(
    title: str,
    labels: list[str],
    values: list[float],
    ylabel: str,
    *,
    colors: list[str],
    width: int = 720,
    height: int = 300,
) -> str:
    esc = html.escape
    pad_l, pad_r, pad_t, pad_b = 72, 28, 56, 80
    pw = width - pad_l - pad_r
    ph = height - pad_t - pad_b
    vmax = max(values) * 1.15
    n = len(values)
    seg = pw / n
    bw = seg * 0.55
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#fafafa"/>',
        f'<text x="{width/2}" y="30" text-anchor="middle" font-size="14" font-weight="700" fill="#111">{esc(title)}</text>',
    ]
    for i in range(5):
        gy = pad_t + (ph * i / 4)
        parts.append(f'<line x1="{pad_l}" y1="{gy:.1f}" x2="{width-pad_r}" y2="{gy:.1f}" stroke="#e0e0e0"/>')
        gv = vmax * (1 - i / 4)
        parts.append(
            f'<text x="{pad_l - 6}" y="{gy + 4:.1f}" text-anchor="end" font-size="9" fill="#555">{gv:.2f}</text>'
        )
    for i, (lab, val, col) in enumerate(zip(labels, values, colors)):
        x0 = pad_l + i * seg + (seg - bw) / 2
        h = (val / vmax) * ph
        y0 = pad_t + ph - h
        parts.append(f'<rect x="{x0:.1f}" y="{y0:.1f}" width="{bw:.1f}" height="{h:.1f}" fill="{col}" stroke="#222" stroke-width="0.6"/>')
        parts.append(
            f'<text x="{x0 + bw/2:.1f}" y="{y0 - 6:.1f}" text-anchor="middle" font-size="11" font-weight="700" fill="#111">{val:.2f}</text>'
        )
        for j, line in enumerate(lab.split("\n")):
            parts.append(
                f'<text x="{x0 + bw/2:.1f}" y="{height - 52 + j*14:.1f}" text-anchor="middle" font-size="10" fill="#333">{esc(line)}</text>'
            )
    parts.append(
        f'<text x="22" y="{pad_t + ph/2}" text-anchor="middle" font-size="11" fill="#333" transform="rotate(-90 22 {pad_t + ph/2})">{esc(ylabel)}</text>'
    )
    parts.append(
        f'<text x="{width/2}" y="{height - 10}" text-anchor="middle" font-size="10" fill="#666">Source: World Bank WLD aggregate</text>'
    )
    parts.append("</svg>")
    return "\n".join(parts)


def build_html(rows: list[dict]) -> str:
    by_year = {r["Year"]: r for r in rows}

    # --- Narrow-window GHG + intensity (used on Page 2 to argue against "not stabilized")
    win = [r for r in rows if r[GHG_COL] is not None and 2008 <= r["Year"] <= 2015]
    xa = [float(r["Year"]) for r in win]
    ya = [kt_to_gt(r[GHG_COL]) for r in win]
    chart_a = svg_line_chart(
        "Global emissions hover near a plateau in the 2010s",
        xa,
        ya,
        "Year",
        "Gt CO₂e (total GHG, World Bank)",
        ylim=(39.8, 44.6),
        color="#2e7d32",
        width=700,
        height=290,
    )

    d2 = [(r["Year"], r[CO2_INT_COL]) for r in rows if r[CO2_INT_COL] is not None and r["Year"] >= 1990]
    xb = [float(y) for y, _ in d2]
    yb = [v for _, v in d2]
    chart_b = svg_line_chart(
        "The world economy keeps producing more GDP per kilogram of CO₂",
        xb,
        yb,
        "Year",
        "kg CO₂ per 2010 US$ of GDP (World)",
        ylim=(min(yb) * 0.92, max(yb) * 1.05),
        color="#1565c0",
        width=700,
        height=290,
    )

    # --- Long-horizon GHG + growth bars (used on Page 1 for "not stabilized")
    full = [(r["Year"], kt_to_gt(r[GHG_COL])) for r in rows if r[GHG_COL] is not None]
    xc = [float(y) for y, _ in full]
    yc = [v for _, v in full]
    chart_c = svg_line_chart(
        "World total greenhouse gases: five decades of increase",
        xc,
        yc,
        "Year",
        "Gt CO₂e (total GHG, World Bank)",
        ylim=(0, max(yc) * 1.06),
        color="#7f0000",
        fill_under=True,
        fill_color="#ffcdd2",
        width=700,
        height=290,
    )

    g1970 = kt_to_gt(by_year[1970][GHG_COL])
    g2000 = kt_to_gt(by_year[2000][GHG_COL])
    g2018 = kt_to_gt(by_year[2018][GHG_COL])
    assert g1970 is not None and g2000 is not None and g2018 is not None
    r_early = (g2000 - g1970) / (2000 - 1970)
    r_late = (g2018 - g2000) / (2018 - 2000)
    chart_d = svg_bar_chart(
        "The 21st century is adding pollution faster than the late 20th century",
        ["1970–2000\n(avg. per year)", "2000–2018\n(avg. per year)"],
        [r_early, r_late],
        "Average yearly increase (Gt CO₂e / year)",
        colors=["#6d4c41", "#bf360c"],
        width=700,
        height=300,
    )

    prop_text = (
        "Global greenhouse gas emissions have not stabilized: world totals are still on a long upward path, "
        "and the 21st century has not broken the pattern of large yearly additions to the atmosphere."
    )

    page3 = f"""
<h1>Page 3 — Checkpoint writeup (required elements)</h1>

<h2>1. Identification</h2>
<p><strong>Course / assignment:</strong> DSC 106 — Project 2, <em>checkpoint</em> submission (one PDF: three pages).</p>
<p><strong>Dataset:</strong> World Bank “climate-change” indicator bundle, pre-cleaned class repository
<code>World-Bank-Data-by-Indicators/climate-change/</code>; we use the processed aggregate export
<code>cleaned/climate_aggregates_wide.csv</code> and the <strong>World</strong> entity (<strong>WLD</strong>) for global totals.
Years shown depend on World Bank coverage (GHG totals about 1970–2018 in this extract).</p>

<h2>2. Proposition (same claim on both sides)</h2>
<p>We address <strong>one</strong> proposition and visualize arguments <strong>for</strong> and <strong>against</strong> it:</p>
<blockquote style="margin:0.5rem 0 1rem 1rem;border-left:4px solid #1976d2;padding-left:0.75rem;">
  “{html.escape(prop_text)}”
</blockquote>
<p><strong>Page 1</strong> presents two charts meant to persuade a reader that this proposition is <strong>true</strong>.
<strong>Page 2</strong> presents two charts meant to persuade a reader that it is <strong>not true</strong>.</p>

<h2>3. Which set of visualizations we are leaning toward for the final report</h2>
<ul>
  <li><strong>Leaning toward Page 1 (for the proposition):</strong> the long-run total-GHG line (full axis from zero) and the
  two-period <em>average yearly increase</em> bars match the proposition’s plain meaning (“not stabilized,” still adding
  pollution quickly) and are harder to dismiss on inspection. Rhetorical choices (color, fill, assertive title) remain,
  but we avoid the most controversial axis tricks.</li>
  <li><strong>Page 2 as a contrast case:</strong> the narrow-window total-GHG panel plus the intensity curve illustrate how
  one can suggest “stability” or “decoupling” without lying in the spreadsheet yet still invite a misleading conclusion about
  <em>total</em> greenhouse pollution.</li>
</ul>

<h2>4. Techniques used — Page 1 (persuade TRUE: emissions have not stabilized)</h2>
<ul>
  <li><strong>Chart 1 (total GHG, 1970–2018):</strong> Mostly <em>earnest</em> conventions: long horizon, y-axis includes
  zero, filled area to emphasize accumulation; color and title stress sustained increase—supports “no stabilization.”</li>
  <li><strong>Chart 2 (bars of average annual additions):</strong> <em>Earnest transformation</em> on the same WLD totals:
  compares mean absolute growth (Gt CO₂e per year) in 1970–2000 vs 2000–2018; undercuts any simple “post-2000 calm” story
  because the later period’s average yearly addition is larger, without distorting axis scale.</li>
</ul>

<h2>5. Techniques used — Page 2 (persuade NOT TRUE: i.e., imply stabilization)</h2>
<ul>
  <li><strong>Chart 1 (total GHG, 2008–2015):</strong> <em>Cherry-picked time window</em> after the mid-2000s run-up and
  before the late-decade rise resumes; pairs with a <em>tight non-zero y-axis</em> so multi-gigatonne movement reads as a
  “plateau.” Framing title implies stabilization beyond what the full series supports.</li>
  <li><strong>Chart 2 (CO₂ per 2010 US$ GDP):</strong> <em>Metric substitution</em> — a real decoupling signal, but not the
  same quantity as total greenhouse gas pollution; persuasive through <em>implied equivalence</em> if readers equate
  “less CO₂ per dollar” with “emissions have stabilized.”</li>
</ul>

<h2>6. Limitations (transparency)</h2>
<ul>
  <li>World Bank composite totals may differ from IPCC national-inventory headline figures; missing years appear as gaps
  in the source table.</li>
  <li>WLD is an aggregate constructed by the World Bank, not a country; we label it clearly as “World aggregate (WLD).”</li>
</ul>

<h2>7. Group roster (required — replace before Gradescope)</h2>
<ul>
  <li>Full name — <code>@ucsd.edu</code> email</li>
  <li>Full name — <code>@ucsd.edu</code> email</li>
  <li>Full name — <code>@ucsd.edu</code> email</li>
  <li>(Optional fourth member) Full name — <code>@ucsd.edu</code> email</li>
</ul>
"""

    css = """
    body { font-family: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif; margin: 0; color: #111; }
    .page { box-sizing: border-box; padding: 0.5in 0.55in; max-width: 8.5in; margin: 0 auto; }
    @page { size: letter; margin: 0.45in; }
    @media print {
      .page { page-break-after: always; min-height: 10.3in; }
      .page:last-child { page-break-after: auto; }
      .no-print { display: none !important; }
    }
    h1 { font-size: 1.05rem; margin: 0 0 0.5rem 0; }
    h2 { font-size: 0.95rem; margin: 1rem 0 0.35rem 0; color: #333; }
    .hdr-meta { font-size: 0.8rem; color: #555; margin-bottom: 0.35rem; }
    .prop-banner { font-size: 0.92rem; line-height: 1.45; margin: 0.35rem 0 0.65rem 0; padding: 0.45rem 0.55rem; background: #f5f5f5; border: 1px solid #ddd; }
    .charts { display: flex; flex-direction: column; gap: 0.95rem; align-items: center; }
    .src { font-size: 0.72rem; color: #555; text-align: center; margin-top: 0.45rem; line-height: 1.35; }
    .note { font-size: 0.78rem; color: #333; background: #fff8e1; border: 1px solid #ffe082; padding: 0.5rem 0.65rem; margin: 0.75rem auto 1rem; max-width: 40rem; }
    #page3-body h1 { margin-top: 0; }
    #page3-body p, #page3-body li { font-size: 0.88rem; line-height: 1.45; }
    #page3-body ul { margin: 0.25rem 0 0.5rem 1.1rem; }
    """

    prop_esc = html.escape(prop_text)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>DSC106 Project 2 — Checkpoint</title>
<style>{css}</style>
</head>
<body>
<p class="note no-print"><strong>Submit as PDF (Gradescope):</strong> Chrome or Firefox → Print → Save as PDF →
enable <strong>Background graphics</strong> → confirm exactly <strong>three</strong> pages → upload.</p>

<section class="page">
  <div class="hdr-meta">DSC 106 · Project 2 — Checkpoint · Dataset: World Bank climate-change (WLD aggregate)</div>
  <h1>Page 1 — Two visualizations supporting the proposition (TRUE)</h1>
  <div class="prop-banner"><strong>Proposition:</strong> “{prop_esc}”<br/>
  <span style="font-size:0.88em;color:#444;">Figures below are designed to persuade readers that this claim is <strong>true</strong>.</span></div>
  <div class="charts">
    {chart_c}
    {chart_d}
  </div>
  <p class="src"><strong>Source:</strong> World Bank composite (climate-change bundle), World aggregate (<code>WLD</code>).
  Units: Gt CO₂e computed as World Bank kt ÷ 10⁶. GHG totals may omit some categories vs IPCC inventory headlines.</p>
</section>

<section class="page">
  <div class="hdr-meta">DSC 106 · Project 2 — Checkpoint · Dataset: World Bank climate-change (WLD aggregate)</div>
  <h1>Page 2 — Two visualizations opposing the proposition (NOT TRUE)</h1>
  <div class="prop-banner"><strong>Same proposition:</strong> “{prop_esc}”<br/>
  <span style="font-size:0.88em;color:#444;">Figures below are designed to persuade readers that this claim is <strong>not true</strong> (or highly misleading).</span></div>
  <div class="charts">
    {chart_a}
    {chart_b}
  </div>
  <p class="src"><strong>Source:</strong> World Bank composite (climate-change bundle), World aggregate (<code>WLD</code>).</p>
</section>

<section class="page" id="page3-wrap">
  <div id="page3-body">
  {page3}
  </div>
</section>
</body>
</html>"""


def main() -> None:
    rows = load_wld()
    OUT_HTML.parent.mkdir(parents=True, exist_ok=True)
    OUT_HTML.write_text(build_html(rows), encoding="utf-8")
    print(f"Wrote {OUT_HTML}")


if __name__ == "__main__":
    main()
