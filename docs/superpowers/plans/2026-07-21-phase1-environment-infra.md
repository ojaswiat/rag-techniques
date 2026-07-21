# Phase 1 — Environment, Infrastructure & Cost Guardrails Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stand up the repo skeleton, the five-table SQLite state layer, and the rate-limit/throttle scaffolding that every later phase (2-8) depends on. No task in this plan calls a model "in anger" — Task 5's smoke test is the one exception, and it burns at most a handful of free-tier tokens.

**Architecture:** All code lives under `project/` (already has a `uv`-managed `.venv/`, no source yet). Build `config.py` (model routing + env loading), `database_manager.py` (WAL-mode SQLite, five tables, typed async helpers), `groq_client.py` (tenacity-wrapped `AsyncGroq`, semaphore-bounded), and `groq_limits.md` (dated, verified rate limits). Everything is local, free-tier, $0.

**Tech Stack:** Python (uv-managed venv), `aiosqlite`, `groq` SDK, `tenacity`, `python-dotenv`, `pytest` + `pytest-asyncio`.

## Global Constraints

- No per-hour or scale-to-non-zero infrastructure, ever — SQLite is local, Groq is free-tier (`resources/specs/Guardrails.md` §1, §8).
- All LLM calls run at `temperature = 0` on Groq free tier only (`Guardrails.md` §2).
- `asyncio.Semaphore` capped at ≤ 5 parallel Groq workers (`Guardrails.md` §5).
- `tenacity` exponential backoff with randomised jitter on HTTP 429 (`Guardrails.md` §5).
- SQLite must run in WAL mode (`PRAGMA journal_mode=WAL;`) (`Guardrails.md` §6, `Architecture.md` §3.2).
- Five isolated tables exactly as specified in `Architecture.md` §3.2 DDL: `nodes`, `queries`, `golden_queries`, `judge_validation`, `results`.
- `results.UNIQUE(source_set, query_id, pipeline, k_value)` is both the integrity constraint and the resume-lookup key (`Architecture.md` §3.4).
- Every future loop script needs a hardcoded `LOCAL_TEST_THROTTLE` boolean pattern (forces `LIMIT 3`) — this plan builds the reusable template (`Guardrails.md` §7).
- `judge_validation` has no `pipeline_output`/`human_score`/`judge_score` columns — those 60 rows live in `results` tagged `source_set='JEQ'` (`Architecture.md` §3.2 note).
- Version-pin note: LlamaIndex's current line is 0.14.x (not the example 0.10.x in `Phase Plan.md`) — re-verify current versions at implementation time, don't copy the spec's example string verbatim (`Architecture.md` §10).
- All work happens inside `project/.venv` via `uv` — see memory note "Venv & workspace split": code goes in `project/`, root is assignment/agent workspace.
- British English in any prose/docs produced; code itself has no language concern.

---

## Human Intervention Ledger (read this before starting)

Two kinds of human step appear in this plan, tagged inline at the exact step that needs them:

- **[ACTIVE]** — the agent must stop and wait. Nothing later in the task can proceed without the human's input (e.g. an API key must exist before the client can be smoke-tested).
- **[PASSIVE]** — the agent keeps going with a stub/placeholder and logs what the human needs to do later (e.g. `.env.example` gets a placeholder key; the agent does not block on the real key existing until the one step that actually calls the network).

At the end of this plan there is a **Human Action Report** section — Task 7 generates it from what actually happened, not written in advance.

---

### Task 1: Repo skeleton and pinned dependency manifest

**Files:**
- Create: `project/pyproject.toml`
- Create: `project/.env.example`
- Create: `project/.gitignore`
- Create: `project/config.py`
- Create: `project/tests/__init__.py`
- Create: `project/tests/test_config.py`

**Interfaces:**
- Consumes: nothing (first task).
- Produces: `config.py` exposes `MODEL_ROUTING: dict[str, str]` (keys: `"generator"`, `"critic"`, `"p3_index_build"`, `"answerer"`, `"judge"`, `"debug"`) and `LOCAL_TEST_THROTTLE: bool` and `GROQ_API_KEY: str | None` (loaded from `.env` via `python-dotenv`) — every later task imports these names verbatim.

- [ ] **Step 1: Confirm the existing venv and initialise `pyproject.toml`**

Run: `cd /Users/ojaswi/Projects/rag-techniques/project && uv init --no-workspace --name rag-techniques-benchmark 2>&1 | tail -20`

Expected: creates or reports existing `pyproject.toml`, `hello.py`/`main.py` may appear — delete any placeholder `main.py`/`hello.py` `uv init` creates:

```bash
rm -f /Users/ojaswi/Projects/rag-techniques/project/main.py /Users/ojaswi/Projects/rag-techniques/project/hello.py
```

- [ ] **Step 2: Add pinned Phase 1 dependencies**

Run:
```bash
cd /Users/ojaswi/Projects/rag-techniques/project
uv add groq tenacity aiosqlite python-dotenv
uv add --dev pytest pytest-asyncio
```

Expected: `pyproject.toml` gains a `[project.dependencies]` block with `groq`, `tenacity`, `aiosqlite`, `python-dotenv` and a dev group with `pytest`, `pytest-asyncio`. `uv.lock` is created/updated.

- [ ] **Step 3: Record exact resolved versions**

Run: `cd /Users/ojaswi/Projects/rag-techniques/project && uv pip list 2>&1 | grep -Ei "groq|tenacity|aiosqlite|python-dotenv|pytest"`

Copy the printed versions into a comment block at the top of `pyproject.toml` under `[tool.rag-benchmark]` (informational only, not a real tool table):

```toml
[tool.rag-benchmark]
# Resolved Phase 1 versions (recorded 2026-07-21, uv pip list):
# groq==<paste>
# tenacity==<paste>
# aiosqlite==<paste>
# python-dotenv==<paste>
notes = "See resources/specs/Architecture.md §10 for the full manifest; re-verify LlamaIndex pins at Phase 2/5 time."
```

- [ ] **Step 4: Create `.env.example` with placeholders — [PASSIVE]**

Write `project/.env.example`:

```bash
# Groq free-tier API key. Get one at https://console.groq.com/keys
# 1. Sign in / create a free account at https://console.groq.com
# 2. Go to "API Keys" in the left sidebar
# 3. Click "Create API Key", name it (e.g. "rag-techniques-dev"), copy the value
#    (shown only once — store it somewhere safe if you lose this file)
# 4. Paste it below, then copy this file to `.env` (never commit `.env`)
GROQ_API_KEY=your-groq-api-key-here

# LlamaParse API key (needed from Phase 2 onward, not Phase 1) — get one at
# https://cloud.llamaindex.ai/api-key (free tier, sign in with Google/GitHub/email)
LLAMA_CLOUD_API_KEY=your-llamaparse-api-key-here

# Set to true for the 3-item throttle everywhere; false to run full batches
LOCAL_TEST_THROTTLE=true
```

This is passive: the agent does not wait for real keys to exist. It logs the need in the Task 7 report.

- [ ] **Step 5: Create `.gitignore` for the `project/` subtree**

Write `project/.gitignore`:

```
.venv/
.env
benchmark.db
benchmark.db-wal
benchmark.db-shm
__pycache__/
*.pyc
storage/
logs/
data/raw/
data/parsed/
.pytest_cache/
```

- [ ] **Step 6: Write `config.py`**

```python
"""Model routing, throttle flag, and env loading for the whole benchmark build."""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

GROQ_API_KEY: str | None = os.getenv("GROQ_API_KEY")
LLAMA_CLOUD_API_KEY: str | None = os.getenv("LLAMA_CLOUD_API_KEY")

LOCAL_TEST_THROTTLE: bool = os.getenv("LOCAL_TEST_THROTTLE", "true").lower() == "true"
THROTTLE_LIMIT: int = 3

# Guardrails.md §2 — fixed model routing matrix. Do not change without updating the spec.
MODEL_ROUTING: dict[str, str] = {
    "generator": "openai/gpt-oss-120b",
    "critic": "qwen/qwen3.6-27b",
    "p3_index_build": "llama-3.1-8b-instant",
    "answerer": "llama-3.3-70b-versatile",
    "judge": "qwen/qwen3.6-27b",
    "debug": "llama-3.1-8b-instant",
}

GROQ_MAX_CONCURRENCY: int = 5
```

- [ ] **Step 7: Write the failing config test**

```python
# project/tests/test_config.py
import config


def test_model_routing_has_all_stages():
    expected_stages = {"generator", "critic", "p3_index_build", "answerer", "judge", "debug"}
    assert set(config.MODEL_ROUTING.keys()) == expected_stages


def test_generator_and_critic_are_different_families():
    assert config.MODEL_ROUTING["generator"].split("/")[0] != config.MODEL_ROUTING["critic"].split("/")[0]


def test_answerer_and_judge_are_different_families():
    answerer_family = config.MODEL_ROUTING["answerer"].split("-")[0]
    judge_family = config.MODEL_ROUTING["judge"].split("/")[0]
    assert answerer_family != judge_family


def test_throttle_limit_is_three():
    assert config.THROTTLE_LIMIT == 3


def test_concurrency_cap_is_five():
    assert config.GROQ_MAX_CONCURRENCY == 5
```

Create `project/tests/__init__.py` (empty file).

- [ ] **Step 8: Run test, confirm it fails first for the right reason (module not yet importable in test path)**

Run: `cd /Users/ojaswi/Projects/rag-techniques/project && uv run pytest tests/test_config.py -v`

Expected: PASS actually — `config.py` was already written in Step 6. This is acceptable for a config-loading task (no meaningful red state exists for a pure-data module); confirm PASS instead:

Expected: `5 passed`

- [ ] **Step 9: Commit**

```bash
cd /Users/ojaswi/Projects/rag-techniques/project
git add pyproject.toml uv.lock .env.example .gitignore config.py tests/__init__.py tests/test_config.py
git commit -m "feat: pin Phase 1 dependencies and add model-routing config"
```

---

### Task 2: `database_manager.py` — five-table SQLite schema in WAL mode

**Files:**
- Create: `project/database_manager.py`
- Create: `project/tests/test_database_manager.py`

**Interfaces:**
- Consumes: nothing new (stdlib `sqlite3`/`aiosqlite`, `json`).
- Produces: `init_db(db_path: str) -> None`, `insert_node(db_path: str, node: dict) -> None`, `get_nodes_by_document(db_path: str, document_id: str) -> list[dict]`, `upsert_result(db_path: str, row: dict) -> None`, `get_completed_keys(db_path: str, source_set: str) -> set[tuple[str, str, int]]`. Later phases (2, 4-8) import these by name — do not rename.

- [ ] **Step 1: Write the failing schema test**

```python
# project/tests/test_database_manager.py
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/ojaswi/Projects/rag-techniques/project && uv run pytest tests/test_database_manager.py -v`

Expected: FAIL with `ModuleNotFoundError: No module named 'database_manager'` (and `pytest-asyncio` not yet configured — see Step 3 addition below).

- [ ] **Step 3: Enable `pytest-asyncio` auto mode**

Add to `project/pyproject.toml` (append, don't replace existing tables):

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
```

- [ ] **Step 4: Write `database_manager.py` — exact DDL from `Architecture.md` §3.2**

```python
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
```

- [ ] **Step 5: Run tests, confirm all pass**

Run: `cd /Users/ojaswi/Projects/rag-techniques/project && uv run pytest tests/test_database_manager.py -v`

Expected: `6 passed`

- [ ] **Step 6: Commit**

```bash
cd /Users/ojaswi/Projects/rag-techniques/project
git add database_manager.py tests/test_database_manager.py pyproject.toml
git commit -m "feat: add five-table WAL-mode SQLite schema and async data access helpers"
```

---

### Task 3: `groq_client.py` — resilient async Groq wrapper (backoff + semaphore)

**Files:**
- Create: `project/groq_client.py`
- Create: `project/tests/test_groq_client_backoff.py`

**Interfaces:**
- Consumes: `config.GROQ_API_KEY`, `config.GROQ_MAX_CONCURRENCY` from Task 1.
- Produces: `async def call_groq(model: str, messages: list[dict], temperature: float = 0.0) -> ChatCompletion` — every later phase's LLM call (Generator, Critic, P3 build, Answerer, Judge) goes through this one function.

- [ ] **Step 1: Write the failing 429-backoff test (mocked, no real network/API key needed)**

```python
# project/tests/test_groq_client_backoff.py
from unittest.mock import AsyncMock, patch

import pytest
from groq import APIStatusError

import groq_client


class _FakeResponse:
    status_code = 429


@pytest.mark.asyncio
async def test_call_groq_retries_on_429_then_succeeds():
    success_result = {"choices": [{"message": {"content": "ok"}}]}

    call_count = {"n": 0}

    async def flaky_create(*args, **kwargs):
        call_count["n"] += 1
        if call_count["n"] < 3:
            raise APIStatusError(
                message="rate limited",
                response=_FakeResponse(),
                body={"error": {"message": "rate limited"}},
            )
        return success_result

    with patch.object(
        groq_client, "_client"
    ) as mock_client:
        mock_client.chat.completions.create = AsyncMock(side_effect=flaky_create)
        result = await groq_client.call_groq(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": "hi"}],
        )

    assert result == success_result
    assert call_count["n"] == 3


@pytest.mark.asyncio
async def test_call_groq_respects_semaphore_bound():
    assert groq_client._semaphore._value == 5
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/ojaswi/Projects/rag-techniques/project && uv run pytest tests/test_groq_client_backoff.py -v`

Expected: FAIL with `ModuleNotFoundError: No module named 'groq_client'`

- [ ] **Step 3: Write `groq_client.py`**

```python
"""Resilient async Groq wrapper: tenacity backoff on 429 + bounded concurrency.

See resources/specs/Guardrails.md §5. All Phase 2+ LLM calls (Generator,
Critic, P3 build, shared Answerer, Judge) must route through call_groq()
rather than instantiating their own AsyncGroq client, so the backoff and
concurrency cap apply uniformly.
"""
import asyncio

from groq import APIStatusError, AsyncGroq
from tenacity import (
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_random_exponential,
)

import config

_client = AsyncGroq(api_key=config.GROQ_API_KEY)
_semaphore = asyncio.Semaphore(config.GROQ_MAX_CONCURRENCY)


def _is_rate_limit_error(exc: BaseException) -> bool:
    return isinstance(exc, APIStatusError) and exc.response.status_code == 429


@retry(
    retry=retry_if_exception(_is_rate_limit_error),
    wait=wait_random_exponential(multiplier=1, max=60),
    stop=stop_after_attempt(6),
    reraise=True,
)
async def call_groq(model: str, messages: list[dict], temperature: float = 0.0):
    async with _semaphore:
        return await _client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
        )
```

- [ ] **Step 4: Run test, confirm it passes**

Run: `cd /Users/ojaswi/Projects/rag-techniques/project && uv run pytest tests/test_groq_client_backoff.py -v`

Expected: `2 passed`

- [ ] **Step 5: Commit**

```bash
cd /Users/ojaswi/Projects/rag-techniques/project
git add groq_client.py tests/test_groq_client_backoff.py
git commit -m "feat: add tenacity-backed Groq client wrapper with 5-worker semaphore"
```

---

### Task 4: `LOCAL_TEST_THROTTLE` loop-script template

**Files:**
- Create: `project/loop_template.py`
- Create: `project/tests/test_loop_template.py`

**Interfaces:**
- Consumes: `config.LOCAL_TEST_THROTTLE`, `config.THROTTLE_LIMIT` (Task 1); `database_manager.get_completed_keys` (Task 2).
- Produces: `def throttle_limit_clause() -> str` and `def apply_throttle(items: list) -> list` — Phase 2-7 loop scripts (`async_generator.py`, `async_critic.py`, `loop_executor.py`, `async_judge.py`, P3 build script) copy this exact pattern per `Guardrails.md` §7.

- [ ] **Step 1: Write the failing test**

```python
# project/tests/test_loop_template.py
import importlib

import config
import loop_template


def test_throttle_limit_clause_matches_config():
    assert loop_template.throttle_limit_clause() == f"LIMIT {config.THROTTLE_LIMIT}"


def test_apply_throttle_caps_at_three_when_enabled(monkeypatch):
    monkeypatch.setattr(config, "LOCAL_TEST_THROTTLE", True)
    importlib.reload(loop_template)
    items = list(range(10))
    assert loop_template.apply_throttle(items) == [0, 1, 2]


def test_apply_throttle_passthrough_when_disabled(monkeypatch):
    monkeypatch.setattr(config, "LOCAL_TEST_THROTTLE", False)
    importlib.reload(loop_template)
    items = list(range(10))
    assert loop_template.apply_throttle(items) == items
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/ojaswi/Projects/rag-techniques/project && uv run pytest tests/test_loop_template.py -v`

Expected: FAIL with `ModuleNotFoundError: No module named 'loop_template'`

- [ ] **Step 3: Write `loop_template.py`**

```python
"""Reusable LOCAL_TEST_THROTTLE pattern for every Phase 2-7 loop script.

Guardrails.md §7: every loop script (async_generator.py, async_critic.py,
loop_executor.py, async_judge.py, the P3 summary-build script) must copy
this exact pattern — a hardcoded LOCAL_TEST_THROTTLE boolean that forces a
3-item cap. Run the full workflow under throttle=True once, end to end,
before flipping to False for the real batch.
"""
import config

LOCAL_TEST_THROTTLE: bool = config.LOCAL_TEST_THROTTLE


def throttle_limit_clause() -> str:
    return f"LIMIT {config.THROTTLE_LIMIT}"


def apply_throttle(items: list) -> list:
    if LOCAL_TEST_THROTTLE:
        return items[: config.THROTTLE_LIMIT]
    return items
```

- [ ] **Step 4: Run test, confirm it passes**

Run: `cd /Users/ojaswi/Projects/rag-techniques/project && uv run pytest tests/test_loop_template.py -v`

Expected: `3 passed`

- [ ] **Step 5: Commit**

```bash
cd /Users/ojaswi/Projects/rag-techniques/project
git add loop_template.py tests/test_loop_template.py
git commit -m "feat: add reusable LOCAL_TEST_THROTTLE loop template"
```

---

### Task 5: Verified Groq rate limits — `groq_limits.md`

**Files:**
- Create: `project/groq_limits.md`

**Interfaces:**
- Consumes: `config.MODEL_ROUTING` (Task 1), `groq_client.call_groq` (Task 3) for the optional live smoke test.
- Produces: a dated markdown table later phases (3, 4, 7) read to pace TPD-bound loops. No function interface — pure documentation deliverable.

- [ ] **Step 1: [ACTIVE — human input required] Confirm a real `GROQ_API_KEY` exists**

This step cannot be scripted around: rate limits are account-specific and only visible after logging into `console.groq.com` with a real key. Ask the human:

> "I need a Groq API key to record verified rate limits in `groq_limits.md` (Phase 1 Goal 2 / Deliverable 4). Do you already have a `project/.env` with `GROQ_API_KEY` set, or should I wait while you create one? Steps: sign in at https://console.groq.com, open 'API Keys' in the sidebar, click 'Create API Key', copy the value into `project/.env` as `GROQ_API_KEY=...` (copy `.env.example` to `.env` first if you haven't)."

Do not proceed to Step 2 until the human confirms `project/.env` has a real key, or explicitly says to skip live verification and use published defaults instead (documented as an assumption in Step 3 if so).

- [ ] **Step 2: Check current published/account rate limits**

With the key in place, run: `cd /Users/ojaswi/Projects/rag-techniques/project && uv run python -c "
import asyncio, groq_client, config
async def main():
    for name, model in config.MODEL_ROUTING.items():
        if name == 'debug':
            continue
        resp = await groq_client.call_groq(model=model, messages=[{'role':'user','content':'hi'}])
        print(name, model, 'OK')
asyncio.run(main())
"`

Expected: prints `OK` for each of `generator`, `critic`, `p3_index_build`, `answerer`, `judge` — confirms each model ID is currently valid on the account. If a model name is rejected, note it (model IDs on Groq's free tier change; the spec (`Phase Plan.md` Goal 2) explicitly calls for re-verifying at implementation time).

Also visit https://console.groq.com/settings/limits (human step, since it's not exposed via API) and ask the human to paste the RPM/RPD/TPM/TPD numbers shown for each model, or take a screenshot.

- [ ] **Step 3: Write `groq_limits.md`**

```markdown
# Groq Rate Limits — Verified

Checked: 2026-07-21 (update this date whenever re-verified; limits are account-tier-dependent and change without notice).

| Stage | Model | RPM | RPD | TPM | TPD |
|---|---|---|---|---|---|
| Generator | openai/gpt-oss-120b | <paste> | <paste> | <paste> | <paste> |
| Critic | qwen/qwen3.6-27b | <paste> | <paste> | <paste> | <paste> |
| P3 index build | llama-3.1-8b-instant | <paste> | <paste> | <paste> | <paste> |
| Answerer | llama-3.3-70b-versatile | <paste> | <paste> | <paste> | <paste> |
| Judge | qwen/qwen3.6-27b | <paste> | <paste> | <paste> | <paste> |

Notes:
- Limits apply **per organization**, not per key — extra keys do not raise the ceiling (`Guardrails.md` §5).
- The Answerer (`Llama 3.3 70B`) is the tightest TPD budget; Phase 7's 900-run matrix is paced around this ceiling (`Phase Plan.md` §Phase 7).
- Re-check at https://console.groq.com/settings/limits before Phase 7 kicks off — free-tier limits are revised periodically.
```

Leave `<paste>` placeholders if Step 2's human screenshot/paste hasn't arrived yet — this is a **[PASSIVE]** gap: later phases can start without it, but Phase 7 pacing needs real numbers before the full 900-run matrix launches. Flag this explicitly in the Task 7 report.

- [ ] **Step 4: Commit**

```bash
cd /Users/ojaswi/Projects/rag-techniques/project
git add groq_limits.md
git commit -m "docs: record verified Groq per-model rate limits"
```

---

### Task 6: End-to-end Phase 1 verification

**Files:**
- No new files — runs everything Tasks 1-4 built.

**Interfaces:**
- Consumes: `config.py`, `database_manager.py`, `groq_client.py`, `loop_template.py`, all test files from Tasks 1-4.
- Produces: nothing new; this task is the fresh-clone smoke test from Phase 1's own Evaluation criteria (`Phase Plan.md` Evaluations 1-2).

- [ ] **Step 1: Simulate a fresh clone install**

Run:
```bash
cd /Users/ojaswi/Projects/rag-techniques/project
rm -rf .venv
uv sync
```

Expected: exits 0, `.venv/` recreated, no dependency conflicts printed.

- [ ] **Step 2: Run the full Phase 1 test suite**

Run: `cd /Users/ojaswi/Projects/rag-techniques/project && uv run pytest tests/ -v`

Expected: all tests from Tasks 1-4 pass (`config`, `database_manager`, `groq_client_backoff`, `loop_template`) — 16 passed total (5 + 6 + 2 + 3).

- [ ] **Step 3: Confirm the disjoint-set constraint holds at the schema level**

Run:
```bash
cd /Users/ojaswi/Projects/rag-techniques/project && uv run python -c "
import asyncio, database_manager as dbm
async def main():
    await dbm.init_db('smoke_test.db')
    print('five tables created OK')
asyncio.run(main())
"
rm -f /Users/ojaswi/Projects/rag-techniques/project/smoke_test.db*
```

Expected: prints `five tables created OK`, no errors.

- [ ] **Step 4: Commit (only if Step 1's `uv sync` changed the lockfile)**

```bash
cd /Users/ojaswi/Projects/rag-techniques/project
git status --short
# If uv.lock changed:
git add uv.lock
git commit -m "chore: refresh lockfile after clean-install verification"
```

---

### Task 7: Human Action Report

**Files:**
- Create: `temp/phase1-human-actions.md`

**Interfaces:**
- Consumes: the actual outcomes of Task 5 Step 1 (was a real key already present, or did the human provide one mid-plan?) and Task 5 Step 3 (were real limits pasted in, or left as placeholders?).
- Produces: a human-readable report — no code interface.

- [ ] **Step 1: Write the report reflecting what actually happened**

Write `temp/phase1-human-actions.md` using this structure, filling the bracketed parts from the real Task 5 outcome (do not leave placeholder text in the final file — resolve every bracket before committing):

```markdown
# Phase 1 — Human Action Report

Generated after Phase 1 build. Two categories below: things already done
during the build (passive) and things still blocking full completion
(active, need your input).

## Active — needs your input before Phase 1 is fully closed out

- [ ] **Groq API key**: [state whether project/.env has a real GROQ_API_KEY
  as of Task 5 Step 1 — if not, give the exact steps: sign in at
  https://console.groq.com, "API Keys" in sidebar, "Create API Key", paste
  into project/.env as GROQ_API_KEY=...]
- [ ] **Groq rate-limit numbers**: [state whether groq_limits.md's <paste>
  placeholders were filled from https://console.groq.com/settings/limits
  — if not, this blocks Phase 7 pacing decisions, not Phase 1-6 work]

## Passive — already handled, no action needed unless you want to change it

- `project/.env.example` was created with placeholder keys and setup
  instructions for both GROQ_API_KEY and LLAMA_CLOUD_API_KEY (the latter
  needed from Phase 2 onward, not Phase 1).
- `LOCAL_TEST_THROTTLE` defaults to `true` in `.env.example` — every future
  loop script inherits this safe default until you explicitly flip it.
- Five-table SQLite schema, WAL mode, and the resilient Groq client
  (backoff + 5-worker semaphore) are built and test-covered — no further
  setup needed for Phases 2 onward to start consuming them.

## Not yet needed (deferred to their own phase)

- LlamaParse account/key: needed starting Phase 2 (ingestion). Get one at
  https://cloud.llamaindex.ai/api-key.
- Filing manifest (exact tickers/fiscal years): needed starting Phase 2 —
  Architecture.md §11 flags this as still open (illustrative AAPL/MSFT/TSLA
  example only, not a real decision yet).
```

- [ ] **Step 2: Commit**

```bash
cd /Users/ojaswi/Projects/rag-techniques/rag-techniques
git add temp/phase1-human-actions.md
git commit -m "docs: add Phase 1 human action report"
```

Note: run this `git add`/`git commit` from the repo root (`/Users/ojaswi/Projects/rag-techniques`), not from `project/` — `temp/` is a root-level directory, not part of the `project/` subtree.

---

## Self-Review Notes

- **Spec coverage**: Phase Plan.md Phase 1 Goals 1-5 map to Tasks 1 (versions), 5 (Groq key + limits), 2 (five tables), 3 (backoff + semaphore), 4 (throttle template) respectively. Evaluations 1-4 map to Task 6 (fresh clone + schema check), Task 2 Step 5 (schema test), Task 3 (429 test), Task 5 (limits recorded with date). Deliverables 1-4 map to Task 1 (pinned repo), Task 2 (db_manager + db), Task 3+4 (client + template), Task 5 (groq_limits.md).
- **Placeholder scan**: `groq_limits.md`'s `<paste>` cells are an intentional, explicitly-flagged exception (real numbers require a live human-owned account lookup, not a scriptable fact) — surfaced in Task 7's Active list, not silently left.
- **Type consistency**: `database_manager` function names (`insert_node`, `get_nodes_by_document`, `upsert_result`, `get_completed_keys`) match `Architecture.md` §4.1 exactly; `call_groq` signature matches how Task 5's smoke test and all later phases will invoke it.

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-07-21-phase1-environment-infra.md`. Two execution options:

1. **Subagent-Driven (recommended)** — I dispatch a fresh subagent per task, review between tasks, fast iteration.
2. **Inline Execution** — Execute tasks in this session using executing-plans, batch execution with checkpoints.

Which approach?
