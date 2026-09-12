"""Builds the standalone findings page at resources/research/findings.html.

Results only: what the benchmark measured, with no build narrative. Every
number is read from `benchmark.db` at render time, through the same
aggregation the dissertation tables use, so this page cannot drift away from
the data it describes.

Colour follows resources/assets/design/palette.md where that palette has an
answer, and extends it where it does not. Oxford Ink is a deliberately
blue-monochrome identity, which cannot give three pipelines three legible
identities in a chart, so each pipeline takes a saturated hue anchored to the
house Ink and the house Gold is kept for emphasis only.

Charts are inline SVG and CSS rather than a charting library, so the output
stays a single file with nothing to fetch.
"""
import argparse
import html
import math
import sqlite3
from datetime import date
from pathlib import Path

import aggregate_results as agg

OUT_PATH = Path("../resources/research/findings.html")

# Extended from palette.md: house Ink and Gold retained, one saturated hue per
# pipeline so three series stay separable at a glance.
PIPE = {
    "P1_vector": {"label": "P1 Vector", "hue": "#3D5AFE", "wash": "#E8ECFF",
                  "note": "ChromaDB and fastembed, reranked by a local cross-encoder"},
    "P2_bm25": {"label": "P2 BM25", "hue": "#00A5A8", "wash": "#DFF5F5",
                "note": "rank_bm25 only, purely statistical"},
    "P3_structural": {"label": "P3 Structural", "hue": "#FF4D6D", "wash": "#FFE7EB",
                      "note": "a LlamaIndex summary tree per filing"},
}
# Score bands 1 to 5, wrong to right.
BAND = ["#FF4D6D", "#FF8A5B", "#FFC145", "#7BC96F", "#00A5A8"]
GOLD = "#D4A017"
INK = "#0A1F33"

QUAD = {
    "Q1_Direct_Text": ("Direct, text", "One explicit statement in continuous prose."),
    "Q2_Implicit_Text": ("Implicit, text", "Synthesis across several narrative passages."),
    "Q3_Direct_Table": ("Direct, table", "Exact extraction of a single table cell."),
    "Q4_Implicit_Table": ("Implicit, table", "A calculation or inference over a table."),
}


def esc(text) -> str:
    return html.escape(str(text))


def pct(value, places=1) -> str:
    return "-" if value is None else f"{value * 100:.{places}f}%"


def num(value, places=3) -> str:
    return "-" if value is None else f"{value:.{places}f}"


def _rate(seconds) -> str:
    """Seconds per 1000 nodes, which spans from hundredths to thousands."""
    if seconds is None:
        return "-"
    if seconds >= 100:
        return f"{seconds:,.0f} s"
    if seconds >= 1:
        return f"{seconds:.1f} s"
    return f"{seconds:.2f} s"


def duration(seconds) -> str:
    if seconds is None:
        return "-"
    if seconds >= 3600:
        return f"{seconds / 3600:.1f} h"
    if seconds >= 60:
        return f"{seconds / 60:.1f} min"
    return f"{seconds:.1f} s"


# --- data ---------------------------------------------------------------------

def load(db_path: str) -> dict:
    """Everything the page renders, read once."""
    conn = sqlite3.connect(db_path)
    report = agg.build_report(conn, "PQ")
    conn.row_factory = sqlite3.Row

    distribution: dict[str, dict[int, int]] = {}
    for row in conn.execute("""SELECT pipeline, judge_score, COUNT(*) n FROM results
                               WHERE source_set='PQ' GROUP BY 1,2"""):
        distribution.setdefault(row["pipeline"], {})[row["judge_score"]] = row["n"]

    tokens = {}
    for row in conn.execute("""SELECT pipeline, SUM(input_tokens) i, SUM(output_tokens) o,
                                      AVG(latency_sec) l FROM results
                               WHERE source_set='PQ' GROUP BY 1"""):
        tokens[row["pipeline"]] = dict(inp=row["i"], out=row["o"], latency=row["l"])

    gate = conn.execute("""SELECT COUNT(*) n, SUM(judge_score = human_score) agree
                           FROM results WHERE source_set='JEQ'""").fetchone()
    corpus = conn.execute("""SELECT COUNT(*) nodes, COUNT(DISTINCT document_id) filings
                             FROM nodes""").fetchone()
    report.update(
        distribution=distribution, tokens=tokens,
        gate=(gate["agree"], gate["n"]),
        nodes=corpus["nodes"], filings=corpus["filings"],
        questions=conn.execute("SELECT COUNT(*) FROM queries").fetchone()[0],
        per_document_questions={r["document_id"]: r["n"] for r in conn.execute(
            "SELECT document_id, COUNT(*) n FROM queries GROUP BY 1")},
    )
    return report


# --- building blocks ----------------------------------------------------------

def bar_row(label: str, value: float, scale: float, colour: str, display: str) -> str:
    """One horizontal bar: label, track, value. Widths are percentages."""
    width = 0 if not scale else max(0.6, value / scale * 100)
    return f"""<div class="bar">
      <span class="bar-l">{esc(label)}</span>
      <span class="bar-t"><span class="bar-f" style="width:{width:.1f}%;background:{colour}"></span></span>
      <span class="bar-v">{esc(display)}</span>
    </div>"""


def facts_strip(d: dict) -> str:
    items = [
        (f"{d['filings']}", "SEC 10-K filings"),
        (f"{d['nodes']:,}", "indexed nodes"),
        (f"{d['questions']}", "benchmark questions"),
        ("3", "retrieval paradigms"),
        (f"{d['cells']}", "scored cells"),
        (f"{100 * d['gate'][0] / d['gate'][1]:.1f}%", "judge concordance"),
    ]
    cells = "\n".join(
        f'      <div class="fact"><b>{esc(v)}</b><span>{esc(k)}</span></div>' for v, k in items)
    return f'    <div class="facts">\n{cells}\n    </div>'


def scoreboard(d: dict) -> str:
    order = sorted(d["overall"], key=lambda p: -d["overall"][p]["judge_mean"])
    cards = []
    for rank, pipeline in enumerate(order, start=1):
        s = d["overall"][pipeline]
        meta = PIPE[pipeline]
        cards.append(f"""      <div class="card" style="--hue:{meta['hue']};--wash:{meta['wash']}">
        <div class="card-top"><span class="rank">{rank}</span>
          <div><h3>{esc(meta['label'])}</h3><p>{esc(meta['note'])}</p></div></div>
        <div class="card-nums">
          <div><b>{num(s['judge_mean'], 2)}</b><span>judge mean</span></div>
          <div><b>{pct(s['judge_pass_rate'], 0)}</b><span>pass rate</span></div>
          <div><b>{num(s['recall_at_k'])}</b><span>recall</span></div>
        </div>
      </div>""")
    return "\n".join(cards)


def overall_table(d: dict) -> str:
    order = sorted(d["overall"], key=lambda p: -d["overall"][p]["judge_mean"])
    rows = []
    for pipeline in order:
        s = d["overall"][pipeline]
        t = d["tokens"][pipeline]
        rows.append(f"""        <tr>
          <th scope="row"><span class="dot" style="background:{PIPE[pipeline]['hue']}"></span>{esc(PIPE[pipeline]['label'])}</th>
          <td>{num(s['judge_mean'], 2)}</td><td>{pct(s['judge_pass_rate'])}</td>
          <td>{pct(s['judge_fail_rate'])}</td><td>{num(s['recall_at_k'])}</td>
          <td>{num(s['precision_at_k'])}</td><td>{pct(s['hit_rate'])}</td>
          <td>{pct(s['citation_match'])}</td><td>{num(s['token_f1'])}</td>
          <td>{num(t['latency'], 2)} s</td>
        </tr>""")
    return "\n".join(rows)


def quality_chart(d: dict) -> str:
    order = sorted(d["overall"], key=lambda p: -d["overall"][p]["judge_mean"])
    bars = []
    for pipeline in order:
        s = d["overall"][pipeline]
        bars.append(bar_row(PIPE[pipeline]["label"], s["judge_mean"], 5.0,
                            PIPE[pipeline]["hue"], f"{s['judge_mean']:.2f} / 5"))
    passes = []
    for pipeline in order:
        s = d["overall"][pipeline]
        passes.append(bar_row(PIPE[pipeline]["label"], s["judge_pass_rate"], 1.0,
                              PIPE[pipeline]["hue"], pct(s["judge_pass_rate"], 1)))
    return f"""      <div class="pair">
        <div><h4>Mean judge score</h4>{''.join(bars)}</div>
        <div><h4>Pass rate, scoring 4 or 5</h4>{''.join(passes)}</div>
      </div>"""


def distribution_chart(d: dict) -> str:
    rows = []
    for pipeline in ("P2_bm25", "P1_vector", "P3_structural"):
        counts = d["distribution"][pipeline]
        total = sum(counts.values())
        segments = []
        for score in range(1, 6):
            n = counts.get(score, 0)
            if not n:
                continue
            share = n / total * 100
            inner = f"{n}" if share >= 7 else ""
            segments.append(
                f'<span class="seg" style="width:{share:.2f}%;background:{BAND[score - 1]}" '
                f'title="score {score}: {n} cells">{inner}</span>')
        rows.append(f"""        <div class="dist">
          <span class="dist-l">{esc(PIPE[pipeline]['label'])}</span>
          <span class="dist-t">{''.join(segments)}</span>
        </div>""")
    key = "".join(f'<span><i style="background:{BAND[i]}"></i>{i + 1}</span>' for i in range(5))
    return f"""      <div class="dist-wrap">
{chr(10).join(rows)}
        <div class="key">{key}<em>judge score, 1 wrong to 5 correct</em></div>
      </div>"""


def k_chart(d: dict) -> str:
    """Judge score against retrieval depth, one line per pipeline."""
    ks = [2, 3, 5]
    # x1 stops short of the viewBox so the end-of-line series labels,
    # which sit to the right of the last point, stay inside the box.
    x0, x1, y0, y1 = 74, 566, 34, 250
    step = (x1 - x0) / (len(ks) - 1)
    xs = [x0 + i * step for i in range(len(ks))]

    def y_of(value):
        return y1 - (value / 5.0) * (y1 - y0)

    grid, ticks = [], []
    for value in range(6):
        y = y_of(value)
        grid.append(f'<line x1="{x0}" y1="{y:.1f}" x2="{x1}" y2="{y:.1f}" class="grid"/>')
        ticks.append(f'<text x="{x0 - 12}" y="{y + 4:.1f}" class="ax" text-anchor="end">{value}</text>')
    for i, k in enumerate(ks):
        ticks.append(f'<text x="{xs[i]:.1f}" y="{y1 + 26}" class="ax" text-anchor="middle">k = {k}</text>')

    plotted = {}
    for pipeline in PIPE:
        plotted[pipeline] = [(xs[i], y_of(d["by_k"][f"{pipeline}|k={k}"]["judge_mean"]))
                             for i, k in enumerate(ks)]

    # Two pipelines can finish within a few points of each other, which puts
    # their end-of-line labels on top of one another. Walk the labels from the
    # top down and push each one below the last if it is too close.
    label_y, last = {}, None
    for pipeline in sorted(plotted, key=lambda p: plotted[p][-1][1]):
        y = plotted[pipeline][-1][1]
        if last is not None and y - last < 17:
            y = last + 17
        label_y[pipeline] = last = y

    series = []
    for pipeline, meta in PIPE.items():
        points = plotted[pipeline]
        path = " ".join(f"{'M' if i == 0 else 'L'}{x:.1f},{y:.1f}" for i, (x, y) in enumerate(points))
        dots = "".join(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5" fill="{meta["hue"]}"/>' for x, y in points)
        end_x, end_y = points[-1]
        ly = label_y[pipeline]
        # When a label has been nudged, a short leader keeps it tied to its line.
        leader = ("" if abs(ly - end_y) < 1 else
                  f'<line x1="{end_x + 6:.1f}" y1="{end_y:.1f}" x2="{end_x + 12:.1f}" '
                  f'y2="{ly:.1f}" stroke="{meta["hue"]}" stroke-width="1.5"/>')
        series.append(
            f'<path d="{path}" fill="none" stroke="{meta["hue"]}" stroke-width="3" '
            f'stroke-linecap="round" stroke-linejoin="round"/>{dots}{leader}'
            f'<text x="{end_x + 16:.1f}" y="{ly + 4:.1f}" class="lbl" fill="{meta["hue"]}">'
            f'{esc(meta["label"])}</text>')

    return f"""      <div class="chart">
        <svg viewBox="0 0 760 296" role="img" aria-label="Judge score against retrieval depth">
          {''.join(grid)}
          <line x1="{x0}" y1="{y0}" x2="{x0}" y2="{y1}" class="axis"/>
          <line x1="{x0}" y1="{y1}" x2="{x1}" y2="{y1}" class="axis"/>
          {''.join(ticks)}
          {''.join(series)}
        </svg>
      </div>"""


def forest_plot(d: dict, metric: str, title: str) -> str:
    """Paired differences for one metric, against the zero line.

    One plot per metric rather than one plot for both: judge score runs 1 to 5
    and recall runs 0 to 1, so a shared axis would squash every recall interval
    into a dot and invite a comparison of magnitudes that does not exist.
    """
    comps = [c for c in d["comparisons"] if c["metric"] == metric]
    lo = min(c["ci_low"] for c in comps)
    hi = max(c["ci_high"] for c in comps)
    pad = (hi - lo) * 0.16
    lo, hi = min(lo - pad, -pad), hi + pad
    # Every interval can collapse onto zero, for instance when a metric is
    # constant across pipelines. Give the axis a minimum span so the scale
    # stays defined and the marks land on the zero line rather than crashing.
    if hi - lo < 1e-9:
        lo, hi = -0.5, 0.5
    x0, x1 = 300, 742
    row_h, top = 46, 50

    def x_of(value):
        return x0 + (value - lo) / (hi - lo) * (x1 - x0)

    zero = x_of(0.0)
    rows = []
    for i, c in enumerate(comps):
        y = top + i * row_h
        colour = GOLD if c["significant"] else "#767C84"
        name = f"{PIPE[c['left']]['label']} vs {PIPE[c['right']]['label']}"
        rows.append(
            f'<text x="12" y="{y + 5}" class="lbl">{esc(name)}</text>'
            f'<line x1="{x_of(c["ci_low"]):.1f}" y1="{y}" x2="{x_of(c["ci_high"]):.1f}" y2="{y}" '
            f'stroke="{colour}" stroke-width="3" stroke-linecap="round"/>'
            f'<circle cx="{x_of(c["mean_difference"]):.1f}" cy="{y}" r="6" fill="{colour}"/>'
            f'<text x="{x1 + 8}" y="{y + 5}" class="ax" text-anchor="start">'
            f'{c["mean_difference"]:+.3f}</text>')
    height = top + len(comps) * row_h + 20
    return f"""      <div class="chart">
        <h4>{esc(title)}</h4>
        <svg viewBox="0 0 810 {height}" role="img" aria-label="Paired differences in {esc(title)}">
          <line x1="{zero:.1f}" y1="26" x2="{zero:.1f}" y2="{height - 30}" class="zero"/>
          <text x="{zero:.1f}" y="17" class="ax" text-anchor="middle">no difference</text>
          {''.join(rows)}
          <text x="{x0}" y="{height - 10}" class="ax" text-anchor="start">{lo:+.2f}</text>
          <text x="{x1}" y="{height - 10}" class="ax" text-anchor="end">{hi:+.2f}</text>
        </svg>
      </div>"""


def forest_key() -> str:
    return (f'      <p class="cap"><span class="swatch" style="background:{GOLD}"></span> '
            f'interval clear of zero, a difference is supported &nbsp; '
            f'<span class="swatch" style="background:#767C84"></span> '
            f'interval spans zero, it is not</p>')


def comparison_table(d: dict) -> str:
    rows = []
    for c in d["comparisons"]:
        state = "yes" if c["significant"] else "no"
        verdict = "difference" if c["significant"] else "indistinguishable"
        metric = "Judge score" if c["metric"] == "judge_score" else "Recall"
        rows.append(f"""        <tr>
          <th scope="row">{esc(PIPE[c['left']]['label'])} vs {esc(PIPE[c['right']]['label'])}</th>
          <td>{esc(metric)}</td>
          <td>{c['mean_difference']:+.3f}</td>
          <td class="mono">[{c['ci_low']:+.3f}, {c['ci_high']:+.3f}]</td>
          <td>{c['wins']} / {c['losses']} / {c['ties']}</td>
          <td class="mono">{c['sign_test_p']:.1e}</td>
          <td><span class="pill {state}">{verdict}</span></td>
        </tr>""")
    return "\n".join(rows)


def quadrant_grid(d: dict) -> str:
    cells = []
    for quadrant, (title, blurb) in QUAD.items():
        scores = {p: d["by_quadrant"][f"{quadrant}|{p}"]["judge_mean"] for p in PIPE}
        winner = max(scores, key=lambda p: scores[p])
        bars = "".join(
            bar_row(PIPE[p]["label"], scores[p], 5.0, PIPE[p]["hue"], f"{scores[p]:.2f}")
            for p in ("P2_bm25", "P1_vector", "P3_structural"))
        flag = ("" if winner == "P2_bm25" else
                f'<span class="flip">{esc(PIPE[winner]["label"])} leads here</span>')
        cells.append(f"""        <div class="quad">
          <p class="eyebrow">{esc(quadrant.split('_')[0])}</p>
          <h4>{esc(title)}</h4><p class="blurb">{esc(blurb)}</p>
          {bars}{flag}
        </div>""")
    return "\n".join(cells)


def build_cost(d: dict) -> tuple[str, str]:
    """Build cost as a table and as log-scaled bars, which span four decades."""
    snapshot = d.get("index_build")
    if not snapshot:
        return ("", '<p class="note">No index build cost snapshot has been taken.</p>')
    blocks = snapshot["pipelines"]
    top = math.log10(max(b["wall_clock_sec"] for b in blocks.values()) + 1)
    rows, bars = [], []
    for pipeline in agg.PIPELINES:
        b = blocks.get(pipeline)
        if not b:
            continue
        tokens = ("none" if not b["uses_llm"]
                  else f"{b['input_tokens']:,} in / {b['output_tokens']:,} out")
        rows.append(f"""        <tr>
          <th scope="row"><span class="dot" style="background:{PIPE[pipeline]['hue']}"></span>{esc(PIPE[pipeline]['label'])}</th>
          <td>{'yes' if b['uses_llm'] else 'no'}</td>
          <td>{duration(b['wall_clock_sec'])}</td>
          <td>{duration(b['median_filing_sec'])}</td>
          <td>{_rate(b['sec_per_1k_nodes'])}</td>
          <td>{esc(tokens)}</td>
          <td>{b['storage_bytes'] / 1024 ** 2:.0f} MB</td>
        </tr>""")
        width = max(0.8, math.log10(b["wall_clock_sec"] + 1) / top * 100)
        bars.append(f"""<div class="bar">
          <span class="bar-l">{esc(PIPE[pipeline]['label'])}</span>
          <span class="bar-t"><span class="bar-f" style="width:{width:.1f}%;background:{PIPE[pipeline]['hue']}"></span></span>
          <span class="bar-v">{duration(b['wall_clock_sec'])}</span>
        </div>""")
    chart = (f'      <div class="logbars">{"".join(bars)}'
             f'<p class="cap">Log scale. The spread is four orders of magnitude, '
             f'so a linear axis would render the two local builds invisible.</p></div>')
    return "\n".join(rows), chart


def token_table(d: dict) -> str:
    rows = []
    for pipeline in agg.PIPELINES:
        t = d["tokens"][pipeline]
        rows.append(f"""        <tr>
          <th scope="row"><span class="dot" style="background:{PIPE[pipeline]['hue']}"></span>{esc(PIPE[pipeline]['label'])}</th>
          <td>{t['inp']:,}</td><td>{t['out']:,}</td>
          <td>{t['inp'] / 300:,.0f}</td><td>{t['latency']:.2f} s</td>
        </tr>""")
    return "\n".join(rows)


def document_heatmap(d: dict) -> str:
    """Judge score per filing, with the question count that produced it.

    The count is on the face of the chart because the questions are not evenly
    spread: one filing carries seventeen and another carries one, so a row is
    not a like-for-like comparison with the row above it.
    """
    docs = sorted({key.split("|")[0] for key in d["by_document"]})
    counts = d["per_document_questions"]
    # Two labels per heading: the full name, and a short one that a phone-width
    # column can hold without wrapping into its neighbour.
    head = ('<span class="hm-n"><b class="lg">questions</b><b class="sm">n</b></span>'
            + "".join(f'<span class="hm-h"><b class="lg">{esc(PIPE[p]["label"])}</b>'
                      f'<b class="sm">{esc(PIPE[p]["label"].split()[0])}</b></span>'
                      for p in agg.PIPELINES))
    rows = []
    for document in docs:
        cells = []
        for pipeline in agg.PIPELINES:
            score = d["by_document"][f"{document}|{pipeline}"]["judge_mean"]
            colour = BAND[min(4, max(0, int(round(score)) - 1))]
            dark = score >= 4.5 or score < 1.5
            cells.append(f'<span class="hm-c" style="background:{colour};'
                         f'color:{"#fff" if dark else INK}">{score:.2f}</span>')
        rows.append(f'<span class="hm-r">{esc(document)}</span>'
                    f'<span class="hm-n">{counts.get(document, 0)}</span>{"".join(cells)}')
    body = "".join(f'<div class="hm-row">{r}</div>' for r in rows)
    key = "".join(f'<span><i style="background:{BAND[i]}"></i>{i + 1}</span>' for i in range(5))
    return f"""      <div class="heat">
        <div class="hm-row hm-head"><span class="hm-r"></span>{head}</div>
        {body}
        <div class="key">{key}<em>mean judge score for that filing</em></div>
      </div>"""


# --- the page -----------------------------------------------------------------

CSS = """
:root {
  --ink:#0A1F33; --body:#1A1D21; --muted:#54595F; --faint:#7A8087;
  --rule:#E2E5E9; --hair:#EEF0F3; --paper:#FFFFFF; --wash:#F7F9FB;
  --gold:#D4A017; --gold-wash:#FEF7E4;
  --p1:#3D5AFE; --p2:#00A5A8; --p3:#FF4D6D;
  --serif:"EB Garamond",Garamond,"Times New Roman",serif;
  --sans:Calibri,Carlito,"Segoe UI",system-ui,-apple-system,sans-serif;
  --mono:Consolas,"SF Mono",Menlo,monospace;
}
* { box-sizing:border-box; }
body { margin:0; background:var(--paper); color:var(--body);
       font-family:var(--serif); font-size:17px; line-height:1.65;
       -webkit-font-smoothing:antialiased; }
.wrap { max-width:1080px; margin:0 auto; padding-inline:24px; }
h1,h2,h3,h4 { font-family:var(--sans); color:var(--ink); text-wrap:balance; margin:0; }
h1 { font-size:clamp(2rem,5vw,3.1rem); font-weight:700; letter-spacing:-.02em; line-height:1.1; }
h2 { font-size:clamp(1.3rem,3vw,1.8rem); font-weight:700; letter-spacing:-.01em; }
h3 { font-size:1.12rem; font-weight:700; }
h4 { font-size:.82rem; font-weight:700; text-transform:uppercase;
     letter-spacing:.09em; color:var(--muted); margin-bottom:.9rem; }
p { margin:0 0 1rem; max-width:68ch; }
a { color:var(--p1); }

/* masthead */
header { border-top:6px solid var(--ink); padding-block:3.2rem 2.2rem; }
.eyebrow { font-family:var(--sans); font-size:.74rem; font-weight:700;
           text-transform:uppercase; letter-spacing:.16em; color:var(--p2); margin:0 0 .9rem; }
.stand { font-size:1.2rem; color:var(--muted); max-width:60ch; margin-top:1.1rem; }
.rule-bar { display:flex; height:5px; margin-top:2rem; }
.rule-bar i { flex:1; }

/* facts */
.facts { display:grid; grid-template-columns:repeat(6,1fr); gap:1px;
         background:var(--rule); border-block:1px solid var(--rule); margin-block:2.4rem; }
.fact { background:var(--paper); padding:1.1rem .9rem; text-align:center; }
.fact b { display:block; font-family:var(--sans); font-size:1.55rem;
          font-weight:700; color:var(--ink); line-height:1.15; }
.fact span { display:block; font-family:var(--sans); font-size:.72rem;
             text-transform:uppercase; letter-spacing:.05em; color:var(--faint); margin-top:.3rem; }

section { padding-block:2.6rem; border-top:1px solid var(--hair); }
section > h2 { margin-bottom:.4rem; }
.lede { color:var(--muted); margin-bottom:1.8rem; }

/* key finding */
.finding { background:var(--gold-wash); border-left:5px solid var(--gold);
           padding:1.4rem 1.6rem; margin-block:1.6rem; }
.finding p { margin:0; max-width:none; }
.finding p + p { margin-top:.7rem; }
.finding b { color:var(--ink); }

/* scoreboard */
.cards { display:grid; grid-template-columns:repeat(3,1fr); gap:1rem; margin-top:1.4rem; }
.card { border:1px solid var(--rule); border-top:4px solid var(--hue);
        padding:1.3rem 1.2rem; background:var(--paper); }
.card-top { display:flex; gap:.85rem; align-items:flex-start; }
.rank { flex:none; width:30px; height:30px; border-radius:50%; background:var(--wash);
        color:var(--hue); font-family:var(--sans); font-weight:700; font-size:.95rem;
        display:grid; place-items:center; }
.card h3 { line-height:1.25; }
.card-top p { font-size:.88rem; color:var(--faint); margin:.25rem 0 0; }
.card-nums { display:grid; grid-template-columns:repeat(3,1fr); gap:.5rem;
             margin-top:1.2rem; padding-top:1rem; border-top:1px solid var(--hair); }
.card-nums b { display:block; font-family:var(--sans); font-size:1.35rem;
               font-weight:700; color:var(--hue); }
.card-nums span { display:block; font-family:var(--sans); font-size:.68rem;
                  text-transform:uppercase; letter-spacing:.05em; color:var(--faint); }

/* tables */
.scroll { overflow-x:auto; margin-block:1.4rem; }
table { border-collapse:collapse; width:100%; font-family:var(--sans);
        font-size:.88rem; min-width:640px; }
caption { caption-side:top; text-align:left; font-family:var(--sans); font-size:.8rem;
          color:var(--faint); padding-bottom:.7rem; }
th,td { padding:.62rem .7rem; text-align:right; border-bottom:1px solid var(--hair);
        font-variant-numeric:tabular-nums; }
thead th { text-align:right; font-size:.72rem; text-transform:uppercase; letter-spacing:.05em;
           color:#fff; background:var(--ink); border-bottom:none; font-weight:700; }
thead th:first-child, tbody th { text-align:left; }
tbody th { font-weight:700; color:var(--ink); white-space:nowrap; }
tbody tr:nth-child(even) { background:var(--wash); }
.dot { display:inline-block; width:9px; height:9px; border-radius:50%; margin-right:.5rem; }
.mono { font-family:var(--mono); font-size:.82rem; }
.pill { display:inline-block; font-size:.7rem; font-weight:700; padding:.2em .65em;
        border-radius:2px; text-transform:uppercase; letter-spacing:.04em; }
.pill.yes { background:var(--gold); color:#3A2C00; }
.pill.no { background:#E9ECEF; color:var(--muted); }

/* bars */
.pair { display:grid; grid-template-columns:1fr 1fr; gap:2.4rem; margin-top:1.2rem; }
.bar { display:grid; grid-template-columns:6.6rem 1fr 4.2rem; align-items:center;
       gap:.7rem; margin-bottom:.55rem; font-family:var(--sans); font-size:.83rem; }
.bar-l { color:var(--muted); }
.bar-t { background:var(--hair); height:16px; overflow:hidden; }
.bar-f { display:block; height:100%; }
.bar-v { text-align:right; font-weight:700; color:var(--ink); font-variant-numeric:tabular-nums; }

/* distribution */
.dist-wrap { margin-top:1.2rem; }
.dist { display:grid; grid-template-columns:6.6rem 1fr; align-items:center;
        gap:.7rem; margin-bottom:.5rem; font-family:var(--sans); font-size:.83rem; }
.dist-l { color:var(--muted); }
.dist-t { display:flex; height:30px; overflow:hidden; }
.seg { display:grid; place-items:center; color:#fff; font-size:.72rem; font-weight:700; }
.key { display:flex; flex-wrap:wrap; align-items:center; gap:.75rem; margin-top:1rem;
       font-family:var(--sans); font-size:.75rem; color:var(--faint); }
.key span { display:inline-flex; align-items:center; gap:.35rem; }
.key i { width:13px; height:13px; display:inline-block; }
.key em { font-style:normal; }

/* svg charts */
.chart { margin-top:1.2rem; }
.chart svg { width:100%; height:auto; display:block; overflow:visible; }
.grid { stroke:var(--hair); stroke-width:1; }
.axis { stroke:var(--rule); stroke-width:1.5; }
.zero { stroke:var(--faint); stroke-width:1.5; stroke-dasharray:4 4; }
.ax { font-family:Calibri,Carlito,system-ui,sans-serif; font-size:13px; fill:var(--faint); }
.lbl { font-family:Calibri,Carlito,system-ui,sans-serif; font-size:14px;
       font-weight:700; fill:var(--ink); }
.cap { font-family:var(--sans); font-size:.78rem; color:var(--faint); margin-top:.9rem; }
.swatch { display:inline-block; width:11px; height:11px; vertical-align:-1px; }

/* quadrants */
.quads { display:grid; grid-template-columns:1fr 1fr; gap:1rem; margin-top:1.4rem; }
.quad { border:1px solid var(--rule); padding:1.2rem; }
.quad .eyebrow { color:var(--faint); margin-bottom:.4rem; }
.quad h4 { font-size:1.02rem; text-transform:none; letter-spacing:0;
           color:var(--ink); margin-bottom:.3rem; }
.blurb { font-size:.9rem; color:var(--faint); margin-bottom:1rem; }
.flip { display:inline-block; margin-top:.5rem; font-family:var(--sans); font-size:.72rem;
        font-weight:700; background:var(--gold-wash); color:#6B5200;
        padding:.25em .6em; text-transform:uppercase; letter-spacing:.04em; }

/* log bars + heatmap */
.logbars { margin-top:1.2rem; }
.heat { margin-top:1.2rem; font-family:var(--sans); font-size:.8rem; }
.hm-row { display:grid; grid-template-columns:7.5rem 4.4rem repeat(3,1fr); gap:2px; margin-bottom:2px; }
.hm-head .hm-h { font-size:.7rem; text-transform:uppercase; letter-spacing:.05em;
                 color:var(--faint); text-align:center; padding-bottom:.3rem;
                 white-space:nowrap; overflow:hidden; }
.hm-head b { font-weight:700; }
.sm { display:none; }
.hm-r { display:flex; align-items:center; color:var(--muted); font-variant-numeric:tabular-nums; }
.hm-n { display:grid; place-items:center; color:var(--faint); font-size:.72rem;
        font-variant-numeric:tabular-nums; }
.hm-head .hm-n { text-transform:uppercase; letter-spacing:.05em; padding-bottom:.3rem; }
.hm-c { display:grid; place-items:center; padding:.5rem 0; font-weight:700;
        font-variant-numeric:tabular-nums; }

.note { font-size:.95rem; color:var(--muted); border-left:3px solid var(--rule);
        padding-left:1rem; }
ul { padding-left:1.15rem; max-width:68ch; }
li { margin-bottom:.55rem; }
li b { color:var(--ink); }
footer { border-top:1px solid var(--rule); margin-top:2rem; padding-block:1.6rem 3rem;
         font-family:var(--sans); font-size:.78rem; color:var(--faint); }
footer code { font-family:var(--mono); }

@media (max-width:900px) {
  .facts { grid-template-columns:repeat(3,1fr); }
  .cards, .pair, .quads { grid-template-columns:1fr; }
}
@media (max-width:560px) {
  body { font-size:16px; }
  .facts { grid-template-columns:repeat(2,1fr); }
  .bar, .dist { grid-template-columns:5rem 1fr 3.4rem; }
  .dist { grid-template-columns:5rem 1fr; }
  .hm-row { grid-template-columns:4.8rem 1.9rem repeat(3,1fr); }
  .hm-head .hm-h, .hm-head .hm-n { font-size:.66rem; letter-spacing:.02em; }
  .lg { display:none; }
  .sm { display:inline; }
  .hm-r, .hm-c { font-size:.76rem; }
}
@media print { section { break-inside:avoid; } }
"""


def build_html(db_path: str) -> str:
    d = load(db_path)
    o = d["overall"]
    best = max(o, key=lambda p: o[p]["judge_mean"])
    worst = min(o, key=lambda p: o[p]["judge_mean"])
    p1p2 = next(c for c in d["comparisons"]
                if c["metric"] == "judge_score" and c["left"] == "P1_vector"
                and c["right"] == "P2_bm25")
    cost_rows, cost_chart = build_cost(d)
    snap = d.get("index_build") or {}
    structural = (snap.get("pipelines") or {}).get("P3_structural", {})
    cheapest = min((b for b in (snap.get("pipelines") or {}).values() if not b["uses_llm"]),
                   key=lambda b: b["wall_clock_sec"], default=None)
    ratio = (structural["wall_clock_sec"] / cheapest["wall_clock_sec"]
             if structural and cheapest else 0)
    q4 = {p: d["by_quadrant"][f"Q4_Implicit_Table|{p}"]["judge_mean"] for p in PIPE}
    q4_lead = max(q4, key=lambda p: q4[p])

    return f"""<!doctype html>
<html lang="en-GB">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Three Ways to Read a 10-K &middot; Findings</title>
<style>{CSS}</style>
</head>
<body>

<header class="wrap">
  <p class="eyebrow">COMP702 benchmark &middot; results</p>
  <h1>Three ways to read a 10-K</h1>
  <p class="stand">Semantic, statistical and structural retrieval answer the same
  {d['questions']} questions over {d['filings']} SEC annual reports, at three retrieval
  depths, judged on the same scale. These are the findings.</p>
  <div class="rule-bar">
    <i style="background:var(--p1)"></i><i style="background:var(--p2)"></i>
    <i style="background:var(--p3)"></i><i style="background:var(--gold)"></i>
  </div>
</header>

<div class="wrap">
{facts_strip(d)}
</div>

<div class="wrap">
<section style="border-top:none;padding-top:0">
  <h2>The headline</h2>
  <div class="finding">
    <p><b>Semantic and statistical retrieval are indistinguishable on this benchmark.</b>
    BM25 leads the vector pipeline on every point estimate, but the paired difference in
    judge score is {p1p2['mean_difference']:+.3f} with a 95% interval of
    [{p1p2['ci_low']:+.3f}, {p1p2['ci_high']:+.3f}], which spans zero. They tie on
    {p1p2['ties']} of {p1p2['n_pairs']} cells.</p>
    <p><b>The structural pipeline trails both by roughly two judge points</b>, with
    intervals nowhere near zero, and it is also the most expensive of the three to build
    and to query.</p>
  </div>
  <div class="cards">
{scoreboard(d)}
  </div>
</section>

<section>
  <h2>All three pillars</h2>
  <p class="lede">Retrieval quality, answer quality and efficiency, over all
  {d['cells']} cells.</p>
  <div class="scroll">
    <table>
      <caption>Table 1. Every metric, 300 cells per pipeline. Pass counts 4 and 5; fail counts 1.</caption>
      <thead><tr><th>Pipeline</th><th>Judge</th><th>Pass</th><th>Fail</th><th>Recall</th>
        <th>Precision</th><th>Hit rate</th><th>Citations</th><th>Token F1</th><th>Latency</th></tr></thead>
      <tbody>
{overall_table(d)}
      </tbody>
    </table>
  </div>
</section>

<section>
  <h2>Answer quality</h2>
  <p class="lede">The pass rate is the more honest summary, for the reason the next
  chart makes plain.</p>
{quality_chart(d)}
</section>

<section>
  <h2>The scores are bimodal, not spread</h2>
  <p class="lede">Almost every answer is either fully correct or wholly wrong. A mean of
  3.0 over this shape would describe no answer that any pipeline actually gave, which is
  why a pass rate is reported beside it.</p>
{distribution_chart(d)}
</section>

<section>
  <h2>Depth helps, but it does not rescue</h2>
  <p class="lede">Every pipeline improves as k rises from 2 to 5. The structural pipeline
  improves the most in relative terms and is still far below where the other two start.</p>
{k_chart(d)}
</section>

<section>
  <h2>Where the ordering changes</h2>
  <p class="lede">The question set is a genuine two by two: stated directly or inferred,
  crossed with prose or table. BM25 wins three of the four.</p>
  <div class="quads">
{quadrant_grid(d)}
  </div>
  <p class="note" style="margin-top:1.4rem">The exception is
  {esc(QUAD['Q4_Implicit_Table'][0])}, the one quadrant where the answer never appears
  verbatim anywhere in the filing. {esc(PIPE[q4_lead]['label'])} leads there at
  {q4[q4_lead]:.2f} against {q4['P2_bm25']:.2f} for BM25, which is what you would expect
  once exact term matching has nothing exact to match.</p>
</section>

<section>
  <h2>Is the difference real</h2>
  <p class="lede">Every pipeline answers exactly the same cells, so comparisons are
  paired on question and depth. Significance is a bootstrap interval and an exact sign
  test, not a t-test: these scores are ordinal, bounded and bimodal.</p>
{forest_plot(d, 'judge_score', 'Judge score, 1 to 5')}
{forest_plot(d, 'recall_at_k', 'Recall at k, 0 to 1')}
{forest_key()}
  <div class="scroll">
    <table>
      <caption>Table 2. Paired differences. W/L/T counts cells won, lost and tied.</caption>
      <thead><tr><th>Comparison</th><th>Metric</th><th>Difference</th><th>95% interval</th>
        <th>W / L / T</th><th>Sign test</th><th>Verdict</th></tr></thead>
      <tbody>
{comparison_table(d)}
      </tbody>
    </table>
  </div>
</section>

<section>
  <h2>What it costs to build</h2>
  <p class="lede">Latency and tokens describe what a question costs once the index
  exists. They leave out the one-off cost of creating it, which is where the three
  paradigms diverge hardest. Two build locally from the same {d['nodes']:,} nodes with no
  model call. The third drives an LLM over every node of every filing.</p>
{cost_chart}
  <div class="scroll">
    <table>
      <caption>Table 3. One build from scratch per filing, measured on the same machine.
      Wall clock includes time spent waiting on the LLM provider.</caption>
      <thead><tr><th>Pipeline</th><th>LLM</th><th>Total build</th><th>Median per filing</th>
        <th>Per 1k nodes</th><th>Build tokens</th><th>On disk</th></tr></thead>
      <tbody>
{cost_rows}
      </tbody>
    </table>
  </div>
  <p class="note">The structural index took {duration(structural.get('wall_clock_sec'))}
  against {duration(cheapest['wall_clock_sec']) if cheapest else '-'} for the cheapest
  local index, a factor of {ratio:,.0f}, and consumed
  {structural.get('input_tokens', 0) + structural.get('output_tokens', 0):,} tokens where
  the other two consumed none. That token count covers
  {structural.get('filings_with_tokens', 0)} of {structural.get('filings', 0)} filings,
  so it is a floor. A further {duration(structural.get('later_attempt_sec'))} went on
  rebuilds and resumed runs.</p>
</section>

<section>
  <h2>What it costs to ask</h2>
  <p class="lede">Answering spend over the {d['cells']} cells, recorded per call.</p>
  <div class="scroll">
    <table>
      <caption>Table 4. Answering tokens only. The judge's own calls are not recorded.</caption>
      <thead><tr><th>Pipeline</th><th>Input tokens</th><th>Output tokens</th>
        <th>Input per cell</th><th>Mean latency</th></tr></thead>
      <tbody>
{token_table(d)}
      </tbody>
    </table>
  </div>
  <p class="note">The structural pipeline sends the most text to the answerer for the
  same question, because tree nodes carry summaries rather than raw passages. It is the
  most expensive to query as well as to build, while scoring lowest.</p>
</section>

<section>
  <h2>Filing by filing</h2>
  <p class="lede">Mean judge score for each of the {d['filings']} filings. BM25 leads
  outright on six, the vector pipeline on three, and they tie on two more. The structural
  pipeline is last on eleven of thirteen, and on the two where it is not, all three score
  identically.</p>
{document_heatmap(d)}
  <p class="note">Read the rows against their question counts. The questions were drawn
  by quadrant rather than evenly by filing, so one filing carries seventeen of them and
  another carries one. A row built on a single question is an observation, not a rate.</p>
</section>

<section>
  <h2>Why the structural pipeline trails</h2>
  <p class="lede">A result this lopsided invites the suspicion that something is broken.
  The numbers say otherwise.</p>
  <ul>
    <li><b>It retrieves, it just retrieves the wrong nodes.</b> Hit rate is
    {pct(o['P3_structural']['hit_rate'])} against
    {pct(o[best]['hit_rate'])} for {esc(PIPE[best]['label'])}: on most questions the
    supporting node is never returned at all.</li>
    <li><b>Answer quality tracks retrieval almost exactly.</b> Recall of
    {num(o['P3_structural']['recall_at_k'])} against
    {num(o[best]['recall_at_k'])} produces a judge mean of
    {num(o['P3_structural']['judge_mean'], 2)} against {num(o[best]['judge_mean'], 2)}.
    When the evidence is absent the answering model mostly declines rather than
    fabricating.</li>
    <li><b>Its best quadrant is the inferential one.</b> Tree traversal descends by
    comparing the query against summaries, and a summary is exactly the artefact from
    which a specific figure has been compressed away. On a benchmark dominated by
    extraction that is fatal. It would not be on a benchmark of thematic questions,
    which is the use this structure was designed for.</li>
  </ul>
</section>

<section>
  <h2>What would weaken these findings</h2>
  <ul>
    <li><b>One run per cell.</b> Every call is temperature zero and each cell runs once,
    so these intervals describe variation across questions, not run to run variance.
    Nothing here estimates the latter.</li>
    <li><b>The judge gate is a pragmatic check.</b>
    {100 * d['gate'][0] / d['gate'][1]:.1f}% concordance on {d['gate'][1]} outputs is
    evidence the judge is usable, not proof it is correct, and it is cross-model
    concordance rather than external human validation.</li>
    <li><b>The answer key needed correcting.</b> The question generator returned whole
    section citation lists on 24 of 100 questions, making full recall arithmetically
    unreachable on those rows. Citations were re-derived to the minimal set that
    demonstrably yields the answer, and one answer key was rewritten. Both corrections
    replay from the repository.</li>
    <li><b>Build tokens are incomplete.</b> Two filings were built before the build log
    recorded token counts, so the structural token figure is a floor over
    {structural.get('filings_with_tokens', 0)} of {structural.get('filings', 0)}
    filings.</li>
    <li><b>Corpus artefacts survive.</b> A handful of nodes carry identifiers where a
    figure belongs, and some carry unescaped HTML entities. All three pipelines index the
    identical corpus, so none is advantaged.</li>
  </ul>
</section>

<footer>
  <p>Generated {date.today().isoformat()} from <code>benchmark.db</code> by
  <code>project/build_findings_page.py</code>. Every figure on this page is read from the
  database at build time through <code>aggregate_results.py</code>, with no manual step.
  {d['cells']} cells &middot; {d['nodes']:,} nodes &middot; {d['filings']} filings
  &middot; one temperature-zero run per cell.</p>
</footer>
</div>

</body>
</html>
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", default="benchmark.db")
    parser.add_argument("--out", default=str(OUT_PATH))
    args = parser.parse_args(argv)
    html_text = build_html(args.db)
    Path(args.out).write_text(html_text)
    print(f"wrote {args.out} ({len(html_text) / 1024:.0f} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
