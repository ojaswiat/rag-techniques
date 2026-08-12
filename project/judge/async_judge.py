"""LLM Judge for the validation gate (Guardrails.md §4, Architecture.md §4.5b).

For each of the 60 JEQ gate outputs this scores the pipeline answer 1-10 with
Qwen3.6-27B and, in the same pass, computes the deterministic metrics in code
(deviations.md #26) so a scored row is written complete in one UPDATE.

Three invariants from Guardrails hold here and are worth stating plainly:
  * §4a -- the prompt carries exactly the 5 golden_queries exemplars that
    share the target row's quadrant, never all 20. This yields four fixed
    prompt prefixes (one per quadrant), each built once and reused across
    every row of that quadrant so provider-side prompt caching applies.
  * §2  -- the Judge has no search tool. It already receives the ground-truth
    answer and citations; it only has to score the output against them, so it
    calls achat(), not achat_with_tools().
  * §3/§4b -- JEQ rows are never used as exemplars (only golden_queries are),
    and the citation check is deterministic code, never delegated to the model.
"""
import asyncio
import json
import logging
import re

from llama_index.core.base.llms.types import ChatMessage, MessageRole

import database_manager as dbm
import llm_client.config as config
from judge.metrics import citation_audit, exact_match, precision_at_k, recall_at_k, token_f1
from llm_client.llm_factory import LLMFactory
from loop_template import LOCAL_TEST_THROTTLE, apply_throttle

logger = logging.getLogger(__name__)

_STAGE = "judge"

_RUBRIC = (
    "You are grading how well a candidate answer responds to a question about a "
    "SEC 10-K filing. You are given the question, the ground-truth answer, and "
    "the set of valid source node ids. Score the candidate answer from 1 to 10, "
    "where 10 means it fully matches the ground-truth answer and cites only valid "
    "sources, and 1 means it is wrong, unsupported, or fabricated. Judge only "
    "correctness against the ground truth provided; do not use outside knowledge "
    "and do not search. Respond with ONLY a JSON object, no markdown fences: "
    '{"score": <integer 1-10>, "justification": "<one sentence>"}.'
)


def _rescale_to_1_10(human_score_0_100: int) -> int:
    """golden_queries.human_score is 0-100; the Judge outputs 1-10, so the
    teaching examples are shown on the Judge's own scale (clamped to 1-10)."""
    return max(1, min(10, round(human_score_0_100 / 10)))


def _format_exemplar(ex: dict) -> str:
    return (
        f"Question: {ex['query_text']}\n"
        f"Ground-truth answer: {ex['ground_truth_answer']}\n"
        f"Valid source node ids: {ex['gt_citations']}\n"
        f"Candidate answer: {ex['example_output']}\n"
        f"Correct score (1-10): {_rescale_to_1_10(ex['human_score'])}\n"
        f"Reason: {ex['human_reasoning']}"
    )


def build_prefix(quadrant: str, exemplars: list[dict]) -> str:
    """The cacheable system message for one quadrant: rubric + its exemplars.

    Same string for every JEQ row of `quadrant`, so a provider that caches
    prompt prefixes charges the exemplar tokens once per quadrant, not once
    per row (Guardrails §4a).
    """
    blocks = "\n\n".join(_format_exemplar(ex) for ex in exemplars)
    return (
        f"{_RUBRIC}\n\n"
        f"Here are graded examples for {quadrant} questions. Score the new "
        f"answer on the same standard.\n\n"
        f"{blocks}"
    )


def _build_target_message(row: dict) -> str:
    return (
        f"Question: {row['query_text']}\n"
        f"Ground-truth answer: {row['ground_truth_answer']}\n"
        f"Valid source node ids: {row['gt_citations']}\n"
        f"Candidate answer: {row['pipeline_output']}\n"
        "Score the candidate answer now."
    )


def parse_judge_score(raw_text: str) -> int:
    """Pull a 1-10 integer out of the Judge's reply, clamped into range.

    Prefers the JSON object the rubric asks for; falls back to the first bare
    1-10 integer so a model that adds prose around the number is still usable.
    """
    try:
        obj = json.loads(raw_text)
    except (json.JSONDecodeError, TypeError):
        obj = None
    if isinstance(obj, dict):
        for key in ("score", "judge_score"):
            if key in obj:
                return max(1, min(10, round(float(obj[key]))))

    match = re.search(r"\b(10|[1-9])\b", raw_text)
    if match:
        return int(match.group(1))
    raise ValueError(f"could not parse a 1-10 judge score from: {raw_text!r}")


def compute_deterministic_metrics(row: dict) -> dict:
    """The code-computed metric columns for one gate row (no LLM).

    evidence_hit is derived from recall (deviations.md #26): retrieval
    surfaced at least one ground-truth citation. exact_match stays None for
    the implicit quadrants Q2/Q4, stored as NULL.
    """
    retrieved = row["retrieved_node_ids"]
    cited = row["cited_node_ids"]
    gt = row["gt_citations"]
    recall = recall_at_k(retrieved, gt)
    em = exact_match(row["pipeline_output"], row["ground_truth_answer"], quadrant=row["quadrant"])
    return {
        "precision_at_k": precision_at_k(retrieved, gt, row["k_value"]),
        "recall_at_k": recall,
        "evidence_hit": 1 if recall > 0 else 0,
        "citation_match": 1 if citation_audit(cited, gt) else 0,
        "token_f1": token_f1(row["pipeline_output"], row["ground_truth_answer"]),
        "exact_match": None if em is None else int(em),
    }


class Judge:
    """Wraps the Qwen judge client; enforces the fixed model and temperature.

    Like the Answerer, the routed model and temperature=0 are constraints, so
    a caller asking for anything else is rejected rather than silently
    overridden -- a gate scored under the wrong model would be meaningless.
    """

    def __init__(self, model: str | None = None, temperature: float = 0.0):
        routed_model = config.MODEL_ROUTING[_STAGE]["model"]
        model = model or routed_model
        if model != routed_model:
            raise ValueError(
                f"Judge model is fixed to {routed_model!r} by "
                f"config.MODEL_ROUTING[{_STAGE!r}]; got {model!r}"
            )
        if temperature != 0.0:
            raise ValueError(f"All benchmark LLM calls run at temperature=0; got {temperature!r}")
        self.model = model
        self.temperature = temperature
        self._client = None

    def _get_client(self):
        if self._client is None:
            self._client = LLMFactory.get_client_for_stage(_STAGE)
        return self._client

    async def score_row(self, row: dict, system_prompt: str) -> int:
        client = self._get_client()
        messages = [
            ChatMessage(role=MessageRole.SYSTEM, content=system_prompt),
            ChatMessage(role=MessageRole.USER, content=_build_target_message(row)),
        ]
        response = await client.achat(messages)
        return parse_judge_score(response.message.content or "")


async def judge_jeq_rows(db_path: str, judge: Judge | None = None) -> dict:
    """Score every JEQ gate row: deterministic metrics + judge_score, one write each.

    Reads the 60 rows joined to their ground truth, builds each quadrant's
    prompt prefix once, then scores the rows and writes the full metric vector
    back per row. Honours LOCAL_TEST_THROTTLE (Guardrails §7): under throttle
    only the first THROTTLE_LIMIT rows run.
    """
    if judge is None:
        judge = Judge()

    rows = await dbm.get_jeq_judging_rows(db_path)
    rows = apply_throttle(rows)

    # Build the four (or fewer) cacheable prefixes up front, one DB read per
    # quadrant present, so scoring can proceed concurrently without racing on
    # the exemplar reads.
    prefixes: dict[str, str] = {}
    for quadrant in {row["quadrant"] for row in rows}:
        exemplars = await dbm.get_golden_queries_by_quadrant(db_path, quadrant)
        prefixes[quadrant] = build_prefix(quadrant, exemplars)

    logger.info(
        "judging %d JEQ row(s)%s",
        len(rows),
        " (LOCAL_TEST_THROTTLE)" if LOCAL_TEST_THROTTLE else "",
    )

    judged = 0
    failures: list[dict] = []

    async def _score_and_write(row: dict) -> None:
        nonlocal judged
        metrics = compute_deterministic_metrics(row)
        metrics["judge_score"] = await judge.score_row(row, prefixes[row["quadrant"]])
        await dbm.update_result_scores(db_path, row["result_id"], metrics)
        judged += 1

    results = await asyncio.gather(
        *(_score_and_write(row) for row in rows), return_exceptions=True
    )
    for row, outcome in zip(rows, results):
        if isinstance(outcome, Exception):
            logger.exception("judging failed for result_id=%s", row["result_id"], exc_info=outcome)
            failures.append({"result_id": row["result_id"], "error": str(outcome)})

    return {"judged": judged, "attempted": len(rows), "failures": failures}


__all__ = [
    "Judge",
    "build_prefix",
    "compute_deterministic_metrics",
    "judge_jeq_rows",
    "parse_judge_score",
]
