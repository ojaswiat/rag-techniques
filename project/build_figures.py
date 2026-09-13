"""Renders the results figures from the benchmark database.

Every figure is built from aggregate_results.build_report(), so the charts and
the reported tables cannot drift apart: both read `results` and nothing else.
Colours and type come from resources/assets/design/palette.md ("Oxford Ink")
rather than matplotlib defaults, so figures match the written deliverables.

Figures are numbered for the results chapter (Figure 5.x) per the project's
section.number convention.
"""
import argparse
import sqlite3
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # No display in this environment; render straight to file.
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

import aggregate_results as agg

# Oxford Ink, section 2.1 categorical order. Three series, so the first three
# entries: each pipeline keeps one colour across every figure.
PIPELINE_COLOURS = {
    "P1_vector": "#15406B",      # Primary Blue
    "P2_bm25": "#2B7A8C",        # Teal Blue
    "P3_structural": "#5C6670",  # Cool Slate
}
PIPELINE_LABELS = {
    "P1_vector": "P1 Vector",
    "P2_bm25": "P2 BM25",
    "P3_structural": "P3 Structural",
}
QUADRANT_LABELS = {
    "Q1_Direct_Text": "Q1\nDirect Text",
    "Q2_Implicit_Text": "Q2\nImplicit Text",
    "Q3_Direct_Table": "Q3\nDirect Table",
    "Q4_Implicit_Table": "Q4\nImplicit Table",
}

INK = "#0A1F33"          # titles
BODY = "#1A1D21"         # body text
MUTED = "#767C84"        # axis labels
GRID = "#B7BCC2"         # grid lines
GOLD = "#D4A017"         # reserved accent, used once for the key finding
SEQUENTIAL = ["#DCE6EE", "#B4CBDE", "#82AAC9", "#2B6CA3", "#15406B"]  # score bands 1-5


def apply_house_style() -> None:
    """Applies the project's type and colour conventions to matplotlib."""
    plt.rcParams.update({
        # Calibri for chart text per the project's typography rules; the
        # fallbacks keep rendering sane on a machine without it rather than
        # letting matplotlib drop to its own default sans.
        "font.family": "sans-serif",
        "font.sans-serif": ["Calibri", "Carlito", "Helvetica Neue", "Arial", "DejaVu Sans"],
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "axes.edgecolor": GRID,
        "axes.labelcolor": BODY,
        "axes.titlecolor": INK,
        "axes.grid": True,
        "axes.axisbelow": True,
        "grid.color": GRID,
        "grid.linewidth": 0.6,
        "grid.alpha": 0.5,
        "xtick.color": MUTED,
        "ytick.color": MUTED,
        "text.color": BODY,
        "figure.dpi": 150,
        "savefig.dpi": 300,
        "savefig.bbox": "tight",
    })


def _finish(ax, title: str, ylabel: str | None = None, ylim=None) -> None:
    ax.set_title(title, fontsize=12, fontweight="bold", pad=12)
    if ylabel:
        ax.set_ylabel(ylabel, fontsize=10)
    if ylim:
        ax.set_ylim(*ylim)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)


def _bar_labels(ax, bars, places=2) -> None:
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, height, f"{height:.{places}f}",
                ha="center", va="bottom", fontsize=8, color=BODY)


def figure_answer_quality(report: dict, path: Path) -> Path:
    """Figure 5.1: judge mean and pass rate per pipeline."""
    order = sorted(report["overall"], key=lambda p: -report["overall"][p]["judge_mean"])
    fig, (left, right) = plt.subplots(1, 2, figsize=(10, 4.2))

    bars = left.bar([PIPELINE_LABELS[p] for p in order],
                    [report["overall"][p]["judge_mean"] for p in order],
                    color=[PIPELINE_COLOURS[p] for p in order], width=0.6)
    _bar_labels(left, bars)
    _finish(left, "Mean judge score", "Judge score (1 to 5)", (0, 5.4))

    bars = right.bar([PIPELINE_LABELS[p] for p in order],
                     [report["overall"][p]["judge_pass_rate"] * 100 for p in order],
                     color=[PIPELINE_COLOURS[p] for p in order], width=0.6)
    _bar_labels(right, bars, places=1)
    _finish(right, "Pass rate (score 4 or 5)", "Percentage of answers", (0, 100))

    fig.suptitle("Figure 5.1  Answer quality by retrieval paradigm",
                 fontsize=13, fontweight="bold", color=INK, y=1.02)
    fig.savefig(path)
    plt.close(fig)
    return path


def figure_retrieval_quality(report: dict, path: Path) -> Path:
    """Figure 5.2: the retrieval pillar, three metrics per pipeline."""
    metrics = [("recall_at_k", "Recall@k"), ("precision_at_k", "Precision@k"),
               ("hit_rate", "Hit rate"), ("citation_match", "Citation match")]
    order = ["P2_bm25", "P1_vector", "P3_structural"]
    fig, ax = plt.subplots(figsize=(9, 4.4))
    width = 0.26
    for offset, pipeline in enumerate(order):
        values = [report["overall"][pipeline][key] for key, _ in metrics]
        positions = [i + (offset - 1) * width for i in range(len(metrics))]
        bars = ax.bar(positions, values, width=width, color=PIPELINE_COLOURS[pipeline],
                      label=PIPELINE_LABELS[pipeline])
        _bar_labels(ax, bars)
    ax.set_xticks(range(len(metrics)))
    ax.set_xticklabels([label for _, label in metrics])
    ax.legend(frameon=False, fontsize=9)
    _finish(ax, "Figure 5.2  Retrieval quality by paradigm", "Score", (0, 1.0))
    fig.savefig(path)
    plt.close(fig)
    return path


def figure_effect_of_k(report: dict, path: Path) -> Path:
    """Figure 5.3: how retrieval depth changes answer quality."""
    fig, (left, right) = plt.subplots(1, 2, figsize=(10, 4.2))
    ks = [2, 3, 5]
    for pipeline in PIPELINE_COLOURS:
        judge = [report["by_k"][f"{pipeline}|k={k}"]["judge_mean"] for k in ks]
        recall = [report["by_k"][f"{pipeline}|k={k}"]["recall_at_k"] for k in ks]
        style = dict(color=PIPELINE_COLOURS[pipeline], marker="o", linewidth=2,
                     markersize=6, label=PIPELINE_LABELS[pipeline])
        left.plot(ks, judge, **style)
        right.plot(ks, recall, **style)
    for ax, title, ylabel, ylim in ((left, "Mean judge score", "Judge score (1 to 5)", (1, 5)),
                                    (right, "Recall@k", "Recall", (0, 1))):
        ax.set_xticks(ks)
        ax.set_xlabel("k (documents retrieved)", fontsize=10)
        _finish(ax, title, ylabel, ylim)
    left.legend(frameon=False, fontsize=9, loc="center right")
    fig.suptitle("Figure 5.3  Effect of retrieval depth",
                 fontsize=13, fontweight="bold", color=INK, y=1.02)
    fig.savefig(path)
    plt.close(fig)
    return path


def figure_by_quadrant(report: dict, path: Path) -> Path:
    """Figure 5.4: per-quadrant judge score, where the ordering changes."""
    fig, ax = plt.subplots(figsize=(9.5, 4.6))
    width = 0.26
    order = ["P2_bm25", "P1_vector", "P3_structural"]
    for offset, pipeline in enumerate(order):
        values = [report["by_quadrant"][f"{q}|{pipeline}"]["judge_mean"] for q in agg.QUADRANTS]
        positions = [i + (offset - 1) * width for i in range(len(agg.QUADRANTS))]
        bars = ax.bar(positions, values, width=width, color=PIPELINE_COLOURS[pipeline],
                      label=PIPELINE_LABELS[pipeline])
        _bar_labels(ax, bars)
    ax.set_xticks(range(len(agg.QUADRANTS)))
    ax.set_xticklabels([QUADRANT_LABELS[q] for q in agg.QUADRANTS], fontsize=9)
    ax.legend(frameon=False, fontsize=9, ncol=3, loc="upper right")

    # Gold is the reserved accent and is spent once, on the single quadrant
    # where the leading pipeline changes.
    ax.annotate("only quadrant where\nP1 overtakes P2", xy=(3.0, 3.45), xytext=(2.45, 4.7),
                fontsize=8.5, color="#8C6D00", ha="center",
                arrowprops=dict(arrowstyle="->", color=GOLD, linewidth=1.4))
    _finish(ax, "Figure 5.4  Answer quality by question type", "Judge score (1 to 5)", (0, 5.6))
    fig.savefig(path)
    plt.close(fig)
    return path


def figure_score_distribution(conn: sqlite3.Connection, path: Path) -> Path:
    """Figure 5.5: the bimodal score distribution the means conceal."""
    rows = agg.load_rows(conn, "PQ")
    fig, ax = plt.subplots(figsize=(9, 4.2))
    order = ["P2_bm25", "P1_vector", "P3_structural"]
    labels = [PIPELINE_LABELS[p] for p in order]
    bottoms = [0.0] * len(order)
    for score in (1, 2, 3, 4, 5):
        counts = [sum(1 for r in rows if r["pipeline"] == p and r["judge_score"] == score)
                  for p in order]
        ax.barh(labels, counts, left=bottoms, height=0.55,
                color=SEQUENTIAL[score - 1], label=f"Score {score}")
        for index, count in enumerate(counts):
            if count >= 18:
                ax.text(bottoms[index] + count / 2, index, str(count), ha="center", va="center",
                        fontsize=8.5, color="white" if score >= 4 else BODY)
        bottoms = [b + c for b, c in zip(bottoms, counts)]
    ax.set_xlim(0, 300)
    ax.set_xlabel("Number of cells (300 per pipeline)", fontsize=10)
    ax.legend(frameon=False, fontsize=8.5, ncol=5, loc="lower center",
              bbox_to_anchor=(0.5, -0.32))
    ax.grid(axis="y", visible=False)
    _finish(ax, "Figure 5.5  Distribution of judge scores, showing bimodality")
    fig.savefig(path)
    plt.close(fig)
    return path


def figure_paired_comparisons(report: dict, path: Path) -> Path:
    """Figure 5.6: paired differences with bootstrap intervals."""
    comparisons = [c for c in report["comparisons"] if c["metric"] == "judge_score"]
    fig, ax = plt.subplots(figsize=(8.5, 3.6))
    labels = []
    for index, c in enumerate(reversed(comparisons)):
        colour = PIPELINE_COLOURS["P1_vector"] if c["significant"] else MUTED
        ax.plot([c["ci_low"], c["ci_high"]], [index, index], color=colour, linewidth=2.4,
                solid_capstyle="round")
        ax.plot(c["mean_difference"], index, "o", color=colour, markersize=8)
        labels.append(f"{PIPELINE_LABELS[c['left']]} vs {PIPELINE_LABELS[c['right']]}")
    ax.axvline(0, color=GOLD, linewidth=1.4, linestyle="--", zorder=1)
    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels(labels, fontsize=9)
    # Half a row of padding at each end, so the outer intervals and their
    # markers are not clipped against the axis.
    ax.set_ylim(-0.6, len(labels) - 0.4)
    ax.set_xlabel("Mean paired difference in judge score (95% bootstrap interval)", fontsize=9.5)
    ax.grid(axis="y", visible=False)
    # Below the axis rather than inside it: the intervals span the full plot
    # width, so any in-axes placement overlaps one of them.
    ax.legend(handles=[
        Patch(color=PIPELINE_COLOURS["P1_vector"], label="Interval excludes zero"),
        Patch(color=MUTED, label="Interval spans zero (no detectable difference)"),
    ], frameon=False, fontsize=8.5, loc="upper center", bbox_to_anchor=(0.5, -0.28), ncol=2)
    _finish(ax, "Figure 5.6  Paired pipeline comparisons")
    fig.savefig(path)
    plt.close(fig)
    return path


def build_all(db_path: str, out_dir: Path) -> list[Path]:
    """Renders every results figure. Returns the paths written, in order."""
    apply_house_style()
    out_dir.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    report = agg.build_report(conn, "PQ")
    return [
        figure_answer_quality(report, out_dir / "figure-5-1-answer-quality.png"),
        figure_retrieval_quality(report, out_dir / "figure-5-2-retrieval-quality.png"),
        figure_effect_of_k(report, out_dir / "figure-5-3-effect-of-k.png"),
        figure_by_quadrant(report, out_dir / "figure-5-4-by-quadrant.png"),
        figure_score_distribution(conn, out_dir / "figure-5-5-score-distribution.png"),
        figure_paired_comparisons(report, out_dir / "figure-5-6-paired-comparisons.png"),
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", default="benchmark.db")
    parser.add_argument("--out-dir", default="../resources/artifacts/figures")
    args = parser.parse_args(argv)
    for path in build_all(args.db, Path(args.out_dir)):
        print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
