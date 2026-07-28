"""Orchestrator: fills queries/golden_queries/judge_validation to 140 total.

Resumable -- re-checks quadrant counts on every startup and skips already-full
quadrant/table slots, so a crash never re-spends Groq quota on accepted
queries (same resumability principle as Phase 3's build). LOCAL_TEST_THROTTLE
caps a run to THROTTLE_LIMIT sections total (Guardrails.md §7).

The numeric suffix of each `query_id` is derived from the freshly-loaded
per-(table, quadrant) row count (`counts[table][quadrant] + 1`), not an
in-process counter -- so it stays correct across restarts: a crash after N
accepted rows in a (table, quadrant) slot means the next process's first
accepted row for that same slot gets suffix N+1, never colliding with
already-committed rows.
"""
import json
from pathlib import Path

from groq import APIStatusError

import config
import database_manager as dbm
from dataset_generation.async_critic import critique_query
from dataset_generation.async_generator import generate_query
from dataset_generation.cross_check import check_query
from dataset_generation.section_grouper import group_sections

_QUADRANTS = ("Q1_Direct_Text", "Q2_Implicit_Text", "Q3_Direct_Table", "Q4_Implicit_Table")
_TABLE_ORDER = ("queries", "golden_queries", "judge_validation")
_TARGETS = {"queries": 25, "golden_queries": 5, "judge_validation": 5}
_MAX_ATTEMPTS_PER_SECTION = 3

# Exceptions that can propagate out of a single generate/critique attempt
# without indicating a bug worth crashing the whole 140-query batch for:
# Critic tool-round exhaustion, malformed/incomplete JSON from either LLM,
# any non-429 Groq API error (429s are already retried inside
# groq_client.call_groq via tenacity), and null-valued fields in an
# otherwise-valid LLM response (e.g. Generator's gt_citications: null ->
# TypeError in cross_check.citations_overlap's set(None); Critic's
# computed_answer: null -> AttributeError in cross_check.values_match's
# None.strip()) -- these are malformed responses, not accept/reject
# decisions, so they're treated the same as a rejected attempt.
_ATTEMPT_EXCEPTIONS = (RuntimeError, json.JSONDecodeError, KeyError, APIStatusError, TypeError, AttributeError)

FAILURE_LOG_PATH = Path("logs/dataset_generation_failures.json")

_ALL_FILINGS = (
    "AAPL_2023", "AAPL_2024", "AAPL_2025",
    "MSFT_2023", "MSFT_2024", "MSFT_2025",
    "TSLA_2023", "TSLA_2024", "TSLA_2025",
)

_INSERTER_NAMES = {
    "queries": "insert_query",
    "golden_queries": "insert_golden_query",
    "judge_validation": "insert_judge_validation",
}


def next_target(counts: dict[str, dict[str, int]]) -> tuple[str, str] | None:
    for quadrant in _QUADRANTS:
        for table in _TABLE_ORDER:
            if counts[table][quadrant] < _TARGETS[table]:
                return table, quadrant
    return None


async def _load_counts(db_path: str) -> dict[str, dict[str, int]]:
    return {table: await dbm.get_quadrant_counts(db_path, table) for table in _TABLE_ORDER}


def append_failure_log(failure_row: dict, log_path: Path | None = None) -> None:
    """Durable JSON-array append, mirroring
    pipelines/structural/build_summary_index.py's append_cost_log pattern.

    ``log_path`` is resolved against the module-level ``FAILURE_LOG_PATH`` at
    call time (rather than bound as a mutable default argument) so tests can
    monkeypatch ``FAILURE_LOG_PATH`` and have it take effect."""
    if log_path is None:
        log_path = FAILURE_LOG_PATH
    log_path.parent.mkdir(parents=True, exist_ok=True)
    rows = json.loads(log_path.read_text()) if log_path.exists() else []
    rows.append(failure_row)
    log_path.write_text(json.dumps(rows, indent=2))


async def _accept_query(db_path: str, table: str, generated: dict, next_seq: int) -> None:
    query_id = f"{generated['quadrant']}_{table}_{next_seq:04d}"
    row = {
        "query_id": query_id,
        "quadrant": generated["quadrant"],
        "query_text": generated["query_text"],
        "ground_truth_answer": generated["ground_truth_answer"],
        "gt_citations": generated["gt_citations"],
        "document_id": generated["document_id"],
    }
    if table == "golden_queries":
        row.update({
            "example_output": generated["ground_truth_answer"],
            "human_score": 1,
            "human_reasoning": "PENDING_HUMAN_LABEL",
        })
    inserter = getattr(dbm, _INSERTER_NAMES[table])
    await inserter(db_path, row)


async def main(db_path: str = "benchmark.db", document_ids: tuple[str, ...] | None = None) -> None:
    await dbm.init_db(db_path)
    document_ids = document_ids or _ALL_FILINGS
    max_sections = config.THROTTLE_LIMIT if config.LOCAL_TEST_THROTTLE else None

    sections_processed = 0

    for document_id in document_ids:
        nodes = await dbm.get_nodes_by_document(db_path, document_id)
        sections = group_sections(nodes)

        for section in sections:
            if max_sections is not None and sections_processed >= max_sections:
                return

            counts = await _load_counts(db_path)
            target = next_target(counts)
            if target is None:
                return
            table, quadrant = target

            for _attempt in range(_MAX_ATTEMPTS_PER_SECTION):
                try:
                    generated = await generate_query(section, quadrant)
                    critic_result = await critique_query(generated["query_text"], nodes)
                    accepted = check_query(
                        gt_citations=generated["gt_citations"],
                        gt_answer=generated["ground_truth_answer"],
                        critic_cited_ids=critic_result["cited_node_ids"],
                        critic_answer=critic_result["computed_answer"],
                    )
                except _ATTEMPT_EXCEPTIONS as exc:
                    append_failure_log({
                        "document_id": document_id,
                        "table": table,
                        "quadrant": quadrant,
                        "attempt": _attempt + 1,
                        "exception_type": type(exc).__name__,
                        "exception_message": str(exc),
                    })
                    continue

                if accepted:
                    next_seq = counts[table][quadrant] + 1
                    await _accept_query(db_path, table, generated, next_seq)
                    break

            sections_processed += 1


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
