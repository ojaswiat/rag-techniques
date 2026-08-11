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

Content-aware, company-balanced fill order
-------------------------------------------
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
import logging
from collections import defaultdict
from functools import lru_cache
from pathlib import Path

import tiktoken
from groq import APIStatusError

import llm_client.config as config
import database_manager as dbm
from dataset_generation.async_critic import critique_query
from dataset_generation.async_generator import generate_query
from dataset_generation.cross_check import check_query, diagnose_rejection, embedding_similarity
from dataset_generation.section_grouper import group_sections

_QUADRANTS = ("Q1_Direct_Text", "Q2_Implicit_Text", "Q3_Direct_Table", "Q4_Implicit_Table")
_TEXT_QUADRANTS = ("Q1_Direct_Text", "Q2_Implicit_Text")
_TABLE_QUADRANTS = ("Q3_Direct_Table", "Q4_Implicit_Table")
_TABLE_ORDER = ("queries", "golden_queries", "judge_validation")
_TARGETS = {"queries": 25, "golden_queries": 5, "judge_validation": 5}
_MAX_ATTEMPTS_PER_SECTION = 3

# Minimum question-text embedding similarity (via
# cross_check.embedding_similarity, same local bge-small-en-v1.5 model
# already used for the Generator/Critic answer-equivalence gate) above which
# a candidate query is treated as a near-verbatim restatement of an
# already-accepted one and rejected as a duplicate.
#
# Deliberately a separate, higher constant from cross_check's
# EMBEDDING_SIMILARITY_THRESHOLD (0.75) rather than a reuse of it: that
# threshold was tuned for "these two answers describe the same fact"
# (semantically loose on purpose -- different phrasings of the same number
# should still match). Question-duplication needs a stricter bar, because
# two different, both-legitimate questions about the same general topic
# (e.g. two different revenue-related questions about the same filing, one
# direct, one implicit -- exactly the Q1/Q2 quadrant design) can still land
# at moderate cosine similarity without being actual duplicates. 0.92 is a
# deliberately conservative starting point for near-verbatim-restatement
# detection, not a tuned value -- unlike EMBEDDING_SIMILARITY_THRESHOLD,
# there is no existing corpus of accepted-vs-rejected duplicate-question
# pairs to calibrate against yet; this is a judgement call to revisit once
# real duplicate/non-duplicate examples are observed.
_DUPLICATE_QUESTION_SIMILARITY_THRESHOLD = 0.92

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

# Hard cap on how many tokens' worth of section content
# generate_query() is ever handed in one Generator call. gpt-oss-120b's
# context window is 128K tokens, but the raw window isn't the right budget
# to chunk against -- the system prompt, per-quadrant guidance, the
# node_ids list, the retry feedback text appended on later attempts, and
# the model's own JSON response all draw from the same window. 60,000 was
# chosen as a value that (a) leaves >65K tokens of headroom under the raw
# 128K limit for all of the above plus a safety margin for the fact that
# tiktoken's cl100k_base encoding (used below) is an approximation of
# gpt-oss-120b's actual tokenizer, not an exact match, and (b) sits well
# above the largest real section measured in the corpus as of this fix
# (~29,478 tokens) -- so today this is a precautionary ceiling that never
# actually triggers a split, not an active behavior change, but the corpus
# can grow well past that before this limit becomes the binding constraint.
_MAX_SECTION_TOKENS = 60_000

# Real-tokenizer counting for chunk_section (see below). nodes.token_count
# in the DB is a plain whitespace word count (len(stripped.split()) in
# ingest/node_builder.py), not a real tokenizer count, so it would
# undercount actual Groq usage -- chunk_section re-counts with tiktoken
# instead. cl100k_base is used as a widely-available stand-in encoding
# (gpt-oss-120b has no public tiktoken encoding registered); combined with
# the headroom reasoning above, an approximate-but-close count is fine for
# a safety ceiling. lru_cache(maxsize=1) avoids re-loading the encoding's
# merge-rank table on every call.

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
PROGRESS_LOG_PATH = Path("logs/dataset_generation_progress.log")

# Total accepted-query count across all three tables' quadrant targets (used
# only for the human-readable running-total in progress log lines, e.g.
# "47/140 accepted") -- derived from _TARGETS/_QUADRANTS rather than
# hardcoded so it stays correct if either changes.
_TOTAL_TARGET = sum(_TARGETS.values()) * len(_QUADRANTS)

# Per-attempt progress commentary, additive to
# (not a replacement for) the structured JSON logs above (append_failure_log,
# _write_summary_log). A run can take hours across up to 140 questions with
# retries, so this gives
# live console visibility plus a durable transcript in
# logs/dataset_generation_progress.log. Uses stdlib `logging` (timestamps and
# levels for free, no new dependency) rather than print().
logger = logging.getLogger(__name__)
_LOG_FORMAT = "%(asctime)s [%(levelname)s] %(message)s"
_LOG_DATE_FORMAT = "%H:%M:%S"


def _configure_logging(log_path: Path | None = None) -> None:
    """Attaches a console handler and a file handler (writing to
    ``log_path``, default ``PROGRESS_LOG_PATH``) to the module logger, both
    sharing one formatter so log-call sites never duplicate formatting code
    per destination.

    Guarded on ``logger.handlers`` so a second call in the same process (e.g.
    ``main()`` invoked more than once, as happens repeatedly across this
    module's test suite) is a no-op rather than attaching duplicate handlers
    -- which would otherwise print/write every subsequent line twice (once
    per accumulated handler set).

    File handler opens in append mode, matching the project's existing
    append-style log precedent (append_failure_log) -- a fresh multi-hour run
    resumed after a crash should extend the same transcript, not silently
    discard the record of what happened before the crash.
    """
    if logger.handlers:
        return
    if log_path is None:
        log_path = PROGRESS_LOG_PATH
    log_path.parent.mkdir(parents=True, exist_ok=True)
    formatter = logging.Formatter(fmt=_LOG_FORMAT, datefmt=_LOG_DATE_FORMAT)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    file_handler = logging.FileHandler(log_path, mode="a")
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    logger.setLevel(logging.INFO)


def _total_accepted(counts: dict[str, dict[str, int]]) -> int:
    """Sum of accepted-query counts across every (table, quadrant) slot --
    used only to render the running total in progress log lines."""
    return sum(counts[table][quadrant] for table in counts for quadrant in counts[table])


def _log_attempt_outcome(
    document_id: str,
    table: str,
    quadrant: str,
    attempt_num: int,
    outcome: str,
    detail: str | None,
    total_accepted: int,
) -> None:
    """One progress line per generate/critique attempt, e.g.:

    ``14:32:07 [INFO] [Q3_Direct_Table/queries] AAPL_2023 attempt 2/3:
    REJECTED (value mismatch: ...) -- 47/140 accepted``
    """
    suffix = f" ({detail})" if detail else ""
    logger.info(
        "[%s/%s] %s attempt %d/%d: %s%s -- %d/%d accepted",
        quadrant,
        table,
        document_id,
        attempt_num + 1,
        _MAX_ATTEMPTS_PER_SECTION,
        outcome,
        suffix,
        total_accepted,
        _TOTAL_TARGET,
    )


MANIFEST_PATH = "data/filings_manifest.json"

_all_filings_cache: tuple[str, ...] | None = None


def _load_all_filings() -> tuple[str, ...]:
    with open(MANIFEST_PATH) as f:
        manifest = json.load(f)
    return tuple(entry["document_id"] for entry in manifest)


def _get_all_filings() -> tuple[str, ...]:
    """Returns _ALL_FILINGS, loading from manifest on first call."""
    global _all_filings_cache
    if _all_filings_cache is None:
        _all_filings_cache = _load_all_filings()
    return _all_filings_cache


def __getattr__(name: str) -> tuple[str, ...]:
    # Reads data/filings_manifest.json on first access rather than at
    # import time, so importing this module from a cwd where that
    # relative path doesn't resolve (e.g. the repo root instead of
    # project/) doesn't crash before any function is even called --
    # matching the lazy-load convention build_bm25_index.py /
    # build_summary_index.py / build_vector_index.py already use.
    if name == "_ALL_FILINGS":
        return _get_all_filings()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

_INSERTER_NAMES = {
    "queries": "insert_query",
    "golden_queries": "insert_golden_query",
    "judge_validation": "insert_judge_validation",
}

# query_id construction only -- the `quadrant` column values, their CHECK
# constraint, and _QUADRANT_GUIDANCE keys in async_generator.py are
# unaffected. "QT" (Query Type) avoids reading as a fiscal quarter in a
# project built on SEC 10-K filings.
_QUADRANT_TO_QT = {
    "Q1_Direct_Text": "QT1",
    "Q2_Implicit_Text": "QT2",
    "Q3_Direct_Table": "QT3",
    "Q4_Implicit_Table": "QT4",
}
_TABLE_CODE = {
    "queries": "PQ",
    "golden_queries": "GQ",
    "judge_validation": "JEQ",
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


@lru_cache(maxsize=1)
def _get_encoding() -> tiktoken.Encoding:
    return tiktoken.get_encoding("cl100k_base")


def _log_oversized_node_skipped(document_id: str, node_id: str, node_tokens: int) -> None:
    """Mirrors _log_attempt_outcome's structured-logging style
    (module logger, one line, key facts in the message) for the rare edge
    case where a single node -- almost always one enormous table -- exceeds
    _MAX_SECTION_TOKENS entirely on its own and can't be chunked further
    without breaking table atomicity (classify_section depends on
    tables staying intact, single nodes). That node is skipped; the rest of
    its section is still packed normally around it."""
    logger.warning(
        "[chunk_section] %s node %s (%d tokens) exceeds _MAX_SECTION_TOKENS (%d) "
        "on its own and cannot be split further without breaking table atomicity "
        "-- skipping this node, packing continues around it",
        document_id,
        node_id,
        node_tokens,
        _MAX_SECTION_TOKENS,
    )


def chunk_section(section: dict, nodes: list[dict]) -> list[dict]:
    """Splits a group_sections() section into one or more Generator-sized
    chunks, each shaped like a normal section dict (document_id,
    section_header, node_ids, content, token_count) so it can enter the
    build_pools/classify_section/pool-consumption flow exactly like an
    unchunked section.

    Like classify_section, group_sections() only keeps node_ids, not each
    node's content/type, so callers must pass the original node list the
    section was grouped from.

    Algorithm: greedy node-boundary packing against a real tiktoken count
    (see _MAX_SECTION_TOKENS's comment for why, and why not
    nodes.token_count), walking `section['node_ids']` in original document
    order (already preserved by group_sections/get_nodes_by_document) and
    closing a chunk whenever the next node would push it over the limit --
    with one refinement: a chunk boundary must never fall between a
    text node and an immediately-following table node. If closing here
    would leave a table as the first node of the next chunk, and the node
    that would be left behind (the current chunk's last node) is text, the
    boundary is backed up -- the table is kept in the CURRENT chunk instead,
    even if that means exceeding _MAX_SECTION_TOKENS for this one chunk. A
    boundary may only land right after a table block ends, never right
    before one starts.

    A section already under the limit produces exactly one chunk: the
    original `section`, unchanged (the overwhelmingly common case, verified
    by a dedicated test -- zero behaviour change for ordinary sections).

    If a single node alone exceeds _MAX_SECTION_TOKENS (almost always one
    huge table), it is logged and skipped via _log_oversized_node_skipped --
    it cannot be split further without breaking table atomicity -- and the
    rest of the section's nodes are packed normally around it.
    """
    node_by_id = {n["node_id"]: n for n in nodes}
    ordered_nodes = [node_by_id[node_id] for node_id in section["node_ids"] if node_id in node_by_id]

    encoding = _get_encoding()
    token_counts = {n["node_id"]: len(encoding.encode(n["content"])) for n in ordered_nodes}

    if sum(token_counts.values()) <= _MAX_SECTION_TOKENS:
        return [section]

    packable_nodes = []
    for node in ordered_nodes:
        node_tokens = token_counts[node["node_id"]]
        if node_tokens > _MAX_SECTION_TOKENS:
            _log_oversized_node_skipped(section["document_id"], node["node_id"], node_tokens)
            continue
        packable_nodes.append(node)

    if not packable_nodes:
        return []

    chunks_of_nodes: list[list[dict]] = []
    current: list[dict] = []
    current_tokens = 0
    for node in packable_nodes:
        node_tokens = token_counts[node["node_id"]]
        would_overflow = bool(current) and current_tokens + node_tokens > _MAX_SECTION_TOKENS
        table_after_text = node["node_type"] == "table" and current and current[-1]["node_type"] == "text"

        if would_overflow and not table_after_text:
            chunks_of_nodes.append(current)
            current = []
            current_tokens = 0

        current.append(node)
        current_tokens += node_tokens

    if current:
        chunks_of_nodes.append(current)

    return [
        {
            "document_id": section["document_id"],
            "section_header": section["section_header"],
            "node_ids": [n["node_id"] for n in chunk_nodes],
            "content": "\n\n".join(n["content"] for n in chunk_nodes),
            "token_count": sum(token_counts[n["node_id"]] for n in chunk_nodes),
        }
        for chunk_nodes in chunks_of_nodes
    ]


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
    the run. Each group_sections() section is first run through
    chunk_section -- a section under _MAX_SECTION_TOKENS
    produces itself unchanged, an oversized one produces multiple
    chunk dicts, each entering the pools as its own independent candidate
    "section". Returns (text_pool, table_pool): each a list of
    section/chunk dicts, classified via classify_section and interleaved
    round-robin across companies via _round_robin_interleave, so every
    company contributes as evenly as possible to both pools."""
    text_by_company: dict[str, list[dict]] = defaultdict(list)
    table_by_company: dict[str, list[dict]] = defaultdict(list)
    order: list[str] = []

    for document_id, nodes in documents:
        company = _company_of(document_id)
        if company not in order:
            order.append(company)
        for section in group_sections(nodes):
            for chunk in chunk_section(section, nodes):
                bucket = table_by_company if classify_section(chunk, nodes) == "table" else text_by_company
                bucket[company].append(chunk)

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
    query_id = f"{_QUADRANT_TO_QT[generated['quadrant']]}_{_TABLE_CODE[table]}_{next_seq:03d}"
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
            _log_attempt_outcome(
                document_id, table, quadrant, attempt_num, "EXCEPTION", type(exc).__name__, _total_accepted(counts)
            )
            feedback = f"the previous attempt raised {type(exc).__name__}: {exc}"
            continue

        if accepted:
            existing_queries = await dbm.get_all_query_texts(db_path)
            duplicate = None
            for dup_id, dup_text in existing_queries:
                score = embedding_similarity(generated["query_text"], dup_text)
                if score >= _DUPLICATE_QUESTION_SIMILARITY_THRESHOLD:
                    duplicate = (dup_id, dup_text, score)
                    break

            if duplicate is not None:
                dup_id, dup_text, score = duplicate
                feedback = (
                    f"too similar to already-accepted query {dup_id!r} "
                    f"({dup_text!r}, similarity {score:.3f}) -- ask about a "
                    "different aspect/section"
                )
                _log_attempt_outcome(
                    document_id, table, quadrant, attempt_num, "DUPLICATE", feedback, _total_accepted(counts)
                )
                continue

            next_seq = counts[table][quadrant] + 1
            await _accept_query(db_path, table, generated, next_seq)
            _log_attempt_outcome(
                document_id, table, quadrant, attempt_num, "ACCEPTED", None, _total_accepted(counts) + 1
            )
            return True

        feedback = diagnose_rejection(
            gt_citations=generated["gt_citations"],
            gt_answer=generated["ground_truth_answer"],
            critic_cited_ids=critic_result["cited_node_ids"],
            critic_answer=critic_result["computed_answer"],
        )
        _log_attempt_outcome(document_id, table, quadrant, attempt_num, "REJECTED", feedback, _total_accepted(counts))
    return False


async def main(db_path: str = "benchmark.db", document_ids: tuple[str, ...] | None = None) -> None:
    _configure_logging()
    await dbm.init_db(db_path)
    document_ids = _get_all_filings() if document_ids is None else document_ids
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
