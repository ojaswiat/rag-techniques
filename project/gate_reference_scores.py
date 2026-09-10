"""Reference scores for the validation gate, written without the Judge's.

On this run the agent supplies the reference score in place of a human, so
the figure the gate computes is cross-model concordance rather than an
external human-agreement rate. Independence is the one property it still
carries, and this module enforces two things structurally rather than by
the scorer's discipline:

* Evidence parity -- the rendered fields (quadrant, query_text,
  ground_truth_answer, pipeline_output) are exactly what
  async_judge._build_target_message() sends the Judge, plus quadrant, which
  the Judge effectively also sees through its quadrant-matched calibration
  exemplars. gt_citations and cited_node_ids are withheld because
  Guardrails Sec 4b forbids the Judge from grading citations; showing them
  to the scorer but not the Judge would make any disagreement partly
  measure that evidence gap rather than the Judge's quality.
* Pipeline blindness -- result_id encodes the pipeline
  (f"R_{source_set}_{query_id}_{pipeline}_K{k_value}"), and the pipeline
  column names it directly, so both are dropped from the rendering and
  replaced with an opaque, order-derived token ("row_0000", ...). A scorer
  who can tell an answer came from P3 -- the pipeline this dissertation
  predicts will perform worst -- could shade the score toward the expected
  result, contaminating both the gate and the headline pipeline comparison
  the project exists to produce. apply_scores() re-derives the same token
  order to translate a token-keyed score mapping back to result_id, so the
  real identifier never has to leave this module.
"""
import asyncio
import logging

import database_manager as dbm

logger = logging.getLogger(__name__)

# Exactly what async_judge._build_target_message() renders for the Judge
# (query_text, ground_truth_answer, pipeline_output), plus quadrant, which
# the Judge receives indirectly via its quadrant-matched calibration
# exemplars. Deliberately excludes judge_score, pipeline, result_id,
# gt_citations and cited_node_ids -- see the module docstring.
_VISIBLE_FIELDS = (
    "quadrant",
    "query_text",
    "ground_truth_answer",
    "pipeline_output",
)


def _token_for(index: int) -> str:
    """An opaque, order-derived stand-in for result_id.

    Deliberately not a function of result_id, query_id, pipeline or
    k_value: a hash of those would still be a function of the pipeline
    name, and a scorer only needs two tokens to repeat in a pattern to
    start reconstructing groupings. A running index carries no information
    about the row it names.
    """
    return f"row_{index:04d}"


async def render_rows_for_scoring(db_path: str) -> list[dict]:
    """The gate rows, reduced to the fields a scorer may see.

    Each row carries an opaque "token" in place of result_id; apply_scores()
    resolves it back to the real row.
    """
    rows = await dbm.get_jeq_judging_rows(db_path)
    return [
        {"token": _token_for(i), **{k: row[k] for k in _VISIBLE_FIELDS if k in row}}
        for i, row in enumerate(rows)
    ]


async def _token_map(db_path: str) -> dict[str, str]:
    """Rebuilds the token -> result_id mapping render_rows_for_scoring used.

    get_jeq_judging_rows orders by result_id, so re-running it (with no rows
    added or removed in between the two calls) reproduces the same token
    assignment without ever having stored or exposed result_id in the
    rendered rows.
    """
    rows = await dbm.get_jeq_judging_rows(db_path)
    return {_token_for(i): row["result_id"] for i, row in enumerate(rows)}


async def apply_scores(db_path: str, scores: dict[str, int]) -> int:
    """Write one reference score per token; returns the count written.

    scores is keyed by the opaque token render_rows_for_scoring handed out,
    not by result_id -- the caller never has the latter. An unknown token
    fails loudly rather than silently leaving a row unscored and shrinking
    the gate's denominator.
    """
    token_map = await _token_map(db_path)
    for token, score in scores.items():
        try:
            result_id = token_map[token]
        except KeyError as exc:
            raise ValueError(f"no results row for token {token!r}") from exc
        await dbm.update_result_human_score(db_path, result_id, score)
    return len(scores)


if __name__ == "__main__":
    import json

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    print(json.dumps(asyncio.run(render_rows_for_scoring("benchmark.db")), indent=2))
