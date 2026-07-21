"""SQLite access layer: five isolated tables, WAL mode, JSON-in-TEXT convention.

See resources/specs/Architecture.md §3.2 for the authoritative DDL and §3.4
for integrity notes. This module is the only place that touches raw JSON
strings for node-ID list columns — everything else works with list[str].
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
    human_score         INTEGER NOT NULL CHECK (human_score BETWEEN 1 AND 10),
    human_reasoning     TEXT NOT NULL,
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
    k_value             INTEGER NOT NULL CHECK (k_value IN (3,5,10)),
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
        await conn.commit()


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
    async with aiosqlite.connect(db_path) as conn:
        await conn.execute(
            f"INSERT INTO results ({', '.join(columns)}) VALUES ({placeholders})",
            {c: row.get(c) for c in columns},
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


def _dumps(items: list[str]) -> str:
    return json.dumps(items)


def _loads(raw: str | None) -> list[str]:
    return json.loads(raw) if raw else []
