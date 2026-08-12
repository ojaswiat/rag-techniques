# Phase 7: Full Benchmark Execution Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Run the 900-cell PQ benchmark and score every output with the validated Judge plus deterministic code metrics, resumably and paced for the free tier.

**Architecture:** Reuse Phase 5 `loop_executor` for generation (retrieval + shared Answerer) and Phase 6 `async_judge`/`metrics` for scoring. Generalize the JEQ-only judging path to also score PQ rows (ground truth read from the `queries` table), make judging resumable (skip already-scored rows), add a per-invocation pacing cap, and guard against the Judge model changing mid-run. A thin `run_benchmark.py` orchestrates generation then judging.

**Tech Stack:** Python 3, `aiosqlite` (SQLite WAL), `llama-index` OpenAILike clients (Groq), `pytest` + `pytest-asyncio` (`asyncio_mode = "auto"`).

## Global Constraints

Copied verbatim from `resources/specs/Guardrails.md` — every task's requirements implicitly include these:

- All benchmark LLM calls run at `temperature = 0`. Each cell runs once (no repeated sampling).
- Judge model is `qwen/qwen3.6-27b` (Groq), and must stay a different family from the Answerer `llama-3.3-70b-versatile`. Judge has no search tool.
- Judge few-shot uses exactly the 5 `golden_queries` exemplars matching the row's quadrant, never all 20. JEQ rows are never used as exemplars.
- Citation matching is deterministic code, never delegated to the Judge.
- Every loop script contains a hardcoded `LOCAL_TEST_THROTTLE` boolean (from `loop_template.py`) forcing a 3-item cap; run clean end-to-end at throttle before the full batch.
- Resumability rests on `results.UNIQUE(source_set, query_id, pipeline, k_value)`; a crash must never re-spend free-tier quota or duplicate rows.
- Work directory is `project/`. Code goes under `project/`. Do not modify `resources/` unless explicitly told. No dev-history comments in code (narrative goes in commit messages / `resources/research/`).
- Build against fixtures/temp DBs only. Do NOT touch the real `benchmark.db`. Stop and get explicit approval before any live/real-data run.
- No schema change on the shared DB (migrations are risky while Phase 4 writes). All new DB access is additive functions only.

**Working baseline:** full suite is green at `337 passed, 2 skipped` (`cd project && uv run pytest -q`). Keep it green after every task.

---

## File Structure

- `project/database_manager.py` (modify) — add `get_judging_rows(db_path, source_set, *, only_unscored=True)`; keep `get_jeq_judging_rows` as a thin wrapper.
- `project/judge/async_judge.py` (modify) — add `judge_rows(db_path, source_set, judge=None, *, max_cells=None, only_unscored=True)`; keep `judge_jeq_rows` as a wrapper. Reuse existing `build_prefix`, `compute_deterministic_metrics`, `Judge`, `parse_judge_score` unchanged.
- `project/loop_executor.py` (modify) — add `max_cells: int | None = None` to `main`, slicing cells after `apply_throttle`.
- `project/run_benchmark.py` (create) — Phase 7 orchestrator: judge-model preflight, generation, judging, CLI.
- `project/tests/test_database_manager_judge.py` (modify) — tests for `get_judging_rows` PQ path + resume filter.
- `project/tests/test_async_judge.py` (modify) — tests for `judge_rows` PQ + resume + pacing.
- `project/tests/test_loop_executor.py` (modify) — test for `max_cells`.
- `project/tests/test_run_benchmark.py` (create) — orchestrator + preflight tests.
- `project/tests/test_run_benchmark_live_smoke.py` (create) — one gated live PQ-judging smoke test.
- `resources/research/deviations.md` (modify) — EM-label clarification note (documentation).

---

### Task 1: Generalize the judging reader for PQ and add resume filter

**Files:**
- Modify: `project/database_manager.py` (the `get_jeq_judging_rows` region, around L360-L400)
- Test: `project/tests/test_database_manager_judge.py`

**Interfaces:**
- Consumes: existing `_loads`, `upsert_result`, `insert_judge_validation`, `insert_query`, `update_result_scores` in `database_manager.py`.
- Produces:
  - `async def get_judging_rows(db_path: str, source_set: str, *, only_unscored: bool = True) -> list[dict]` — JEQ→`judge_validation`, PQ→`queries`; each row is the `results` row joined to `quadrant`, `query_text`, `ground_truth_answer`, `gt_citations`, `document_id`, with `retrieved_node_ids`/`cited_node_ids`/`gt_citations` decoded to `list[str]`; when `only_unscored`, rows with a non-NULL `judge_score` are excluded.
  - `async def get_jeq_judging_rows(db_path: str) -> list[dict]` — unchanged signature, now delegates to `get_judging_rows(db_path, "JEQ")`.

- [ ] **Step 1: Write the failing tests**

Add to `project/tests/test_database_manager_judge.py`. Reuse the module's existing `clean_db` fixture, `_jeq`, `_result_row`, and add a PQ helper.

```python
def _pq(query_id, quadrant, doc="SEC_10K_AAPL_2025"):
    return {
        "query_id": query_id,
        "quadrant": quadrant,
        "query_text": f"pq question for {query_id}?",
        "ground_truth_answer": "$394.3B",
        "gt_citations": ["AAPL_2025_n0421"],
        "document_id": doc,
        "verified": 1,
    }


@pytest.mark.asyncio
async def test_get_judging_rows_pq_joins_queries_table():
    await dbm.init_db(TEST_DB)
    await dbm.insert_query(TEST_DB, _pq("PQ_001", "Q1_Direct_Text"))
    pq_row = _result_row("R_PQ_1", "PQ_001", "P1_vector")
    pq_row["source_set"] = "PQ"
    await dbm.upsert_result(TEST_DB, pq_row)

    rows = await dbm.get_judging_rows(TEST_DB, "PQ")

    assert len(rows) == 1
    row = rows[0]
    assert row["result_id"] == "R_PQ_1"
    assert row["quadrant"] == "Q1_Direct_Text"
    assert row["ground_truth_answer"] == "$394.3B"
    assert row["gt_citations"] == ["AAPL_2025_n0421"]
    assert row["retrieved_node_ids"] == ["AAPL_2025_n0421", "AAPL_2025_n0420"]


@pytest.mark.asyncio
async def test_get_judging_rows_only_unscored_by_default():
    await dbm.init_db(TEST_DB)
    await dbm.insert_query(TEST_DB, _pq("PQ_001", "Q1_Direct_Text"))
    await dbm.insert_query(TEST_DB, _pq("PQ_002", "Q1_Direct_Text"))
    for rid, qid in (("R1", "PQ_001"), ("R2", "PQ_002")):
        r = _result_row(rid, qid, "P1_vector")
        r["source_set"] = "PQ"
        await dbm.upsert_result(TEST_DB, r)
    await dbm.update_result_scores(TEST_DB, "R1", {"judge_score": 8})

    unscored = await dbm.get_judging_rows(TEST_DB, "PQ")
    assert {r["result_id"] for r in unscored} == {"R2"}

    everything = await dbm.get_judging_rows(TEST_DB, "PQ", only_unscored=False)
    assert {r["result_id"] for r in everything} == {"R1", "R2"}


@pytest.mark.asyncio
async def test_get_judging_rows_rejects_unknown_source_set():
    await dbm.init_db(TEST_DB)
    with pytest.raises(ValueError, match="source_set"):
        await dbm.get_judging_rows(TEST_DB, "GQ")


@pytest.mark.asyncio
async def test_get_jeq_judging_rows_still_works():
    await dbm.init_db(TEST_DB)
    await dbm.insert_judge_validation(TEST_DB, _jeq("JEQ_001", "Q3_Direct_Table"))
    await dbm.upsert_result(TEST_DB, _result_row("R1", "JEQ_001", "P1_vector"))
    rows = await dbm.get_jeq_judging_rows(TEST_DB)
    assert rows[0]["quadrant"] == "Q3_Direct_Table"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd project && uv run pytest tests/test_database_manager_judge.py -k "judging_rows" -v`
Expected: FAIL — `get_judging_rows` does not exist (AttributeError).

- [ ] **Step 3: Implement `get_judging_rows` and rewrite `get_jeq_judging_rows` as a wrapper**

In `project/database_manager.py`, replace the existing `get_jeq_judging_rows` function with:

```python
_JUDGING_SOURCE_TABLES = {"PQ": "queries", "JEQ": "judge_validation"}


async def get_judging_rows(db_path: str, source_set: str, *, only_unscored: bool = True) -> list[dict]:
    """results rows for one source_set, joined to their ground truth for judging.

    The ground truth for a PQ row lives in `queries`; for a JEQ row it lives in
    `judge_validation`. Both carry the same quadrant/query/answer/citation
    columns, so one join shape serves both. With only_unscored (the default), a
    row that already has a judge_score is skipped -- the resume path for a
    multi-day judging run, so a restart never re-spends quota on a scored row.
    JSON list columns from both tables are decoded to list[str].
    """
    try:
        table = _JUDGING_SOURCE_TABLES[source_set]
    except KeyError as exc:
        raise ValueError(
            f"source_set must be one of {sorted(_JUDGING_SOURCE_TABLES)}, got {source_set!r}"
        ) from exc

    sql = f"""SELECT r.*, t.quadrant, t.query_text, t.ground_truth_answer,
                     t.gt_citations, t.document_id
              FROM results r
              JOIN {table} t ON t.query_id = r.query_id
              WHERE r.source_set = ?"""
    if only_unscored:
        sql += " AND r.judge_score IS NULL"
    sql += " ORDER BY r.result_id"

    async with aiosqlite.connect(db_path) as conn:
        conn.row_factory = aiosqlite.Row
        cursor = await conn.execute(sql, (source_set,))
        rows = await cursor.fetchall()
    result = []
    for row in rows:
        d = dict(row)
        d["retrieved_node_ids"] = _loads(d["retrieved_node_ids"])
        d["cited_node_ids"] = _loads(d["cited_node_ids"])
        d["gt_citations"] = _loads(d["gt_citations"])
        result.append(d)
    return result


async def get_jeq_judging_rows(db_path: str) -> list[dict]:
    """The JEQ gate rows joined to their ground truth (Phase 6 gate).

    Thin wrapper over get_judging_rows so the Phase 6 callers keep their exact
    signature; only_unscored stays True so re-running the gate skips rows the
    Judge already scored.
    """
    return await get_judging_rows(db_path, "JEQ")
```

Note: `source_set` is bound as a query parameter and `table` comes from a fixed whitelist dict, so no user input reaches the SQL string directly.

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd project && uv run pytest tests/test_database_manager_judge.py -v`
Expected: PASS (all prior + new tests).

- [ ] **Step 5: Commit**

```bash
git add project/database_manager.py project/tests/test_database_manager_judge.py
git commit -m "feat(phase7): generalize judging reader to PQ and add resume filter

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 2: Generalize async_judge to judge any source_set, resumably, with a pacing cap

**Files:**
- Modify: `project/judge/async_judge.py` (the `judge_jeq_rows` region, around L170-L215)
- Test: `project/tests/test_async_judge.py`

**Interfaces:**
- Consumes: `get_judging_rows` (Task 1); existing `Judge`, `build_prefix`, `compute_deterministic_metrics` in this module; `apply_throttle`, `LOCAL_TEST_THROTTLE` from `loop_template`; `dbm.get_golden_queries_by_quadrant`, `dbm.update_result_scores`.
- Produces:
  - `async def judge_rows(db_path: str, source_set: str, judge: Judge | None = None, *, max_cells: int | None = None, only_unscored: bool = True) -> dict` — returns `{"source_set", "judged", "attempted", "failures"}`; scores each row's deterministic metrics + `judge_score` and writes them in one `update_result_scores` call.
  - `async def judge_jeq_rows(db_path: str, judge: Judge | None = None) -> dict` — wrapper delegating to `judge_rows(db_path, "JEQ", judge)`.

- [ ] **Step 1: Write the failing tests**

Add to `project/tests/test_async_judge.py` (reuse existing `clean_db`, `_fake_judge_client`, `_row`, `_exemplar`, and the `insert_judge_validation`/`insert_golden_query`/`upsert_result` seeding pattern from `test_judge_jeq_rows_scores_and_writes`). Add a small PQ seeding helper at module level:

```python
async def _seed_pq(db_path, result_id, query_id, quadrant="Q3_Direct_Table"):
    await dbm.insert_query(db_path, {
        "query_id": query_id, "quadrant": quadrant,
        "query_text": "What were FY2025 net sales?",
        "ground_truth_answer": "$394.3B",
        "gt_citations": ["AAPL_2025_n0421"],
        "document_id": "SEC_10K_AAPL_2025", "verified": 1,
    })
    row = {
        "result_id": result_id, "source_set": "PQ", "query_id": query_id,
        "pipeline": "P1_vector", "k_value": 5,
        "retrieved_node_ids": ["AAPL_2025_n0421", "AAPL_2025_n0420"],
        "pipeline_output": "Net sales were $394.3B. [[node:AAPL_2025_n0421]]",
        "cited_node_ids": ["AAPL_2025_n0421"],
    }
    await dbm.upsert_result(db_path, row)


@pytest.mark.asyncio
async def test_judge_rows_scores_pq_from_queries_table(monkeypatch):
    monkeypatch.setattr(async_judge, "LOCAL_TEST_THROTTLE", False, raising=False)
    await dbm.init_db(TEST_DB)
    for i in range(5):
        await dbm.insert_golden_query(TEST_DB, _exemplar(f"GQ_T3_{i}", "Q3_Direct_Table"))
    await _seed_pq(TEST_DB, "R_PQ_1", "PQ_001")

    client = _fake_judge_client('{"score": 9}')
    with patch("judge.async_judge.LLMFactory.get_client_for_stage", return_value=client):
        summary = await async_judge.judge_rows(TEST_DB, "PQ")

    assert summary["source_set"] == "PQ"
    assert summary["judged"] == 1
    row = next(r for r in await dbm.get_results(TEST_DB, "PQ") if r["result_id"] == "R_PQ_1")
    assert row["judge_score"] == 9
    assert row["precision_at_k"] == 0.2
    assert row["exact_match"] == 1


@pytest.mark.asyncio
async def test_judge_rows_skips_already_scored(monkeypatch):
    monkeypatch.setattr(async_judge, "LOCAL_TEST_THROTTLE", False, raising=False)
    await dbm.init_db(TEST_DB)
    for i in range(5):
        await dbm.insert_golden_query(TEST_DB, _exemplar(f"GQ_T3_{i}", "Q3_Direct_Table"))
    await _seed_pq(TEST_DB, "R1", "PQ_001")
    await _seed_pq(TEST_DB, "R2", "PQ_002")
    await dbm.update_result_scores(TEST_DB, "R1", {"judge_score": 5})  # pre-scored

    client = _fake_judge_client('{"score": 9}')
    with patch("judge.async_judge.LLMFactory.get_client_for_stage", return_value=client):
        summary = await async_judge.judge_rows(TEST_DB, "PQ")

    assert summary["judged"] == 1  # only R2
    rows = {r["result_id"]: r for r in await dbm.get_results(TEST_DB, "PQ")}
    assert rows["R1"]["judge_score"] == 5   # untouched
    assert rows["R2"]["judge_score"] == 9


@pytest.mark.asyncio
async def test_judge_rows_max_cells_caps_one_invocation(monkeypatch):
    monkeypatch.setattr(async_judge, "LOCAL_TEST_THROTTLE", False, raising=False)
    await dbm.init_db(TEST_DB)
    for i in range(5):
        await dbm.insert_golden_query(TEST_DB, _exemplar(f"GQ_T3_{i}", "Q3_Direct_Table"))
    for i in range(3):
        await _seed_pq(TEST_DB, f"R{i}", f"PQ_00{i}")

    client = _fake_judge_client('{"score": 7}')
    with patch("judge.async_judge.LLMFactory.get_client_for_stage", return_value=client):
        summary = await async_judge.judge_rows(TEST_DB, "PQ", max_cells=1)

    assert summary["judged"] == 1
    remaining = await dbm.get_judging_rows(TEST_DB, "PQ")  # only_unscored
    assert len(remaining) == 2  # two still to do -> resumable
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd project && uv run pytest tests/test_async_judge.py -k "judge_rows" -v`
Expected: FAIL — `judge_rows` does not exist (AttributeError).

- [ ] **Step 3: Rewrite the batch loop as `judge_rows`, keep `judge_jeq_rows` wrapper**

In `project/judge/async_judge.py`, replace the existing `judge_jeq_rows` function with:

```python
async def judge_rows(
    db_path: str,
    source_set: str,
    judge: Judge | None = None,
    *,
    max_cells: int | None = None,
    only_unscored: bool = True,
) -> dict:
    """Score every outstanding row of one source_set: metrics + judge_score.

    Reads the rows joined to their ground truth (PQ from queries, JEQ from
    judge_validation), builds each quadrant's cacheable prefix once, then
    scores the rows and writes the full metric vector back per row. Two safety
    controls for the multi-day full run: only_unscored skips rows the Judge has
    already scored (resume), and max_cells caps how many rows one invocation
    processes (TPD pacing). LOCAL_TEST_THROTTLE still forces a 3-row cap on top
    of both (Guardrails Section 7).
    """
    if judge is None:
        judge = Judge()

    rows = await dbm.get_judging_rows(db_path, source_set, only_unscored=only_unscored)
    rows = apply_throttle(rows)
    if max_cells is not None:
        rows = rows[:max_cells]

    prefixes: dict[str, str] = {}
    for quadrant in {row["quadrant"] for row in rows}:
        exemplars = await dbm.get_golden_queries_by_quadrant(db_path, quadrant)
        prefixes[quadrant] = build_prefix(quadrant, exemplars)

    logger.info(
        "judging %d %s row(s)%s",
        len(rows),
        source_set,
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

    outcomes = await asyncio.gather(
        *(_score_and_write(row) for row in rows), return_exceptions=True
    )
    for row, outcome in zip(rows, outcomes):
        if isinstance(outcome, Exception):
            logger.exception("judging failed for result_id=%s", row["result_id"], exc_info=outcome)
            failures.append({"result_id": row["result_id"], "error": str(outcome)})

    return {"source_set": source_set, "judged": judged, "attempted": len(rows), "failures": failures}


async def judge_jeq_rows(db_path: str, judge: Judge | None = None) -> dict:
    """Score the 60 JEQ gate rows (Phase 6). Wrapper over judge_rows."""
    return await judge_rows(db_path, "JEQ", judge)
```

Update `__all__` to add `"judge_rows"` (keep `"judge_jeq_rows"`).

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd project && uv run pytest tests/test_async_judge.py -v`
Expected: PASS (existing `judge_jeq_rows` test still green via the wrapper, plus the three new ones).

- [ ] **Step 5: Commit**

```bash
git add project/judge/async_judge.py project/tests/test_async_judge.py
git commit -m "feat(phase7): judge_rows for any source_set with resume and pacing cap

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 3: Add a per-invocation pacing cap to loop_executor

**Files:**
- Modify: `project/loop_executor.py` (the `main` function, L110-L179)
- Test: `project/tests/test_loop_executor.py`

**Interfaces:**
- Consumes: existing `build_cells`, `apply_throttle`, `run_cell`, `dbm.get_queries`, `dbm.get_completed_keys`.
- Produces: `main(..., k_values=K_VALUES, max_cells: int | None = None)` — after throttle, at most `max_cells` cells run this invocation; the rest stay outstanding for the next run (resume via `get_completed_keys`).

- [ ] **Step 1: Write the failing test**

Add to `project/tests/test_loop_executor.py`, following the module's existing fake-retriever / fake-answerer / temp-DB pattern (mirror the closest existing `main` test for seeding queries and building a fake `Answerer`).

```python
@pytest.mark.asyncio
async def test_main_max_cells_caps_invocation(monkeypatch, tmp_path):
    import loop_executor
    monkeypatch.setattr(loop_executor.config, "LOCAL_TEST_THROTTLE", False, raising=False)
    monkeypatch.setattr("loop_template.LOCAL_TEST_THROTTLE", False, raising=False)

    db_path = str(tmp_path / "cap.db")
    await dbm.init_db(db_path)
    # three PQ queries, one pipeline, one K -> 3 outstanding cells
    for i in range(3):
        await dbm.insert_query(db_path, {
            "query_id": f"PQ_00{i}", "quadrant": "Q1_Direct_Text",
            "query_text": "q", "ground_truth_answer": "a",
            "gt_citations": ["n1"], "document_id": "DOC", "verified": 1,
        })

    summary = await loop_executor.main(
        db_path=db_path, source_set="PQ",
        retrievers={"P1_vector": _FakeRetriever()},
        answerer=_FakeAnswerer(),
        k_values=(5,), max_cells=2,
    )

    assert summary["attempted"] == 2
    completed = await dbm.get_completed_keys(db_path, "PQ")
    assert len(completed) == 2  # one cell remains for the next invocation
```

If `_FakeRetriever` / `_FakeAnswerer` do not already exist in the test file, add minimal versions: a retriever whose `retrieve()` returns one `NodeWithScore`, and an `Answerer`-shaped object whose `answer()` returns an `AnswerResult` with fixed text/tokens (mirror `test_answerer.py`'s node construction).

- [ ] **Step 2: Run test to verify it fails**

Run: `cd project && uv run pytest tests/test_loop_executor.py::test_main_max_cells_caps_invocation -v`
Expected: FAIL — `main()` got an unexpected keyword argument `max_cells`.

- [ ] **Step 3: Add the `max_cells` parameter and slice**

In `project/loop_executor.py`, change the `main` signature to add `max_cells: int | None = None`, and immediately after the existing `cells = apply_throttle(cells)` line insert:

```python
    # Pacing cap for the multi-day full run: process at most max_cells this
    # invocation; the remainder stays outstanding and is picked up next run
    # through the ordinary get_completed_keys resume path.
    if max_cells is not None:
        cells = cells[:max_cells]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd project && uv run pytest tests/test_loop_executor.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add project/loop_executor.py project/tests/test_loop_executor.py
git commit -m "feat(phase7): add max_cells pacing cap to loop_executor.main

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 4: Judge-model drift guard (sidecar + preflight)

**Files:**
- Create: `project/run_benchmark.py` (this task adds only the preflight helpers; Task 5 adds the orchestrator to the same file)
- Test: `project/tests/test_run_benchmark.py`

**Interfaces:**
- Consumes: `llm_client.config.MODEL_ROUTING`.
- Produces:
  - `def run_meta_path(db_path: str) -> str` — returns `db_path + ".run_meta.json"`.
  - `def check_judge_model(db_path: str) -> str` — on first call writes `{"judge_model": <routed>}` and returns it; on later calls raises `SystemExit` if the routed judge model differs from the recorded one, else returns the recorded model.

- [ ] **Step 1: Write the failing tests**

Create `project/tests/test_run_benchmark.py`:

```python
import json
import os

import pytest

import llm_client.config as config
import run_benchmark

META_DB = "test_run_benchmark.db"


@pytest.fixture(autouse=True)
def clean():
    for p in (META_DB, run_benchmark.run_meta_path(META_DB)):
        if os.path.exists(p):
            os.remove(p)
    yield
    for p in (META_DB, run_benchmark.run_meta_path(META_DB)):
        if os.path.exists(p):
            os.remove(p)


def test_check_judge_model_records_on_first_run():
    model = run_benchmark.check_judge_model(META_DB)
    assert model == config.MODEL_ROUTING["judge"]["model"]
    with open(run_benchmark.run_meta_path(META_DB)) as fh:
        assert json.load(fh)["judge_model"] == model


def test_check_judge_model_passes_when_unchanged():
    run_benchmark.check_judge_model(META_DB)
    assert run_benchmark.check_judge_model(META_DB) == config.MODEL_ROUTING["judge"]["model"]


def test_check_judge_model_raises_on_change(monkeypatch):
    run_benchmark.check_judge_model(META_DB)  # records current
    monkeypatch.setitem(config.MODEL_ROUTING, "judge", {"model": "other/model", "provider": "groq"})
    with pytest.raises(SystemExit, match="judge model changed"):
        run_benchmark.check_judge_model(META_DB)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd project && uv run pytest tests/test_run_benchmark.py -v`
Expected: FAIL — `No module named 'run_benchmark'`.

- [ ] **Step 3: Create `run_benchmark.py` with the preflight helpers**

Create `project/run_benchmark.py`:

```python
"""Phase 7 full-benchmark orchestrator (resPphase Plan Phase 7).

Runs the 900 PQ cells through P1/P2/P3 at K in {3,5,10} via loop_executor,
then scores every outstanding row with the validated Judge via async_judge.
Both stages are resumable and honour LOCAL_TEST_THROTTLE; a per-invocation
--max-cells cap paces the token-heavy work across days for the free tier.

A judge-model preflight guards the calibration: the validation gate proved the
Judge against the human standard for one specific model, so if the routed
judge model changes mid-run (this project has already lost a model to provider
withdrawal), the run stops and the gate must be re-run rather than silently
grading 900 outputs with an unvalidated judge.
"""
import argparse
import asyncio
import json
import logging
import os

import llm_client.config as config

logger = logging.getLogger(__name__)


def run_meta_path(db_path: str) -> str:
    """Sidecar file next to the DB; no schema change on the shared database."""
    return db_path + ".run_meta.json"


def check_judge_model(db_path: str) -> str:
    """Record the judge model on first run; refuse to continue if it changed.

    The gate validated one specific judge model. A different model later is a
    different, unvalidated instrument, so this stops rather than grade with it.
    """
    routed = config.MODEL_ROUTING["judge"]["model"]
    path = run_meta_path(db_path)
    if not os.path.exists(path):
        with open(path, "w") as fh:
            json.dump({"judge_model": routed}, fh)
        logger.info("recorded judge model for this run: %s", routed)
        return routed

    with open(path) as fh:
        recorded = json.load(fh)["judge_model"]
    if recorded != routed:
        raise SystemExit(
            f"judge model changed since the gate ({recorded!r} -> {routed!r}); "
            "re-run the validation gate before continuing the benchmark"
        )
    return recorded
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd project && uv run pytest tests/test_run_benchmark.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add project/run_benchmark.py project/tests/test_run_benchmark.py
git commit -m "feat(phase7): judge-model drift preflight via sidecar meta file

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 5: Orchestrator — generation then judging, paced and resumable

**Files:**
- Modify: `project/run_benchmark.py` (add `run_benchmark`, arg parsing, `__main__`)
- Test: `project/tests/test_run_benchmark.py`

**Interfaces:**
- Consumes: `check_judge_model` (Task 4); `loop_executor.main`, `loop_executor.build_retrievers`, `loop_executor.PIPELINES`; `judge.async_judge.judge_rows` (Task 2).
- Produces: `async def run_benchmark(db_path: str, retrievers=None, answerer=None, judge=None, *, k_values=(3, 5, 10), max_cells: int | None = None) -> dict` — returns `{"generation": <loop_executor summary>, "judging": <judge_rows summary>}`. Runs `check_judge_model` first, then generation (`source_set="PQ"`), then `judge_rows(db_path, "PQ", ...)`.

- [ ] **Step 1: Write the failing tests**

Add to `project/tests/test_run_benchmark.py`:

```python
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.mark.asyncio
async def test_run_benchmark_generates_pq_then_judges():
    retrievers = {"P1_vector": MagicMock(), "P2_bm25": MagicMock(), "P3_structural": MagicMock()}
    with patch.object(run_benchmark, "check_judge_model", return_value="qwen/qwen3.6-27b") as pre, \
         patch.object(run_benchmark.loop_executor, "main", new=AsyncMock(return_value={"completed": 900})) as gen, \
         patch.object(run_benchmark, "judge_rows", new=AsyncMock(return_value={"judged": 900})) as judge:
        summary = await run_benchmark.run_benchmark(META_DB, retrievers=retrievers, max_cells=150)

    pre.assert_called_once_with(META_DB)
    gk = gen.await_args.kwargs
    assert gk["source_set"] == "PQ"
    assert gk["k_values"] == (3, 5, 10)
    assert gk["max_cells"] == 150
    assert gk["retrievers"] is retrievers
    jk_args, jk_kwargs = judge.await_args.args, judge.await_args.kwargs
    assert jk_args[0] == META_DB and jk_args[1] == "PQ"
    assert jk_kwargs["max_cells"] == 150
    assert summary["generation"] == {"completed": 900}
    assert summary["judging"] == {"judged": 900}


@pytest.mark.asyncio
async def test_run_benchmark_defaults_to_all_three_pipelines():
    built = {"P1_vector": MagicMock(), "P2_bm25": MagicMock(), "P3_structural": MagicMock()}
    with patch.object(run_benchmark, "check_judge_model", return_value="qwen/qwen3.6-27b"), \
         patch.object(run_benchmark.loop_executor, "build_retrievers", return_value=built) as build, \
         patch.object(run_benchmark.loop_executor, "main", new=AsyncMock(return_value={})), \
         patch.object(run_benchmark, "judge_rows", new=AsyncMock(return_value={})):
        await run_benchmark.run_benchmark(META_DB)
    assert set(build.call_args.args[0]) == {"P1_vector", "P2_bm25", "P3_structural"}


@pytest.mark.asyncio
async def test_run_benchmark_stops_if_judge_model_changed():
    with patch.object(run_benchmark, "check_judge_model", side_effect=SystemExit("judge model changed")), \
         patch.object(run_benchmark.loop_executor, "main", new=AsyncMock()) as gen:
        with pytest.raises(SystemExit):
            await run_benchmark.run_benchmark(META_DB, retrievers={"P1_vector": MagicMock()})
    gen.assert_not_awaited()  # preflight blocks before any generation
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd project && uv run pytest tests/test_run_benchmark.py -k run_benchmark -v`
Expected: FAIL — `run_benchmark` module has no attribute `run_benchmark` / `loop_executor`.

- [ ] **Step 3: Add the orchestrator, imports, and CLI**

In `project/run_benchmark.py`, add these imports near the top (after `import llm_client.config as config`):

```python
import loop_executor
from judge.async_judge import judge_rows
from pipelines.answerer import Answerer
from pipelines.base import Retriever
```

Add the orchestrator function (after `check_judge_model`):

```python
async def run_benchmark(
    db_path: str,
    retrievers: dict[str, Retriever] | None = None,
    answerer: Answerer | None = None,
    judge=None,
    *,
    k_values: tuple[int, ...] = (3, 5, 10),
    max_cells: int | None = None,
) -> dict:
    """Full PQ benchmark: preflight, generate 900 cells, then judge them.

    Preflight runs first so a changed judge model stops the run before any
    quota is spent. Generation and judging are both resumable and both honour
    max_cells, so a daily `--max-cells N` invocation advances the run and the
    next day resumes where it stopped.
    """
    check_judge_model(db_path)

    if retrievers is None:
        retrievers = loop_executor.build_retrievers(list(loop_executor.PIPELINES))

    generation = await loop_executor.main(
        db_path=db_path,
        source_set="PQ",
        retrievers=retrievers,
        answerer=answerer,
        k_values=k_values,
        max_cells=max_cells,
    )
    judging = await judge_rows(db_path, "PQ", judge, max_cells=max_cells)

    logger.info(
        "benchmark: generated %s cell(s), judged %s row(s)",
        generation.get("completed"),
        judging.get("judged"),
    )
    return {"generation": generation, "judging": judging}
```

Add arg parsing and `__main__` at the bottom:

```python
def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db-path", default="benchmark.db")
    parser.add_argument("--pipelines", nargs="+",
                        default=list(loop_executor.PIPELINES),
                        choices=list(loop_executor.PIPELINES))
    parser.add_argument("--k-values", nargs="+", type=int, default=[3, 5, 10], choices=[3, 5, 10])
    parser.add_argument("--max-cells", type=int, default=None)
    return parser.parse_args(argv)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    args = _parse_args()
    summary = asyncio.run(
        run_benchmark(
            db_path=args.db_path,
            retrievers=loop_executor.build_retrievers(args.pipelines),
            k_values=tuple(args.k_values),
            max_cells=args.max_cells,
        )
    )
    print(summary)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd project && uv run pytest tests/test_run_benchmark.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add project/run_benchmark.py project/tests/test_run_benchmark.py
git commit -m "feat(phase7): full-benchmark orchestrator (generate then judge, paced)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 6: Live-smoke test for PQ judging (gated, skipped by default)

**Files:**
- Create: `project/tests/test_run_benchmark_live_smoke.py`

**Interfaces:**
- Consumes: `judge.async_judge.Judge`, `judge.async_judge.build_prefix`, `llm_client.config`.
- Produces: nothing importable — one gated test proving a real Qwen call scores a PQ-shaped row into a valid 1-10.

Note: this mirrors `tests/test_async_judge_live_smoke.py` exactly (frozen data, no DB, gated on `RUN_LIVE_GROQ_TESTS=1` and `config.GROQ_API_KEY`). Its value over the existing Phase 6 smoke is asserting the PQ code path end-to-end once real judging is wired; keep it minimal.

- [ ] **Step 1: Write the test**

Create `project/tests/test_run_benchmark_live_smoke.py`:

```python
"""ONE live, gated smoke test: a real Qwen judge call scores a PQ-shaped row.

Skipped by default; mirrors tests/test_async_judge_live_smoke.py. Requires
RUN_LIVE_GROQ_TESTS=1 and a real GROQ_API_KEY. Costs one Groq call per opt-in.
"""
import os

import pytest

import llm_client.config as config
from judge.async_judge import Judge, build_prefix

_RUN_LIVE = os.getenv("RUN_LIVE_GROQ_TESTS") == "1"

_EXEMPLAR = {
    "query_id": "GQ_T1_LIVE", "quadrant": "Q1_Direct_Text",
    "query_text": "Who is Apple's CEO?",
    "ground_truth_answer": "Tim Cook", "gt_citations": ["AAPL_2025_n0001"],
    "example_output": "The CEO is Tim Cook. [[node:AAPL_2025_n0001]]",
    "human_score": 90, "human_reasoning": "Correct and cited.",
    "is_good": 1, "document_id": "SEC_10K_AAPL_2025",
}

_PQ_ROW = {
    "result_id": "R_PQ_LIVE", "query_id": "PQ_LIVE", "pipeline": "P1_vector", "k_value": 5,
    "retrieved_node_ids": ["AAPL_2025_n0001"],
    "pipeline_output": "Apple's CEO is Tim Cook. [[node:AAPL_2025_n0001]]",
    "cited_node_ids": ["AAPL_2025_n0001"],
    "quadrant": "Q1_Direct_Text", "query_text": "Who is Apple's CEO?",
    "ground_truth_answer": "Tim Cook", "gt_citations": ["AAPL_2025_n0001"],
    "document_id": "SEC_10K_AAPL_2025",
}


@pytest.mark.live
@pytest.mark.skipif(not _RUN_LIVE, reason="Live Groq smoke test; set RUN_LIVE_GROQ_TESTS=1 to run.")
@pytest.mark.skipif(not config.GROQ_API_KEY, reason="No GROQ_API_KEY resolved via config.py.")
@pytest.mark.asyncio
async def test_pq_judging_live_round_trip():
    prefix = build_prefix("Q1_Direct_Text", [_EXEMPLAR])
    score = await Judge().score_row(_PQ_ROW, prefix)
    assert isinstance(score, int) and 1 <= score <= 10
```

- [ ] **Step 2: Run to verify it is skipped by default**

Run: `cd project && uv run pytest tests/test_run_benchmark_live_smoke.py -q`
Expected: `1 skipped`.

- [ ] **Step 3: Commit**

```bash
git add project/tests/test_run_benchmark_live_smoke.py
git commit -m "test(phase7): gated live smoke for PQ judging

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 7: Document the exact_match / containment label (documentation)

**Files:**
- Modify: `resources/research/deviations.md` (append to entry #26, or add a short clarification)

**Interfaces:** none (documentation only).

Rationale: the `exact_match` column implements numeric-tolerant containment, which the RAG-evaluation literature treats as distinct from strict Exact Match. The write-up must not let a reader assume strict string equality. No code or schema change — the column name is fixed and a migration on the shared DB is not warranted.

- [ ] **Step 1: Append the clarification note**

Add this paragraph under deviations.md entry #26 (point 5 or as a new trailing note). Use British English, no em-dashes (this is `resources/`):

```markdown
**Metric-label clarification (exact_match):** the `results.exact_match` column
stores a numeric-tolerant *containment* result, not strict string Exact Match.
For a numeric ground truth it is 1 when a figure normalising within +/-1% of the
ground truth appears anywhere in the answer; for a text ground truth it is 1 when
the answer contains the ground-truth phrase (case and punctuation insensitive).
The RAG-evaluation literature treats Exact Match (strict normalised equality)
and containment as different metrics, so the Phase 8 analysis and the
dissertation methods section must describe this column as "answer containment
(numeric-tolerant)" rather than strict Exact Match. The column name is retained
because the schema is fixed and a migration on the shared database is not
warranted for a naming change.
```

- [ ] **Step 2: Commit**

```bash
git add resources/research/deviations.md
git commit -m "docs(phase7): clarify exact_match column is numeric-tolerant containment

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 8: Full-suite verification and graphify refresh

**Files:** none (verification + generated artifact).

- [ ] **Step 1: Run the full suite**

Run: `cd project && uv run pytest -q`
Expected: all green; new count is the baseline (`337 passed, 2 skipped`) plus the new tests, with `3 skipped` (the added live smoke). Confirm zero failures before proceeding.

- [ ] **Step 2: Refresh the knowledge graph (run from repo ROOT, not project/)**

Run: `cd /Users/ojaswi/Projects/ragbench-phase6 && graphify update .`
Expected: `graph.json`, `GRAPH_REPORT.md` updated under the repo-root `graphify-out/`. Do NOT create a `project/graphify-out/`.

- [ ] **Step 3: Commit the graph refresh**

```bash
git add graphify-out
git commit -m "chore(graphify): refresh knowledge graph for Phase 7 modules

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

- [ ] **Step 4: Stop before any real run**

Do NOT run `run_benchmark.py` against the real `benchmark.db`. Report completion and hand back. The live run is a separate, explicitly-approved step that requires: the validation gate passed (>80%), `queries` populated with 100 PQ rows, and a clean throttled end-to-end dry run first.

---

## Self-Review

**1. Spec coverage (Phase Plan Phase 7 goals):**
- Goal 1 (900 PQ x pipelines x K, once, temp 0): Task 5 orchestrator drives `loop_executor` at `k_values=(3,5,10)`; temperature fixed in clients. Covered.
- Goal 2 (score every run with Judge + code metrics; citation audit flags coincidental correctness): Tasks 1-2 score PQ; `compute_deterministic_metrics` writes `citation_match` etc. Covered.
- Goal 3 (pace across days; commit after each run; resume from last written row): generation resumes via `get_completed_keys` (existing); judging resumes via `only_unscored` (Task 1-2); pacing via `max_cells` (Tasks 2-3, 5). Covered.
- Goal 4 (strict-$0 default): no infra added; `max_cells` + throttle keep it local/free. Covered.
- Evaluations 1-3 (crash-resume, throughput ceilings, all 900 present with scores): resume filter + pacing + existing backoff in `groq_client`. Covered; the "downgrade mismatched citations" interpretation is Phase 8 analysis, noted in Task 7.

**2. Placeholder scan:** No TBD/"handle edge cases"/"similar to Task N". Every code step has real code. One known typo to fix on implementation: the `run_benchmark.py` docstring opening ("resPphase") is corrected to "resources/specs Phase Plan Phase 7" when writing the file.

**3. Type consistency:** `get_judging_rows(db_path, source_set, *, only_unscored)` is defined in Task 1 and consumed identically in Task 2. `judge_rows(db_path, source_set, judge, *, max_cells, only_unscored)` defined in Task 2, consumed in Task 5 as `judge_rows(db_path, "PQ", judge, max_cells=...)`. `loop_executor.main(..., max_cells=...)` defined in Task 3, consumed in Task 5. `check_judge_model(db_path)` defined in Task 4, consumed in Task 5. Consistent.

---

## Notes for the implementer

- Run everything from `project/` (that is where `conftest.py` puts the import root). The shell working directory can reset between commands; prefer `cd project && uv run ...` in one line.
- Do not commit `graphify-out` except in Task 8, and only the repo-root one.
- Keep the two existing live-smoke tests skipped; never set `RUN_LIVE_GROQ_TESTS=1` in the default suite.
- No real `benchmark.db` access at any point in this plan.
