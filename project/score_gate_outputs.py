"""Human scoring and the Judge validation gate (Architecture.md §4.5b).

The final Phase 6 step. It collects the researcher's human_score for each of
the 60 JEQ gate rows, then measures how closely the automated Judge agrees
with that human standard and enforces the hard gate before Phase 7.

Agreement rule (deviations.md #26): both scores are rescaled from 1-10 to
0-100 (x10); a row *agrees* when they differ by no more than +/-10 points on
that scale (equivalently within +/-1 on 1-10 -- a single point of ordinal
subjectivity is not treated as disagreement). The Agreement Rate is the
percentage of scored rows that agree, and the gate is a strict
Agreement Rate > 80%.

Anti-bias: the human is never shown the Judge's score while scoring, so the
two judgements stay independent -- the whole point of the gate.
"""
import argparse
import asyncio
import logging

import database_manager as dbm

logger = logging.getLogger(__name__)

# Per-row agreement band and gate threshold, both on the 0-100 scale.
AGREEMENT_TOLERANCE = 10
GATE_THRESHOLD = 80.0


def rows_agree(human_score: int, judge_score: int, *, tolerance: int = AGREEMENT_TOLERANCE) -> bool:
    """True when the two 1-10 scores agree within the tolerance band on 0-100."""
    return abs(human_score * 10 - judge_score * 10) <= tolerance


def compute_agreement_rate(rows: list[dict], *, tolerance: int = AGREEMENT_TOLERANCE) -> dict:
    """Agreement Rate and gate verdict over rows carrying both scores.

    Every row must already have both a human_score and a judge_score; a
    missing one is an error rather than a silent skip, because the gate's
    denominator is the full set of 60 rows and a dropped row would inflate the
    rate. The gate is strict: exactly 80% does not pass.
    """
    pairs = []
    for row in rows:
        human, judge = row.get("human_score"), row.get("judge_score")
        if human is None or judge is None:
            raise ValueError(
                f"row {row.get('result_id')!r} is missing a human or judge score "
                "-- score all 60 rows before computing agreement"
            )
        pairs.append((human, judge))
    if not pairs:
        raise ValueError("no scored rows to compute an agreement rate over")

    agreements = sum(1 for human, judge in pairs if rows_agree(human, judge, tolerance=tolerance))
    rate = agreements / len(pairs) * 100
    return {
        "n": len(pairs),
        "agreements": agreements,
        "agreement_rate": rate,
        "gate_passed": rate > GATE_THRESHOLD,
    }


def _render_row_for_human(row: dict) -> str:
    """What the researcher sees before scoring one row -- no judge_score."""
    return (
        "\n--- Score this answer 1-10 ---\n"
        f"Question: {row['query_text']}\n"
        f"Ground-truth answer: {row['ground_truth_answer']}\n"
        f"Valid source node ids: {row['gt_citations']}\n"
        f"Pipeline ({row['pipeline']}) answer: {row['pipeline_output']}\n"
        f"Cited node ids: {row['cited_node_ids']}"
    )


def _read_score(input_fn, output_fn) -> int:
    """Read a 1-10 integer, re-prompting until the input is valid."""
    while True:
        raw = input_fn("human_score (1-10): ")
        try:
            score = int(str(raw).strip())
        except (TypeError, ValueError):
            output_fn(f"not an integer: {raw!r} -- enter a whole number 1-10")
            continue
        if 1 <= score <= 10:
            return score
        output_fn(f"out of range: {score} -- enter a whole number 1-10")


async def prompt_human_scores(db_path: str, *, input_fn=input, output_fn=print) -> int:
    """Collect a human_score for each JEQ row that lacks one; return the count.

    Rows already carrying a human_score are skipped, so an interrupted scoring
    session resumes where it left off. The Judge's score is deliberately never
    rendered (see module docstring).
    """
    rows = await dbm.get_jeq_judging_rows(db_path)
    pending = [row for row in rows if row.get("human_score") is None]

    scored = 0
    for row in pending:
        output_fn(_render_row_for_human(row))
        score = _read_score(input_fn, output_fn)
        await dbm.update_result_human_score(db_path, row["result_id"], score)
        scored += 1
    return scored


def _render_verdict(summary: dict) -> str:
    head = (
        f"Agreement Rate: {summary['agreement_rate']:.1f}% "
        f"({summary['agreements']}/{summary['n']} rows within +/-1) "
        f"-- gate is > {GATE_THRESHOLD:.0f}%"
    )
    if summary["gate_passed"]:
        return head + "\nGATE PASSED. Phase 7 (full 900-run benchmark) may begin."
    return (
        head + "\nGATE FAILED. Do not run the full matrix. Revise the Judge rubric "
        "and/or swap the Judge model (e.g. gpt-oss-120b, still != the Llama answerer), "
        "then re-run the gate. Do not silently retry."
    )


async def run_scoring_gate(db_path: str, *, input_fn=input, output_fn=print) -> dict:
    """Prompt for any missing human scores, then compute and report the gate."""
    await prompt_human_scores(db_path, input_fn=input_fn, output_fn=output_fn)
    rows = await dbm.get_results(db_path, "JEQ")
    summary = compute_agreement_rate(rows)
    output_fn(_render_verdict(summary))
    return summary


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db-path", default="benchmark.db")
    return parser.parse_args(argv)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    args = _parse_args()
    result = asyncio.run(run_scoring_gate(db_path=args.db_path))
    print(result)


__all__ = [
    "rows_agree",
    "compute_agreement_rate",
    "prompt_human_scores",
    "run_scoring_gate",
    "AGREEMENT_TOLERANCE",
    "GATE_THRESHOLD",
]
