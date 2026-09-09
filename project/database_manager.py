"""SQLite access layer: five isolated tables, WAL mode, JSON-in-TEXT convention.

This is the only module that touches raw JSON strings for node-id list
columns; everything else works with list[str].
"""
import json

import aiosqlite

_SCHEMA = """
CREATE TABLE IF NOT EXISTS nodes (
    node_id            TEXT PRIMARY KEY,
    document_id        TEXT NOT NULL,
    parent_item_header TEXT,
    node_type          TEXT NOT NULL CHECK (node_type IN ('text', 'table')),
    source_page_num    INTEGER,
    content            TEXT NOT NULL,
    token_count        INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_nodes_document_id ON nodes(document_id);

CREATE TABLE IF NOT EXISTS queries (
    query_id            TEXT PRIMARY KEY,
    quadrant            TEXT NOT NULL CHECK (quadrant IN
                         ('Q1_Direct_Text','Q2_Implicit_Text','Q3_Direct_Table','Q4_Implicit_Table')),
    query_text          TEXT NOT NULL,
    ground_truth_answer TEXT NOT NULL,
    gt_citations        TEXT NOT NULL,
    document_id         TEXT NOT NULL,
    verified            INTEGER NOT NULL DEFAULT 0 CHECK (verified IN (0,1))
);
CREATE INDEX IF NOT EXISTS idx_queries_document_id ON queries(document_id);

CREATE TABLE IF NOT EXISTS golden_queries (
    query_id            TEXT PRIMARY KEY,
    quadrant            TEXT NOT NULL CHECK (quadrant IN
                         ('Q1_Direct_Text','Q2_Implicit_Text','Q3_Direct_Table','Q4_Implicit_Table')),
    query_text          TEXT NOT NULL,
    ground_truth_answer TEXT NOT NULL,
    gt_citations        TEXT NOT NULL,
    example_output      TEXT NOT NULL,
    human_score         INTEGER NOT NULL CHECK (human_score BETWEEN 0 AND 100),
    human_reasoning     TEXT NOT NULL,
    is_good             INTEGER CHECK (is_good IS NULL OR is_good IN (0, 1)),
    document_id         TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS judge_validation (
    query_id            TEXT PRIMARY KEY,
    quadrant            TEXT NOT NULL CHECK (quadrant IN
                         ('Q1_Direct_Text','Q2_Implicit_Text','Q3_Direct_Table','Q4_Implicit_Table')),
    query_text          TEXT NOT NULL,
    ground_truth_answer TEXT NOT NULL,
    gt_citations        TEXT NOT NULL,
    document_id         TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS results (
    result_id           TEXT PRIMARY KEY,
    source_set          TEXT NOT NULL CHECK (source_set IN ('PQ','JEQ')),
    query_id            TEXT NOT NULL,
    pipeline            TEXT NOT NULL CHECK (pipeline IN ('P1_vector','P2_bm25','P3_structural')),
    k_value             INTEGER NOT NULL CHECK (k_value IN (2,3,5)),
    retrieved_node_ids  TEXT NOT NULL,
    pipeline_output     TEXT,
    cited_node_ids      TEXT,
    precision_at_k      REAL,
    recall_at_k         REAL,
    evidence_hit        INTEGER CHECK (evidence_hit IN (0,1)),
    citation_match      INTEGER CHECK (citation_match IN (0,1)),
    token_f1            REAL,
    exact_match         INTEGER CHECK (exact_match IN (0,1)),
    judge_score         INTEGER CHECK (judge_score BETWEEN 1 AND 10),
    human_score         INTEGER CHECK (human_score BETWEEN 1 AND 10),
    latency_sec         REAL,
    input_tokens        INTEGER,
    output_tokens        INTEGER,
    UNIQUE (source_set, query_id, pipeline, k_value)
);
CREATE INDEX IF NOT EXISTS idx_results_query_id   ON results(query_id);
CREATE INDEX IF NOT EXISTS idx_results_pipeline_k ON results(pipeline, k_value);
"""


async def init_db(db_path: str) -> None:
    async with aiosqlite.connect(db_path) as conn:
        await conn.execute("PRAGMA journal_mode=WAL;")
        await conn.executescript(_SCHEMA)
        await _migrate_golden_queries_schema(conn)
        await conn.commit()


async def _migrate_golden_queries_schema(conn: aiosqlite.Connection) -> None:
    """CREATE TABLE IF NOT EXISTS never alters an already-existing table, so a
    golden_queries table built under an older schema (missing is_good, or the
    old human_score BETWEEN 1 AND 10 CHECK) would otherwise persist unchanged.
    Rebuilds the table in place when stale, but only if it holds no real
    rows: SQLite cannot alter an existing CHECK constraint, so fixing one
    means recreating the table, and this refuses to silently discard real
    hand-labelled research data.
    """
    cursor = await conn.execute("PRAGMA table_info(golden_queries)")
    columns = {row[1] for row in await cursor.fetchall()}
    if "is_good" in columns:
        return

    cursor = await conn.execute("SELECT COUNT(*) FROM golden_queries")
    (row_count,) = await cursor.fetchone()
    if row_count > 0:
        raise RuntimeError(
            f"golden_queries has an outdated schema (missing is_good column) "
            f"and {row_count} real row(s) -- refusing to silently drop data. "
            "Write a manual migration to preserve the existing rows."
        )

    await conn.execute("DROP TABLE golden_queries")
    await conn.executescript(_SCHEMA)


async def insert_node(db_path: str, node: dict) -> None:
    async with aiosqlite.connect(db_path) as conn:
        await conn.execute(
            """INSERT INTO nodes
               (node_id, document_id, parent_item_header, node_type, source_page_num, content, token_count)
               VALUES (:node_id, :document_id, :parent_item_header, :node_type,
                       :source_page_num, :content, :token_count)""",
            node,
        )
        await conn.commit()


async def get_nodes_by_document(db_path: str, document_id: str) -> list[dict]:
    async with aiosqlite.connect(db_path) as conn:
        conn.row_factory = aiosqlite.Row
        cursor = await conn.execute(
            "SELECT * FROM nodes WHERE document_id = ?", (document_id,)
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def upsert_result(db_path: str, row: dict) -> None:
    columns = (
        "result_id", "source_set", "query_id", "pipeline", "k_value",
        "retrieved_node_ids", "pipeline_output", "cited_node_ids",
        "precision_at_k", "recall_at_k", "evidence_hit", "citation_match",
        "token_f1", "exact_match", "judge_score", "human_score",
        "latency_sec", "input_tokens", "output_tokens",
    )
    placeholders = ", ".join(f":{c}" for c in columns)

    # Serialize JSON columns: retrieved_node_ids is always list[str],
    # cited_node_ids is list[str] | None
    params = {c: row.get(c) for c in columns}
    params["retrieved_node_ids"] = _dumps(row["retrieved_node_ids"])
    if row.get("cited_node_ids") is not None:
        params["cited_node_ids"] = _dumps(row["cited_node_ids"])

    async with aiosqlite.connect(db_path) as conn:
        await conn.execute(
            f"INSERT INTO results ({', '.join(columns)}) VALUES ({placeholders})",
            params,
        )
        await conn.commit()


async def get_completed_keys(db_path: str, source_set: str) -> set[tuple[str, str, int]]:
    async with aiosqlite.connect(db_path) as conn:
        cursor = await conn.execute(
            "SELECT query_id, pipeline, k_value FROM results WHERE source_set = ?",
            (source_set,),
        )
        rows = await cursor.fetchall()
        return {(r[0], r[1], r[2]) for r in rows}


_QUADRANTS = ("Q1_Direct_Text", "Q2_Implicit_Text", "Q3_Direct_Table", "Q4_Implicit_Table")
_QUADRANT_TABLES = ("queries", "golden_queries", "judge_validation")


async def insert_query(db_path: str, row: dict) -> None:
    params = {**row, "gt_citations": _dumps(row["gt_citations"]), "verified": int(row.get("verified", 1))}
    async with aiosqlite.connect(db_path) as conn:
        await conn.execute(
            """INSERT INTO queries
               (query_id, quadrant, query_text, ground_truth_answer, gt_citations, document_id, verified)
               VALUES (:query_id, :quadrant, :query_text, :ground_truth_answer, :gt_citations, :document_id, :verified)""",
            params,
        )
        await conn.commit()


async def insert_golden_query(db_path: str, row: dict) -> None:
    params = {**row, "gt_citations": _dumps(row["gt_citations"])}
    async with aiosqlite.connect(db_path) as conn:
        await conn.execute(
            """INSERT INTO golden_queries
               (query_id, quadrant, query_text, ground_truth_answer, gt_citations,
                example_output, human_score, human_reasoning, document_id)
               VALUES (:query_id, :quadrant, :query_text, :ground_truth_answer, :gt_citations,
                       :example_output, :human_score, :human_reasoning, :document_id)""",
            params,
        )
        await conn.commit()


async def insert_judge_validation(db_path: str, row: dict) -> None:
    params = {**row, "gt_citations": _dumps(row["gt_citations"])}
    async with aiosqlite.connect(db_path) as conn:
        await conn.execute(
            """INSERT INTO judge_validation
               (query_id, quadrant, query_text, ground_truth_answer, gt_citations, document_id)
               VALUES (:query_id, :quadrant, :query_text, :ground_truth_answer, :gt_citations, :document_id)""",
            params,
        )
        await conn.commit()


async def get_quadrant_counts(db_path: str, table: str) -> dict[str, int]:
    if table not in _QUADRANT_TABLES:
        raise ValueError(f"unsupported table for quadrant counts: {table!r}")
    async with aiosqlite.connect(db_path) as conn:
        cursor = await conn.execute(f"SELECT quadrant, COUNT(*) FROM {table} GROUP BY quadrant")
        rows = await cursor.fetchall()
    counts = {q: 0 for q in _QUADRANTS}
    counts.update({r[0]: r[1] for r in rows})
    return counts


async def get_all_query_texts(db_path: str) -> list[tuple[str, str]]:
    """(query_id, query_text) pairs from all three quadrant-fill tables
    (queries, golden_queries, judge_validation), combined. Used by the
    duplicate-question check: a duplicate between a PQ and a GQ is just as
    real a problem as a duplicate within one table, so the check must see
    the whole 140-query set, not just one table at a time."""
    async with aiosqlite.connect(db_path) as conn:
        cursor = await conn.execute(
            """SELECT query_id, query_text FROM queries
               UNION ALL
               SELECT query_id, query_text FROM golden_queries
               UNION ALL
               SELECT query_id, query_text FROM judge_validation"""
        )
        rows = await cursor.fetchall()
    return [(r[0], r[1]) for r in rows]


_SOURCE_SET_TABLES = {"PQ": "queries", "JEQ": "judge_validation"}


async def get_queries(db_path: str, source_set: str) -> list[dict]:
    """Benchmark queries for one results.source_set value.

    Only 'PQ' and 'JEQ' are addressable here: those are the two values the
    results table's CHECK constraint permits, so golden_queries ('GQ', the
    Judge's few-shot exemplar pool) is deliberately unreachable, keeping the
    exemplar set out of any code path that feeds a pipeline.
    """
    try:
        table = _SOURCE_SET_TABLES[source_set]
    except KeyError as exc:
        raise ValueError(
            f"source_set must be one of {sorted(_SOURCE_SET_TABLES)}, got {source_set!r}"
        ) from exc

    async with aiosqlite.connect(db_path) as conn:
        conn.row_factory = aiosqlite.Row
        cursor = await conn.execute(f"SELECT * FROM {table} ORDER BY query_id")
        rows = await cursor.fetchall()
    result = []
    for row in rows:
        d = dict(row)
        d["gt_citations"] = _loads(d["gt_citations"])
        result.append(d)
    return result


async def get_golden_queries(db_path: str) -> list[dict]:
    async with aiosqlite.connect(db_path) as conn:
        conn.row_factory = aiosqlite.Row
        cursor = await conn.execute("SELECT * FROM golden_queries")
        rows = await cursor.fetchall()
    result = []
    for row in rows:
        d = dict(row)
        d["gt_citations"] = _loads(d["gt_citations"])
        result.append(d)
    return result


async def update_golden_query_labels(
    db_path: str,
    query_id: str,
    human_score: int,
    human_reasoning: str,
    is_good: bool | None = None,
) -> None:
    if not isinstance(human_score, int) or isinstance(human_score, bool) or not (0 <= human_score <= 100):
        raise ValueError(f"{query_id}: human_score {human_score!r} must be an integer in 0-100")
    if is_good is not None and is_good not in (True, False, 0, 1):
        raise ValueError(f"{query_id}: is_good {is_good!r} must be None, True/1, or False/0")

    async with aiosqlite.connect(db_path) as conn:
        cursor = await conn.execute(
            "UPDATE golden_queries SET human_score = ?, human_reasoning = ?, is_good = ? WHERE query_id = ?",
            (human_score, human_reasoning, None if is_good is None else int(is_good), query_id),
        )
        await conn.commit()
        if cursor.rowcount == 0:
            raise ValueError(f"No golden_query found with query_id={query_id!r} -- check for a typo")


async def get_results(db_path: str, source_set: str) -> list[dict]:
    """Every results row for one source_set, JSON node-id columns decoded.

    The JSON-in-TEXT boundary stays here: callers receive retrieved_node_ids
    and cited_node_ids as plain list[str].
    """
    async with aiosqlite.connect(db_path) as conn:
        conn.row_factory = aiosqlite.Row
        cursor = await conn.execute(
            "SELECT * FROM results WHERE source_set = ? ORDER BY result_id",
            (source_set,),
        )
        rows = await cursor.fetchall()
    result = []
    for row in rows:
        d = dict(row)
        d["retrieved_node_ids"] = _loads(d["retrieved_node_ids"])
        d["cited_node_ids"] = _loads(d["cited_node_ids"])
        result.append(d)
    return result


async def get_jeq_judging_rows(db_path: str) -> list[dict]:
    """The 60 gate rows, each joined to its judge_validation ground truth.

    async_judge.py scores one results row at a time but needs that row's
    quadrant, ground-truth answer, and gt_citations, none of which live in
    results. The join supplies them so the Judge never has to reach across
    tables itself; JSON list columns from both tables are decoded to
    list[str].
    """
    async with aiosqlite.connect(db_path) as conn:
        conn.row_factory = aiosqlite.Row
        cursor = await conn.execute(
            """SELECT r.*, jv.quadrant, jv.query_text, jv.ground_truth_answer,
                      jv.gt_citations, jv.document_id
               FROM results r
               JOIN judge_validation jv ON jv.query_id = r.query_id
               WHERE r.source_set = 'JEQ'
               ORDER BY r.result_id"""
        )
        rows = await cursor.fetchall()
    result = []
    for row in rows:
        d = dict(row)
        d["retrieved_node_ids"] = _loads(d["retrieved_node_ids"])
        d["cited_node_ids"] = _loads(d["cited_node_ids"])
        d["gt_citations"] = _loads(d["gt_citations"])
        result.append(d)
    return result


async def get_golden_queries_by_quadrant(db_path: str, quadrant: str) -> list[dict]:
    """The teaching exemplars for one quadrant.

    async_judge.py builds a prompt from exactly the 5 GQ that share the
    target row's quadrant, never all 20, so this reads a single quadrant's
    slice rather than the whole golden_queries table.
    """
    async with aiosqlite.connect(db_path) as conn:
        conn.row_factory = aiosqlite.Row
        cursor = await conn.execute(
            "SELECT * FROM golden_queries WHERE quadrant = ? ORDER BY query_id",
            (quadrant,),
        )
        rows = await cursor.fetchall()
    result = []
    for row in rows:
        d = dict(row)
        d["gt_citations"] = _loads(d["gt_citations"])
        result.append(d)
    return result


# Columns async_judge.py may write per gate row: the deterministic metrics plus
# the LLM judge_score. Everything else on a results row is fixed at insert time
# by loop_executor and must not be reachable through this update path.
_UPDATABLE_SCORE_COLUMNS = frozenset(
    {
        "precision_at_k",
        "recall_at_k",
        "evidence_hit",
        "citation_match",
        "token_f1",
        "exact_match",
        "judge_score",
    }
)


async def update_result_scores(db_path: str, result_id: str, scores: dict) -> None:
    """Write the deterministic metrics and judge_score onto one results row.

    upsert_result is INSERT-only (it fails loudly on a re-inserted cell), so
    scoring a row after loop_executor produced it needs this separate UPDATE.
    Only the score columns are writable; any other key is rejected so this
    can never be used to rewrite the run's identity or its raw output.
    """
    if not scores:
        raise ValueError("update_result_scores: no score columns supplied")
    unknown = set(scores) - _UPDATABLE_SCORE_COLUMNS
    if unknown:
        raise ValueError(f"unknown score column(s): {sorted(unknown)}")

    assignments = ", ".join(f"{c} = :{c}" for c in scores)
    params = {**scores, "result_id": result_id}
    async with aiosqlite.connect(db_path) as conn:
        cursor = await conn.execute(
            f"UPDATE results SET {assignments} WHERE result_id = :result_id",
            params,
        )
        await conn.commit()
        if cursor.rowcount == 0:
            raise ValueError(f"no results row with result_id={result_id!r}")


async def update_result_human_score(db_path: str, result_id: str, human_score: int) -> None:
    """Record the researcher's hand-score for one JEQ gate row (1-10)."""
    if not isinstance(human_score, int) or isinstance(human_score, bool) or not (1 <= human_score <= 10):
        raise ValueError(f"human_score {human_score!r} must be an integer in 1-10")
    async with aiosqlite.connect(db_path) as conn:
        cursor = await conn.execute(
            "UPDATE results SET human_score = ? WHERE result_id = ?",
            (human_score, result_id),
        )
        await conn.commit()
        if cursor.rowcount == 0:
            raise ValueError(f"no results row with result_id={result_id!r}")


def _dumps(items: list[str]) -> str:
    return json.dumps(items)


def _loads(raw: str | None) -> list[str]:
    return json.loads(raw) if raw else []
