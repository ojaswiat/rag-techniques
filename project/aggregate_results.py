"""Aggregates the benchmark `results` table into the tri-pillar comparison.

Everything here is derived from `results` joined to its answer key, with no
manual step in between, so the tables can be regenerated from the database
alone. Three pillars per Phase 8: retrieval quality, answer quality, and
efficiency.

Two reporting choices are deliberate. First, answer quality carries a pass
rate beside its mean, because the Judge's 1-5 distribution is strongly
bimodal: most answers are either fully correct or wholly wrong, and a mean of
3.0 over that shape describes no actual answer. Second, comparisons between
pipelines are paired on (query_id, k_value) rather than compared as two
independent samples, since every pipeline answers exactly the same cells; the
pairing removes per-question difficulty, which is the dominant source of
variance in the set.

Efficiency has a third leg beside latency and tokens: what it cost to
build each index in the first place. That figure is per corpus rather than
per cell, so it is carried alongside the per-cell tables rather than inside
them, and it is read from the committed snapshot described in
index_build_cost.

Significance is reported as a bootstrap interval and an exact sign test
rather than a t-test: the per-cell scores are ordinal, bounded and bimodal,
so a test assuming approximate normality of the underlying values would be
reporting a property the data does not have. Both are computed here rather
than imported, since scipy is not a dependency of this project.
"""
import argparse
import json
import math
import random
import sqlite3
from collections import defaultdict

import index_build_cost

# A judged answer counts as a pass at 4 or better: correct on the value, with
# at most a shortfall in completeness or framing. See judge/async_judge.py.
PASS_THRESHOLD = 4

BOOTSTRAP_RESAMPLES = 10_000
BOOTSTRAP_SEED = 20260911
CONFIDENCE = 0.95

PIPELINES = ("P1_vector", "P2_bm25", "P3_structural")
QUADRANTS = ("Q1_Direct_Text", "Q2_Implicit_Text", "Q3_Direct_Table", "Q4_Implicit_Table")


def load_rows(conn: sqlite3.Connection, source_set: str = "PQ") -> list[dict]:
    """Every scored cell for one source set, carrying its quadrant."""
    table = {"PQ": "queries", "JEQ": "judge_validation"}[source_set]
    conn.row_factory = sqlite3.Row
    cursor = conn.execute(
        f"""SELECT r.*, gt.quadrant, gt.document_id
            FROM results r JOIN {table} gt ON gt.query_id = r.query_id
            WHERE r.source_set = ?
            ORDER BY r.result_id""",
        (source_set,),
    )
    return [dict(row) for row in cursor]


def _mean(values: list) -> float | None:
    """Mean over the non-null values, or None when there are none.

    exact_match is NULL by design on the implicit quadrants, so a column can
    be legitimately empty for a group rather than missing by accident.
    """
    present = [v for v in values if v is not None]
    return sum(present) / len(present) if present else None


def summarise(rows: list[dict]) -> dict:
    """The tri-pillar metric block for one group of cells."""
    if not rows:
        return {"n": 0}
    judged = [r["judge_score"] for r in rows if r["judge_score"] is not None]
    return {
        "n": len(rows),
        # Pillar 1: retrieval
        "precision_at_k": _mean([r["precision_at_k"] for r in rows]),
        "recall_at_k": _mean([r["recall_at_k"] for r in rows]),
        "hit_rate": _mean([r["evidence_hit"] for r in rows]),
        "citation_match": _mean([r["citation_match"] for r in rows]),
        # Pillar 2: answer quality
        "judge_mean": _mean(judged),
        "judge_pass_rate": (sum(1 for s in judged if s >= PASS_THRESHOLD) / len(judged)
                            if judged else None),
        "judge_fail_rate": (sum(1 for s in judged if s == 1) / len(judged)
                            if judged else None),
        "token_f1": _mean([r["token_f1"] for r in rows]),
        "exact_match": _mean([r["exact_match"] for r in rows]),
        # Pillar 3: efficiency
        "latency_sec": _mean([r["latency_sec"] for r in rows]),
        "input_tokens": _mean([r["input_tokens"] for r in rows]),
        "output_tokens": _mean([r["output_tokens"] for r in rows]),
    }


def group_by(rows: list[dict], *keys: str) -> dict[tuple, dict]:
    """Summarises `rows` grouped by the given column names."""
    buckets: dict[tuple, list[dict]] = defaultdict(list)
    for row in rows:
        buckets[tuple(row[k] for k in keys)].append(row)
    return {key: summarise(group) for key, group in sorted(buckets.items(), key=lambda kv: str(kv[0]))}


def _paired_values(rows: list[dict], left: str, right: str, metric: str) -> list[tuple[float, float]]:
    """Metric values for two pipelines on the cells they both answered.

    Pairing is on (query_id, k_value): the same question at the same depth is
    the only fair unit of comparison, since question difficulty dominates the
    spread and is shared by both sides of the pair.
    """
    indexed: dict[str, dict[tuple, float]] = {left: {}, right: {}}
    for row in rows:
        if row["pipeline"] in indexed and row[metric] is not None:
            indexed[row["pipeline"]][(row["query_id"], row["k_value"])] = row[metric]
    shared = sorted(set(indexed[left]) & set(indexed[right]))
    return [(indexed[left][key], indexed[right][key]) for key in shared]


def _sign_test(pairs: list[tuple[float, float]]) -> float:
    """Two-sided exact sign test p-value over the non-tied pairs.

    Ties carry no directional information and are dropped, which is the
    standard treatment; the reported n_effective says how many remained.
    """
    wins = sum(1 for a, b in pairs if a > b)
    losses = sum(1 for a, b in pairs if a < b)
    n = wins + losses
    if n == 0:
        return 1.0
    extreme = min(wins, losses)
    tail = sum(math.comb(n, i) for i in range(extreme + 1)) / (2 ** n)
    return min(1.0, 2 * tail)


def _bootstrap_ci(pairs: list[tuple[float, float]]) -> tuple[float, float]:
    """Percentile confidence interval for the mean paired difference."""
    diffs = [a - b for a, b in pairs]
    if not diffs:
        return (float("nan"), float("nan"))
    rng = random.Random(BOOTSTRAP_SEED)
    n = len(diffs)
    means = []
    for _ in range(BOOTSTRAP_RESAMPLES):
        means.append(sum(diffs[rng.randrange(n)] for _ in range(n)) / n)
    means.sort()
    lo = int((1 - CONFIDENCE) / 2 * BOOTSTRAP_RESAMPLES)
    hi = int((1 + CONFIDENCE) / 2 * BOOTSTRAP_RESAMPLES) - 1
    return (means[lo], means[hi])


def compare(rows: list[dict], left: str, right: str, metric: str = "judge_score") -> dict:
    """Paired comparison of two pipelines on one metric."""
    pairs = _paired_values(rows, left, right, metric)
    diffs = [a - b for a, b in pairs]
    wins = sum(1 for a, b in pairs if a > b)
    losses = sum(1 for a, b in pairs if a < b)
    lo, hi = _bootstrap_ci(pairs)
    return {
        "left": left, "right": right, "metric": metric,
        "n_pairs": len(pairs),
        "n_effective": wins + losses,
        "mean_difference": (sum(diffs) / len(diffs)) if diffs else None,
        "ci_low": lo, "ci_high": hi,
        "wins": wins, "losses": losses, "ties": len(pairs) - wins - losses,
        "sign_test_p": _sign_test(pairs),
        # A difference whose interval spans zero is not evidence of a
        # difference, however large the point estimate looks.
        "significant": not (lo <= 0.0 <= hi),
    }


def build_report(conn: sqlite3.Connection, source_set: str = "PQ",
                 build_cost_path=index_build_cost.SNAPSHOT_PATH) -> dict:
    """The complete aggregation: overall, per k, per quadrant, and comparisons."""
    rows = load_rows(conn, source_set)
    comparisons = []
    for metric in ("judge_score", "recall_at_k"):
        for i, left in enumerate(PIPELINES):
            for right in PIPELINES[i + 1:]:
                comparisons.append(compare(rows, left, right, metric))
    return {
        "source_set": source_set,
        "cells": len(rows),
        "overall": {k[0]: v for k, v in group_by(rows, "pipeline").items()},
        "by_k": {f"{k[0]}|k={k[1]}": v for k, v in group_by(rows, "pipeline", "k_value").items()},
        "by_quadrant": {f"{k[0]}|{k[1]}": v for k, v in group_by(rows, "quadrant", "pipeline").items()},
        "by_document": {f"{k[0]}|{k[1]}": v for k, v in group_by(rows, "document_id", "pipeline").items()},
        "comparisons": comparisons,
        # Per corpus, not per cell, so it sits beside the tables rather than
        # in them. None when the snapshot has not been taken.
        "index_build": index_build_cost.load_snapshot(build_cost_path),
    }


def _fmt(value, width=7, places=3) -> str:
    if value is None:
        return "-".rjust(width)
    return f"{value:>{width}.{places}f}"


def print_report(report: dict) -> None:
    print(f"\n{'=' * 78}\nBENCHMARK AGGREGATION: {report['source_set']}, {report['cells']} cells\n{'=' * 78}")

    print(f"\nOVERALL\n{'pipeline':<16}{'n':>5}{'judge':>7}{'pass':>7}{'recall':>8}{'prec':>7}"
          f"{'hit':>7}{'cite':>7}{'tokF1':>7}{'lat':>7}")
    for pipeline, s in sorted(report["overall"].items(), key=lambda kv: -(kv[1]["judge_mean"] or 0)):
        print(f"{pipeline:<16}{s['n']:>5}{_fmt(s['judge_mean'],7,2)}{_fmt(s['judge_pass_rate'])}"
              f"{_fmt(s['recall_at_k'],8)}{_fmt(s['precision_at_k'])}{_fmt(s['hit_rate'])}"
              f"{_fmt(s['citation_match'])}{_fmt(s['token_f1'])}{_fmt(s['latency_sec'],7,2)}")

    print(f"\nBY K\n{'pipeline / k':<20}{'judge':>7}{'pass':>7}{'recall':>8}{'hit':>7}")
    for key, s in report["by_k"].items():
        print(f"{key:<20}{_fmt(s['judge_mean'],7,2)}{_fmt(s['judge_pass_rate'])}"
              f"{_fmt(s['recall_at_k'],8)}{_fmt(s['hit_rate'])}")

    print(f"\nBY QUADRANT\n{'quadrant / pipeline':<36}{'judge':>7}{'pass':>7}{'recall':>8}{'hit':>7}")
    for key, s in report["by_quadrant"].items():
        print(f"{key:<36}{_fmt(s['judge_mean'],7,2)}{_fmt(s['judge_pass_rate'])}"
              f"{_fmt(s['recall_at_k'],8)}{_fmt(s['hit_rate'])}")

    print(f"\nPAIRED COMPARISONS (paired on query_id and k_value)\n"
          f"{'metric':<14}{'comparison':<32}{'diff':>8}{'95% CI':>18}{'W/L/T':>14}{'p':>9}  sig")
    for c in report["comparisons"]:
        ci = f"[{c['ci_low']:+.3f}, {c['ci_high']:+.3f}]"
        wlt = f"{c['wins']}/{c['losses']}/{c['ties']}"
        print(f"{c['metric']:<14}{c['left'] + ' vs ' + c['right']:<32}{c['mean_difference']:>+8.3f}"
              f"{ci:>18}{wlt:>14}{c['sign_test_p']:>9.2e}  {'yes' if c['significant'] else 'no'}")

    print_index_build(report.get("index_build"))

    print("\nNote: one temperature-0 run per cell, so these intervals describe "
          "variation across questions, not run-to-run variance.\n")


def _hours(seconds: float) -> str:
    return f"{seconds / 3600:.2f}h" if seconds >= 3600 else f"{seconds:.1f}s"


def print_index_build(snapshot: dict | None) -> None:
    """The one-off cost of building each index, the third efficiency leg."""
    if not snapshot:
        print("\nINDEX BUILD COST\n  no snapshot; run index_build_cost.py to take one")
        return

    print(f"\nINDEX BUILD COST (one off, {snapshot['corpus_nodes']:,} nodes)\n"
          f"{'pipeline':<16}{'LLM':>5}{'filings':>9}{'total':>10}{'median':>10}"
          f"{'s/1k nodes':>12}{'in tok':>12}{'out tok':>12}{'later':>9}")
    for pipeline in PIPELINES:
        b = snapshot["pipelines"].get(pipeline)
        if not b:
            continue
        median = f"{b['median_filing_sec'] / 60:.1f}m" if b["median_filing_sec"] else "-"
        print(f"{pipeline:<16}{'yes' if b['uses_llm'] else 'no':>5}{b['filings']:>9}"
              f"{_hours(b['wall_clock_sec']):>10}{median:>10}"
              f"{b['sec_per_1k_nodes']:>12.1f}{b['input_tokens']:>12,}"
              f"{b['output_tokens']:>12,}{_hours(b['later_attempt_sec']):>9}")
    print("  One build from scratch per filing. Wall clock as measured, including "
          "time spent\n  waiting on the LLM provider. 'later' is time spent on "
          "rebuilds and resumed runs\n  on top of that first build.")
    for pipeline in PIPELINES:
        b = snapshot["pipelines"].get(pipeline) or {}
        missing = b.get("filings_missing_tokens") or []
        if missing:
            print(f"  {pipeline}: token counts are a floor over "
                  f"{b['filings_with_tokens']} of {b['filings']} filings; "
                  f"{', '.join(missing)} built before the token log recorded them.")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", default="benchmark.db")
    parser.add_argument("--source-set", default="PQ", choices=["PQ", "JEQ"])
    parser.add_argument("--json-out", help="write the full aggregation to this path")
    args = parser.parse_args(argv)

    conn = sqlite3.connect(args.db)
    report = build_report(conn, args.source_set)
    print_report(report)
    if args.json_out:
        with open(args.json_out, "w") as handle:
            json.dump(report, handle, indent=2)
        print(f"wrote {args.json_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
