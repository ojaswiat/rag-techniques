import asyncio
import json
import os

import pytest

import database_manager as dbm

TEST_DB = "test_benchmark.db"


@pytest.fixture(autouse=True)
def clean_db():
    for suffix in ("", "-wal", "-shm"):
        path = TEST_DB + suffix
        if os.path.exists(path):
            os.remove(path)
    yield
    for suffix in ("", "-wal", "-shm"):
        path = TEST_DB + suffix
        if os.path.exists(path):
            os.remove(path)


@pytest.mark.asyncio
async def test_init_db_creates_five_tables():
    await dbm.init_db(TEST_DB)
    import aiosqlite

    async with aiosqlite.connect(TEST_DB) as conn:
        cursor = await conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        rows = await cursor.fetchall()
        table_names = {row[0] for row in rows}
    assert {"nodes", "queries", "golden_queries", "judge_validation", "results"} <= table_names


@pytest.mark.asyncio
async def test_wal_mode_enabled():
    await dbm.init_db(TEST_DB)
    import aiosqlite

    async with aiosqlite.connect(TEST_DB) as conn:
        cursor = await conn.execute("PRAGMA journal_mode;")
        (mode,) = await cursor.fetchone()
    assert mode.lower() == "wal"


@pytest.mark.asyncio
async def test_insert_and_get_node():
    await dbm.init_db(TEST_DB)
    node = {
        "node_id": "TEST_2025_n0001",
        "document_id": "SEC_10K_TEST_2025",
        "parent_item_header": "Item 8",
        "node_type": "table",
        "source_page_num": 12,
        "content": "| Year | Net Sales |\n|---|---|\n| 2025 | 100 |",
        "token_count": 20,
    }
    await dbm.insert_node(TEST_DB, node)
    fetched = await dbm.get_nodes_by_document(TEST_DB, "SEC_10K_TEST_2025")
    assert len(fetched) == 1
    assert fetched[0]["node_id"] == "TEST_2025_n0001"


@pytest.mark.asyncio
async def test_upsert_result_and_get_completed_keys():
    await dbm.init_db(TEST_DB)
    row = {
        "result_id": "R_TEST_001",
        "source_set": "PQ",
        "query_id": "Q1_001",
        "pipeline": "P1_vector",
        "k_value": 5,
        "retrieved_node_ids": json.dumps(["TEST_2025_n0001"]),
        "pipeline_output": "Net sales were 100. [[node:TEST_2025_n0001]]",
        "cited_node_ids": json.dumps(["TEST_2025_n0001"]),
        "precision_at_k": 1.0,
        "recall_at_k": 1.0,
        "evidence_hit": 1,
        "citation_match": 1,
        "token_f1": 0.9,
        "exact_match": 1,
        "judge_score": 8,
        "human_score": None,
        "latency_sec": 1.2,
        "input_tokens": 500,
        "output_tokens": 30,
    }
    await dbm.upsert_result(TEST_DB, row)
    completed = await dbm.get_completed_keys(TEST_DB, "PQ")
    assert ("Q1_001", "P1_vector", 5) in completed


@pytest.mark.asyncio
async def test_results_unique_constraint_blocks_duplicate():
    await dbm.init_db(TEST_DB)
    row = {
        "result_id": "R_TEST_002",
        "source_set": "PQ",
        "query_id": "Q1_002",
        "pipeline": "P2_bm25",
        "k_value": 3,
        "retrieved_node_ids": json.dumps([]),
        "pipeline_output": None,
        "cited_node_ids": None,
        "precision_at_k": None,
        "recall_at_k": None,
        "evidence_hit": None,
        "citation_match": None,
        "token_f1": None,
        "exact_match": None,
        "judge_score": None,
        "human_score": None,
        "latency_sec": None,
        "input_tokens": None,
        "output_tokens": None,
    }
    await dbm.upsert_result(TEST_DB, row)
    row["result_id"] = "R_TEST_003"  # different PK, same (source_set, query_id, pipeline, k_value)
    with pytest.raises(Exception):
        await dbm.upsert_result(TEST_DB, row)
