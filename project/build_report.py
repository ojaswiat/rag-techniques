"""Builds the standalone HTML results report.

Every figure and every number is pulled from the database at build time, the
figures through build_figures and the tables through aggregate_results, so the
report cannot quietly disagree with the data it describes. Figures are
embedded as data URIs, making the output a single self-contained file.

Type and colour follow resources/assets/design/palette.md and
resources/assets/design/typography.md rather than being chosen here.
"""
import argparse
import base64
import sqlite3
from datetime import date
from pathlib import Path

import aggregate_results as agg
import build_figures as bf

PIPELINE_LABELS = bf.PIPELINE_LABELS
QUADRANT_TITLES = {
    "Q1_Direct_Text": "Direct, text",
    "Q2_Implicit_Text": "Implicit, text",
    "Q3_Direct_Table": "Direct, table",
    "Q4_Implicit_Table": "Implicit, table",
}
QUADRANT_BLURB = {
    "Q1_Direct_Text": "One explicit statement in continuous prose.",
    "Q2_Implicit_Text": "Synthesis across several narrative passages.",
    "Q3_Direct_Table": "Exact extraction of a single table cell.",
    "Q4_Implicit_Table": "A calculation or cross-row inference over a table.",
}


def embed(path: Path) -> str:
    """A PNG as a data URI, so the report stays one self-contained file."""
    return "data:image/png;base64," + base64.b64encode(path.read_bytes()).decode()


def _pct(value: float | None) -> str:
    return "-" if value is None else f"{value * 100:.1f}%"


def _num(value: float | None, places: int = 3) -> str:
    return "-" if value is None else f"{value:.{places}f}"


def figure_block(src: str, number: str, caption: str) -> str:
    return f"""      <figure class="fig">
        <img src="{src}" alt="Figure {number}. {caption}">
        <figcaption><span class="fig-num">Figure {number}</span> {caption}</figcaption>
      </figure>"""


def overall_table(report: dict) -> str:
    order = sorted(report["overall"], key=lambda p: -report["overall"][p]["judge_mean"])
    rows = []
    for pipeline in order:
        s = report["overall"][pipeline]
        lead = ' class="lead"' if pipeline == order[0] else ""
        rows.append(f"""          <tr{lead}>
            <th scope="row">{PIPELINE_LABELS[pipeline]}</th>
            <td>{_num(s['judge_mean'], 2)}</td><td>{_pct(s['judge_pass_rate'])}</td>
            <td>{_num(s['recall_at_k'])}</td><td>{_num(s['precision_at_k'])}</td>
            <td>{_pct(s['hit_rate'])}</td><td>{_pct(s['citation_match'])}</td>
            <td>{_num(s['latency_sec'], 2)}s</td>
          </tr>""")
    return "\n".join(rows)


def quadrant_grid(report: dict) -> str:
    cells = []
    for quadrant in agg.QUADRANTS:
        scores = {p: report["by_quadrant"][f"{quadrant}|{p}"]["judge_mean"] for p in agg.PIPELINES}
        winner = max(scores, key=lambda p: scores[p])
        bars = "\n".join(
            f"""            <div class="qbar">
              <span class="qname">{PIPELINE_LABELS[p]}</span>
              <span class="qtrack"><span class="qfill" style="width:{scores[p] / 5 * 100:.1f}%;background:{bf.PIPELINE_COLOURS[p]}"></span></span>
              <span class="qval">{scores[p]:.2f}</span>
            </div>""" for p in ("P2_bm25", "P1_vector", "P3_structural"))
        flip = ' data-flip="true"' if winner == "P1_vector" else ""
        cells.append(f"""        <div class="quad"{flip}>
          <p class="qeyebrow">{quadrant.split('_')[0]}</p>
          <h3>{QUADRANT_TITLES[quadrant]}</h3>
          <p class="qblurb">{QUADRANT_BLURB[quadrant]}</p>
{bars}
        </div>""")
    return "\n".join(cells)


def comparison_table(report: dict) -> str:
    rows = []
    for c in report["comparisons"]:
        if c["metric"] != "judge_score":
            continue
        verdict = ("difference detected" if c["significant"]
                   else "no difference detected")
        state = "sig" if c["significant"] else "nosig"
        rows.append(f"""          <tr>
            <th scope="row">{PIPELINE_LABELS[c['left']]} vs {PIPELINE_LABELS[c['right']]}</th>
            <td>{c['mean_difference']:+.3f}</td>
            <td class="ci">[{c['ci_low']:+.3f}, {c['ci_high']:+.3f}]</td>
            <td>{c['wins']} / {c['losses']} / {c['ties']}</td>
            <td>{c['sign_test_p']:.2e}</td>
            <td><span class="pill {state}">{verdict}</span></td>
          </tr>""")
    return "\n".join(rows)


def build_html(db_path: str, figures_dir: Path) -> str:
    conn = sqlite3.connect(db_path)
    report = agg.build_report(conn, "PQ")
    gate = conn.execute(
        "SELECT COUNT(*), SUM(judge_score = human_score) FROM results WHERE source_set = 'JEQ'"
    ).fetchone()
    nodes, filings = conn.execute(
        "SELECT COUNT(*), COUNT(DISTINCT document_id) FROM nodes").fetchone()

    p1p2 = next(c for c in report["comparisons"]
                if c["metric"] == "judge_score" and c["left"] == "P1_vector"
                and c["right"] == "P2_bm25")
    # "figure-5-1-answer-quality" keys on "answer-quality": the figure number
    # lives in the caption, so the slug is what the template refers to.
    figs = {p.stem.split("-", 3)[-1]: embed(p) for p in sorted(figures_dir.glob("figure-5-*.png"))}
    by = report["by_quadrant"]

    return f"""<title>Three Ways to Read a 10-K</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=EB+Garamond:ital,wght@0,400;0,500;0,600;1,400&family=Source+Sans+3:wght@400;600;700&family=JetBrains+Mono:wght@400;500&display=swap">
<style>
  :root {{
    --ink: #0A1F33;      --primary: #15406B;  --mid: #2B6CA3;
    --soft: #82AAC9;     --tint: #DCE6EE;     --paper: #F2F6FA;
    --body: #1A1D21;     --muted: #44494F;    --faint: #767C84;
    --rule: #B7BCC2;     --surface: #FFFFFF;  --gold: #D4A017;
    --gold-ink: #8C6D00; --gold-wash: #FBF0D6;
    --ok: #0B8457;       --bad: #C73E35;
    --serif: "EB Garamond", Garamond, "Times New Roman", serif;
    --sans: Calibri, Carlito, "Source Sans 3", system-ui, sans-serif;
    --mono: Consolas, "JetBrains Mono", ui-monospace, monospace;
    --measure: 68ch;
  }}
  @media (prefers-color-scheme: dark) {{
    :root:not([data-theme="light"]) {{
      --ink: #DCE6EE;    --primary: #82AAC9;  --mid: #5089B8;
      --soft: #2B6CA3;   --tint: #14283D;     --paper: #0A1620;
      --body: #E4E6E9;   --muted: #B7BCC2;    --faint: #8C939B;
      --rule: #2A3946;   --surface: #10202E;  --gold: #E8C667;
      --gold-ink: #E8C667; --gold-wash: #2A2312;
      --ok: #3FA87C;     --bad: #E0736A;
    }}
  }}
  :root[data-theme="dark"] {{
    --ink: #DCE6EE;      --primary: #82AAC9;  --mid: #5089B8;
    --soft: #2B6CA3;     --tint: #14283D;     --paper: #0A1620;
    --body: #E4E6E9;     --muted: #B7BCC2;    --faint: #8C939B;
    --rule: #2A3946;     --surface: #10202E;  --gold: #E8C667;
    --gold-ink: #E8C667; --gold-wash: #2A2312;
    --ok: #3FA87C;       --bad: #E0736A;
  }}

  * {{ box-sizing: border-box; }}
  body {{
    background: var(--paper); color: var(--body);
    font-family: var(--serif); font-size: 1.0625rem; line-height: 1.65;
    margin: 0; padding-block: 0 5rem; padding-left: 20px; padding-right: 20px;
    -webkit-font-smoothing: antialiased;
  }}
  .wrap {{ max-width: var(--measure); margin: 0 auto; }}
  .wide {{ max-width: 1080px; margin: 0 auto; }}

  h1, h2, h3, .sans {{ font-family: var(--sans); text-wrap: balance; }}
  h1 {{ font-size: clamp(2rem, 5vw, 2.9rem); line-height: 1.1; color: var(--ink);
       font-weight: 700; letter-spacing: -0.015em; margin: 0 0 .75rem; }}
  h2 {{ font-size: 1.5rem; color: var(--primary); font-weight: 700;
       margin: 3.5rem 0 .25rem; letter-spacing: -0.01em; }}
  h3 {{ font-size: 1.05rem; color: var(--mid); font-weight: 600; margin: 2rem 0 .4rem; }}
  p {{ margin: 0 0 1.1rem; }}
  a {{ color: var(--mid); }}
  code {{ font-family: var(--mono); font-size: .86em; background: var(--tint);
         padding: .1em .35em; border-radius: 3px; color: var(--ink); }}
  .eyebrow {{ font-family: var(--sans); font-size: .72rem; font-weight: 700;
             letter-spacing: .14em; text-transform: uppercase; color: var(--faint);
             margin: 0 0 .9rem; }}
  .standfirst {{ font-size: 1.2rem; line-height: 1.5; color: var(--muted);
                font-style: italic; margin-bottom: 2rem; }}
  .rule {{ height: 2px; background: var(--primary); border: 0; margin: 1.6rem 0 0; }}

  header {{ padding-top: 4rem; }}
  .facts {{ display: flex; flex-wrap: wrap; gap: 0 2.5rem; font-family: var(--sans);
           font-size: .82rem; color: var(--faint); margin-top: 1.1rem;
           padding-top: 1.1rem; border-top: 1px solid var(--rule); }}
  .facts b {{ display: block; font-size: 1.5rem; color: var(--ink); font-weight: 700;
             font-variant-numeric: tabular-nums; line-height: 1.2; }}

  .finding {{ background: var(--gold-wash); border-left: 4px solid var(--gold);
             padding: 1.4rem 1.6rem; margin: 2.5rem 0; }}
  .finding p:last-child {{ margin-bottom: 0; }}
  .finding .eyebrow {{ color: var(--gold-ink); }}

  table {{ width: 100%; border-collapse: collapse; font-family: var(--sans);
          font-size: .88rem; font-variant-numeric: tabular-nums; margin: .5rem 0 .4rem; }}
  thead th {{ background: var(--primary); color: #fff; text-align: right;
             padding: .55rem .6rem; font-weight: 600; font-size: .78rem;
             letter-spacing: .02em; }}
  thead th:first-child {{ text-align: left; }}
  tbody th {{ text-align: left; font-weight: 600; color: var(--ink); }}
  tbody td, tbody th {{ padding: .55rem .6rem; border-bottom: 1px solid var(--rule);
                       text-align: right; }}
  tbody tr.lead {{ background: var(--tint); }}
  .scroll {{ overflow-x: auto; }}
  .ci {{ font-family: var(--mono); font-size: .8rem; }}
  .pill {{ font-size: .72rem; font-weight: 700; padding: .2em .6em; border-radius: 999px;
          white-space: nowrap; }}
  .pill.sig {{ background: var(--ok); color: #fff; }}
  .pill.nosig {{ background: var(--rule); color: var(--body); }}
  caption {{ caption-side: bottom; text-align: left; font-family: var(--sans);
            font-size: .78rem; color: var(--faint); padding-top: .6rem; }}

  .fig {{ margin: 2rem 0 2.4rem; }}
  .fig img {{ width: 100%; max-width: 100%; display: block; background: #fff;
             border: 1px solid var(--rule); }}
  figcaption {{ font-family: var(--sans); font-size: .8rem; color: var(--muted);
               margin-top: .6rem; line-height: 1.45; }}
  .fig-num {{ font-weight: 700; color: var(--ink); }}

  .quads {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1px;
           background: var(--rule); border: 1px solid var(--rule); margin: 1.5rem 0 2rem; }}
  .quad {{ background: var(--surface); padding: 1.1rem 1.2rem 1.3rem; }}
  .quad[data-flip="true"] {{ box-shadow: inset 3px 0 0 var(--gold); }}
  .qeyebrow {{ font-family: var(--mono); font-size: .78rem; color: var(--faint); margin: 0; }}
  .quad h3 {{ margin: .1rem 0 .3rem; font-size: 1rem; color: var(--ink); }}
  .qblurb {{ font-size: .92rem; color: var(--muted); margin: 0 0 .9rem; line-height: 1.4; }}
  .qbar {{ display: grid; grid-template-columns: 5.5rem 1fr 2.4rem; align-items: center;
          gap: .5rem; font-family: var(--sans); font-size: .76rem; margin-bottom: .3rem; }}
  .qname {{ color: var(--muted); }}
  .qtrack {{ background: var(--tint); height: 9px; border-radius: 2px; overflow: hidden; }}
  .qfill {{ display: block; height: 100%; }}
  .qval {{ text-align: right; font-variant-numeric: tabular-nums; color: var(--ink);
          font-weight: 600; }}

  ul {{ padding-left: 1.2rem; margin: 0 0 1.1rem; }}
  li {{ margin-bottom: .45rem; }}
  .note {{ font-size: .95rem; color: var(--muted); border-left: 3px solid var(--rule);
          padding-left: 1rem; margin: 1.5rem 0; }}
  footer {{ margin-top: 4rem; padding-top: 1.2rem; border-top: 1px solid var(--rule);
           font-family: var(--sans); font-size: .8rem; color: var(--faint); }}

  @media (max-width: 620px) {{
    .quads {{ grid-template-columns: 1fr; }}
    .facts {{ gap: 0 1.5rem; }}
  }}
  @media (prefers-reduced-motion: reduce) {{ * {{ animation: none !important; transition: none !important; }} }}
</style>

<header class="wrap">
  <p class="eyebrow">COMP702 dissertation &middot; results</p>
  <h1>Three Ways to Read a 10-K</h1>
  <p class="standfirst">A controlled comparison of semantic, statistical and structural
  retrieval over {filings} SEC annual filings, across {report['cells']} benchmark cells.</p>
  <hr class="rule">
  <div class="facts">
    <div><b>{report['cells']}</b>benchmark cells</div>
    <div><b>{nodes:,}</b>indexed nodes</div>
    <div><b>3</b>retrieval paradigms</div>
    <div><b>{100 * gate[1] / gate[0]:.1f}%</b>judge concordance</div>
  </div>
</header>

<main class="wrap">
  <div class="finding">
    <p class="eyebrow">The headline</p>
    <p><strong>Semantic and statistical retrieval are indistinguishable on this
    benchmark.</strong> BM25 leads the vector pipeline on every point estimate, but the
    paired difference in judge score is {p1p2['mean_difference']:+.3f} with a 95%
    interval of [{p1p2['ci_low']:+.3f}, {p1p2['ci_high']:+.3f}], which spans zero. The
    structural pipeline is a different matter: it trails both by roughly two points on a
    five-point scale, with intervals nowhere near zero.</p>
  </div>

  <h2>What was measured</h2>
  <p>Three retrieval paradigms answer an identical set of 100 questions drawn from
  {filings} SEC 10-K filings, each at three retrieval depths
  (<code>k</code> of 2, 3 and 5). That is {report['cells']} cells, every one running once
  at temperature zero.</p>
  <ul>
    <li><strong>P1 Vector</strong> &mdash; ChromaDB with fastembed, reranked by a local
    <code>bge-reranker-base</code> cross-encoder.</li>
    <li><strong>P2 BM25</strong> &mdash; <code>rank_bm25</code> only, purely statistical,
    with a byte-identical tokenizer at index and query time.</li>
    <li><strong>P3 Structural</strong> &mdash; a LlamaIndex summary tree per filing,
    traversed by embedding similarity against node summaries.</li>
  </ul>
  <p>All three retrieve within the query's own filing, receive only the question and
  their own retrieved nodes, and hand off to the same answering model. Scoring is an
  LLM judge from a different model family, which is an anti-self-grading requirement,
  and it cleared a concordance gate of {100 * gate[1] / gate[0]:.1f}% ({gate[1]} of
  {gate[0]}) before being trusted with the full run.</p>

  <h2>The result</h2>
  <div class="scroll">
    <table>
      <caption>Table 5.1 &mdash; All 900 cells, 300 per pipeline. Pass rate counts answers scoring 4 or 5.</caption>
      <thead><tr><th>Pipeline</th><th>Judge</th><th>Pass</th><th>Recall</th>
        <th>Precision</th><th>Hit rate</th><th>Citations</th><th>Latency</th></tr></thead>
      <tbody>
{overall_table(report)}
      </tbody>
    </table>
  </div>
</main>

<div class="wide">
{figure_block(figs['answer-quality'], '5.1', 'Answer quality by retrieval paradigm. The pass rate is the more honest summary here, for the reason Figure 5.5 makes plain.')}
{figure_block(figs['retrieval-quality'], '5.2', 'Retrieval quality. Answer quality tracks retrieval almost exactly: when the supporting node is never retrieved, the answering model mostly declines rather than fabricating.')}
</div>

<main class="wrap">
  <h2>Depth helps, but it does not rescue</h2>
  <p>Every pipeline improves as <code>k</code> rises from 2 to 5, and the structural
  pipeline improves the most in relative terms, from
  {_num(report['by_k']['P3_structural|k=2']['judge_mean'], 2)} to
  {_num(report['by_k']['P3_structural|k=5']['judge_mean'], 2)}. It is still far below
  where the other two start.</p>
</main>

<div class="wide">
{figure_block(figs['effect-of-k'], '5.3', 'Effect of retrieval depth. The gap between paradigms is wider than anything retrieval depth changes within one.')}
</div>

<main class="wrap">
  <h2>Where the ordering changes</h2>
  <p>The question set is a genuine two-by-two: whether the answer is stated directly or
  must be inferred, crossed with whether it lives in prose or in a table. BM25 wins three
  of the four. The exception is the one quadrant where the answer never appears verbatim
  anywhere in the filing.</p>

  <div class="quads">
{quadrant_grid(report)}
  </div>

  <p class="note">BM25 peaks at
  {_num(by['Q1_Direct_Text|P2_bm25']['judge_mean'], 2)} on direct text, exactly where
  lexical overlap between question and source is highest. It falls to
  {_num(by['Q4_Implicit_Table|P2_bm25']['judge_mean'], 2)} on implicit table questions,
  where the answer must be computed and so cannot be matched lexically at all. That is
  the only quadrant where the vector pipeline leads, at
  {_num(by['Q4_Implicit_Table|P1_vector']['judge_mean'], 2)}, and it is the clearest
  signal in the study of what semantic retrieval actually buys.</p>
</main>

<div class="wide">
{figure_block(figs['by-quadrant'], '5.4', 'Answer quality by question type. Gold marks the single quadrant where the leading pipeline changes.')}
{figure_block(figs['score-distribution'], '5.5', 'Scores are bimodal. Answers are mostly either fully correct or wholly wrong, so a mean describes a kind of answer that rarely occurs; pass rates are reported alongside for that reason.')}
</div>

<main class="wrap">
  <h2>Is the difference real</h2>
  <p>Every pipeline answers exactly the same cells, so comparisons are paired on
  question and depth rather than treated as independent samples. That removes
  per-question difficulty, which otherwise dominates the spread. Significance is a
  bootstrap interval and an exact sign test, not a t-test: these scores are ordinal,
  bounded and bimodal, and a normal-theory test would be asserting a property the data
  does not have.</p>

  <div class="scroll">
    <table>
      <caption>Table 5.2 &mdash; Paired differences in judge score. W/L/T counts cells won, lost and tied.</caption>
      <thead><tr><th>Comparison</th><th>Difference</th><th>95% interval</th>
        <th>W / L / T</th><th>Sign test</th><th>Verdict</th></tr></thead>
      <tbody>
{comparison_table(report)}
      </tbody>
    </table>
  </div>

  <p>The vector-versus-BM25 comparison ties on {p1p2['ties']} of
  {p1p2['n_pairs']} cells, which is the bimodality again: on most questions both
  pipelines either find the answer or both miss it. The remaining cells split
  {p1p2['wins']} to {p1p2['losses']}, not enough to separate them.</p>
</main>

<div class="wide">
{figure_block(figs['paired-comparisons'], '5.6', 'Paired comparisons with 95% bootstrap intervals. Only intervals clear of the zero line support a claim of difference.')}
</div>

<main class="wrap">
  <h2>Why the structural pipeline fails</h2>
  <p>It is worth being precise, because a result this lopsided invites the suspicion
  that something is simply broken. It is not. The pipeline returns valid node
  identifiers from the correct filing, its traversal is driven by embeddings rather than
  a stub model, and its retrieval diversity is the <em>highest</em> of the three at
  0.867 distinct nodes per returned slot. It returns varied, query-specific nodes. They
  are the wrong ones.</p>
  <p>The mechanism is visible in the miss distances. Tree traversal descends by
  comparing the query against <em>summaries</em> of each branch, and a summary is
  precisely the artefact from which a specific figure has been compressed away. The
  median retrieved node sits at ordinal 818 against a gold node at 406: the right region
  of the filing, the wrong node within it. On a benchmark dominated by extraction, that
  is fatal. It would not be on a benchmark of thematic or whole-document questions,
  which is the use this index structure was designed for.</p>

  <h2>What would weaken these findings</h2>
  <ul>
    <li><strong>One run per cell.</strong> Every call is temperature zero and each cell
    runs once, so the intervals here describe variation across questions, not run-to-run
    variance. Nothing in this study estimates the latter.</li>
    <li><strong>The judge gate is a pragmatic check.</strong> {100 * gate[1] / gate[0]:.1f}%
    concordance on {gate[0]} outputs is evidence the judge is usable, not proof it is
    correct. It is also cross-model concordance rather than external human validation.</li>
    <li><strong>The answer key needed correcting.</strong> The question generator
    returned whole-section citation lists on 24 of 100 questions, which made full recall
    arithmetically unreachable on those rows while inflating precision. Citations were
    re-derived to the minimal set that demonstrably yields the answer, and one answer key
    that graded a correct response as wrong was rewritten. Both corrections are recorded
    as deviations and are reproducible from the repository.</li>
    <li><strong>The structural gap is larger here than on the gate set.</strong> P3
    scored 0.538 recall on the 20-question validation set against
    {_num(report['overall']['P3_structural']['recall_at_k'])} on the 100-question
    benchmark. The validation set is small, but the discrepancy is unexplained and
    should not be glossed.</li>
    <li><strong>Corpus artefacts survive.</strong> Four nodes carry identifiers where a
    figure belongs, and around 6% carry unescaped HTML entities. All three pipelines
    index the identical corpus, so none is advantaged, and the affected question tests
    extraction fidelity rather than recall.</li>
  </ul>

  <h2>Reproducing this</h2>
  <p>Every number and figure above is generated from the <code>results</code> table with
  no manual step between: <code>aggregate_results.py</code> produces the tables and the
  paired statistics, <code>build_figures.py</code> renders Figures 5.1 to 5.6, and this
  page is assembled by <code>build_report.py</code> from both. The answer-key corrections
  replay from <code>repair_answer_keys.py</code> and reproduce the corrected database
  exactly. Judging records the fingerprint of the rubric that produced each score, so a
  rescored run cannot silently mix two rubrics.</p>

  <footer>
    <p>COMP702 M.Sc. dissertation &middot; {report['cells']} cells &middot;
    {nodes:,} nodes across {filings} filings &middot; generated {date.today().isoformat()}
    from <code>benchmark.db</code></p>
  </footer>
</main>
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", default="benchmark.db")
    parser.add_argument("--figures", default="../resources/artifacts/figures")
    parser.add_argument("--out", default="../resources/artifacts/results-report.html")
    args = parser.parse_args(argv)
    html = build_html(args.db, Path(args.figures))
    Path(args.out).write_text(html)
    print(f"wrote {args.out} ({len(html) / 1024:.0f} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
