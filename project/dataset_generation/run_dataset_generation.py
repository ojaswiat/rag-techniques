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

Content-aware, company-balanced fill order (Doubt #2 fix)
-----------------------------------------------------------
Sections are classified as table-type or text-type (see classify_section)
and routed to whichever quadrants that content can actually support:
table sections -> Q3/Q4 (table-extraction/table-math), text sections ->
Q1/Q2. This prevents the Generator being handed a pure-prose section and
asked to invent a table question anyway.

Within each pool, sections are interleaved round-robin across companies
(see build_pools/_round_robin_interleave) instead of exhausted one document
at a time, so no single company's filings dominate a quadrant just because
they happened to be processed first. Each pool is cycled up to
_MAX_POOL_CYCLES times if a single pass doesn't fill its targets -- capped,
not unbounded, so a structurally too-small pool (e.g. too few table
sections in the corpus) can't spin forever burning Groq quota.
"""
import json
from collections import defaultdict
from pathlib import Path

from groq import APIStatusError

import config
import database_manager as dbm
from dataset_generation.async_critic import critique_query
from dataset_generation.async_generator import generate_query
from dataset_generation.cross_check import check_query, diagnose_rejection
from dataset_generation.section_grouper import group_sections

_QUADRANTS = ("Q1_Direct_Text", "Q2_Implicit_Text", "Q3_Direct_Table", "Q4_Implicit_Table")
_TEXT_QUADRANTS = ("Q1_Direct_Text", "Q2_Implicit_Text")
_TABLE_QUADRANTS = ("Q3_Direct_Table", "Q4_Implicit_Table")
_TABLE_ORDER = ("queries", "golden_queries", "judge_validation")
_TARGETS = {"queries": 25, "golden_queries": 5, "judge_validation": 5}
_MAX_ATTEMPTS_PER_SECTION = 3

# Safety cap on how many full passes ("cycles") a content pool (the
# table-section pool feeding Q3/Q4, or the text-section pool feeding Q1/Q2)
# gets revisited if one pass through it doesn't fill its quadrants' targets.
# Chosen as 5: each section already gets _MAX_ATTEMPTS_PER_SECTION (3)
# independent generate/critique attempts per visit, so a 5-cycle cap gives
# every section up to 15 total attempts across the run -- generous enough to
# absorb a realistic Generator/Critic reject rate without risking an
# effectively unbounded loop (and unbounded Groq quota spend) if a pool is
# structurally too small to ever reach its target (e.g. the corpus simply
# doesn't have enough table sections).
_MAX_POOL_CYCLES = 5

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
SUMMARY_LOG_PATH = Path("logs/dataset_generation_summary.json")

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


def next_target(
    counts: dict[str, dict[str, int]], quadrants: tuple[str, ...] = _QUADRANTS
) -> tuple[str, str] | None:
    """First still-unfilled (table, quadrant) slot, searched quadrant-major
    then table-minor within `quadrants` (defaults to all four). Passing a
    restricted subset (e.g. _TEXT_QUADRANTS) confines the search to the
    quadrants a given content pool is allowed to fill."""
    for quadrant in quadrants:
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


def _company_of(document_id: str) -> str:
    """First underscore-delimited token of a document_id (e.g. 'AAPL_2023' ->
    'AAPL'). Used only to spread pool interleaving across companies as
    evenly as possible -- not a schema field, and not used for any
    pipeline-comparison logic."""
    return document_id.split("_")[0]


def classify_section(section: dict, nodes: list[dict]) -> str:
    """Classify a group_sections() section as 'table' or 'text'.

    group_sections() only keeps node_ids, not each node's node_type, so
    callers must pass the original node list the section was grouped from.

    Rule: 'table' if ANY node making up the section is node_type=='table',
    else 'text'. An "any" rule (rather than "majority") was chosen because a
    single table node is already enough raw material for a genuine Q3/Q4
    (table-extraction/table-math) question, and 10-K sections routinely mix
    one table with a lot of surrounding narrative text in the same
    (document_id, parent_item_header) group -- a majority rule would
    discard real, usable table content just because it's outnumbered by
    prose nodes in the same section.
    """
    type_by_id = {n["node_id"]: n["node_type"] for n in nodes}
    is_table = any(type_by_id.get(node_id) == "table" for node_id in section["node_ids"])
    return "table" if is_table else "text"


def _round_robin_interleave(buckets: dict[str, list[dict]], order: list[str]) -> list[dict]:
    """Flattens per-company section lists into one list by taking one
    section from each company in `order` per round (AAPL, MSFT, TSLA, ...,
    AAPL, MSFT, TSLA, ...), rather than exhausting one company's sections
    before moving to the next. Companies that run out of sections simply
    stop contributing further rounds; remaining companies keep going."""
    result: list[dict] = []
    indices = {company: 0 for company in order}
    progressed = True
    while progressed:
        progressed = False
        for company in order:
            items = buckets.get(company, [])
            i = indices[company]
            if i < len(items):
                result.append(items[i])
                indices[company] = i + 1
                progressed = True
    return result


def build_pools(documents: list[tuple[str, list[dict]]]) -> tuple[list[dict], list[dict]]:
    """Builds the two content pools upfront, across ALL filings.

    `documents` is a list of (document_id, nodes) pairs for every filing in
    the run. Returns (text_pool, table_pool): each a list of section dicts
    (as returned by group_sections), classified via classify_section and
    interleaved round-robin across companies via _round_robin_interleave, so
    every company contributes as evenly as possible to both pools."""
    text_by_company: dict[str, list[dict]] = defaultdict(list)
    table_by_company: dict[str, list[dict]] = defaultdict(list)
    order: list[str] = []

    for document_id, nodes in documents:
        company = _company_of(document_id)
        if company not in order:
            order.append(company)
        for section in group_sections(nodes):
            bucket = table_by_company if classify_section(section, nodes) == "table" else text_by_company
            bucket[company].append(section)

    text_pool = _round_robin_interleave(text_by_company, order)
    table_pool = _round_robin_interleave(table_by_company, order)
    return text_pool, table_pool


def format_underfill_summary(counts: dict[str, dict[str, int]]) -> str:
    """Human-readable per-table, per-quadrant fill status, one line per
    table, e.g.:

    'queries: Q1_Direct_Text 25/25, Q2_Implicit_Text 25/25,
    Q3_Direct_Table 18/25 (underfilled), Q4_Implicit_Table 25/25'
    """
    lines = []
    for table in _TABLE_ORDER:
        target = _TARGETS[table]
        parts = []
        for quadrant in _QUADRANTS:
            n = counts[table][quadrant]
            marker = " (underfilled)" if n < target else ""
            parts.append(f"{quadrant} {n}/{target}{marker}")
        lines.append(f"{table}: " + ", ".join(parts))
    return "\n".join(lines)


def _write_summary_log(counts: dict[str, dict[str, int]], log_path: Path | None = None) -> None:
    """Durable snapshot of the final fill state, mirroring the failure-log
    precedent (append_failure_log). Unlike the failure log this is a single
    current-state snapshot (overwritten each run), not an append-only
    history -- there is exactly one "how did the run end up" answer worth
    keeping durably, not one entry per run."""
    if log_path is None:
        log_path = SUMMARY_LOG_PATH
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text(json.dumps({"counts": counts, "summary": format_underfill_summary(counts)}, indent=2))


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


async def _attempt_fill(
    db_path: str,
    section: dict,
    table: str,
    quadrant: str,
    nodes: list[dict],
    counts: dict[str, dict[str, int]],
    document_id: str,
) -> bool:
    """Runs up to _MAX_ATTEMPTS_PER_SECTION generate/critique attempts for
    one (section, table, quadrant) slot. Returns True iff a query was
    accepted and inserted.

    All Groq calls run at temperature=0, so an identical `generate_query`
    input on retry would deterministically reproduce the identical (already
    -rejected) output. `feedback` carries forward what went wrong on the
    previous attempt -- a rejection reason from `diagnose_rejection`, or the
    caught exception's message -- so each retry's prompt genuinely differs
    from the last and a different candidate is actually possible."""
    feedback: str | None = None
    for attempt_num in range(_MAX_ATTEMPTS_PER_SECTION):
        try:
            generated = await generate_query(section, quadrant, previous_attempt_feedback=feedback)
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
                "attempt": attempt_num + 1,
                "exception_type": type(exc).__name__,
                "exception_message": str(exc),
            })
            feedback = f"the previous attempt raised {type(exc).__name__}: {exc}"
            continue

        if accepted:
            next_seq = counts[table][quadrant] + 1
            await _accept_query(db_path, table, generated, next_seq)
            return True

        feedback = diagnose_rejection(
            gt_citations=generated["gt_citations"],
            gt_answer=generated["ground_truth_answer"],
            critic_cited_ids=critic_result["cited_node_ids"],
            critic_answer=critic_result["computed_answer"],
        )
    return False


async def main(db_path: str = "benchmark.db", document_ids: tuple[str, ...] | None = None) -> None:
    await dbm.init_db(db_path)
    document_ids = document_ids or _ALL_FILINGS
    max_sections = config.THROTTLE_LIMIT if config.LOCAL_TEST_THROTTLE else None

    nodes_by_document: dict[str, list[dict]] = {}
    for document_id in document_ids:
        nodes_by_document[document_id] = await dbm.get_nodes_by_document(db_path, document_id)

    text_pool, table_pool = build_pools(list(nodes_by_document.items()))

    sections_processed = 0
    throttled = False

    for pool, quadrants in ((text_pool, _TEXT_QUADRANTS), (table_pool, _TABLE_QUADRANTS)):
        if throttled or not pool:
            continue

        for _cycle in range(_MAX_POOL_CYCLES):
            counts = await _load_counts(db_path)
            if next_target(counts, quadrants) is None:
                break  # this pool's quadrants are already fully filled

            for section in pool:
                if max_sections is not None and sections_processed >= max_sections:
                    throttled = True
                    break

                counts = await _load_counts(db_path)
                target = next_target(counts, quadrants)
                if target is None:
                    break
                table, quadrant = target

                document_id = section["document_id"]
                nodes = nodes_by_document[document_id]
                await _attempt_fill(db_path, section, table, quadrant, nodes, counts, document_id)
                sections_processed += 1

            if throttled:
                break

    final_counts = await _load_counts(db_path)
    summary = format_underfill_summary(final_counts)
    print(summary)
    _write_summary_log(final_counts)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
