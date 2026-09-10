"""Reference scores for the validation gate, written without the Judge's.

On this run the agent supplies the reference score in place of a human, so
the figure the gate computes is cross-model concordance rather than an
external human-agreement rate. Independence is the one property it still
carries, and this module enforces it structurally: the rows it hands out
for scoring have judge_score removed, so a scorer cannot anchor on it even
by accident.
"""
import asyncio
import logging

import database_manager as dbm

logger = logging.getLogger(__name__)

# Everything the scorer needs to judge the answer, and nothing that reveals
# what the Judge already decided.
_VISIBLE_FIELDS = (
    "result_id",
    "query_id",
    "pipeline",
    "k_value",
    "quadrant",
    "query_text",
    "ground_truth_answer",
    "gt_citations",
    "pipeline_output",
    "cited_node_ids",
)


async def render_rows_for_scoring(db_path: str) -> list[dict]:
    """The gate rows, reduced to the fields a scorer may see."""
    rows = await dbm.get_jeq_judging_rows(db_path)
    return [{k: row[k] for k in _VISIBLE_FIELDS if k in row} for row in rows]


async def apply_scores(db_path: str, scores: dict[str, int]) -> int:
    """Write one reference score per result_id; returns the count written.

    update_result_human_score raises on an unknown result_id, so a typo in
    the mapping fails loudly rather than silently leaving a row unscored and
    shrinking the gate's denominator.
    """
    for result_id, score in scores.items():
        await dbm.update_result_human_score(db_path, result_id, score)
    return len(scores)


if __name__ == "__main__":
    import json

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    print(json.dumps(asyncio.run(render_rows_for_scoring("benchmark.db")), indent=2))
