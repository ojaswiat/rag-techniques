"""Orchestrator: fills queries/golden_queries/judge_validation to 140 total.

Resumable -- re-checks quadrant counts on every startup and skips already-full
quadrant/table slots, so a crash never re-spends Groq quota on accepted
queries (same resumability principle as Phase 3's build). LOCAL_TEST_THROTTLE
caps a run to THROTTLE_LIMIT sections total (Guardrails.md §7).
"""
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


async def _accept_query(db_path: str, table: str, generated: dict, query_index: int) -> None:
    query_id = f"{generated['quadrant']}_{table}_{query_index:04d}"
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
    query_index = 0

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
                generated = await generate_query(section, quadrant)
                critic_result = await critique_query(generated["query_text"], nodes)
                accepted = check_query(
                    gt_citations=generated["gt_citations"],
                    gt_answer=generated["ground_truth_answer"],
                    critic_cited_ids=critic_result["cited_node_ids"],
                    critic_answer=critic_result["computed_answer"],
                )
                if accepted:
                    query_index += 1
                    await _accept_query(db_path, table, generated, query_index)
                    break

            sections_processed += 1


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
